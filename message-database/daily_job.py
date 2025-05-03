#!/usr/bin/env python3
"""
Daily job script to run the Hostaway Message Database ETL process.
This script is designed to be called by a cron job.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

# Import the daily job module
from src.scheduler.daily_job import run_daily_job

if __name__ == "__main__":
    # Run the daily job
    run_daily_job() 