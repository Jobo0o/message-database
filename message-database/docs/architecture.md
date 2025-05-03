# Hostaway Message Database Architecture

## Document Purpose

This document serves as the definitive architecture specification for the Hostaway Message Database Application. It provides implementation details, design decisions, and serves as a reference for future development and maintenance.

## 1. System Architecture

### 1.1 High-Level Architecture

The application follows an ETL (Extract, Transform, Load) architecture pattern:

```
+----------------+      +----------------+      +----------------+
|                |      |                |      |                |
|     Extract    +----->+   Transform    +----->+     Load       |
|                |      |                |      |                |
+----------------+      +----------------+      +----------------+
     ^                                               |
     |                                               |
     |                       +---------------------+ |
     |                       |                     | |
     +-----------------------+     Scheduler       |<+
                             |                     |
                             +---------------------+
```

### 1.2 Component Breakdown

1. **Extract Component**
   - Purpose: Fetches data from the Hostaway API
   - Key modules: `api/hostaway_client.py`
   - Functions: Authentication, pagination handling, rate limiting

2. **Transform Component**
   - Purpose: Structures and validates the raw API data
   - Key modules: `models/message.py`, `pipeline/etl.py`
   - Functions: Data cleaning, normalization, type conversion

3. **Load Component**
   - Purpose: Stores processed data in MongoDB
   - Key modules: `database/mongodb.py`
   - Functions: Connection management, CRUD operations, index creation

4. **Scheduler Component**
   - Purpose: Automates the ETL process on a daily basis
   - Key modules: `scheduler/daily_job.py`, `daily_job.py`
   - Functions: Job scheduling, incremental updates

5. **Utilities**
   - Purpose: Provides cross-cutting functionality
   - Key modules: `utils/logger.py`, `config.py`
   - Functions: Logging, configuration, error notification

## 2. Data Flow

### 2.1 Initial Data Load

1. Application validates configuration
2. Connects to MongoDB
3. Retrieves all historical messages from Hostaway API (with pagination)
4. For each message:
   - Transforms into the target data model
   - Enriches with property and reservation details if needed
   - Validates the data structure
   - Inserts into MongoDB (with upsert to prevent duplicates)
5. Creates necessary indexes
6. Logs completion statistics

### 2.2 Incremental Updates

1. Daily job is triggered by cron at 1:00 AM UTC
2. Retrieves the timestamp of the latest message from MongoDB
3. Queries Hostaway API for messages after that timestamp
4. Processes new messages (same as initial load)
5. Updates MongoDB
6. Logs completion statistics
7. Sends error notifications if needed

## 3. Database Design

### 3.1 MongoDB Collection Structure

The application uses a single collection (`messages`) with the following structure:

```json
{
  "_id": "ObjectId",
  "message_id": "string",
  "property": {
    "id": "string",
    "name": "string"
  },
  "guest": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "nationality": "string"
  },
  "content": "string",
  "timestamp": "datetime",
  "direction": "string",
  "reservation": {
    "id": "string",
    "price": "decimal"
  },
  "message_type": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 3.2 Indexes

The application creates the following indexes for efficient querying:

1. Text index on `content` field for full-text search
2. Compound index on `(property.id, timestamp)` for property-specific queries
3. Compound index on `(guest.nationality, timestamp)` for nationality analysis
4. Unique index on `message_id` to prevent duplicates

## 4. API Integration

### 4.1 Hostaway API

The application interacts with the Hostaway API to retrieve message data:

- Base URL: `https://api.hostaway.com/v1`
- Authentication: API key in headers
- Rate limiting: 1-second delay between requests
- Pagination: Implemented with limit/offset

### 4.2 Error Handling

The API client implements robust error handling:

- HTTP errors: Automatic retry with exponential backoff
- API-level errors: Detailed error messages with logging
- Rate limiting: Configurable delay between requests
- Timeout handling: Configurable request timeouts
- Dry-run mode: Testing without actual API calls

## 5. System Requirements

### 5.1 Development Environment

- Python 3.8+
- MongoDB 5.0+
- Required Python packages listed in `requirements.txt`

### 5.2 Production Environment

- Linux-based OS (Ubuntu 20.04 LTS recommended)
- Docker runtime
- 2GB RAM, 1 vCPU minimum
- 20GB storage
- MongoDB Atlas (shared tier)
- Network access to Hostaway API

## 6. Security Considerations

### 6.1 Credential Management

- API credentials stored in environment variables
- MongoDB connection string with username/password in environment variables
- No hard-coded credentials in the codebase

### 6.2 Data Security

- MongoDB network access restricted to application IP
- Error handling doesn't expose sensitive information
- Logs are sanitized of sensitive data

## 7. Testing Strategy

### 7.1 Unit Tests

- API client tests (mocking HTTP requests)
- Data model validation tests
- Database operation tests (with mocked MongoDB)
- ETL pipeline tests

### 7.2 Integration Tests

- End-to-end ETL process testing
- MongoDB connection testing
- API error handling testing

## 8. Deployment

### 8.1 Docker Deployment

The application is containerized with Docker:

1. Build the image:
   ```
   docker build -t hostaway-message-db .
   ```

2. Run with environment variables:
   ```
   docker run --env-file .env -v logs:/app/logs hostaway-message-db
   ```

### 8.2 Cron Setup

For production deployment with automated job:

```
docker run --env-file .env -v logs:/app/logs hostaway-message-db bash -c "cron && tail -f /app/logs/cron.log"
```

## 9. Monitoring and Maintenance

### 9.1 Logging

- Daily log files in the `logs` directory
- Log rotation with date-based naming
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Standard log format with timestamps

### 9.2 Error Notifications

- Email notifications for critical errors
- Daily job failure notifications
- Statistics on processed messages

## 10. Future Enhancements

- Add a REST API for querying the message database
- Implement sentiment analysis on message content
- Create a dashboard for visualizing message patterns
- Add support for additional Hostaway data entities
- Implement full audit logging of API interactions 