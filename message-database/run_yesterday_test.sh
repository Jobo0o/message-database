#!/bin/bash
# Script to run the yesterday messages test

# Function to display usage instructions
usage() {
    echo "Usage: $0 --client-id ID --client-secret SECRET"
    echo ""
    echo "Options:"
    echo "  --client-id ID          Your Hostaway OAuth client ID (required)"
    echo "  --client-secret SECRET  Your Hostaway OAuth client secret (required)"
    echo "  --help                  Display this help message"
    echo ""
    exit 1
}

# Parse command line arguments
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

# Run the test
echo "============================================"
echo "Running test to retrieve messages from yesterday"
echo "============================================"
./test_yesterday.py 