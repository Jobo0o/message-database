#!/bin/bash
# Script to run the Hostaway API tests

# Function to display usage instructions
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --client-id ID          OAuth client ID (required)"
    echo "  --client-secret SECRET  OAuth client secret (required)"
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

# Validate authentication parameters
if [[ -z "$CLIENT_ID" || -z "$CLIENT_SECRET" ]]; then
    echo "Error: You must provide both client ID and client secret."
    usage
fi

# Export environment variables
echo "Using OAuth client credentials authentication"
export HOSTAWAY_CLIENT_ID="$CLIENT_ID"
export HOSTAWAY_CLIENT_SECRET="$CLIENT_SECRET"

# Make the test scripts executable
chmod +x test_api.py
chmod +x test_api_params.py

echo "============================================"
echo "Running test_api_params.py to find correct format..."
echo "============================================"
./test_api_params.py

echo -e "\n\n"
echo "============================================"
echo "Running test_api.py to test client implementation..."
echo "============================================"
./test_api.py 