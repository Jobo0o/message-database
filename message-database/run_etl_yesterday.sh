#!/bin/bash
# Script to run the ETL process to retrieve messages from yesterday only

# Function to display usage instructions
usage() {
    echo "Usage: $0 --client-id ID --client-secret SECRET [OPTIONS]"
    echo ""
    echo "Required:"
    echo "  --client-id ID          Your Hostaway OAuth client ID"
    echo "  --client-secret SECRET  Your Hostaway OAuth client secret"
    echo ""
    echo "Options:"
    echo "  --mongodb-uri URI      MongoDB URI (default: mongodb://localhost:27017)"
    echo "  --dry-run              Run without saving to MongoDB"
    echo "  --help                 Display this help message"
    echo ""
    exit 1
}

# Parse command line arguments
MONGODB_URI="mongodb://localhost:27017"
DRY_RUN="False"

while [[ $# -gt 0 ]]; do
    case $1 in
        --client-id)
            CLIENT_ID="$2"
            shift 2
            ;;
        --client-secret)
            CLIENT_SECRET="$2"
            shift 2
            ;;
        --mongodb-uri)
            MONGODB_URI="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="True"
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate arguments
if [[ -z "$CLIENT_ID" || -z "$CLIENT_SECRET" ]]; then
    echo "Error: You must provide both client ID and client secret."
    usage
fi

# Export environment variables
export HOSTAWAY_CLIENT_ID="$CLIENT_ID"
export HOSTAWAY_CLIENT_SECRET="$CLIENT_SECRET"
export MONGODB_URI="$MONGODB_URI"
export ENABLE_DRY_RUN="$DRY_RUN"

echo "============================================"
echo "Running ETL process for messages from yesterday"
echo "============================================"
echo "OAuth Client ID: $CLIENT_ID"
echo "MongoDB URI: $MONGODB_URI"
echo "Dry Run Mode: $DRY_RUN"
echo "============================================"

# Run the ETL process with the days parameter set to 1 (yesterday)
python -m src.main etl --days 1 