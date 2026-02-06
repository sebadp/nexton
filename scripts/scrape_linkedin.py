#!/usr/bin/env python3
"""
Example script to scrape LinkedIn messages.

Usage:
    python scripts/scrape_linkedin.py

Environment variables:
    LINKEDIN_EMAIL: Your LinkedIn email
    LINKEDIN_PASSWORD: Your LinkedIn password
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.logging import get_logger
from app.scraper import LinkedInScraper, ScraperConfig

logger = get_logger(__name__)


async def main():
    """Main scraper execution."""
    # Get credentials from environment
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email or not password:
        print("Error: LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set")
        print("\nUsage:")
        print("  export LINKEDIN_EMAIL='your@email.com'")
        print("  export LINKEDIN_PASSWORD='your-password'")
        print("  python scripts/scrape_linkedin.py")
        sys.exit(1)

    # Create scraper configuration
    config = ScraperConfig(
        email=email,
        password=password,
        headless=True,  # Set to False to see browser
        max_requests_per_minute=10,
        min_delay_seconds=3.0,
        save_cookies=True,
    )

    logger.info("starting_linkedin_scraper")

    # Use context manager for automatic cleanup
    async with LinkedInScraper(config) as scraper:
        # Get unread message count
        unread_count = await scraper.get_unread_count()
        logger.info("unread_messages_found", count=unread_count)
        print(f"\n📬 Found {unread_count} unread messages")

        if unread_count == 0:
            print("No unread messages to scrape.")
            return

        # Scrape unread messages
        print("\n🔍 Scraping messages (max 5)...\n")
        messages = await scraper.scrape_messages(limit=5, unread_only=True)

        # Display results
        print(f"✅ Scraped {len(messages)} messages:\n")
        print("=" * 80)

        for i, msg in enumerate(messages, 1):
            print(f"\n📩 Message {i}:")
            print(f"From: {msg.sender_name}")
            print(f"Time: {msg.timestamp}")
            print(f"Message:\n{msg.message_text[:200]}...")  # First 200 chars
            print(f"URL: {msg.conversation_url}")
            print("-" * 80)

        logger.info("scraping_complete", message_count=len(messages))

    print("\n✨ Scraping completed successfully!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error("scraping_failed", error=str(e))
        print(f"\n❌ Error: {e}")
        sys.exit(1)
