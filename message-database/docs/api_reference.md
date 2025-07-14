# API Reference

This document provides comprehensive documentation for all public APIs, functions, and components in the Hostaway Message Database application.

## Table of Contents

1. [API Client](#api-client)
2. [Database Operations](#database-operations)
3. [Data Models](#data-models)
4. [ETL Pipeline](#etl-pipeline)
5. [Configuration](#configuration)
6. [Utilities](#utilities)
7. [Scheduler](#scheduler)
8. [Command Line Interface](#command-line-interface)

---

## API Client

### HostawayClient

The `HostawayClient` class handles all communication with the Hostaway API, including authentication and data retrieval.

**Location**: `src/api/hostaway_client.py`

#### Constructor

```python
from api.hostaway_client import HostawayClient

client = HostawayClient()
```

**Description**: Initializes the Hostaway API client with configuration from environment variables.

**Configuration Required**:
- `HOSTAWAY_CLIENT_ID`: OAuth client ID
- `HOSTAWAY_CLIENT_SECRET`: OAuth client secret
- `HOSTAWAY_BASE_URL`: API base URL (default: https://api.hostaway.com/v1)

#### Methods

##### `get_messages(since_timestamp=None, limit=100, offset=0)`

Retrieves messages from the Hostaway API with pagination support.

**Parameters**:
- `since_timestamp` (str, optional): ISO format timestamp to filter messages
- `limit` (int): Maximum number of messages per request (default: 100)
- `offset` (int): Pagination offset (default: 0)

**Returns**: Dict containing API response with messages

**Example**:
```python
from api.hostaway_client import api_client

# Get recent messages
response = api_client.get_messages(
    since_timestamp="2023-01-01T00:00:00",
    limit=50
)

messages = response.get("result", [])
print(f"Retrieved {len(messages)} messages")
```

##### `get_all_messages(since_timestamp=None)`

Generator that yields all messages from the API using automatic pagination.

**Parameters**:
- `since_timestamp` (str, optional): ISO format timestamp to filter messages

**Yields**: Individual message dictionaries

**Example**:
```python
from api.hostaway_client import api_client

# Process all messages since yesterday
for message in api_client.get_all_messages("2023-12-01T00:00:00"):
    print(f"Processing message {message.get('id')}")
    # Process each message
```

##### `get_property_details(property_id)`

Retrieves detailed information for a specific property.

**Parameters**:
- `property_id` (str): The Hostaway property ID

**Returns**: Dict containing property details

**Example**:
```python
property_details = api_client.get_property_details("12345")
print(f"Property: {property_details.get('name')}")
```

##### `get_reservation_details(reservation_id)`

Retrieves detailed information for a specific reservation.

**Parameters**:
- `reservation_id` (str): The Hostaway reservation ID

**Returns**: Dict containing reservation details

**Example**:
```python
reservation = api_client.get_reservation_details("67890")
print(f"Total price: {reservation.get('totalPrice')}")
```

##### `get_conversation_messages(conversation_id)`

Retrieves all messages for a specific conversation.

**Parameters**:
- `conversation_id` (str): The Hostaway conversation ID

**Returns**: List of message dictionaries

**Example**:
```python
messages = api_client.get_conversation_messages("conv123")
for msg in messages:
    print(f"Message: {msg.get('body')}")
```

#### Exceptions

##### `HostawayAPIError`

Raised when API requests fail or return errors.

**Example**:
```python
from api.hostaway_client import api_client, HostawayAPIError

try:
    messages = api_client.get_messages()
except HostawayAPIError as e:
    print(f"API error: {e}")
```

---

## Database Operations

### MongoDB

The `MongoDB` class manages all database connections and operations for storing messages.

**Location**: `src/database/mongodb.py`

#### Constructor

```python
from database.mongodb import MongoDB

db = MongoDB()
```

#### Methods

##### `connect(max_retries=3, retry_delay=5)`

Establishes connection to MongoDB with retry mechanism.

**Parameters**:
- `max_retries` (int): Maximum connection attempts (default: 3)
- `retry_delay` (int): Seconds between retries (default: 5)

**Returns**: bool - True if successful, False otherwise

**Example**:
```python
from database.mongodb import db

if db.connect():
    print("Successfully connected to MongoDB")
else:
    print("Failed to connect to MongoDB")
```

##### `disconnect()`

Closes the MongoDB connection.

**Example**:
```python
db.disconnect()
print("Disconnected from MongoDB")
```

##### `insert_message(message_data)`

Inserts or updates a message in the database using upsert operation.

**Parameters**:
- `message_data` (dict): Dictionary representation of a message

**Returns**: bool - True if successful, False otherwise

**Example**:
```python
message_data = {
    "message_id": "msg123",
    "content": "Hello, guest!",
    "timestamp": datetime.now(),
    # ... other fields
}

success = db.insert_message(message_data)
if success:
    print("Message inserted successfully")
```

##### `get_latest_message_timestamp()`

Retrieves the timestamp of the most recent message in the database.

**Returns**: Optional[str] - ISO format timestamp or None

**Example**:
```python
latest = db.get_latest_message_timestamp()
if latest:
    print(f"Latest message timestamp: {latest}")
else:
    print("No messages found in database")
```

##### `count_messages()`

Returns the total number of messages in the collection.

**Returns**: int - Number of messages

**Example**:
```python
count = db.count_messages()
print(f"Total messages in database: {count}")
```

---

## Data Models

### Message Model

The core data model representing a communication message.

**Location**: `src/models/message.py`

#### Message

```python
from models.message import Message

class Message(BaseModel):
    message_id: str
    property: Property
    guest: Guest
    content: str
    timestamp: datetime
    direction: str  # "incoming" or "outgoing"
    reservation: Optional[Reservation] = None
    message_type: str  # "automated" or "manual"
    created_at: datetime
    updated_at: datetime
```

**Methods**:

##### `to_dict()`

Converts the model to a MongoDB-compatible dictionary.

**Returns**: Dict[str, Any]

**Example**:
```python
message = Message(
    message_id="msg123",
    property=Property(id="prop1", name="Beach House"),
    guest=Guest(name="John Doe"),
    content="Thank you for staying with us!",
    timestamp=datetime.now(),
    direction="outgoing",
    message_type="manual"
)

message_dict = message.to_dict()
# Ready for MongoDB insertion
```

##### `from_api_response(api_data)` (classmethod)

Creates a Message instance from raw Hostaway API data.

**Parameters**:
- `api_data` (dict): Raw API response data

**Returns**: Message instance

**Example**:
```python
api_data = {
    "id": "123",
    "content": "Hello!",
    "propertyId": "prop1",
    "guestName": "Jane Smith",
    # ... other API fields
}

message = Message.from_api_response(api_data)
```

#### Property

```python
class Property(BaseModel):
    id: str
    name: str
```

#### Guest

```python
class Guest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    nationality: Optional[str] = None
```

#### Reservation

```python
class Reservation(BaseModel):
    id: str
    price: Optional[Decimal] = None
```

---

## ETL Pipeline

### ETLPipeline

The main Extract, Transform, Load pipeline for processing messages.

**Location**: `src/pipeline/etl.py`

#### Constructor

```python
from pipeline.etl import ETLPipeline

pipeline = ETLPipeline()
```

#### Methods

##### `extract_transform_load(since_timestamp=None)`

Runs the complete ETL process.

**Parameters**:
- `since_timestamp` (str, optional): Process only messages after this timestamp

**Returns**: bool - True if successful, False otherwise

**Example**:
```python
from pipeline.etl import pipeline

# Process all new messages
success = pipeline.extract_transform_load()

# Process messages since specific date
success = pipeline.extract_transform_load("2023-12-01T00:00:00")

if success:
    print(f"ETL completed successfully. Processed {pipeline.processed_count} messages")
else:
    print(f"ETL completed with {pipeline.error_count} errors")
```

**Process Flow**:
1. Validates configuration
2. Connects to MongoDB
3. Fetches conversations from Hostaway API
4. For each conversation, fetches individual messages
5. Transforms each message to standard format
6. Loads messages into MongoDB
7. Reports completion statistics

---

## Configuration

Configuration management for the application.

**Location**: `src/config.py`

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `HOSTAWAY_CLIENT_ID` | OAuth client ID | Yes | - |
| `HOSTAWAY_CLIENT_SECRET` | OAuth client secret | Yes | - |
| `HOSTAWAY_BASE_URL` | API base URL | No | https://api.hostaway.com/v1 |
| `MONGODB_URI` | MongoDB connection string | Yes | - |
| `MONGODB_DATABASE` | Database name | No | hostaway_messages |
| `MONGODB_COLLECTION` | Collection name | No | messages |
| `LOG_LEVEL` | Logging level | No | INFO |
| `LOG_DIR` | Log directory path | No | ./logs |
| `API_REQUEST_DELAY` | Delay between API requests | No | 1.0 |
| `ENABLE_DRY_RUN` | Enable dry run mode | No | False |
| `NOTIFICATION_EMAIL` | Email for notifications | No | - |

### Functions

##### `validate_config()`

Validates that all required configuration is available.

**Raises**: ValueError if required variables are missing

**Example**:
```python
from config import validate_config

try:
    validate_config()
    print("Configuration is valid")
except ValueError as e:
    print(f"Configuration error: {e}")
```

---

## Utilities

### Logger

Logging utilities and error notification system.

**Location**: `src/utils/logger.py`

#### Functions

##### `setup_logging(name="hostaway_message_db")`

Sets up logging with both file and console handlers.

**Parameters**:
- `name` (str): Logger name

**Returns**: logging.Logger - Configured logger instance

**Example**:
```python
from utils.logger import setup_logging

logger = setup_logging("my_app")
logger.info("Application started")
```

##### `send_error_notification(subject, message)`

Sends error notification email if configured.

**Parameters**:
- `subject` (str): Email subject
- `message` (str): Email body

**Example**:
```python
from utils.logger import send_error_notification

send_error_notification(
    "ETL Process Failed",
    "The ETL process encountered an error and stopped."
)
```

---

## Scheduler

### Daily Job

Automated scheduling for regular ETL runs.

**Location**: `src/scheduler/daily_job.py`

#### Functions

##### `run_daily_job()`

Executes the daily ETL job with error handling and notifications.

**Example**:
```python
from scheduler.daily_job import run_daily_job

# Run the daily job (typically called by cron)
run_daily_job()
```

**Cron Setup**:
```bash
# Add to crontab for daily execution at 1:00 AM
0 1 * * * cd /path/to/message-database && python -m scheduler.daily_job
```

---

## Command Line Interface

### Main CLI

Command-line interface for manual ETL execution.

**Location**: `src/main.py`

#### Usage

```bash
# Run ETL for all messages
python -m main etl

# Run ETL for messages since specific date
python -m main etl --since 2023-01-01T00:00:00

# Run ETL for messages from last 5 days
python -m main etl --days 5
```

#### Functions

##### `main()`

Main entry point for CLI application.

**Example**:
```python
from main import main
import sys

# Programmatic usage
sys.argv = ['main.py', 'etl', '--days', '1']
main()
```

---

## Complete Usage Examples

### Basic ETL Workflow

```python
from api.hostaway_client import api_client
from database.mongodb import db
from pipeline.etl import pipeline
from utils.logger import setup_logging

# Set up logging
logger = setup_logging()

# Run complete ETL process
success = pipeline.extract_transform_load("2023-12-01T00:00:00")

if success:
    logger.info("ETL process completed successfully")
else:
    logger.error("ETL process failed")
```

### Custom Message Processing

```python
from api.hostaway_client import api_client
from models.message import Message
from database.mongodb import db

# Connect to database
db.connect()

# Fetch and process messages manually
for conversation in api_client.get_all_messages():
    conversation_id = conversation.get("id")
    messages = api_client.get_conversation_messages(conversation_id)
    
    for msg_data in messages:
        # Transform to Message object
        message = Message.from_api_response(msg_data)
        
        # Insert to database
        db.insert_message(message.to_dict())

db.disconnect()
```

### Error Handling Best Practices

```python
from api.hostaway_client import api_client, HostawayAPIError
from database.mongodb import db
from utils.logger import logger, send_error_notification

try:
    # Connect to database
    if not db.connect():
        raise Exception("Failed to connect to MongoDB")
    
    # Fetch messages
    messages = api_client.get_all_messages()
    
    # Process messages
    for message in messages:
        # Your processing logic here
        pass
        
except HostawayAPIError as e:
    logger.error(f"API error: {e}")
    send_error_notification("API Error", str(e))
    
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    send_error_notification("System Error", str(e))
    
finally:
    db.disconnect()
```

---

## Error Handling

All components include comprehensive error handling:

- **API Errors**: `HostawayAPIError` for API-related issues
- **Database Errors**: MongoDB connection and operation errors
- **Configuration Errors**: Missing or invalid configuration
- **Data Validation Errors**: Pydantic model validation errors

## Performance Considerations

- **API Rate Limiting**: Built-in request delays to respect API limits
- **Database Indexing**: Automatic index creation for optimal query performance
- **Memory Management**: Generator-based message processing for large datasets
- **Connection Pooling**: Efficient MongoDB connection management

## Security Features

- **OAuth 2.0**: Secure API authentication with automatic token refresh
- **TLS/SSL**: Encrypted database connections
- **Environment Variables**: Secure credential management
- **Input Validation**: Pydantic models ensure data integrity