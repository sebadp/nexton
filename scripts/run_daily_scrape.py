#!/usr/bin/env python3
"""
Run the daily scrape and summary task on demand.

This script triggers the same task that runs daily at 9 AM,
but executes it immediately. It will:
1. Scrape unread LinkedIn messages
2. Process each through the DSPy pipeline
3. Generate AI responses based on your profile
4. Send ONE summary email with all opportunities

Usage:
    python scripts/run_daily_scrape.py

    # Or via Celery CLI:
    celery -A app.tasks.celery_app call app.tasks.scraping_tasks.scrape_and_send_daily_summary
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tasks.scraping_tasks import scrape_and_send_daily_summary


def main():
    print("=" * 60)
    print("LinkedIn Daily Scrape & Summary")
    print("=" * 60)
    print()
    print("This will:")
    print("  1. Scrape unread LinkedIn messages")
    print("  2. Process each through DSPy pipeline")
    print("  3. Generate AI responses (based on your profile)")
    print("  4. Send ONE summary email")
    print()
    print("View emails at: http://localhost:8025 (Mailpit)")
    print()
    print("-" * 60)
    print()

    # Execute the task synchronously (not via Celery queue)
    result = scrape_and_send_daily_summary()

    print()
    print("-" * 60)
    print()
    print("Result:")
    print(f"  Status: {result.get('status', 'unknown')}")
    print(f"  Messages found: {result.get('messages_found', 0)}")
    print(f"  Opportunities created: {result.get('opportunities_created', 0)}")
    print(f"  Summary sent: {result.get('summary_sent', False)}")

    if result.get("status") == "success":
        print()
        print("View the email at: http://localhost:8025")
        return 0
    elif result.get("status") == "no_new_messages":
        print()
        print("No new messages to process.")
        return 0
    else:
        print()
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())