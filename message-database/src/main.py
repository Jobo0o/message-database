"""
Main entry point for the Hostaway Message Database application.
This script can be used to run the ETL process manually.
"""
import argparse
import sys
from datetime import datetime, timedelta

from .pipeline.etl import pipeline
from .utils.logger import logger, setup_logging

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Hostaway Message Database ETL Application"
    )
    
    # Subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # ETL command
    etl_parser = subparsers.add_parser("etl", help="Run the ETL process")
    etl_parser.add_argument(
        "--since", 
        dest="since_timestamp",
        help="Only process messages since this timestamp (ISO format, e.g., 2023-01-01T00:00:00)"
    )
    etl_parser.add_argument(
        "--days", 
        dest="days_ago",
        type=int,
        help="Only process messages from the specified number of days ago"
    )
    
    # Parse args
    return parser.parse_args()

def main():
    """Main function to run the application."""
    # Set up logging
    logger = setup_logging()
    
    # Parse command line arguments
    args = parse_args()
    
    if not args.command:
        logger.error("No command specified. Use 'etl' to run the ETL process.")
        sys.exit(1)
    
    if args.command == "etl":
        # Determine the since_timestamp
        since_timestamp = None
        
        if args.since_timestamp:
            since_timestamp = args.since_timestamp
        elif args.days_ago:
            # Calculate timestamp from days ago
            days_ago = datetime.now() - timedelta(days=args.days_ago)
            since_timestamp = days_ago.isoformat()
        
        # Run the ETL process
        success = pipeline.extract_transform_load(since_timestamp)
        
        if not success:
            logger.error("ETL process completed with errors")
            sys.exit(1)
        
        logger.info("ETL process completed successfully")

if __name__ == "__main__":
    main() 