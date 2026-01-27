# Copilot Instructions

Guidelines for AI assistants working on this repository.

## Before Committing

Always run these checks before committing any code changes:

```bash
# Format code
python -m black src/azure_pricing_mcp/

# Lint code
python -m ruff check src/azure_pricing_mcp/

# Type checking
python -m mypy src/azure_pricing_mcp/ --ignore-missing-imports

# Run tests
python -m pytest tests/ -q
```

All checks must pass before pushing.

## Branch Strategy

1. **Never push directly to main** - Always create a new branch for changes
2. **Branch naming**: Use descriptive names like `feature/retirement-warnings` or `fix/mypy-errors`
3. **Create PRs**: After pushing a feature branch, create a pull request to merge into main

## Commit Messages

- No emojis in commit messages
- No em-dashes (use regular hyphens)
- Use clear, descriptive messages
- Format: `Short summary (50 chars or less)`

Example:
```
Add VM SKU retirement status warnings

- Add automatic retirement warnings for VM SKUs
- Fetch data dynamically from Microsoft docs
- Include migration guidance
```

## Code Style

- Follow PEP 8 guidelines
- Add type hints for all function parameters and return values
- Include docstrings for public functions
- Use `black` for formatting (line length 100)

## Version Updates

When adding significant features:
1. Update version in `pyproject.toml`
2. Update version in `src/azure_pricing_mcp/__init__.py`
3. Update version reference in `README.md` (Acknowledgments section)

## Documentation

When adding new features:
1. Update `README.md` with feature description
2. Update `USAGE_EXAMPLES.md` with usage examples
3. Update `docs/USAGE_EXAMPLES.md` (mirror of root file)
