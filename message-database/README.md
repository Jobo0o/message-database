# Hostaway Message Database

A utility for retrieving, processing, and storing messages from the Hostaway API to MongoDB.

## Overview

This application provides an ETL (Extract, Transform, Load) pipeline for Hostaway messages. It retrieves messages from the Hostaway API, processes them, and stores them in MongoDB for analysis and querying.

## Requirements

- Python 3.8+
- MongoDB 4.4+
- Hostaway API credentials (OAuth client ID and secret)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd message-database
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration:
```
# Hostaway API Configuration
HOSTAWAY_CLIENT_ID=your_client_id
HOSTAWAY_CLIENT_SECRET=your_client_secret
HOSTAWAY_BASE_URL=https://api.hostaway.com/v1

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=hostaway_messages
MONGODB_COLLECTION=messages

# Application Settings
API_REQUEST_DELAY=1.0
ENABLE_DRY_RUN=false
```

## Usage

### Running the ETL Process

To run the ETL process and retrieve all messages since a specific date:

```bash
python -m src.main etl --since 2023-01-01T00:00:00
```

To retrieve messages from a specific number of days ago:

```bash
python -m src.main etl --days 5
```

### Convenience Scripts

Several convenience scripts are provided:

#### Retrieving Messages from Yesterday

```bash
./run_etl_yesterday.sh --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

Options:
- `--mongodb-uri URI` - Specify a custom MongoDB URI
- `--dry-run` - Run in dry-run mode without saving to MongoDB

#### Testing the API Connection

```bash
./run_tests.sh --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

#### Testing Yesterday's Messages

```bash
./run_yesterday_test.sh --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

### Setting Up a Daily Job

To set up a daily cron job to retrieve new messages:

```bash
# Edit your crontab
crontab -e

# Add a line to run the job at 1:00 AM every day
0 1 * * * cd /path/to/message-database && ./daily_job.py
```

## Authentication

This application uses OAuth 2.0 client credentials flow to authenticate with the Hostaway API. See the [authentication documentation](docs/authentication.md) for more details.

## License

[Specify your license here] 