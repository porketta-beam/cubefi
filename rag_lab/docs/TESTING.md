# Testing Guide for RAG Lab

This document provides comprehensive information about the testing setup and procedures for the RAG Lab project.

## Test Structure

The project uses a centralized testing structure with all tests located in the `/tests` directory:

```
tests/
├── __init__.py           # Test module initialization and path setup
├── conftest.py          # Pytest configuration and shared fixtures
├── unit/                # Unit tests for individual components
│   ├── __init__.py
│   ├── test_document_service.py
│   └── test_config_endpoint.py
├── integration/         # Integration tests for API endpoints
│   ├── __init__.py
│   ├── test_api_endpoints.py
│   ├── test_api_quick.py
│   └── test_sync_add_apis.py
└── e2e/                # End-to-end tests for complete workflows
    ├── __init__.py
    └── test_rag_pipeline.py
```

## Running Tests

### Quick Start

```bash
# Run all tests (excluding e2e by default)
python run_tests.py

# Run with verbose output
python run_tests.py --verbose

# Run specific test categories
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --e2e

# Run all tests including e2e
python run_tests.py --all
```

### Platform-Specific Scripts

**Windows:**
```cmd
run_tests.bat
run_tests.bat --unit
run_tests.bat --coverage
```

**Unix/Linux/macOS:**
```bash
./run_tests.sh
./run_tests.sh --integration
./run_tests.sh --verbose
```

### Advanced Usage

```bash
# Run tests with coverage report
python run_tests.py --coverage

# Run tests in parallel (requires pytest-xdist)
python run_tests.py --parallel 4

# Run specific test file
python run_tests.py --file integration/test_api_endpoints.py

# Run tests matching pattern
python run_tests.py --pattern "test_upload"

# Run tests with specific markers
python run_tests.py --markers "not slow"

# Debug mode with PDB
python run_tests.py --debug

# Dry run (show what would be executed)
python run_tests.py --dry-run
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Test individual functions and classes in isolation
- Use mocks and stubs for dependencies
- Fast execution, high code coverage
- Examples: DocumentService, configuration validation

### Integration Tests (`tests/integration/`)
- Test API endpoints and component interactions
- Use TestClient for FastAPI testing
- Test database interactions and external services
- Examples: API endpoints, document upload/sync workflows

### End-to-End Tests (`tests/e2e/`)
- Test complete user workflows
- Test full system functionality
- Slower execution, comprehensive coverage
- Examples: Complete RAG pipeline, document lifecycle

## Test Fixtures and Utilities

### Shared Fixtures (in `conftest.py`)

- `project_root`: Project root directory path
- `server_root`: Server directory path
- `test_client`: FastAPI TestClient instance
- `temp_raw_data`: Temporary directory for test data
- `sample_pdf_content`: Sample PDF file content
- `sample_text_content`: Sample text file content
- `uploaded_pdf_file`: UploadFile object for PDF testing
- `uploaded_text_file`: UploadFile object for text testing

### Environment Setup

Tests automatically configure:
- Python path to include project and server directories
- Environment variables from `.env` file
- Temporary directories for isolated testing
- Mock external dependencies when needed

## Writing Tests

### Basic Test Structure

```python
import pytest
from fastapi.testclient import TestClient
from server.modules.fastapi_app import app

class TestMyFeature:
    def test_basic_functionality(self, test_client):
        response = test_client.get("/api/my-endpoint")
        assert response.status_code == 200
        assert "expected_value" in response.json()
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        # Test async code
        result = await some_async_function()
        assert result is not None
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
def test_api_endpoint():
    pass

@pytest.mark.e2e
def test_complete_workflow():
    pass

@pytest.mark.slow
def test_expensive_operation():
    pass

@pytest.mark.requires_server
def test_with_running_server():
    pass
```

### Mocking External Dependencies

```python
from unittest.mock import patch, MagicMock

@patch('server.modules.services.external_service.ExternalService')
def test_with_mocked_service(mock_service):
    mock_service.return_value.method.return_value = "mocked_result"
    # Test code here
```

## Configuration

### pytest.ini

The project includes a comprehensive pytest configuration:

- Test discovery patterns
- Markers for categorizing tests  
- Output formatting
- Async test support
- Coverage options (when enabled)
- Directory exclusions

### Test Dependencies

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

Key testing packages:
- `pytest`: Core testing framework
- `pytest-asyncio`: Async test support
- `pytest-cov`: Coverage reporting
- `pytest-xdist`: Parallel execution
- `httpx`: HTTP client for API testing
- `fastapi[testing]`: FastAPI testing utilities

## Continuous Integration

### GitHub Actions

The project can be configured with GitHub Actions for automated testing:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - run: pip install -r requirements-test.txt
    - run: python run_tests.py --all --coverage
```

## Test Data Management

### Temporary Data

Tests use temporary directories and files that are automatically cleaned up:
- `temp_raw_data` fixture provides isolated document storage
- ChromaDB uses temporary paths during testing
- All test data is automatically destroyed after tests complete

### Sample Data

Standard test data is provided via fixtures:
- Sample PDF content for document upload tests
- Sample text content for text processing tests
- Mock configurations for service testing

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `PYTHONPATH` includes project and server directories
2. **Permission Errors**: Check file permissions on test data directories
3. **Database Conflicts**: Tests use temporary databases to avoid conflicts
4. **Port Conflicts**: TestClient doesn't use actual ports

### Debug Mode

Use debug mode for troubleshooting:

```bash
python run_tests.py --debug
```

This enables:
- PDB debugger on failures
- Verbose output
- No output capture (print statements visible)

### Environment Variables

Set environment variables for testing:

```bash
export RAG_LAB_ENV=test
export LOG_LEVEL=DEBUG
python run_tests.py
```

## Migration from Old Structure

The tests have been migrated from scattered locations to this centralized structure:

- **Before**: Tests spread across `server/test_*.py` files
- **After**: Organized in `/tests/` with proper categories
- **Backup**: Old test files are preserved in `backup_old_tests/`

### Import Path Changes

Old imports:
```python
from modules.api.services.document_service import DocumentService
```

New imports:
```python
from server.modules.api.services.document_service import DocumentService
```

All test files have been updated with the correct import paths.

## Performance

### Speed Optimization

- Unit tests: < 1 second each
- Integration tests: < 5 seconds each  
- E2E tests: < 30 seconds each
- Parallel execution available for faster CI/CD

### Resource Usage

Tests are designed to be lightweight:
- Temporary databases prevent conflicts
- Minimal external dependencies
- Efficient cleanup of test resources
- Memory-conscious fixture design

---

For more information about specific test implementations, see the individual test files and their docstrings.