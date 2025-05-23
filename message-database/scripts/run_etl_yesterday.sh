#!/bin/bash
# Run the ETL process for yesterday's messages

set -e

# Determine the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Add the project root to PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Default values
MONGODB_URI=""
CLIENT_ID=""
CLIENT_SECRET=""
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --mongodb-uri)
            MONGODB_URI="$2"
            shift
            shift
            ;;
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
        --dry-run)
            DRY_RUN=true
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

if [[ -n "$MONGODB_URI" ]]; then
    export MONGODB_URI="$MONGODB_URI"
fi

if [[ "$DRY_RUN" == true ]]; then
    export ENABLE_DRY_RUN=true
fi

# Run the ETL process
echo "Running ETL process for yesterday's messages..."
python -m message_database.main etl --days 1

echo "ETL process completed!" 