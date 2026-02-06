#!/usr/bin/env python
"""
Standalone script to test LinkedIn scraper.

Usage:
    python test_scraper.py --email your@email.com --password yourpassword
    python test_scraper.py --headless false  # See browser in action
"""

import argparse
import asyncio

from app.scraper.linkedin_scraper import LinkedInScraper, ScraperConfig


def print_message(msg, prefix="📩"):
    """Pretty print message."""
    print(f"\n{prefix} Message from: {msg.sender_name}")
    print(f"   Timestamp: {msg.timestamp}")
    print(f"   Preview: {msg.message_text[:100]}...")
    print(f"   URL: {msg.conversation_url}")
    print("-" * 80)


async def test_scraper(email: str, password: str, headless: bool = True, limit: int = 5):
    """
    Test the LinkedIn scraper.

    Args:
        email: LinkedIn email
        password: LinkedIn password
        headless: Run in headless mode
        limit: Max messages to scrape
    """
    print("\n" + "=" * 80)
    print("🚀 LinkedIn Scraper Test")
    print("=" * 80)

    # Create scraper config
    config = ScraperConfig(
        email=email,
        password=password,
        headless=headless,
        max_retries=3,
        max_requests_per_minute=10,
    )

    print("\n📋 Configuration:")
    print(f"   Email: {email}")
    print(f"   Headless: {headless}")
    print(f"   Limit: {limit} messages")

    # Create scraper
    scraper = LinkedInScraper(config)

    try:
        # Initialize (login)
        print("\n🔐 Initializing scraper (logging in)...")
        await scraper.initialize()
        print("✅ Login successful!")

        # Scrape messages
        print(f"\n📥 Scraping messages (limit: {limit})...")
        messages = await scraper.scrape_messages(limit=limit, unread_only=False)

        # Display results
        print(f"\n✨ Successfully scraped {len(messages)} messages!")
        print("=" * 80)

        for i, msg in enumerate(messages, 1):
            print_message(msg, prefix=f"📩 {i}.")

        # Summary
        print("\n" + "=" * 80)
        print("📊 Summary:")
        print(f"   Total messages: {len(messages)}")
        print(f"   Unread: {sum(1 for m in messages if not m.is_read)}")
        print(f"   Read: {sum(1 for m in messages if m.is_read)}")

        # Display senders
        senders = {m.sender_name for m in messages}
        print(f"   Unique senders: {len(senders)}")
        if senders:
            print(f"   Senders: {', '.join(list(senders)[:5])}")

        print("=" * 80)
        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await scraper.cleanup()
        print("✅ Cleanup complete!")

    return True


async def test_messenger(
    email: str, password: str, conversation_url: str, message: str, headless: bool = True
):
    """
    Test LinkedIn messenger (sending messages).

    Args:
        email: LinkedIn email
        password: LinkedIn password
        conversation_url: URL of conversation to send message to
        message: Message text to send
        headless: Run in headless mode
    """
    from app.services.linkedin_messenger import LinkedInMessenger

    print("\n" + "=" * 80)
    print("📤 LinkedIn Messenger Test")
    print("=" * 80)

    print("\n📋 Configuration:")
    print(f"   Email: {email}")
    print(f"   Headless: {headless}")
    print(f"   Conversation: {conversation_url}")
    print(f"   Message: {message[:50]}...")

    messenger = LinkedInMessenger(email=email, password=password, headless=headless)

    try:
        # Initialize
        print("\n🔐 Initializing messenger (logging in)...")
        await messenger.initialize()
        print("✅ Login successful!")

        # Send message
        print("\n📤 Sending message...")
        success = await messenger.send_message(conversation_url, message)

        if success:
            print("✅ Message sent successfully!")
        else:
            print("❌ Failed to send message")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await messenger.cleanup()
        print("✅ Cleanup complete!")

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test LinkedIn scraper and messenger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test scraper (read messages)
  python test_scraper.py scrape --email your@email.com --password yourpassword

  # Test scraper without headless (see browser)
  python test_scraper.py scrape --email your@email.com --password yourpassword --headless false

  # Test messenger (send message)
  python test_scraper.py send --email your@email.com --password yourpassword \\
    --url "https://linkedin.com/messaging/thread/12345" \\
    --message "Test message"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Test message scraping")
    scrape_parser.add_argument("--email", required=True, help="LinkedIn email")
    scrape_parser.add_argument("--password", required=True, help="LinkedIn password")
    scrape_parser.add_argument(
        "--headless", default="true", choices=["true", "false"], help="Run headless"
    )
    scrape_parser.add_argument("--limit", type=int, default=5, help="Max messages to scrape")

    # Send command
    send_parser = subparsers.add_parser("send", help="Test message sending")
    send_parser.add_argument("--email", required=True, help="LinkedIn email")
    send_parser.add_argument("--password", required=True, help="LinkedIn password")
    send_parser.add_argument("--url", required=True, help="Conversation URL")
    send_parser.add_argument("--message", required=True, help="Message to send")
    send_parser.add_argument(
        "--headless", default="true", choices=["true", "false"], help="Run headless"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    headless = args.headless == "true"

    if args.command == "scrape":
        # Test scraper
        success = asyncio.run(
            test_scraper(args.email, args.password, headless=headless, limit=args.limit)
        )
        exit(0 if success else 1)

    elif args.command == "send":
        # Test messenger
        success = asyncio.run(
            test_messenger(
                args.email,
                args.password,
                args.url,
                args.message,
                headless=headless,
            )
        )
        exit(0 if success else 1)


if __name__ == "__main__":
    main()
