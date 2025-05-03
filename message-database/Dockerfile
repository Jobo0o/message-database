FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=UTC

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Create a non-root user to run the application
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Setup cron (as root, then switch back to appuser for app execution)
USER root
RUN apt-get update && apt-get install -y cron
# Add crontab entry to run the daily job at 1:00 AM UTC
RUN echo "0 1 * * * cd /app && python3 daily_job.py >> /app/logs/cron.log 2>&1" > /etc/cron.d/daily_job
RUN chmod 0644 /etc/cron.d/daily_job
RUN crontab /etc/cron.d/daily_job
USER appuser

# Command to run the application
CMD ["python", "-m", "src.main", "etl"]

# Alternative command to run with cron for production
# CMD ["bash", "-c", "cron && tail -f /app/logs/cron.log"] 