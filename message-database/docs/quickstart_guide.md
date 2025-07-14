# Quickstart Guide

This guide will help you get the Hostaway Message Database application up and running quickly.

## Prerequisites

- Python 3.8 or higher
- MongoDB 4.4 or higher
- Hostaway API credentials (OAuth client ID and secret)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd message-database
```

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Hostaway API Configuration
HOSTAWAY_CLIENT_ID=your_client_id_here
HOSTAWAY_CLIENT_SECRET=your_client_secret_here
HOSTAWAY_BASE_URL=https://api.hostaway.com/v1

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=hostaway_messages
MONGODB_COLLECTION=messages

# Application Settings
API_REQUEST_DELAY=1.0
ENABLE_DRY_RUN=false
LOG_LEVEL=INFO
LOG_DIR=./logs
```

### 4. Set Up MongoDB

#### Option A: Local MongoDB Installation

1. Install MongoDB following the [official installation guide](https://docs.mongodb.com/manual/installation/)
2. Start MongoDB service
3. Create a database (optional - will be created automatically)

#### Option B: MongoDB Atlas (Cloud)

1. Create a MongoDB Atlas account
2. Create a cluster
3. Get connection string and update `MONGODB_URI` in `.env`

Example MongoDB Atlas connection string:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/hostaway_messages?retryWrites=true&w=majority
```

## Quick Start

### Test Configuration

First, verify your configuration is correct:

```bash
python -c "from src.config import validate_config; validate_config(); print('Configuration is valid!')"
```

### Run Your First ETL

Run the ETL process to fetch and store messages:

```bash
# Fetch messages from the last 5 days
python -m src.main etl --days 5
```

### Verify Data

Check that messages were stored successfully:

```python
from src.database.mongodb import db

# Connect and check message count
db.connect()
count = db.count_messages()
print(f"Total messages in database: {count}")
db.disconnect()
```

## Common Usage Patterns

### 1. Daily ETL Process

Set up a daily job to automatically fetch new messages:

```bash
# Add to crontab for daily execution at 1:00 AM
crontab -e

# Add this line:
0 1 * * * cd /path/to/message-database && /path/to/python -m src.scheduler.daily_job
```

### 2. Manual ETL with Date Range

```bash
# Fetch messages since specific date
python -m src.main etl --since 2024-01-01T00:00:00
```

### 3. Dry Run Mode

Test your configuration without actually storing data:

```bash
# Set ENABLE_DRY_RUN=true in .env file, then run:
python -m src.main etl --days 1
```

### 4. Custom Processing Script

Create a custom script for specific processing needs:

```python
# custom_processor.py
from src.api.hostaway_client import api_client
from src.database.mongodb import db
from src.models.message import Message

# Connect to database
db.connect()

# Process messages with custom logic
for conversation in api_client.get_all_messages("2024-01-01T00:00:00"):
    conversation_id = conversation.get("id")
    messages = api_client.get_conversation_messages(conversation_id)
    
    for msg_data in messages:
        # Your custom processing logic here
        if "urgent" in msg_data.get("body", "").lower():
            print(f"Found urgent message: {msg_data.get('id')}")
            
        # Store in database
        message = Message.from_api_response(msg_data)
        db.insert_message(message.to_dict())

db.disconnect()
```

## Using the Scripts

The project includes several convenience scripts in the `scripts/` directory:

### Run ETL for Yesterday's Messages

```bash
./scripts/run_etl_yesterday.sh --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

### Test API Connection

```bash
./scripts/run_tests.sh --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

### Test Yesterday's Messages

```bash
./scripts/run_yesterday_test.sh --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

## Development Setup

### Install in Development Mode

```bash
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api_client.py

# Run with coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Monitoring and Logging

### Log Files

Logs are stored in the `logs/` directory with daily rotation:
```
logs/
  2024-01-15.log
  2024-01-16.log
  ...
```

### Log Levels

Configure logging level in `.env`:
```bash
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Error Notifications

Set up email notifications for errors:
```bash
NOTIFICATION_EMAIL=admin@yourdomain.com
```

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check MongoDB service is running
   - Verify connection string in `.env`
   - Check firewall settings

2. **Hostaway API Authentication Failed**
   - Verify client ID and secret
   - Check API endpoint URL
   - Ensure credentials have proper permissions

3. **No Messages Retrieved**
   - Check date range parameters
   - Verify API has messages for the specified period
   - Check API rate limiting

### Debug Mode

Enable detailed logging for troubleshooting:
```bash
LOG_LEVEL=DEBUG
```

### Dry Run Testing

Test without affecting production data:
```bash
ENABLE_DRY_RUN=true
```

## Next Steps

1. **Schedule Regular ETL**: Set up cron jobs for automated processing
2. **Monitor Performance**: Review logs and optimize as needed
3. **Customize Processing**: Extend the ETL pipeline for specific requirements
4. **Set Up Alerting**: Configure email notifications for errors
5. **Scale Up**: Consider horizontal scaling for large message volumes

## Additional Resources

- [API Reference](api_reference.md) - Complete API documentation
- [Architecture](architecture.md) - System architecture overview
- [Deployment](deployment.md) - Production deployment guide
- [ETL Pipeline](etl_pipeline.md) - Detailed ETL process documentation

## Support

For additional help:
1. Check the logs in the `logs/` directory
2. Review the troubleshooting section
3. Consult the API reference documentation
4. Check the GitHub issues for similar problems