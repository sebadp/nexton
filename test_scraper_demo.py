#!/usr/bin/env python
"""
Demo script showing scraper functionality without real credentials.

This demonstrates the scraper API without actually connecting to LinkedIn.
Useful for understanding the code flow and data structures.
"""

import asyncio
from datetime import datetime
from dataclasses import dataclass


@dataclass
class MockMessage:
    """Mock LinkedIn message for demo."""

    sender_name: str
    message_text: str
    timestamp: datetime
    conversation_url: str
    is_read: bool = False


async def demo_scraper():
    """
    Demonstrate scraper functionality with mock data.

    This shows what the scraper does without needing real LinkedIn credentials.
    """
    print("\n" + "=" * 80)
    print("🎭 LinkedIn Scraper Demo (Mock Data)")
    print("=" * 80)

    print("\n📋 This demo shows:")
    print("  ✅ What the scraper extracts from LinkedIn")
    print("  ✅ Data structure of messages")
    print("  ✅ How to process scraped messages")
    print("\n💡 To test with real data, use: python test_scraper_quick.py")

    # Simulate login
    print("\n🔐 [DEMO] Logging in to LinkedIn...")
    await asyncio.sleep(1)
    print("✅ [DEMO] Login successful!")

    # Simulate scraping
    print("\n📥 [DEMO] Scraping messages...")
    await asyncio.sleep(1)

    # Create mock messages (similar to real scraped data)
    messages = [
        MockMessage(
            sender_name="Sarah Johnson - Senior Tech Recruiter",
            message_text=(
                "Hi! I came across your profile and was impressed by your experience with Python and FastAPI. "
                "We have an exciting Senior Backend Engineer position at TechCorp ($160k-$200k) that I think "
                "would be perfect for you. Are you open to discussing this opportunity?"
            ),
            timestamp=datetime(2026, 1, 18, 10, 30),
            conversation_url="https://www.linkedin.com/messaging/thread/2-ABC123...",
            is_read=False,
        ),
        MockMessage(
            sender_name="Michael Chen - Engineering Manager",
            message_text=(
                "Hello! We're building a new AI platform and looking for experienced Python developers. "
                "Your background with DSPy and LLMs caught my attention. Would you be interested in a "
                "quick call to discuss? Position: $180k-$220k + equity."
            ),
            timestamp=datetime(2026, 1, 18, 9, 15),
            conversation_url="https://www.linkedin.com/messaging/thread/2-DEF456...",
            is_read=False,
        ),
        MockMessage(
            sender_name="Emily Rodriguez - CTO @ StartupXYZ",
            message_text=(
                "Hi there! Love your open source contributions. We're a Series A startup building developer "
                "tools and we're looking for a founding engineer. $150k-$180k + 0.5% equity. Let me know if "
                "you'd like to chat!"
            ),
            timestamp=datetime(2026, 1, 17, 16, 45),
            conversation_url="https://www.linkedin.com/messaging/thread/2-GHI789...",
            is_read=True,
        ),
        MockMessage(
            sender_name="David Kim - Talent Acquisition",
            message_text=(
                "Quick question - are you open to remote opportunities? We have several Backend Engineer "
                "positions ($120k-$160k) across different clients. Stack: Python, Docker, Kubernetes, AWS."
            ),
            timestamp=datetime(2026, 1, 17, 14, 20),
            conversation_url="https://www.linkedin.com/messaging/thread/2-JKL012...",
            is_read=True,
        ),
        MockMessage(
            sender_name="Lisa Anderson - Technical Recruiter",
            message_text=(
                "Hi! I saw your profile and wanted to reach out about a Staff Engineer role at BigTech. "
                "It's a remote position working on infrastructure ($200k-$250k). Tech stack includes Python, "
                "Go, and Kubernetes. Interested?"
            ),
            timestamp=datetime(2026, 1, 16, 11, 0),
            conversation_url="https://www.linkedin.com/messaging/thread/2-MNO345...",
            is_read=True,
        ),
    ]

    # Display results
    print(f"\n✨ [DEMO] Found {len(messages)} messages:\n")

    for i, msg in enumerate(messages, 1):
        status = "📬 UNREAD" if not msg.is_read else "📭 read"
        print(f"{i}. {status} - From: {msg.sender_name}")
        print(f"   📅 {msg.timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"   💬 {msg.message_text[:100]}...")
        print()

    # Show how data would be processed
    print("=" * 80)
    print("📊 [DEMO] Message Analysis:")
    print(f"   Total messages: {len(messages)}")
    print(f"   Unread: {sum(1 for m in messages if not m.is_read)}")
    print(f"   Read: {sum(1 for m in messages if m.is_read)}")

    # Extract keywords (simple demo)
    all_text = " ".join(m.message_text for m in messages)
    keywords = {
        "Python": all_text.count("Python"),
        "Backend": all_text.count("Backend"),
        "Remote": all_text.count("remote") + all_text.count("Remote"),
        "Senior": all_text.count("Senior"),
    }

    print("\n   Common keywords:")
    for keyword, count in sorted(keywords.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"      {keyword}: {count}x")

    # Show salary ranges found
    print("\n   Salary ranges mentioned:")
    for msg in messages:
        if "$" in msg.message_text:
            # Simple extraction (in real app, DSPy would handle this)
            text = msg.message_text
            start = text.find("$")
            end = text.find(")", start) if ")" in text[start:] else start + 20
            salary = text[start:end]
            print(f"      {salary}")

    print("\n" + "=" * 80)
    print("💡 Next Steps:")
    print("   1. Test with real data: python test_scraper_quick.py")
    print("   2. Configure credentials in .env")
    print("   3. Read docs/SCRAPER_TESTING.md for detailed guide")
    print("=" * 80)

    print("\n✅ [DEMO] Complete!")


async def demo_workflow():
    """
    Demonstrate the complete workflow: scrape → analyze → respond.
    """
    print("\n" + "=" * 80)
    print("🔄 Complete Workflow Demo")
    print("=" * 80)

    print("\n📝 Workflow Steps:")
    print("   1. 📥 Scrape LinkedIn messages")
    print("   2. 🤖 Analyze with DSPy pipeline")
    print("   3. 📊 Score and classify opportunities")
    print("   4. 📧 Send email notification")
    print("   5. 👤 User reviews and approves")
    print("   6. 📤 Send response to LinkedIn")

    print("\n" + "=" * 80)
    print("Step 1: Scrape Messages")
    print("=" * 80)
    await asyncio.sleep(0.5)
    print("✅ Scraped 3 new messages")

    print("\n" + "=" * 80)
    print("Step 2: Analyze with DSPy")
    print("=" * 80)
    await asyncio.sleep(0.5)
    print("   Message 1: Extracting company, role, salary...")
    print("   → Company: TechCorp")
    print("   → Role: Senior Backend Engineer")
    print("   → Salary: $160k-$200k")
    print("   ✅ Analysis complete")

    print("\n" + "=" * 80)
    print("Step 3: Score & Classify")
    print("=" * 80)
    await asyncio.sleep(0.5)
    print("   Tech Stack Match: 85/100")
    print("   Salary Match: 90/100")
    print("   Seniority Match: 95/100")
    print("   Company Score: 80/100")
    print("   → Total Score: 88/100")
    print("   → Tier: A (High Priority)")
    print("   ✅ Classification complete")

    print("\n" + "=" * 80)
    print("Step 4: Generate Response")
    print("=" * 80)
    await asyncio.sleep(0.5)
    print("   🤖 AI generating response...")
    print('   Generated: "Thank you for reaching out! I\'m very interested in...')
    print("   ✅ Response generated")

    print("\n" + "=" * 80)
    print("Step 5: Send Email Notification")
    print("=" * 80)
    await asyncio.sleep(0.5)
    print("   📧 Sending to: user@example.com")
    print("   📋 Subject: New A-Tier Opportunity: TechCorp - Senior Backend Engineer")
    print("   💬 Including AI-generated response")
    print("   🔘 Action buttons: Approve | Edit | Decline")
    print("   ✅ Email sent")

    print("\n" + "=" * 80)
    print("Step 6: User Interaction")
    print("=" * 80)
    await asyncio.sleep(0.5)
    print("   👤 User clicks 'Approve & Send'")
    print("   ✅ Response approved")

    print("\n" + "=" * 80)
    print("Step 7: Send to LinkedIn")
    print("=" * 80)
    await asyncio.sleep(0.5)
    print("   📤 Celery task queued")
    print("   🌐 Opening LinkedIn conversation")
    print("   ⌨️  Typing response message")
    print("   📨 Clicking send button")
    print("   ✅ Message sent successfully!")

    print("\n" + "=" * 80)
    print("✅ Complete Workflow Demo Finished!")
    print("=" * 80)

    print("\n💡 To run the real system:")
    print("   docker-compose up -d")
    print("   See README.md for full setup")


async def main():
    """Main demo runner."""
    print("\n🎭 LinkedIn Agent Scraper - Demo Mode")
    print("\nChoose a demo:")
    print("  1. Scraper Demo (show message extraction)")
    print("  2. Complete Workflow Demo (show entire process)")
    print("  3. Both demos")

    choice = input("\nEnter choice (1/2/3): ").strip()

    if choice in ["1", "3"]:
        await demo_scraper()

    if choice in ["2", "3"]:
        await demo_workflow()

    print("\n" + "=" * 80)
    print("📚 For more information:")
    print("   - Quick test: python test_scraper_quick.py")
    print("   - Full guide: docs/SCRAPER_TESTING.md")
    print("   - Main README: README.md")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
