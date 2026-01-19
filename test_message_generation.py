#!/usr/bin/env python
"""
Test script for LinkedIn scraper + DSPy message generation.

Scrapes real LinkedIn messages and generates AI responses without sending.
"""


import asyncio
import os
from datetime import datetime

# Load environment variables FIRST, before importing app modules
from dotenv import load_dotenv
load_dotenv()

from app.scraper.linkedin_scraper import LinkedInScraper, ScraperConfig
from app.dspy_pipeline.opportunity_analyzer import OpportunityAnalyzer
from app.dspy_pipeline.response_generator import ResponseGenerator
from app.core.config import settings


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_section(text: str):
    """Print a section divider."""
    print("\n" + "-" * 80)
    print(f"  {text}")
    print("-" * 80 + "\n")


async def main():
    """Test message generation pipeline."""
    # Get credentials
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email or not password:
        print("❌ Error: LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env")
        return

    print_header("🤖 LinkedIn Message Generation Test")
    print(f"📧 Email: {email}")
    print(f"🔒 Password: {'*' * len(password)}")
    print(f"📍 Using LLM: {settings.LLM_PROVIDER}/{settings.LLM_MODEL}")

    # Initialize components
    print_section("🔧 Initializing Components")

    # 1. Scraper
    config = ScraperConfig(
        email=email,
        password=password,
        headless=False,  # Show browser
        max_retries=3,
    )
    scraper = LinkedInScraper(config)

    # 2. DSPy Pipeline
    try:
        print("🧠 Initializing DSPy OpportunityAnalyzer...")
        analyzer = OpportunityAnalyzer()
        print("✅ OpportunityAnalyzer ready")

        print("✍️  Initializing DSPy ResponseGenerator...")
        generator = ResponseGenerator()
        print("✅ ResponseGenerator ready")

    except Exception as e:
        print(f"❌ Failed to initialize DSPy: {e}")
        print("\n💡 Make sure you have:")
        print("   - LLM_PROVIDER and LLM_MODEL set in .env")
        print("")
        print("   For Ollama (recommended):")
        print("     1. Install: curl -fsSL https://ollama.com/install.sh | sh")
        print("     2. Download model: ollama pull llama3.2")
        print("     3. Start Ollama: ollama serve")
        print("     4. In .env: LLM_PROVIDER=ollama, LLM_MODEL=llama3.2")
        print("")
        print("   For Anthropic:")
        print("     - ANTHROPIC_API_KEY set in .env")
        print("     - LLM_PROVIDER=anthropic")
        print("")
        print("   For OpenAI:")
        print("     - OPENAI_API_KEY set in .env")
        print("     - LLM_PROVIDER=openai")
        return

    try:
        # Step 1: Scrape messages
        print_section("📥 Step 1: Scraping LinkedIn Messages")

        print("🔐 Logging in to LinkedIn...")
        await scraper.initialize()
        print("✅ Login successful!")

        print("\n📨 Fetching messages...")
        messages = await scraper.scrape_messages(limit=10, unread_only=False)

        if not messages:
            print("❌ No messages found")
            return

        print(f"✅ Found {len(messages)} messages\n")

        # Step 2: Analyze and generate responses for each message
        processed_count = 0
        skipped_count = 0

        for i, msg in enumerate(messages, 1):
            print_section(f"📩 Message {i}/{len(messages)}")

            # Show original message
            print("👤 From:", msg.sender_name)
            print("📅 Date:", msg.timestamp.strftime("%Y-%m-%d %H:%M"))
            print("🔗 URL:", msg.conversation_url)

            # Show if message is from user
            if msg.is_from_user:
                print("⚠️  Last message is FROM YOU - Skipping response generation")

            print("\n💬 Original Message:")
            print("-" * 40)
            print(msg.message_text)
            print("-" * 40)

            # Skip processing if the last message is from the user
            if msg.is_from_user:
                print("\n⏭️  Skipping - waiting for recruiter's response\n")
                skipped_count += 1
                if i < len(messages):
                    print("\n" + "▼" * 80)
                continue

            # Analyze opportunity
            processed_count += 1
            print("\n🔍 Analyzing opportunity...")
            try:
                analysis = analyzer.analyze(
                    message=msg.message_text,
                    sender=msg.sender_name,
                )

                print("\n📊 Analysis Results:")
                print(f"   Company: {analysis.company_name or 'N/A'}")
                print(f"   Role: {analysis.role_title or 'N/A'}")
                print(f"   Salary: {analysis.salary_range or 'N/A'}")
                print(f"   Location: {analysis.location or 'N/A'}")
                print(f"   Work Mode: {analysis.work_mode or 'N/A'}")
                print(f"   Tech Stack: {', '.join(analysis.tech_stack) if analysis.tech_stack else 'N/A'}")
                print(f"\n   📈 Scores:")
                print(f"      Tech Match: {analysis.tech_match_score}/100")
                print(f"      Salary Match: {analysis.salary_match_score}/100")
                print(f"      Seniority Match: {analysis.seniority_match_score}/100")
                print(f"      Company Score: {analysis.company_score}/100")
                print(f"      TOTAL: {analysis.total_score}/100")
                print(f"\n   🎯 Tier: {analysis.tier}")
                print(f"   📝 Summary: {analysis.summary}")

                # Generate response
                print("\n✍️  Generating AI response...")

                response = generator.generate(
                    message=msg.message_text,
                    sender=msg.sender_name,
                    analysis=analysis,
                )

                print("\n🤖 Generated Response:")
                print("=" * 40)
                print(response.response_text)
                print("=" * 40)
                print(f"\n   Tone: {response.tone}")
                print(f"   Length: {response.length} characters")
                print(f"   Key Points: {', '.join(response.key_points)}")
                print(f"   Reasoning: {response.reasoning}")

            except Exception as e:
                print(f"\n❌ Error processing message: {e}")
                import traceback
                traceback.print_exc()
                continue

            # Divider between messages
            if i < len(messages):
                print("\n" + "▼" * 80)

        # Summary
        print_section("✅ Test Complete")
        print(f"📊 Total messages found: {len(messages)}")
        print(f"✅ Processed (from recruiters): {processed_count}")
        print(f"⏭️  Skipped (from you): {skipped_count}")
        print(f"🤖 Generated {processed_count} AI responses")
        print("\n💡 These responses were NOT sent to LinkedIn")
        print("   To send responses, use the full app workflow:")
        print("   1. Approve responses in the web UI")
        print("   2. Or use the send endpoint to send approved responses")

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
