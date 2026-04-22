#!/bin/bash

# Script to install git hooks
# Run this after cloning the repository

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "Installing git hooks..."

# Check if we're in a git repository
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "Error: Not a git repository. Please run 'git init' first."
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'HOOK_CONTENT'
#!/bin/bash

# Pre-commit hook to run frontend and backend tests
# This hook prevents commits if tests fail

set -e

echo "================================================"
echo "Running pre-commit tests..."
echo "================================================"

# Store the project root directory
PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# Track if any tests failed
TESTS_FAILED=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2 passed${NC}"
    else
        echo -e "${RED}✗ $2 failed${NC}"
        TESTS_FAILED=1
    fi
}

echo ""
echo -e "${YELLOW}Running Frontend Tests...${NC}"
echo "------------------------------------------------"

# Run frontend tests
cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install --silent
fi

# Run frontend tests
if npm run test 2>&1; then
    print_status 0 "Frontend tests"
else
    print_status 1 "Frontend tests"
fi

echo ""
echo -e "${YELLOW}Running Backend Tests...${NC}"
echo "------------------------------------------------"

# Run backend tests
cd "$PROJECT_ROOT/backend"

# Check if virtual environment exists and activate it
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
elif [ -d "venv" ]; then
    source "venv/bin/activate"
fi

# Install test dependencies if pytest is not available
if ! command -v pytest &> /dev/null; then
    echo "Installing test dependencies..."
    pip install -q pytest pytest-asyncio pytest-cov
fi

# Run backend tests
if python -m pytest 2>&1; then
    print_status 0 "Backend tests"
else
    print_status 1 "Backend tests"
fi

echo ""
echo "================================================"

# Final status
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! Proceeding with commit.${NC}"
    echo "================================================"
    exit 0
else
    echo -e "${RED}Tests failed! Commit aborted.${NC}"
    echo -e "${RED}Please fix the failing tests before committing.${NC}"
    echo "================================================"
    exit 1
fi
HOOK_CONTENT

# Make hook executable
chmod +x "$HOOKS_DIR/pre-commit"

echo "✓ Pre-commit hook installed successfully!"
echo ""
echo "The hook will run frontend and backend tests before each commit."
echo "To skip the hook (not recommended), use: git commit --no-verify"
