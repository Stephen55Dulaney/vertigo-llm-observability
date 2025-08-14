#!/usr/bin/env python3
"""
Create a Cloud Scheduler job for the 5:30 PM end-of-day summary.
"""

import subprocess
import json
import os

def create_eod_summary_job():
    """Create a Cloud Scheduler job that runs at 5:30 PM CST daily."""
    
    # Job configuration
    job_name = "daily-summary-530pm"
    schedule = "30 17 * * *"  # 5:30 PM daily (UTC)
    timezone = "America/Chicago"
    target_url = "https://us-central1-vertigo-466116.cloudfunctions.net/email-processor-v2"
    
    # Create the job
    cmd = [
        "gcloud", "scheduler", "jobs", "create", "http", job_name,
        "--schedule", schedule,
        "--time-zone", timezone,
        "--uri", target_url,
        "--http-method", "POST",
        "--headers", "Content-Type=application/json",
        "--message-body", json.dumps({
            "action": "generate_daily_summary",
            "recipient": "sdulaney@mergeworld.com",
            "summary_type": "end_of_day"
        }),
        "--location", "us-central1",
        "--description", "Generate and send 5:30 PM end-of-day summary to sdulaney@mergeworld.com"
    ]
    
    try:
        print(f"Creating Cloud Scheduler job: {job_name}")
        print(f"Schedule: {schedule} ({timezone})")
        print(f"Target: {target_url}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Successfully created 5:30 PM end-of-day summary job!")
        print(result.stdout)
        
        # Enable the job
        enable_cmd = ["gcloud", "scheduler", "jobs", "enable", job_name, "--location=us-central1"]
        subprocess.run(enable_cmd, check=True)
        print("✅ Job enabled and ready to run!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating job: {e}")
        print(f"Error output: {e.stderr}")
        return False
    
    return True

def list_scheduler_jobs():
    """List all scheduler jobs."""
    try:
        result = subprocess.run(
            ["gcloud", "scheduler", "jobs", "list", "--location=us-central1"],
            capture_output=True,
            text=True,
            check=True
        )
        print("📋 Current Cloud Scheduler jobs:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error listing jobs: {e}")

if __name__ == "__main__":
    print("🚀 Setting up 5:30 PM End-of-Day Summary Scheduler Job")
    print("=" * 60)
    
    # List current jobs
    list_scheduler_jobs()
    print()
    
    # Create the new job
    success = create_eod_summary_job()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Setup Complete!")
        print("=" * 60)
        print("The 5:30 PM end-of-day summary job has been created and will:")
        print("• Run automatically at 5:30 PM Central Time daily")
        print("• Generate an end-of-day summary based on the day's activities")
        print("• Send the summary to sdulaney@mergeworld.com")
        print("\nYou can test it manually by running:")
        print("gcloud scheduler jobs run daily-summary-530pm --location=us-central1")
    else:
        print("\n❌ Setup failed. Please check the error messages above.") 