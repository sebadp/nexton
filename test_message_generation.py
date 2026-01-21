#!/usr/bin/env python
"""
Test script for LinkedIn scraper + DSPy message generation.

Scrapes real LinkedIn messages and generates AI responses without sending.
Updated to show conversation state analysis and hard filter results.
"""


import asyncio
import os
from datetime import datetime

# Load environment variables FIRST, before importing app modules
from dotenv import load_dotenv
load_dotenv()

from app.scraper.linkedin_scraper import LinkedInScraper, ScraperConfig
from app.dspy_modules.pipeline import OpportunityPipeline, configure_dspy
from app.dspy_modules.profile_loader import get_profile, get_profile_dict
from app.dspy_modules.models import ConversationState
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


def get_state_emoji(state: ConversationState) -> str:
    """Get emoji for conversation state."""
    return {
        ConversationState.NEW_OPPORTUNITY: "🆕",
        ConversationState.FOLLOW_UP: "🔄",
        ConversationState.COURTESY_CLOSE: "👋",
    }.get(state, "❓")


def get_status_emoji(status: str) -> str:
    """Get emoji for processing status."""
    return {
        "processed": "✅",
        "ignored": "🚫",
        "declined": "❌",
        "manual_review": "👀",
        "auto_responded": "🤖",
    }.get(status, "❓")


async def main():
    """Test message generation pipeline."""
    # Get credentials
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email or not password:
        print("Error: LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env")
        return

    print_header("LinkedIn Message Generation Test (v2 - with Conversation State)")
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print(f"Using LLM: {settings.LLM_PROVIDER}/{settings.LLM_MODEL}")

    # Initialize components
    print_section("Initializing Components")

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
        print("Configuring DSPy...")
        configure_dspy()
        print("DSPy configured")

        print("Initializing OpportunityPipeline...")
        pipeline = OpportunityPipeline()
        print("Pipeline ready")

        print("Loading candidate profile...")
        profile = get_profile()
        profile_dict = get_profile_dict()
        print(f"Profile loaded: {profile.name}")
        print(f"  - Preferred work week: {profile_dict.get('preferred_work_week', '5-days')}")
        print(f"  - Minimum salary: ${profile.minimum_salary_usd:,} USD")
        print(f"  - Remote policy: {profile.preferred_remote_policy}")

        # Show job search status
        job_status = profile_dict.get("job_search_status", {})
        print(f"  - Urgency: {job_status.get('urgency', 'moderate')}")
        print(f"  - Must-have requirements:")
        for req in job_status.get("must_have", [])[:3]:
            print(f"      * {req}")

    except Exception as e:
        print(f"Failed to initialize DSPy: {e}")
        print("\nMake sure you have:")
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
        print_section("Step 1: Scraping LinkedIn Messages")

        print("Logging in to LinkedIn...")
        await scraper.initialize()
        print("Login successful!")

        print("\nFetching messages...")
        messages = await scraper.scrape_messages(limit=10, unread_only=False)

        if not messages:
            print("No messages found")
            return

        print(f"Found {len(messages)} messages\n")

        # Step 2: Analyze and generate responses for each message
        stats = {
            "total": len(messages),
            "processed": 0,
            "ignored": 0,
            "declined": 0,
            "manual_review": 0,
            "auto_responded": 0,
            "skipped_from_user": 0,
        }

        for i, msg in enumerate(messages, 1):
            print_section(f"Message {i}/{len(messages)}")

            # Show original message
            print("From:", msg.sender_name)
            print("Date:", msg.timestamp.strftime("%Y-%m-%d %H:%M"))
            print("URL:", msg.conversation_url)

            # Show if message is from user
            if msg.is_from_user:
                print("\n[Last message is FROM YOU - Skipping response generation]")

            print("\nOriginal Message:")
            print("-" * 40)
            print(msg.message_text[:500] + ("..." if len(msg.message_text) > 500 else ""))
            print("-" * 40)

            # Skip processing if the last message is from the user
            if msg.is_from_user:
                print("\nSkipping - waiting for recruiter's response\n")
                stats["skipped_from_user"] += 1
                if i < len(messages):
                    print("\n" + "=" * 80)
                continue

            # Process through pipeline
            print("\nProcessing through pipeline...")
            try:
                result = pipeline.forward(
                    message=msg.message_text,
                    recruiter_name=msg.sender_name,
                    profile=profile,
                )

                # Show conversation state analysis
                print("\n--- CONVERSATION STATE ANALYSIS ---")
                if result.conversation_state:
                    state = result.conversation_state
                    emoji = get_state_emoji(state.state)
                    print(f"   State: {emoji} {state.state.value}")
                    print(f"   Confidence: {state.confidence}")
                    print(f"   Contains job details: {'Yes' if state.contains_job_details else 'No'}")
                    print(f"   Should process: {'Yes' if state.should_process else 'No'}")
                    print(f"   Reasoning: {state.reasoning}")

                # If ignored (courtesy close), show minimal info
                if result.status == "ignored":
                    print("\n--- RESULT: IGNORED (No response needed) ---")
                    print(f"   Status: {get_status_emoji(result.status)} {result.status.upper()}")
                    print("   AI Response: [None - courtesy message detected]")
                    stats["ignored"] += 1
                    if i < len(messages):
                        print("\n" + "=" * 80)
                    continue

                # Show extracted data
                print("\n--- EXTRACTED DATA ---")
                print(f"   Company: {result.extracted.company}")
                print(f"   Role: {result.extracted.role}")
                print(f"   Seniority: {result.extracted.seniority}")
                print(f"   Tech Stack: {', '.join(result.extracted.tech_stack[:5]) if result.extracted.tech_stack else 'N/A'}")
                print(f"   Salary: ", end="")
                if result.extracted.salary_min:
                    if result.extracted.salary_max:
                        print(f"${result.extracted.salary_min:,} - ${result.extracted.salary_max:,} {result.extracted.currency}")
                    else:
                        print(f"${result.extracted.salary_min:,}+ {result.extracted.currency}")
                else:
                    print("Not mentioned")
                print(f"   Remote Policy: {result.extracted.remote_policy}")
                print(f"   Work Week: {result.extracted.work_week}")

                # Show scoring
                print("\n--- SCORING ---")
                print(f"   Tech Match: {result.scoring.tech_stack_score}/40 ({result.scoring.tech_stack_score/40*100:.0f}%)")
                print(f"   Salary: {result.scoring.salary_score}/30")
                print(f"   Seniority: {result.scoring.seniority_score}/20")
                print(f"   Company: {result.scoring.company_score}/10")
                print(f"   TOTAL: {result.scoring.total_score}/100")
                print(f"   Tier: {result.scoring.tier}")

                # Show hard filter results
                print("\n--- HARD FILTER VALIDATION ---")
                if result.hard_filter_result:
                    hf = result.hard_filter_result
                    print(f"   All filters passed: {'Yes' if hf.passed else 'NO'}")
                    print(f"   Work week status: {hf.work_week_status}")
                    print(f"   Score penalty: -{hf.score_penalty} points")
                    print(f"   Should decline: {'YES' if hf.should_decline else 'No'}")
                    if hf.failed_filters:
                        print(f"   Failed filters:")
                        for f in hf.failed_filters:
                            print(f"      * {f}")

                # Show follow-up analysis if present
                if result.follow_up_analysis:
                    print("\n--- FOLLOW-UP ANALYSIS ---")
                    fa = result.follow_up_analysis
                    print(f"   Question type: {fa.question_type or 'NONE'}")
                    print(f"   Can auto-respond: {'Yes' if fa.can_auto_respond else 'No'}")
                    print(f"   Requires context: {'Yes' if fa.requires_context else 'No'}")
                    if fa.detected_question:
                        print(f"   Detected question: {fa.detected_question}")
                    print(f"   Reasoning: {fa.reasoning}")

                # Show final status and response
                print("\n--- RESULT ---")
                print(f"   Status: {get_status_emoji(result.status)} {result.status.upper()}")
                print(f"   Processing time: {result.processing_time_ms}ms")

                # Show manual review info if applicable
                if result.requires_manual_review:
                    print(f"   Requires manual review: YES")
                    if result.manual_review_reason:
                        print(f"   Reason: {result.manual_review_reason[:100]}...")

                # Update stats
                if result.status == "declined":
                    stats["declined"] += 1
                elif result.status == "manual_review":
                    stats["manual_review"] += 1
                elif result.status == "auto_responded":
                    stats["auto_responded"] += 1
                else:
                    stats["processed"] += 1

                # Show generated response
                print("\n--- GENERATED RESPONSE ---")
                print("=" * 40)
                if result.ai_response:
                    print(result.ai_response)
                elif result.requires_manual_review:
                    print("[No auto-response - MANUAL REVIEW REQUIRED]")
                    print("This message needs your personal attention.")
                else:
                    print("[No response generated]")
                print("=" * 40)

            except Exception as e:
                print(f"\nError processing message: {e}")
                import traceback
                traceback.print_exc()
                continue

            # Divider between messages
            if i < len(messages):
                print("\n" + "=" * 80)

        # Summary
        print_section("Test Complete - Summary")
        print(f"Total messages found: {stats['total']}")
        print(f"Skipped (from you): {stats['skipped_from_user']}")
        print(f"Processed (new opportunities): {stats['processed']}")
        print(f"Ignored (courtesy messages): {stats['ignored']}")
        print(f"Declined (failed hard filters): {stats['declined']}")
        print(f"Manual review required: {stats['manual_review']}")
        print(f"Auto-responded (follow-ups): {stats['auto_responded']}")
        print("\nThese responses were NOT sent to LinkedIn")
        print("   To send responses, use the full app workflow:")
        print("   1. Approve responses in the web UI")
        print("   2. Or use the send endpoint to send approved responses")
        if stats['manual_review'] > 0:
            print(f"\n   Note: {stats['manual_review']} message(s) require manual review")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nCleaning up...")
        await scraper.cleanup()
        print("Done!")


async def test_with_sample_messages():
    """Test pipeline with sample messages (no LinkedIn login required)."""
    print_header("Testing Pipeline with Sample Messages")

    # Sample messages to test different scenarios
    sample_messages = [
        # NEW_OPPORTUNITY - Standard job offer
        {
            "sender": "María García",
            "message": """Hola Sebastián!

            Vi tu perfil y me parece muy interesante. Estamos buscando un Senior Backend Engineer
            para TechCorp, una empresa de AI/ML con sede en San Francisco.

            El puesto es 100% remoto, con un salario de $120,000-$150,000 USD anuales.
            Stack: Python, FastAPI, PostgreSQL, AWS.

            ¿Te interesaría saber más?

            Saludos,
            María"""
        },
        # COURTESY_CLOSE - Simple thanks (should be ignored)
        {
            "sender": "Juan Pérez",
            "message": "Gracias por tu respuesta, quedamos en contacto!"
        },
        # COURTESY_CLOSE - Short acknowledgment (should be ignored)
        {
            "sender": "Ana López",
            "message": "Ok, perfecto"
        },
        # NEW_OPPORTUNITY - Low salary, should decline
        {
            "sender": "Carlos Ruiz",
            "message": """Hola!

            Tenemos una posición de Python Developer en una consultora.
            Es presencial en Buenos Aires, 5 días a la semana.
            Salario: $50,000 USD.

            ¿Te interesa?"""
        },
        # NEW_OPPORTUNITY - 4-day week mentioned, should process well
        {
            "sender": "Laura Martínez",
            "message": """Hi Sebastián,

            We have a Staff Engineer position at a 4-day work week company!
            Remote-first, $140,000-$180,000 USD, focused on AI/ML products.
            Tech: Python, LangChain, FastAPI, Kubernetes.

            Would you like to chat this week?"""
        },
        # FOLLOW_UP - Vague response (should require MANUAL_REVIEW)
        {
            "sender": "Pedro González",
            "message": "Sure, Sebastián! mandame si queres un mensajito"
        },
        # FOLLOW_UP - Clear salary question (should auto-respond)
        {
            "sender": "Sofia Torres",
            "message": "Gracias por tu interés! ¿Cuál es tu expectativa salarial?"
        },
        # FOLLOW_UP - Availability question (should auto-respond)
        {
            "sender": "Diego Fernández",
            "message": "Perfecto! ¿Cuándo podrías empezar si avanzamos con el proceso?"
        },
        # FOLLOW_UP - Vague message (should require MANUAL_REVIEW)
        {
            "sender": "Elena Ruiz",
            "message": "Buenísimo! Te cuento más la semana que viene."
        },
    ]

    try:
        print("Configuring DSPy...")
        configure_dspy()

        print("Initializing OpportunityPipeline...")
        pipeline = OpportunityPipeline()

        print("Loading candidate profile...")
        profile = get_profile()
        profile_dict = get_profile_dict()
        print(f"Profile: {profile.name}")
        print(f"Preferred work week: {profile_dict.get('preferred_work_week', '5-days')}")
        print(f"Minimum salary: ${profile.minimum_salary_usd:,} USD")

        for i, sample in enumerate(sample_messages, 1):
            print_section(f"Sample Message {i}/{len(sample_messages)}")
            print(f"From: {sample['sender']}")
            print(f"\nMessage:\n{sample['message']}\n")

            result = pipeline.forward(
                message=sample["message"],
                recruiter_name=sample["sender"],
                profile=profile,
            )

            # Conversation state
            if result.conversation_state:
                state = result.conversation_state
                emoji = get_state_emoji(state.state)
                print(f"Conversation State: {emoji} {state.state.value}")
                print(f"   Reasoning: {state.reasoning}")

            # Quick summary based on status
            print(f"\nStatus: {get_status_emoji(result.status)} {result.status.upper()}")

            if result.status not in ["ignored", "manual_review"]:
                print(f"Score: {result.scoring.total_score}/100 ({result.scoring.tier})")

                if result.hard_filter_result and result.hard_filter_result.failed_filters:
                    print(f"Failed filters: {', '.join(result.hard_filter_result.failed_filters)}")

            # Show follow-up analysis if present
            if result.follow_up_analysis:
                fa = result.follow_up_analysis
                print(f"\nFollow-up Analysis:")
                print(f"   Question type: {fa.question_type or 'NONE'}")
                print(f"   Can auto-respond: {'Yes' if fa.can_auto_respond else 'No'}")
                if fa.detected_question:
                    print(f"   Detected: {fa.detected_question}")

            # Show manual review info
            if result.requires_manual_review:
                print(f"\nManual Review Required: YES")
                if result.manual_review_reason:
                    print(f"   Reason: {result.manual_review_reason[:80]}...")

            print(f"\nGenerated Response:")
            print("-" * 40)
            if result.ai_response:
                print(result.ai_response)
            elif result.requires_manual_review:
                print("[No auto-response - MANUAL REVIEW REQUIRED]")
            else:
                print("[No response - message ignored]")
            print("-" * 40)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        # Test with sample messages (no LinkedIn login)
        asyncio.run(test_with_sample_messages())
    else:
        # Test with real LinkedIn messages
        asyncio.run(main())