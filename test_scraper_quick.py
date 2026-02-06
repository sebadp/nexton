#!/usr/bin/env python
"""
Quick test script for LinkedIn scraper.

Just run: python test_scraper_quick.py

Configure via .env:
    LINKEDIN_EMAIL=your@email.com
    LINKEDIN_PASSWORD=yourpassword
"""

import asyncio
import os

# Load environment variables FIRST, before importing app modules
from dotenv import load_dotenv

load_dotenv()

from app.scraper.linkedin_scraper import LinkedInScraper, ScraperConfig


async def main():
    """Quick scraper test."""
    # Get credentials from environment
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email or not password:
        print("❌ Error: LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env")
        print("\nCreate a .env file with:")
        print("  LINKEDIN_EMAIL=your@email.com")
        print("  LINKEDIN_PASSWORD=yourpassword")
        return

    print("🚀 Quick LinkedIn Scraper Test")
    print("=" * 60)
    print(f"📧 Email: {email}")
    print(f"🔒 Password: {'*' * len(password)}")
    print("=" * 60)

    # Create config
    config = ScraperConfig(
        email=email,
        password=password,
        headless=False,  # Show browser for debugging
        max_retries=3,
    )

    # Create scraper
    scraper = LinkedInScraper(config)

    try:
        # Login
        print("\n🔐 Logging in to LinkedIn...")
        await scraper.initialize()
        print("✅ Login successful!\n")

        # Scrape messages
        print("📥 Scraping messages...")
        messages = await scraper.scrape_messages(limit=5, unread_only=False)

        # Show results
        print(f"\n✨ Found {len(messages)} messages:\n")

        for i, msg in enumerate(messages, 1):
            print(f"{i}. 📩 From: {msg.sender_name}")
            print(f"   📅 {msg.timestamp}")
            print(f"   💬 {msg.message_text[:80]}...")
            print()

        print("=" * 60)
        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\n🧹 Cleaning up...")
        await scraper.cleanup()
        print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
