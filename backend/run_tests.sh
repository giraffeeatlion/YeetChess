#!/bin/bash
# YeetChess Backend Test Runner

set -e

echo "🚀 Running YeetChess Backend Tests"
echo "=================================="

cd "$(dirname "$0")"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Run this script from the backend directory"
    exit 1
fi

# Install dependencies if needed
echo "📦 Installing dependencies..."
poetry install

# Run tests with coverage
echo "🧪 Running tests with coverage..."
poetry run pytest tests/ --cov=backend --cov-report=term-missing --cov-report=html

# Generate coverage report
echo "📊 Coverage report generated in htmlcov/"

# Optional: Run specific test categories
echo ""
echo "🎯 Quick test commands:"
echo "  poetry run pytest tests/test_auth.py -v    # Auth tests only"
echo "  poetry run pytest tests/test_games.py -v   # Game tests only"
echo "  poetry run pytest tests/ -k 'test_register'  # Specific test pattern"

echo ""
echo "✅ All tests completed successfully!"