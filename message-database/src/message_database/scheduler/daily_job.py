"""
Daily scheduler job for the Hostaway Message Database application.
Runs the ETL process to fetch new messages and store them in MongoDB.
"""
import time
import traceback
from datetime import datetime

from message_database.pipeline.etl import pipeline
from message_database.utils.logger import logger, send_error_notification

def run_daily_job():
    """
    Run the daily ETL job to fetch new messages.
    
    This function should be called by a cron job at 1:00 AM UTC.
    """
    logger.info("Starting daily message retrieval job")
    job_start_time = datetime.now()
    
    try:
        # Run the ETL pipeline
        success = pipeline.extract_transform_load()
        
        if success:
            logger.info(f"Daily job completed successfully. Processed {pipeline.processed_count} messages.")
        else:
            logger.error(f"Daily job completed with errors. Processed {pipeline.processed_count} messages with {pipeline.error_count} errors.")
            # Send notification about errors
            send_error_notification(
                "Hostaway Message ETL Job Completed with Errors",
                f"Daily ETL job completed with {pipeline.error_count} errors. Please check the logs."
            )
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"Daily job failed with unhandled exception: {str(e)}")
        logger.debug(f"Traceback: {error_traceback}")
        
        # Send notification about the failure
        send_error_notification(
            "Hostaway Message ETL Job Failed",
            f"Daily ETL job failed with error: {str(e)}\n\n{error_traceback}"
        )
    
    finally:
        # Log job completion time
        job_duration = datetime.now() - job_start_time
        logger.info(f"Daily job completed in {job_duration.total_seconds():.2f} seconds")

if __name__ == "__main__":
    # This allows the script to be run directly for testing
    run_daily_job() 