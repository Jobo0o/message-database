#!/bin/bash
set -e

# Start the cron service in the background
cron -f &

# Execute the command passed to this script (or the CMD in Dockerfile)
# This will be uvicorn src.api_v2.main:app --host 0.0.0.0 --port 8000
exec "$@"
