import pytest
from runtime.providers.base import BaseProvider

def test_base_provider_abstract():
    class IncompleteProvider(BaseProvider):
        pass
    
    with pytest.raises(TypeError):
        IncompleteProvider()
