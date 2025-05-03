# ETL Pipeline Documentation

This document provides detailed information about the Extract, Transform, Load (ETL) pipeline used in the Hostaway Message Database application.

## Overview

The ETL pipeline is responsible for:

1. Extracting message data from the Hostaway API
2. Transforming the data into a consistent, structured format
3. Loading the processed data into MongoDB
4. Handling incremental updates to keep the database in sync with the Hostaway system

## Pipeline Components

### 1. Extract Phase

**Purpose:** Retrieve raw message data from the Hostaway API.

**Implementation:** The extract phase is implemented in the `api/hostaway_client.py` module, which handles:

- API authentication using the Hostaway API key
- Pagination to handle large data sets
- Rate limiting to avoid overwhelming the API
- Error handling and retries for resilience

**Key Methods:**
- `get_messages()` - Retrieves a batch of messages with pagination
- `get_all_messages()` - Iterator that yields all messages, handling pagination automatically

**Configuration Options:**
- `API_REQUEST_DELAY` - Delay between API requests (default: 1.0 seconds)
- `ENABLE_DRY_RUN` - Run in test mode without actual API calls

**Example:**
```python
# Get all messages since a specific timestamp
messages = api_client.get_all_messages(since_timestamp="2023-01-01T00:00:00")
for message in messages:
    process_message(message)
```

### 2. Transform Phase

**Purpose:** Convert raw API data into a structured format suitable for storage and analysis.

**Implementation:** The transform phase is implemented in the `models/message.py` and `pipeline/etl.py` modules, which handle:

- Data validation using Pydantic models
- Data cleaning and normalization
- Type conversion
- Enrichment with additional data where needed

**Key Methods:**
- `Message.from_api_response()` - Creates a structured Message object from raw API data
- `_transform_message()` - Transforms raw API data, including enrichment with property and reservation details

**Data Enrichment:**
The transform phase may make additional API calls to enrich the message data:
- If a property ID is present but the name is missing, it fetches property details
- If a reservation ID is present, it fetches reservation details for pricing information

**Example:**
```python
# Transform a raw message from the API
raw_message = api_client.get_messages()["result"][0]
message = Message.from_api_response(raw_message)
message_dict = message.to_dict()  # Prepare for MongoDB storage
```

### 3. Load Phase

**Purpose:** Store the processed data in MongoDB for future analysis.

**Implementation:** The load phase is implemented in the `database/mongodb.py` module, which handles:

- MongoDB connection management
- Collection and index creation
- Upsert operations to avoid duplicates
- Transaction management for data consistency

**Key Methods:**
- `connect()` - Establishes a connection to MongoDB with retry logic
- `insert_message()` - Inserts a message into MongoDB with upsert semantics
- `get_latest_message_timestamp()` - Retrieves the most recent message timestamp for incremental updates

**Indexing Strategy:**
The load phase creates the following indexes to optimize query performance:
- Text index on message content for full-text search
- Compound index on property ID and timestamp
- Compound index on guest nationality and timestamp
- Unique index on message ID to prevent duplicates

**Example:**
```python
# Load a processed message into MongoDB
db.connect()
db.insert_message(message_dict)
db.disconnect()
```

## Complete Pipeline Execution

The entire ETL pipeline is orchestrated by the `pipeline/etl.py` module, which integrates all three phases:

1. First, it validates the configuration
2. Then, it connects to MongoDB
3. For incremental updates, it gets the latest message timestamp
4. It extracts messages from the API (with incremental filtering if applicable)
5. For each message, it:
   - Transforms the message into the structured format
   - Loads it into MongoDB
6. Finally, it logs completion statistics and disconnects

**Key Methods:**
- `extract_transform_load()` - Runs the complete ETL process
- `_process_message()` - Processes a single message through transform and load phases

**Error Handling:**
The pipeline includes comprehensive error handling:
- API connection errors with retry logic
- MongoDB connection errors with retry logic
- Individual message processing errors (which don't stop the entire pipeline)
- Detailed logging of all errors
- Email notifications for critical failures

## Incremental Updates

The pipeline supports efficient incremental updates to avoid processing the same data multiple times:

1. It retrieves the timestamp of the most recent message in the database
2. It queries the API for only messages since that timestamp
3. It processes and stores only the new messages
4. If no timestamp is available (first run), it processes all messages

This approach minimizes API calls and processing time for regular updates.

## Scheduler Integration

The ETL pipeline is designed to be run on a schedule:

- The daily job in `scheduler/daily_job.py` calls the ETL pipeline at 1:00 AM UTC
- The job handles error notifications and logging
- The `daily_job.py` script in the project root provides a simple entry point for cron

## Testing the Pipeline

The ETL pipeline includes comprehensive tests:

- Unit tests for each component
- Integration tests for the complete pipeline
- Mock objects for API and database to enable testing without external dependencies

## Performance Considerations

The pipeline is designed for efficiency:

- API requests are batched to minimize network overhead
- MongoDB operations use upsert to handle both new and updated messages
- Indexes are created to optimize query performance
- The pipeline processes messages in a streaming fashion to minimize memory usage

## Monitoring and Troubleshooting

To monitor the pipeline:

- Check the daily log files in the `logs` directory
- Review the MongoDB collection to verify data is being stored correctly
- Monitor the cron job logs for automated runs

Common issues:
- API authentication failures
- MongoDB connection issues
- Rate limiting by the Hostaway API
- Data format changes in the API response

## Future Enhancements

Planned enhancements to the ETL pipeline:

- Parallel processing for faster extraction of large message volumes
- More sophisticated data enrichment with additional Hostaway API endpoints
- Advanced error recovery mechanisms
- Performance metrics collection for pipeline optimization