#!/bin/bash
# Run the test suite for the Hostaway Message Database application

set -e

# Determine the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Add the project root to PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Default values
CLIENT_ID=""
CLIENT_SECRET=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --client-id)
            CLIENT_ID="$2"
            shift
            shift
            ;;
        --client-secret)
            CLIENT_SECRET="$2"
            shift
            shift
            ;;
        *)
            echo "Unknown option: $key"
            exit 1
            ;;
    esac
done

# Check for required parameters
if [[ -z "$CLIENT_ID" || -z "$CLIENT_SECRET" ]]; then
    echo "Error: --client-id and --client-secret parameters are required"
    exit 1
fi

# Set up environment variables
export HOSTAWAY_CLIENT_ID="$CLIENT_ID"
export HOSTAWAY_CLIENT_SECRET="$CLIENT_SECRET"
export ENABLE_DRY_RUN=true  # Always use dry run for tests

# Run the tests
echo "Running test suite..."
pytest -v tests/

echo "Tests completed!" 