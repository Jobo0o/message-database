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
python -m message_database.main etl --since 2023-01-01T00:00:00
```

To retrieve messages from a specific number of days ago:

```bash
python -m message_database.main etl --days 5
```

### Convenience Scripts

Several convenience scripts are provided in the `scripts` directory:

#### Retrieving Messages from Yesterday

```bash
./scripts/run_etl_yesterday.sh --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

Options:
- `--mongodb-uri URI` - Specify a custom MongoDB URI
- `--dry-run` - Run in dry-run mode without saving to MongoDB

#### Testing the API Connection

```bash
./scripts/run_tests.sh --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

#### Testing Yesterday's Messages

```bash
./scripts/run_yesterday_test.sh --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

### Setting Up a Daily Job

To set up a daily cron job to retrieve new messages:

```bash
# Edit your crontab
crontab -e

# Add a line to run the job at 1:00 AM every day
0 1 * * * cd /path/to/message-database && ./scripts/daily_job.py
```

## Project Structure

```
message-database/
├── docs/                  # Documentation
├── message_database/      # Main package
│   ├── api/               # API clients
│   ├── database/          # Database operations
│   ├── models/            # Data models
│   ├── pipeline/          # ETL pipeline
│   ├── scheduler/         # Job scheduler
│   └── utils/             # Utilities
├── scripts/               # Shell scripts
├── tests/                 # Test suite
├── requirements.txt       # Dependencies
└── setup.py               # Package setup
```

## Documentation

For more detailed information, see the documentation in the `docs` directory:

- [Authentication](docs/authentication.md)
- [ETL Pipeline](docs/etl_pipeline.md)
- [Architecture](docs/architecture.md)
- [Deployment](docs/deployment.md)

## License

[Specify your license here] 

---

## Running the Message Database Frontend and API (V2)

This section describes how to run the FastAPI V2 backend and the simple HTML/JS frontend.

**Prerequisites:**

1.  **Python Environment:** Ensure you have Python 3.8+ installed.
2.  **Dependencies:** Install all required Python packages. From the `message-database` directory, run:
    ```bash
    pip install -r requirements.txt
    ```
    This will install `fastapi`, `uvicorn`, `pymongo`, and other necessary libraries.
3.  **MongoDB:** Make sure you have a MongoDB instance running and accessible. The connection URI should be configured in your `.env` file (see "Installation" section).
4.  **Environment Variables:** Ensure your `.env` file in the `message-database` directory is correctly set up with `MONGODB_URI`, `HOSTAWAY_CLIENT_ID`, and `HOSTAWAY_CLIENT_SECRET`. Although the V2 API doesn't directly use Hostaway credentials for its current read-only operations, the underlying database module might expect them for a full setup.

**1. Running the FastAPI Backend (API V2):**

The API V2 provides endpoints to read messages from the database.

*   **Navigate to the `message-database` directory:**
    ```bash
    cd path/to/your/message-database
    ```
*   **Set PYTHONPATH (if needed):**
    Depending on your setup, Python might not automatically find the `src` package. To ensure modules are imported correctly, you can set/prepend the `PYTHONPATH` environment variable to include the parent directory of `src` (which is the `message-database` directory itself if you are running the command from there).

    *   For Linux/macOS:
        ```bash
        export PYTHONPATH=$(pwd):$PYTHONPATH
        ```
    *   For Windows (Command Prompt):
        ```bash
        set PYTHONPATH=%cd%;%PYTHONPATH%
        ```
    *   For Windows (PowerShell):
        ```bash
        $env:PYTHONPATH = "$pwd;$env:PYTHONPATH"
        ```
    Alternatively, you might be able to run uvicorn as a module from the parent directory without explicitly setting `PYTHONPATH`:
    ```bash
    python -m uvicorn src.api_v2.main:app --reload --port 8000
    ```

*   **Run Uvicorn:**
    From the `message-database` directory, start the Uvicorn server:
    ```bash
    uvicorn src.api_v2.main:app --reload --port 8000
    ```
    If you didn't set `PYTHONPATH` and the above command has issues finding `src`, try the `python -m uvicorn ...` command mentioned above.

    The API will be available at `http://localhost:8000`. The V2 API endpoints themselves are under `/api_v2/` (e.g. `http://localhost:8000/api_v2/messages`). You can access the auto-generated API documentation for all endpoints (including V2) at `http://localhost:8000/docs`.

**2. Accessing the Frontend:**

The frontend is a simple HTML, CSS, and JavaScript application that interacts with the API V2. It is now served directly by the FastAPI application.

*   **Access via browser:**
    Once the Uvicorn server is running (as described above), open your web browser and navigate to:
    ```
    http://localhost:8000/ui/
    ```
    This will load `index.html` and its associated CSS and JavaScript files.

*   **API URL Configuration (Internal):**
    The frontend (`js/app.js`) is configured to connect to the API at `http://localhost:8000/api_v2`. This configuration should work correctly when the frontend is served from `/ui/` and the API from the root, as the JavaScript makes absolute URL calls.

You should now be able to see the message viewer and interact with the API. If you previously accessed `index.html` directly from the file system, ensure you clear your browser cache or perform a hard refresh when accessing `http://localhost:8000/ui/` to get the latest assets.