#!/bin/bash
# Unix shell script to run tests

echo
echo "====================================="
echo "RAG Lab Test Runner (Unix/Linux/Mac)"
echo "====================================="
echo

# Get script directory (project root)
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/server:$PYTHONPATH"

# Change to project directory
cd "$PROJECT_ROOT"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed or not in PATH"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Load virtual environment if it exists
if [[ -f "server/venv/bin/activate" ]]; then
    echo "Activating virtual environment..."
    source server/venv/bin/activate
fi

# Check if pytest is installed
if ! $PYTHON_CMD -c "import pytest" &> /dev/null; then
    echo "WARNING: pytest is not installed. Installing..."
    $PYTHON_CMD -m pip install pytest pytest-asyncio
fi

# Run the test runner
$PYTHON_CMD run_tests.py "$@"

exit_code=$?

# Show results
if [[ $exit_code -eq 0 ]]; then
    echo
    echo "✅ All tests completed successfully!"
else
    echo
    echo "❌ Tests failed with exit code $exit_code"
fi

exit $exit_code