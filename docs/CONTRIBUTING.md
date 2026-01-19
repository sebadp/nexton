# Contributing to LinkedIn AI Agent

Thank you for your interest in contributing to LinkedIn AI Agent! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and collaborative environment.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or screenshots

### Suggesting Features

Feature suggestions are welcome! Please:
- Check existing issues to avoid duplicates
- Clearly describe the feature and its benefits
- Provide use cases and examples
- Consider implementation complexity

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/linkedin-ai-agent.git
   cd linkedin-ai-agent
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation as needed

4. **Run tests and linters**
   ```bash
   # Run tests
   pytest tests/ -v --cov=app
   
   # Format code
   black app/ tests/
   ruff check --fix app/ tests/
   
   # Type checking
   mypy app/
   
   # Security scan
   bandit -r app/
   ```

5. **Commit your changes**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
   
   Use conventional commit format:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `test:` - Test additions/changes
   - `refactor:` - Code refactoring
   - `perf:` - Performance improvements
   - `chore:` - Maintenance tasks

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   
   Then create a Pull Request on GitHub.

## Development Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Poetry (optional, for dependency management)

### Local Setup

1. **Clone and setup**
   ```bash
   git clone https://github.com/yourusername/linkedin-ai-agent.git
   cd linkedin-ai-agent
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

3. **Start dependencies**
   ```bash
   docker-compose up -d postgres redis ollama
   ```

4. **Run migrations**
   ```bash
   alembic upgrade head
   ```

5. **Run application**
   ```bash
   uvicorn app.main:app --reload
   ```

## Code Style Guidelines

### Python Style
- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use Ruff for linting
- Use MyPy for type checking
- Maximum function length: ~50 lines
- Maximum file length: ~500 lines

### Code Organization
```python
# Standard library imports
import os
from typing import Optional

# Third-party imports
from fastapi import FastAPI
from pydantic import BaseModel

# Local imports
from app.core.config import settings
```

### Docstrings
Use Google-style docstrings:
```python
def process_message(message: str, sender: str) -> dict:
    """Process a LinkedIn message.
    
    Args:
        message: The message text to process
        sender: Name of the message sender
        
    Returns:
        Dictionary containing analysis results
        
    Raises:
        ValueError: If message is empty
    """
    pass
```

### Type Hints
Always use type hints:
```python
def analyze_opportunity(
    message: str,
    sender: str,
    preferences: dict[str, Any]
) -> OpportunityAnalysis:
    pass
```

## Testing Guidelines

### Test Coverage
- Maintain **80%+ code coverage**
- Write tests for all new features
- Update tests when modifying existing code

### Test Types
- **Unit tests**: Test individual functions/classes
- **Integration tests**: Test component interactions
- **Performance tests**: Test system performance

### Test Structure
```python
def test_feature_name():
    """Test description."""
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result.status == "success"
```

### Running Tests
```bash
# All tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_cache.py -v

# Specific test
pytest tests/unit/test_cache.py::test_cache_set -v

# With debugging
pytest tests/ -v -s --pdb
```

## Documentation

### Code Documentation
- Add docstrings to all public functions, classes, and modules
- Keep docstrings up-to-date
- Include examples for complex functions

### User Documentation
- Update README.md for user-facing changes
- Add guides to `docs/guides/` for new features
- Update API documentation in `docs/API.md`

## Performance Considerations

- Profile code before optimizing
- Use async/await for I/O operations
- Implement caching for expensive operations
- Batch database queries when possible
- Use connection pooling

## Security Guidelines

- Never commit secrets or credentials
- Use environment variables for configuration
- Validate all user inputs with Pydantic
- Use parameterized queries (SQLAlchemy ORM)
- Scan dependencies regularly (`safety check`)
- Follow OWASP top 10 guidelines

## Review Process

### PR Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass and coverage is maintained
- [ ] Documentation is updated
- [ ] No secrets or sensitive data committed
- [ ] Security scan passes
- [ ] Performance impact considered
- [ ] Breaking changes documented

### Review Timeline
- Initial review within 2-3 business days
- Follow-up reviews within 1-2 business days
- Merges after approval from maintainer

## Release Process

1. Version bump in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release branch
4. Run full test suite
5. Create GitHub release with notes
6. Deploy to production (if applicable)

## Getting Help

- **Documentation**: Check [docs/](../docs/)
- **Issues**: Search existing issues first
- **Discussions**: Use GitHub Discussions for questions
- **Discord**: Join our Discord server (link in README)

## Recognition

Contributors will be:
- Listed in `CONTRIBUTORS.md`
- Mentioned in release notes
- Given credit in documentation

Thank you for contributing! 🎉
