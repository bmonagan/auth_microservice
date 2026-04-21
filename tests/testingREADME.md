# Test Suite Documentation

This directory contains a comprehensive test suite for the authentication microservice.

## Overview

The test suite is organized into logical modules covering:

- **test_app.py**: API structure, documentation, and health checks
- **test_auth.py**: Authentication endpoints (register, login)
- **test_users.py**: Protected user profile endpoints and session management
- **test_jwt.py**: Token generation, encoding, and validation
- **test_auth_helpers.py**: Password hashing and dependency injection
- **conftest.py**: Pytest fixtures and configuration
- **test_utils.py**: Helper functions for tests

## Running Tests

### Run all tests
```bash
uv run pytest
```

### Run tests with verbose output
```bash
uv run pytest -v
```

### Run a specific test file
```bash
uv run pytest tests/test_auth.py -v
```

### Run a specific test class
```bash
uv run pytest tests/test_auth.py::TestRegister -v
```

### Run a specific test function
```bash
uv run pytest tests/test_auth.py::TestRegister::test_register_success -v
```

### Run tests matching a pattern
```bash
uv run pytest -k "register" -v
```

### Run with coverage report
```bash
uv run pytest --cov=src --cov-report=html
```

Then open `htmlcov/index.html` to view coverage.

## Test Organization

### Fixtures (conftest.py)

- **test_db**: In-memory SQLite database for each test (auto-cleanup)
- **client**: FastAPI TestClient bound to test database
- **test_user**: Pre-created test user in database
- **auth_headers**: Authorization headers with valid access token

### Test Categories

#### Authentication Tests (test_auth.py)
- User registration with validation
- Password strength requirements
- Email validation
- Duplicate email handling
- User login with credentials
- Token generation and persistence
- Edge cases (invalid input, weak passwords)

#### User Profile Tests (test_users.py)
- Retrieve current user profile
- Update email address
- Change password
- Delete account
- Session management (list, revoke)
- Authorization and authentication checks

#### JWT Token Tests (test_jwt.py)
- Access token creation and payload
- Refresh token creation and payload
- Token expiration times
- Token decoding and validation
- Invalid/expired token handling
- Token type validation
- Secret key validation

#### Auth Helpers Tests (test_auth_helpers.py)
- Password hashing with salt
- Password verification
- Case sensitivity
- Empty password handling
- Current user dependency resolution
- Token type validation in routes

#### API Structure Tests (test_app.py)
- OpenAPI specification availability
- Swagger UI and ReDoc documentation
- Endpoint documentation
- API info and metadata
- 404 error handling
- No 500 errors on invalid requests

## Writing New Tests

### Basic Test Structure
```python
class TestFeatureName:
    """Descriptive docstring about what's being tested."""
    
    def test_specific_behavior(self, client, test_user):
        """Test description as docstring."""
        # Arrange
        response = client.post("/endpoint", json={...})
        
        # Assert
        assert response.status_code == 200
```

### Using Fixtures
```python
def test_with_auth(self, client, auth_headers, test_user):
    """Test that requires authentication."""
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
```

### Using Test Database
```python
def test_database_operation(self, client, test_db, test_user):
    """Test with direct database access."""
    from src.models import User
    
    # Verify user in database
    user = test_db.query(User).filter(User.id == test_user.id).first()
    assert user is not None
```

## Test Markers

Mark tests to categorize them:

```python
@pytest.mark.auth
def test_login():
    ...

@pytest.mark.slow
def test_heavy_computation():
    ...
```

Run tests by marker:
```bash
uv run pytest -m auth -v
uv run pytest -m "not slow" -v
```

Available markers:
- `auth`: Authentication tests
- `users`: User profile tests
- `jwt`: JWT token tests
- `hashing`: Password hashing tests
- `integration`: Integration tests
- `unit`: Unit tests
- `slow`: Long-running tests

## Coverage Goals

Current coverage should be >85% of core authentication logic.

Key areas to maintain coverage:
- All endpoint handlers
- Authentication/authorization checks
- Password hashing and verification
- Token generation and validation
- Error handling paths

## Common Issues

### Database Lock Errors
If you see "database is locked", check if you have a server running (`./scripts/dev.sh`). Stop it before running tests.

### Import Errors
Ensure you're running tests with `uv run pytest`, not bare `pytest`.

### Fixture Not Found
Make sure `conftest.py` is in the `tests/` directory. Pytest discovers it automatically.

## Debugging Tests

### Run with pdb breakpoint
```python
def test_something(self, client):
    breakpoint()  # Execution pauses here
    response = client.get("/endpoint")
```

Run tests with immediate output:
```bash
uv run pytest -s
```

Show local variables on failure:
```bash
uv run pytest -l
```

## CI/CD Integration

This test suite is designed to run in CI/CD pipelines:

```bash
# Run all tests with coverage
uv run pytest --cov=src --cov-report=xml

# Fail if coverage drops below threshold
uv run pytest --cov=src --cov-fail-under=80
```

## Performance

- Full test suite completes in <5 seconds
- Each test runs in isolation with its own database
- No external dependencies required (uses in-memory SQLite)
