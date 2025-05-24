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

The architecture now also includes a Frontend Application and a Message Query API (API V2) that interact with the Load component (MongoDB).

*   **Frontend Application:** A web-based UI allowing users to view messages. It fetches data from the Message Query API (API V2).
*   **Message Query API (API V2):** A FastAPI application providing RESTful endpoints to query messages stored in MongoDB.

These components extend the system's capabilities from a purely ETL-focused application to one that also offers data access and visualization.

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

6. **Message Query API (API V2)**
   - Purpose: Provides RESTful HTTP endpoints for querying messages stored in the MongoDB database.
   - Key technologies: FastAPI, Pydantic.
   - Key modules: `src/api_v2/main.py`.
   - Endpoints:
     - `GET /`: Root endpoint for API V2.
     - `GET /messages`: Lists messages with pagination.
     - `GET /messages/{message_id}`: Retrieves a specific message by its ID.
   - Interaction: Relies on the Load Component (MongoDB via `src/database/mongodb.py`) to fetch data.
   - Documentation: Provides auto-generated interactive API documentation (Swagger UI/OpenAPI) at its `/docs` endpoint.

7. **Frontend Application**
   - Purpose: Offers a user-friendly web interface for viewing messages from the database.
   - Key technologies: HTML, CSS, JavaScript.
   - Key files: `frontend/index.html`, `frontend/css/style.css`, `frontend/js/app.js`.
   - Serving: Served as static files by the Message Query API (API V2) itself, accessible via the `/ui/` path.
   - Interaction: Communicates with the Message Query API (API V2) to fetch and display messages.

## 2. Data Flow

The original ETL data flow (Initial Data Load and Incremental Updates) remains the same. The new components introduce a query-specific data flow:

### 2.1 ETL Data Flow (Initial and Incremental)
This remains as described previously, focusing on getting data *into* MongoDB.

### 2.2 Query Data Flow (API V2 and Frontend)

1.  **User Interaction:** A user accesses the Frontend Application in their web browser (e.g., `http://localhost:8000/ui/`).
2.  **Frontend Request:** The JavaScript in the Frontend Application makes an HTTP request to the Message Query API (API V2) (e.g., to `GET /api_v2/messages` or `GET /api_v2/messages/{message_id}`).
3.  **API V2 Processing:**
    *   The FastAPI application receives the request.
    *   The relevant endpoint in `src/api_v2/main.py` is triggered.
    *   The endpoint uses the `src/database/mongodb.py` module (Load Component) to query MongoDB.
4.  **MongoDB Response:** MongoDB returns the requested data (list of messages or a single message) to the API V2.
5.  **API V2 Response:** The API V2 serializes the data (using Pydantic models) into a JSON HTTP response and sends it back to the Frontend Application.
6.  **Frontend Display:** The JavaScript in the Frontend Application receives the JSON data and dynamically updates the HTML to display the messages to the user.

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

The deployment section should be updated to consider how the API V2 and its frontend are run.

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
   To run the API V2 and frontend (which are part of the same FastAPI application process as the ETL if structured that way, or could be a separate process):
   If API V2 is part of the main application:
   The Docker container would need to expose the API port (e.g., 8000) and run Uvicorn.
   ```bash
   # Example: If uvicorn runs the src.api_v2.main:app
   docker run -p 8000:8000 --env-file .env -v logs:/app/logs hostaway-message-db \
     bash -c "uvicorn src.api_v2.main:app --host 0.0.0.0 --port 8000 & cron && tail -f /app/logs/cron.log /app/logs/uvicorn.log"
   ```
   A more robust setup might use a process manager like Supervisor within Docker, or separate Docker containers for the ETL/scheduler and the API. The current setup runs `src.api_v2.main:app` which includes the API and frontend.

### 8.2 Cron Setup
The cron setup remains relevant for the ETL part. If the API is run in the same container, the cron job continues to function alongside the web server.

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

- Add a REST API for querying the message database (This is now implemented as API V2)
- Implement sentiment analysis on message content
- Create a dashboard for visualizing message patterns (The simple frontend is a first step)
- Add support for additional Hostaway data entities
- Implement full audit logging of API interactions 