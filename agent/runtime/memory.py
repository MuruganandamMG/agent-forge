"""ChromaDB wrapper: store(), retrieve(), reflect()."""

import json
import uuid

try:
    import chromadb
except Exception:
    chromadb = None

from runtime.models import chat


class Memory:
    """Persistent memory backed by ChromaDB with sessions and reflections."""

    def __init__(self, persist_dir: str) -> None:
        if chromadb is None:
            raise ImportError("ChromaDB is not available in this environment")
        self.client = chromadb.PersistentClient(path=persist_dir)
        self._sessions = self.client.get_or_create_collection("sessions")
        self._reflections = self.client.get_or_create_collection("reflections")

    def _collection(self, name: str) -> "chromadb.Collection":
        if name == "sessions":
            return self._sessions
        elif name == "reflections":
            return self._reflections
        raise ValueError(f"Unknown collection: {name}")

    def store_session(
        self, query: str, result: str, metadata: dict | None = None
    ) -> str:
        """Store a raw task + result pair in the sessions collection."""
        doc_id = str(uuid.uuid4())
        document = f"QUERY: {query}\nRESULT: {result}"
        kwargs: dict = {
            "ids": [doc_id],
            "documents": [document],
        }
        if metadata:
            kwargs["metadatas"] = [metadata]
        self._sessions.add(**kwargs)
        return doc_id

    def store_reflection(self, reflection: dict) -> str:
        """Store a distilled reflection document."""
        doc_id = str(uuid.uuid4())
        document = json.dumps(reflection, indent=2)
        metadata = {
            "confidence": reflection.get("confidence", "unknown"),
            "tags": ",".join(reflection.get("tags", [])),
        }
        self._reflections.add(
            ids=[doc_id],
            documents=[document],
            metadatas=[metadata],
        )
        return doc_id

    def retrieve(
        self, query: str, collection: str = "sessions", n_results: int = 5
    ) -> list[dict]:
        """Retrieve the most relevant documents from a collection."""
        coll = self._collection(collection)
        if coll.count() == 0:
            return []
        n = min(n_results, coll.count())
        results = coll.query(query_texts=[query], n_results=n)
        docs = []
        for i, doc in enumerate(results["documents"][0]):
            entry: dict = {"document": doc}
            if results["metadatas"] and results["metadatas"][0]:
                entry["metadata"] = results["metadatas"][0][i]
            docs.append(entry)
        return docs

    def reflect(self, task_description: str, result: str) -> dict:
        """Generate a reflection summary using the model, then store it."""
        prompt = (
            "Analyze this completed coding task and produce a JSON reflection.\n\n"
            f"TASK: {task_description}\n"
            f"RESULT: {result}\n\n"
            "OUTPUT FORMAT — JSON only:\n"
            '{"problem": "", "cause": "", "solution": "", "confidence": "high|medium|low", '
            '"tags": ["tag1", "tag2"]}'
        )
        response = chat(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        try:
            reflection = json.loads(response.strip())
        except json.JSONDecodeError:
            reflection = {
                "problem": task_description,
                "cause": "unknown",
                "solution": result,
                "confidence": "low",
                "tags": [],
            }

        self.store_reflection(reflection)
        return reflection
