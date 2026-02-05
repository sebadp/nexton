#!/usr/bin/env python3
"""
LinkedIn Agent Lite - Minimal version without infrastructure.

Just: scrape → process → email

No: Database, Celery, Redis, FastAPI, monitoring, Docker.

Usage:
    # With real LinkedIn scraping
    python scripts/run_lite.py

    # With sample messages (no LinkedIn login needed)
    python scripts/run_lite.py --sample

    # Limit number of messages
    python scripts/run_lite.py --limit 5

    # Skip email (just process and print)
    python scripts/run_lite.py --no-email

Requirements:
    pip install -r requirements-lite.txt
    playwright install chromium
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import cast

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path setup
from app.core.config import settings
from app.core.logging import get_logger
from app.dspy_modules.models import OpportunityResult
from app.dspy_modules.pipeline import configure_dspy, get_pipeline
from app.dspy_modules.profile_loader import get_profile
from app.notifications.service import NotificationService
from app.scraper import LinkedInMessage, LinkedInScraper, ScraperConfig

logger = get_logger(__name__)


# Sample messages for testing without LinkedIn login
SAMPLE_MESSAGES = [
    LinkedInMessage(
        sender_name="María García - Tech Recruiter",
        message_text="""Hola! Espero que estés bien.

Te contacto porque tenemos una posición de Senior Backend Engineer en TechCorp que creo encaja perfecto con tu perfil.

Detalles:
- Stack: Python, FastAPI, PostgreSQL, Redis, AWS
- Salario: $150,000 - $180,000 USD/año
- 100% Remoto
- Semana de 4 días laborales

¿Te interesaría saber más?

Saludos,
María""",
        timestamp=datetime.now(),
        conversation_url="https://linkedin.com/messaging/thread/1",
        is_read=False,
        is_from_user=False,
    ),
    LinkedInMessage(
        sender_name="John Smith - Amazon Recruiter",
        message_text="""Hi there!

I found your profile and thought you'd be a great fit for a Backend Developer position at Amazon.

Details:
- Tech: Java, Spring Boot, DynamoDB
- Salary: $120,000 - $140,000
- Hybrid (3 days office)
- Standard 5-day work week

Let me know if you're interested!

Best,
John""",
        timestamp=datetime.now(),
        conversation_url="https://linkedin.com/messaging/thread/2",
        is_read=False,
        is_from_user=False,
    ),
    LinkedInMessage(
        sender_name="Ana López",
        message_text="""Gracias por tu respuesta! Quedamos en contacto entonces.""",
        timestamp=datetime.now(),
        conversation_url="https://linkedin.com/messaging/thread/3",
        is_read=False,
        is_from_user=False,
    ),
    LinkedInMessage(
        sender_name="Carlos Mendez - Startup Founder",
        message_text="""Hola!

Estamos buscando un Tech Lead para nuestra startup fintech.

- Stack: Python, Django, React, Kubernetes
- Equity: 0.5%
- Salario: $90,000 USD
- Full remote
- Horario flexible

¿Podemos hablar?""",
        timestamp=datetime.now(),
        conversation_url="https://linkedin.com/messaging/thread/4",
        is_read=False,
        is_from_user=False,
    ),
    LinkedInMessage(
        sender_name="Recruiter at BigCorp",
        message_text="""¿Cuál es tu disponibilidad para empezar un nuevo proyecto?""",
        timestamp=datetime.now(),
        conversation_url="https://linkedin.com/messaging/thread/5",
        is_read=False,
        is_from_user=False,
    ),
]


def print_banner():
    """Print startup banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║           LinkedIn Agent Lite                             ║
║           No DB • No Redis • No Docker                    ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_result(idx: int, result: OpportunityResult):
    """Print a single result in a formatted way."""
    # Status emoji
    status_emoji = {
        "processed": "✅",
        "declined": "❌",
        "manual_review": "⚠️",
        "auto_responded": "↩️",
        "ignored": "⏭️",
    }.get(result.status, "❓")

    # Conversation state emoji
    state_emoji = {
        "NEW_OPPORTUNITY": "🆕",
        "FOLLOW_UP": "🔄",
        "COURTESY_CLOSE": "👋",
    }.get(result.conversation_state.state.value if result.conversation_state else "UNKNOWN", "❓")

    print(f"\n{'=' * 60}")
    print(f"Message #{idx + 1} {status_emoji} {state_emoji}")
    print(f"{'=' * 60}")
    print(f"From: {result.recruiter_name}")

    if result.conversation_state:
        print(f"State: {result.conversation_state.state.value}")
        print(f"  → {result.conversation_state.reasoning}")

    if result.status != "ignored":
        print("\nExtracted Data:")
        print(f"  Company: {result.extracted.company}")
        print(f"  Role: {result.extracted.role}")
        print(f"  Tech Stack: {', '.join(result.extracted.tech_stack) or 'N/A'}")
        print(f"  Seniority: {result.extracted.seniority}")

        if result.extracted.salary_min or result.extracted.salary_max:
            salary = f"${result.extracted.salary_min:,}" if result.extracted.salary_min else ""
            if result.extracted.salary_max:
                salary += f" - ${result.extracted.salary_max:,}"
            print(f"  Salary: {salary}")

        print("\nScoring:")
        print(f"  Total: {result.scoring.total_score}/100 ({result.scoring.tier})")
        print(f"  Tech Stack: {result.scoring.tech_stack_score}/40")
        print(f"  Salary: {result.scoring.salary_score}/30")
        print(f"  Seniority: {result.scoring.seniority_score}/20")
        print(f"  Company: {result.scoring.company_score}/10")

        if result.hard_filter_result:
            if result.hard_filter_result.failed_filters:
                print(f"\n⚠️  Failed Filters: {', '.join(result.hard_filter_result.failed_filters)}")
            if result.hard_filter_result.work_week_status != "UNKNOWN":
                print(f"  Work Week: {result.hard_filter_result.work_week_status}")

    if result.requires_manual_review:
        print("\n⚠️  MANUAL REVIEW REQUIRED")
        print(f"  Reason: {result.manual_review_reason}")

    if result.ai_response:
        print("\n💬 AI Response:")
        print("-" * 40)
        # Indent the response
        for line in result.ai_response.split("\n"):
            print(f"  {line}")
        print("-" * 40)

    print(f"\nProcessing time: {result.processing_time_ms}ms")


async def scrape_linkedin_messages(limit: int) -> list[LinkedInMessage]:
    """Scrape messages from LinkedIn."""
    logger.info("Starting LinkedIn scraper...")

    config = ScraperConfig(
        email=settings.LINKEDIN_EMAIL,
        password=settings.LINKEDIN_PASSWORD,
        headless=settings.SCRAPER_HEADLESS,
        max_requests_per_minute=settings.SCRAPER_RATE_LIMIT,
    )

    messages = []
    async with LinkedInScraper(config) as scraper:
        messages = await scraper.scrape_messages(limit=limit, unread_only=True)

    return cast(list[LinkedInMessage], messages)


async def process_messages(
    messages: list[LinkedInMessage],
) -> list[OpportunityResult]:
    """Process messages through the DSPy pipeline."""
    logger.info(f"Processing {len(messages)} messages...")

    # Get pipeline and profile
    pipeline = get_pipeline()
    profile = get_profile()

    results = []
    for idx, msg in enumerate(messages):
        # Skip messages from the user (we sent the last message)
        if msg.is_from_user:
            logger.info(f"Skipping message {idx + 1}: last message is from user")
            continue

        logger.info(f"Processing message {idx + 1}/{len(messages)} from {msg.sender_name}")

        try:
            result = pipeline.forward(
                message=msg.message_text,
                recruiter_name=msg.sender_name,
                profile=profile,
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process message {idx + 1}: {e}")
            continue

    return results


async def send_email_summary(results: list[OpportunityResult]) -> bool:
    """Send email summary of processed messages."""
    if not results:
        logger.info("No results to send")
        return False

    logger.info(f"Sending email summary with {len(results)} results...")

    service = NotificationService()
    success = await service.send_lite_summary(results)

    if success:
        logger.info("Email sent successfully!")
        print(f"\n📧 Email sent to: {settings.NOTIFICATION_EMAIL}")
        print("   View at: http://localhost:8025 (if using Mailpit)")
    else:
        logger.warning("Failed to send email or notifications disabled")

    return success


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LinkedIn Agent Lite - Process messages without infrastructure"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Use sample messages instead of scraping LinkedIn",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of messages to process (default: 10)",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip sending email summary",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    print_banner()

    # Configure DSPy
    print(f"🔧 Configuring DSPy with {settings.LLM_PROVIDER}/{settings.LLM_MODEL}...")
    configure_dspy()

    # Get messages
    if args.sample:
        print(f"📝 Using {len(SAMPLE_MESSAGES)} sample messages...")
        messages = SAMPLE_MESSAGES[: args.limit]
    else:
        print(f"🔍 Scraping LinkedIn messages (limit: {args.limit})...")
        if not settings.LINKEDIN_EMAIL or not settings.LINKEDIN_PASSWORD:
            print("\n❌ Error: LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env")
            print("   Use --sample flag to test with sample messages")
            sys.exit(1)
        messages = await scrape_linkedin_messages(args.limit)

    if not messages:
        print("\n📭 No messages to process")
        return

    print(f"\n📨 Found {len(messages)} messages to process")

    # Process messages
    results = await process_messages(messages)

    if not results:
        print("\n📭 No results after processing")
        return

    # Print results
    print(f"\n{'=' * 60}")
    print("RESULTS SUMMARY")
    print(f"{'=' * 60}")

    for idx, result in enumerate(results):
        print_result(idx, result)

    # Summary stats
    stats = {
        "processed": sum(1 for r in results if r.status == "processed"),
        "declined": sum(1 for r in results if r.status == "declined"),
        "manual_review": sum(1 for r in results if r.status == "manual_review"),
        "auto_responded": sum(1 for r in results if r.status == "auto_responded"),
        "ignored": sum(1 for r in results if r.status == "ignored"),
    }

    print(f"\n{'=' * 60}")
    print("FINAL STATS")
    print(f"{'=' * 60}")
    print(f"Total processed: {len(results)}")
    print(f"  ✅ Processed: {stats['processed']}")
    print(f"  ❌ Declined: {stats['declined']}")
    print(f"  ⚠️  Manual Review: {stats['manual_review']}")
    print(f"  ↩️  Auto-Responded: {stats['auto_responded']}")
    print(f"  ⏭️  Ignored: {stats['ignored']}")

    # Send email
    if not args.no_email:
        print("\n📧 Sending email summary...")
        await send_email_summary(results)
    else:
        print("\n📧 Skipping email (--no-email flag)")

    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
