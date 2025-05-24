# Deployment Guide

This document provides step-by-step instructions for deploying the Hostaway Message Database application in various environments.

## Prerequisites

Before deployment, ensure you have:

1. A Hostaway API key with access to message data
2. A MongoDB Atlas account (or another MongoDB deployment)
3. Docker (for containerized deployment)
4. Basic understanding of Linux and Docker commands

## Environment Setup

### 1. MongoDB Setup

1. **Create a MongoDB Atlas Cluster:**
   - Sign up or log in to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Create a new cluster (shared tier is sufficient)
   - Set up network access to allow connections from your deployment environment
   - Create a database user with read/write permissions

2. **Get Your Connection String:**
   - In MongoDB Atlas, click "Connect" on your cluster
   - Select "Connect your application"
   - Copy the connection string (it should look like: `mongodb+srv://username:password@cluster.mongodb.net/`)
   - Replace `<username>` and `<password>` with your database credentials

### 2. Environment Variables

Create a `.env` file with the following variables:

```
# Hostaway API Configuration
HOSTAWAY_API_KEY=your_api_key_here
HOSTAWAY_BASE_URL=https://api.hostaway.com/v1

# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=hostaway_messages
MONGODB_COLLECTION=messages

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=./logs

# Application Settings
API_REQUEST_DELAY=1.0
ENABLE_DRY_RUN=False
NOTIFICATION_EMAIL=your_email@example.com
```

## Deployment Options

### Option 1: Local Deployment

For development or testing purposes, you can run the application locally:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd message-database
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file in the project root with your configuration**

5. **Run the application for initial data load:**
   ```bash
   python -m src.main etl
   ```

6. **Set up a cron job for daily updates:**
   ```bash
   crontab -e
   ```
   Add the following line:
   ```
   0 1 * * * cd /path/to/message-database && /path/to/python daily_job.py >> logs/cron.log 2>&1
   ```

### Option 2: Docker Deployment

For production environments, use Docker to containerize the application:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd message-database
   ```

2. **Build the Docker image:**
   ```bash
   docker build -t hostaway-message-db .
   ```

3. **Create a `.env` file in the project root with your configuration**

4. **Run the container for initial data load:**
   ```bash
   docker run --env-file .env -v $(pwd)/logs:/app/logs hostaway-message-db python -m src.main etl
   ```
   (Note: The default CMD in the Dockerfile is now to start the Uvicorn server, so to run ETL only, you'd override the command as shown above or use a separate ETL-focused Dockerfile/service).

5. **Run the container to serve the API and Frontend, with automated ETL updates:**
   The updated Dockerfile uses an `entrypoint.sh` script that starts the `cron` service in the background and then starts the `uvicorn` server for the API V2 and frontend.
   ```bash
   docker run -d --name hostaway-app -p 8000:8000 --env-file .env -v $(pwd)/logs:/app/logs hostaway-message-db
   ```
   - `-d`: Runs the container in detached mode.
   - `--name hostaway-app`: Assigns a name to the container.
   - `-p 8000:8000`: Maps port 8000 of the host to port 8000 of the container (where Uvicorn runs).
   - `--env-file .env`: Loads environment variables from your `.env` file.
   - `-v $(pwd)/logs:/app/logs`: Mounts the local `logs` directory into the container's `/app/logs` directory.
   
   With this setup:
   - The API V2 will be accessible at `http://<your-docker-host-ip>:8000/api_v2/`.
   - The Frontend will be accessible at `http://<your-docker-host-ip>:8000/ui/`.
   - The cron job for daily ETL (defined in the Dockerfile) will run as scheduled, logging to `/app/logs/cron.log` inside the container (and thus to your mounted `logs` directory).

6. **Manually running ETL jobs:**
   If you need to run an ETL job manually (e.g., for a specific date range) while the API container is running:
   ```bash
   docker exec -it hostaway-app python -m src.main etl --days 7 
   ```
   Or, to run the `daily_job.py` script (which typically handles "yesterday's" data):
   ```bash
   docker exec -it hostaway-app python daily_job.py
   ```
   Output and logs from these manual runs will appear in the container's stdout/stderr (viewable with `docker logs hostaway-app`) and potentially in the application's log files within `/app/logs`.

### Option 3: Cloud Deployment (AWS EC2)

For a scalable cloud deployment:

1. **Launch an EC2 instance:**
   - Ubuntu 20.04 LTS
   - t3.micro instance type (minimum)
   - 20GB storage
   - Security group with outbound access to Hostaway API and MongoDB Atlas

2. **SSH into your instance:**
   ```bash
   ssh -i your-key.pem ubuntu@your-instance-ip
   ```

3. **Install Docker:**
   ```bash
   sudo apt update
   sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
   sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
   sudo apt update
   sudo apt install -y docker-ce
   sudo usermod -aG docker ${USER}
   ```
   Log out and log back in to apply the group changes.

4. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd message-database
   ```

5. **Create a `.env` file with your configuration**

6. **Build and run the Docker container:**
   ```bash
   docker build -t hostaway-message-db .
   # Run the container as described in "Option 2: Docker Deployment", step 5.
   docker run -d --name hostaway-app -p 8000:8000 --restart always --env-file .env -v $(pwd)/logs:/app/logs hostaway-message-db
   ```
   Ensure your EC2 instance's security group allows inbound traffic on port 8000.

7. **Set up log rotation:**
   ```bash
   sudo apt install -y logrotate
   sudo nano /etc/logrotate.d/hostaway-messages
   ```
   Add the following configuration:
   ```
   /home/ubuntu/message-database/logs/*.log {
     daily
     missingok
     rotate 30
     compress
     delaycompress
     notifempty
     create 0640 ubuntu ubuntu
   }
   ```

## Testing the Deployment

After deployment, you should verify that everything is working correctly:

1. **Check Docker container status:**
   ```bash
   docker ps
   ```
   Ensure the container is running.

2. **Check the logs:**
   ```bash
   tail -f logs/$(date +%Y-%m-%d).log
   ```
   You should see log entries indicating that the application is running.

3. **Check MongoDB data:**
   Connect to your MongoDB Atlas cluster and verify that data is being stored in the `messages` collection.

## Dry Run Mode

For initial testing with the Hostaway API, you can enable dry run mode:

1. Set `ENABLE_DRY_RUN=True` in your `.env` file
2. Run the application
3. Check the logs to see what API calls would have been made
4. When satisfied, set `ENABLE_DRY_RUN=False` and run again

## Incremental Data Loading

If you have a large number of messages, you can load data incrementally:

1. First, load a small batch of recent messages:
   ```bash
   python -m src.main etl --days 7
   ```

2. Then load older messages in batches:
   ```bash
   python -m src.main etl --days 30
   python -m src.main etl --days 90
   python -m src.main etl --days 365
   ```

3. Finally, load all remaining messages:
   ```bash
   python -m src.main etl
   ```

## Monitoring and Maintenance

### Monitoring

1. **Check container status:**
   ```bash
   docker ps
   ```

2. **View logs:**
   ```bash
   tail -f logs/$(date +%Y-%m-%d).log
   ```

3. **Check MongoDB data:**
   - Connect to MongoDB Atlas
   - Run a count query: `db.messages.count()`
   - Check the latest message: `db.messages.find().sort({timestamp: -1}).limit(1)`

### Maintenance

1. **Updating the application:**
   ```bash
   git pull
   docker build -t hostaway-message-db .
   docker stop hostaway-messages
   docker rm hostaway-messages
   docker run -d --name hostaway-app --restart always --env-file .env -v $(pwd)/logs:/app/logs hostaway-message-db
   ```

2. **Backup your data:**
   Regularly backup your MongoDB data using MongoDB Atlas backups or alternative tools.

3. **Check for errors:**
   Regularly review logs for any errors or warnings that might indicate issues with the API or database.

## Troubleshooting

### Common Issues

1. **MongoDB Connection Errors:**
   - Verify your connection string in the `.env` file
   - Check if your IP address is allowed in MongoDB Atlas network access
   - Ensure your MongoDB Atlas user has the correct permissions

2. **API Connection Errors:**
   - Verify your API key in the `.env` file
   - Check if your IP address is allowed by the Hostaway API
   - Look for rate limiting errors in the logs

3. **Docker Issues:**
   - Check container logs: `docker logs hostaway-messages`
   - Verify that the `.env` file is correctly mounted
   - Ensure the logs volume is accessible

4. **Cron Job Not Running:**
   - Check cron logs within the container or the mounted log volume: `tail -f logs/cron.log`
   - Verify the cron job is correctly configured in the Dockerfile and `entrypoint.sh` starts the cron service.
   - Check if the container has permission to run cron (should be handled by `USER root` for cron setup in Dockerfile).

### Getting Support

If you encounter persistent issues:

1. Check the project documentation
2. Review the logs for specific error messages
3. Search for similar issues in the project repository
4. Contact the development team with detailed information about your issue 