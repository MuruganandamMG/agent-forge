# Coding Style Guide

<!-- Fill this in with YOUR coding conventions. This file is injected
     into every executor prompt exactly as-is. Be specific. -->

## Naming
- snake_case for functions, variables, modules
- PascalCase for classes
- UPPER_SNAKE_CASE for constants

## Imports
- stdlib first, then third-party, then local, separated by blank lines
- Use `from x import y` for specific items, `import x` for modules

## Typing
- Type-annotate all function signatures
- Use `X | None` instead of `Optional[X]`

## Error Handling
- Raise specific exceptions, never bare `except:`
- Include context in error messages

## Testing
- One test file per module: `tests/test_<module>.py`
- Use pytest, not unittest
- Group related tests in classes

## Formatting
- Line length: 99 characters (enforced by black)
- Single trailing newline in all files
