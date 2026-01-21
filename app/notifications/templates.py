"""
Email templates for opportunity notifications.

Creates HTML emails with opportunity details and response suggestions.
"""

from app.notifications.models import DailySummaryEmail, LiteSummaryEmail, OpportunityEmail


def render_opportunity_email(email_data: OpportunityEmail) -> str:
    """
    Render HTML email for opportunity notification.

    Args:
        email_data: Email data including opportunity details

    Returns:
        str: HTML email body
    """
    # Tier color mapping
    tier_colors = {
        "A": "#10b981",  # Green
        "B": "#3b82f6",  # Blue
        "C": "#f59e0b",  # Orange
        "D": "#ef4444",  # Red
    }
    tier_color = tier_colors.get(email_data.tier, "#6b7280")

    # Score color based on value
    if email_data.total_score >= 80:
        score_color = "#10b981"  # Green
    elif email_data.total_score >= 60:
        score_color = "#3b82f6"  # Blue
    elif email_data.total_score >= 40:
        score_color = "#f59e0b"  # Orange
    else:
        score_color = "#ef4444"  # Red

    # Build tech stack HTML
    tech_stack_html = "".join(
        f'<span style="display: inline-block; background: #e5e7eb; padding: 4px 12px; '
        f'border-radius: 12px; margin: 4px; font-size: 13px;">{tech}</span>'
        for tech in email_data.tech_stack
    )

    # Build response section if available
    response_section = ""
    if email_data.suggested_response:
        response_section = f"""
        <div style="margin: 24px 0; padding: 20px; background: #f9fafb; border-left: 4px solid #3b82f6; border-radius: 8px;">
            <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 16px;">
                💬 Suggested Response
            </h3>
            <p style="margin: 0; color: #4b5563; line-height: 1.6; white-space: pre-wrap;">
                {email_data.suggested_response}
            </p>
        </div>
        """

    # Build action buttons
    action_buttons = ""
    if email_data.approve_url or email_data.edit_url or email_data.decline_url:
        buttons = []

        if email_data.approve_url:
            buttons.append(
                f'<a href="{email_data.approve_url}" style="display: inline-block; '
                f'background: #10b981; color: white; padding: 12px 24px; text-decoration: none; '
                f'border-radius: 6px; font-weight: 600; margin-right: 8px;">✓ Approve & Send</a>'
            )

        if email_data.edit_url:
            buttons.append(
                f'<a href="{email_data.edit_url}" style="display: inline-block; '
                f'background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; '
                f'border-radius: 6px; font-weight: 600; margin-right: 8px;">✏️ Edit Response</a>'
            )

        if email_data.decline_url:
            buttons.append(
                f'<a href="{email_data.decline_url}" style="display: inline-block; '
                f'background: #6b7280; color: white; padding: 12px 24px; text-decoration: none; '
                f'border-radius: 6px; font-weight: 600;">✗ Decline</a>'
            )

        action_buttons = f"""
        <div style="margin: 24px 0; padding: 20px; background: white; border: 2px solid #e5e7eb; border-radius: 8px; text-align: center;">
            {"".join(buttons)}
        </div>
        """

    # Build complete HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LinkedIn Opportunity</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f3f4f6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 32px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="margin: 0; color: white; font-size: 24px; font-weight: 700;">
                    🎯 New LinkedIn Opportunity
                </h1>
            </div>

            <!-- Content -->
            <div style="background: white; padding: 32px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <!-- Tier Badge -->
                <div style="margin-bottom: 24px;">
                    <span style="display: inline-block; background: {tier_color}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: 700; font-size: 14px;">
                        Tier {email_data.tier}
                    </span>
                    <span style="display: inline-block; background: {score_color}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: 700; font-size: 14px; margin-left: 8px;">
                        Score: {email_data.total_score}/100
                    </span>
                </div>

                <!-- Opportunity Details -->
                <div style="margin-bottom: 24px;">
                    <div style="margin-bottom: 16px;">
                        <p style="margin: 0 0 4px 0; color: #6b7280; font-size: 13px; font-weight: 600; text-transform: uppercase;">
                            From
                        </p>
                        <p style="margin: 0; color: #1f2937; font-size: 16px; font-weight: 600;">
                            {email_data.recruiter_name}
                        </p>
                    </div>

                    <div style="margin-bottom: 16px;">
                        <p style="margin: 0 0 4px 0; color: #6b7280; font-size: 13px; font-weight: 600; text-transform: uppercase;">
                            Company
                        </p>
                        <p style="margin: 0; color: #1f2937; font-size: 16px; font-weight: 600;">
                            {email_data.company}
                        </p>
                    </div>

                    <div style="margin-bottom: 16px;">
                        <p style="margin: 0 0 4px 0; color: #6b7280; font-size: 13px; font-weight: 600; text-transform: uppercase;">
                            Position
                        </p>
                        <p style="margin: 0; color: #1f2937; font-size: 16px; font-weight: 600;">
                            {email_data.position}
                        </p>
                    </div>

                    <div style="margin-bottom: 16px;">
                        <p style="margin: 0 0 4px 0; color: #6b7280; font-size: 13px; font-weight: 600; text-transform: uppercase;">
                            Salary Range
                        </p>
                        <p style="margin: 0; color: #1f2937; font-size: 16px; font-weight: 600;">
                            {email_data.salary_range}
                        </p>
                    </div>

                    <div>
                        <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 13px; font-weight: 600; text-transform: uppercase;">
                            Tech Stack
                        </p>
                        <div style="margin: 0;">
                            {tech_stack_html}
                        </div>
                    </div>
                </div>

                <!-- Suggested Response -->
                {response_section}

                <!-- Action Buttons -->
                {action_buttons}

                <!-- Footer -->
                <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #e5e7eb; text-align: center;">
                    <p style="margin: 0; color: #6b7280; font-size: 13px;">
                        LinkedIn AI Agent • Opportunity ID: {email_data.opportunity_id}
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def render_daily_summary_email(email_data: DailySummaryEmail) -> str:
    """
    Render HTML email for daily opportunity summary.

    Args:
        email_data: Email data including list of opportunities

    Returns:
        str: HTML email body
    """
    # Tier color mapping
    tier_colors = {
        "HIGH_PRIORITY": "#10b981",  # Green
        "INTERESANTE": "#3b82f6",  # Blue
        "POCO_INTERESANTE": "#f59e0b",  # Orange
        "NO_INTERESA": "#ef4444",  # Red
    }

    # Build opportunity cards HTML
    opportunity_cards = []
    for opp in email_data.opportunities:
        # Format salary range
        if opp.salary_min and opp.salary_max:
            salary_range = (
                f"{opp.currency}{opp.salary_min:,} - "
                f"{opp.currency}{opp.salary_max:,}"
            )
        elif opp.salary_min:
            salary_range = f"{opp.currency}{opp.salary_min:,}+"
        else:
            salary_range = "Not specified"

        # Tier color
        tier_color = tier_colors.get(opp.tier, "#6b7280")

        # Score color
        if opp.total_score >= 80:
            score_color = "#10b981"
        elif opp.total_score >= 60:
            score_color = "#3b82f6"
        elif opp.total_score >= 40:
            score_color = "#f59e0b"
        else:
            score_color = "#ef4444"

        # Tech stack HTML
        tech_stack_html = "".join(
            f'<span style="display: inline-block; background: #e5e7eb; padding: 3px 10px; '
            f'border-radius: 10px; margin: 3px; font-size: 12px;">{tech}</span>'
            for tech in (opp.tech_stack or [])
        )

        # Response section
        response_section = ""
        if opp.ai_response:
            # Truncate long responses
            response_preview = opp.ai_response
            if len(response_preview) > 300:
                response_preview = response_preview[:297] + "..."

            response_section = f"""
            <div style="margin: 16px 0; padding: 16px; background: #f9fafb; border-left: 3px solid #3b82f6; border-radius: 6px;">
                <p style="margin: 0 0 8px 0; color: #1f2937; font-size: 13px; font-weight: 600;">
                    💬 Suggested Response:
                </p>
                <p style="margin: 0; color: #4b5563; font-size: 13px; line-height: 1.5; white-space: pre-wrap;">
                    {response_preview}
                </p>
            </div>
            """

        # Build opportunity card
        card_html = f"""
        <div style="background: white; border: 2px solid #e5e7eb; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);">
            <!-- Tier and Score -->
            <div style="margin-bottom: 16px;">
                <span style="display: inline-block; background: {tier_color}; color: white; padding: 6px 14px; border-radius: 16px; font-weight: 700; font-size: 13px;">
                    {opp.tier}
                </span>
                <span style="display: inline-block; background: {score_color}; color: white; padding: 6px 14px; border-radius: 16px; font-weight: 700; font-size: 13px; margin-left: 8px;">
                    {opp.total_score}/100
                </span>
            </div>

            <!-- Details -->
            <div style="margin-bottom: 12px;">
                <p style="margin: 0 0 4px 0; color: #6b7280; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                    From
                </p>
                <p style="margin: 0; color: #1f2937; font-size: 15px; font-weight: 600;">
                    {opp.recruiter_name}
                </p>
            </div>

            <div style="margin-bottom: 12px;">
                <p style="margin: 0 0 4px 0; color: #6b7280; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                    Company & Position
                </p>
                <p style="margin: 0; color: #1f2937; font-size: 15px; font-weight: 600;">
                    {opp.company or "Unknown"} - {opp.role or "Unknown"}
                </p>
            </div>

            <div style="margin-bottom: 12px;">
                <p style="margin: 0 0 4px 0; color: #6b7280; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                    Salary
                </p>
                <p style="margin: 0; color: #1f2937; font-size: 15px; font-weight: 600;">
                    {salary_range}
                </p>
            </div>

            <div style="margin-bottom: 12px;">
                <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                    Tech Stack
                </p>
                <div>
                    {tech_stack_html or '<span style="color: #9ca3af; font-size: 13px;">Not specified</span>'}
                </div>
            </div>

            <!-- AI Response -->
            {response_section}
        </div>
        """
        opportunity_cards.append(card_html)

    # Join all cards
    all_cards_html = "".join(opportunity_cards)

    # Build complete HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily LinkedIn Summary</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f3f4f6;">
        <div style="max-width: 700px; margin: 0 auto; padding: 20px;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="margin: 0 0 8px 0; color: white; font-size: 28px; font-weight: 700;">
                    📊 Daily LinkedIn Summary
                </h1>
                <p style="margin: 0; color: rgba(255, 255, 255, 0.9); font-size: 16px;">
                    {email_data.date} • {email_data.total_count} new opportunit{"y" if email_data.total_count == 1 else "ies"}
                </p>
            </div>

            <!-- Content -->
            <div style="background: #fafafa; padding: 32px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <!-- Opportunities -->
                {all_cards_html}

                <!-- Footer -->
                <div style="margin-top: 32px; padding-top: 24px; border-top: 2px solid #e5e7eb; text-align: center;">
                    <p style="margin: 0 0 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">
                        View all opportunities in your dashboard
                    </p>
                    <p style="margin: 0; color: #6b7280; font-size: 13px;">
                        LinkedIn AI Agent • Daily Summary
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def render_lite_summary_email(email_data: LiteSummaryEmail) -> str:
    """
    Render HTML email for lite mode summary (uses OpportunityResult directly).

    Args:
        email_data: Email data including list of OpportunityResult

    Returns:
        str: HTML email body
    """
    # Status colors and icons
    status_config = {
        "processed": {"color": "#10b981", "icon": "&#10003;", "label": "Processed"},
        "declined": {"color": "#ef4444", "icon": "&#10007;", "label": "Declined"},
        "manual_review": {"color": "#f59e0b", "icon": "&#9888;", "label": "Review Required"},
        "auto_responded": {"color": "#3b82f6", "icon": "&#8617;", "label": "Auto-Responded"},
        "ignored": {"color": "#9ca3af", "icon": "&#8212;", "label": "Ignored"},
    }

    # Tier colors
    tier_colors = {
        "HIGH_PRIORITY": "#10b981",
        "INTERESANTE": "#3b82f6",
        "POCO_INTERESANTE": "#f59e0b",
        "NO_INTERESA": "#ef4444",
    }

    # Build result cards
    result_cards = []
    for result in email_data.results:
        # Get status config
        status = status_config.get(result.status, status_config["processed"])

        # Get tier and score
        tier = result.scoring.tier if result.scoring else "N/A"
        score = result.scoring.total_score if result.scoring else 0
        tier_color = tier_colors.get(tier, "#6b7280")

        # Score color
        if score >= 75:
            score_color = "#10b981"
        elif score >= 50:
            score_color = "#3b82f6"
        elif score >= 30:
            score_color = "#f59e0b"
        else:
            score_color = "#ef4444"

        # Get conversation state
        state = result.conversation_state.state.value if result.conversation_state else "UNKNOWN"
        state_label = {
            "NEW_OPPORTUNITY": "New Opportunity",
            "FOLLOW_UP": "Follow-Up",
            "COURTESY_CLOSE": "Courtesy",
        }.get(state, state)

        # Tech stack HTML
        tech_stack_html = "".join(
            f'<span style="display: inline-block; background: #e5e7eb; padding: 3px 10px; '
            f'border-radius: 10px; margin: 3px; font-size: 12px;">{tech}</span>'
            for tech in (result.extracted.tech_stack or [])
        )

        # Hard filter section
        hard_filter_section = ""
        if result.hard_filter_result and result.hard_filter_result.failed_filters:
            failed_filters_html = "".join(
                f'<span style="display: inline-block; background: #fee2e2; color: #dc2626; padding: 3px 10px; '
                f'border-radius: 10px; margin: 3px; font-size: 12px;">{f}</span>'
                for f in result.hard_filter_result.failed_filters
            )
            hard_filter_section = f"""
            <div style="margin: 12px 0; padding: 12px; background: #fef2f2; border-radius: 6px;">
                <p style="margin: 0 0 8px 0; color: #dc2626; font-size: 12px; font-weight: 600;">
                    Failed Filters:
                </p>
                <div>{failed_filters_html}</div>
            </div>
            """

        # Response section
        response_section = ""
        if result.ai_response:
            response_preview = result.ai_response
            if len(response_preview) > 400:
                response_preview = response_preview[:397] + "..."

            response_section = f"""
            <div style="margin: 16px 0; padding: 16px; background: #f9fafb; border-left: 3px solid #3b82f6; border-radius: 6px;">
                <p style="margin: 0 0 8px 0; color: #1f2937; font-size: 13px; font-weight: 600;">
                    AI Response:
                </p>
                <p style="margin: 0; color: #4b5563; font-size: 13px; line-height: 1.5; white-space: pre-wrap;">
                    {response_preview}
                </p>
            </div>
            """

        # Manual review section
        manual_review_section = ""
        if result.requires_manual_review:
            reason = result.manual_review_reason or "Requires human review"
            manual_review_section = f"""
            <div style="margin: 16px 0; padding: 16px; background: #fef3c7; border-left: 3px solid #f59e0b; border-radius: 6px;">
                <p style="margin: 0 0 8px 0; color: #92400e; font-size: 13px; font-weight: 600;">
                    Manual Review Required
                </p>
                <p style="margin: 0; color: #78350f; font-size: 13px; line-height: 1.5;">
                    {reason}
                </p>
            </div>
            """

        # Build card
        card_html = f"""
        <div style="background: white; border: 2px solid #e5e7eb; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);">
            <!-- Status and Tier -->
            <div style="margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 8px;">
                <span style="display: inline-block; background: {status['color']}; color: white; padding: 6px 14px; border-radius: 16px; font-weight: 700; font-size: 13px;">
                    {status['icon']} {status['label']}
                </span>
                <span style="display: inline-block; background: {tier_color}; color: white; padding: 6px 14px; border-radius: 16px; font-weight: 700; font-size: 13px;">
                    {tier}
                </span>
                <span style="display: inline-block; background: {score_color}; color: white; padding: 6px 14px; border-radius: 16px; font-weight: 700; font-size: 13px;">
                    {score}/100
                </span>
                <span style="display: inline-block; background: #e5e7eb; color: #374151; padding: 6px 14px; border-radius: 16px; font-size: 13px;">
                    {state_label}
                </span>
            </div>

            <!-- Details -->
            <div style="margin-bottom: 12px;">
                <p style="margin: 0 0 4px 0; color: #6b7280; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                    From
                </p>
                <p style="margin: 0; color: #1f2937; font-size: 15px; font-weight: 600;">
                    {result.recruiter_name}
                </p>
            </div>

            <div style="margin-bottom: 12px;">
                <p style="margin: 0 0 4px 0; color: #6b7280; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                    Company & Role
                </p>
                <p style="margin: 0; color: #1f2937; font-size: 15px; font-weight: 600;">
                    {result.extracted.company or "Unknown"} - {result.extracted.role or "Unknown"}
                </p>
            </div>

            <div style="margin-bottom: 12px;">
                <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                    Tech Stack
                </p>
                <div>
                    {tech_stack_html or '<span style="color: #9ca3af; font-size: 13px;">Not specified</span>'}
                </div>
            </div>

            <!-- Hard Filters -->
            {hard_filter_section}

            <!-- Manual Review -->
            {manual_review_section}

            <!-- AI Response -->
            {response_section}
        </div>
        """
        result_cards.append(card_html)

    all_cards_html = "".join(result_cards)

    # Build summary stats
    stats = {
        "processed": sum(1 for r in email_data.results if r.status == "processed"),
        "declined": sum(1 for r in email_data.results if r.status == "declined"),
        "manual_review": sum(1 for r in email_data.results if r.status == "manual_review"),
        "auto_responded": sum(1 for r in email_data.results if r.status == "auto_responded"),
    }

    # Build complete HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LinkedIn Agent Lite Summary</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f3f4f6;">
        <div style="max-width: 700px; margin: 0 auto; padding: 20px;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #059669 0%, #0891b2 100%); padding: 40px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="margin: 0 0 8px 0; color: white; font-size: 28px; font-weight: 700;">
                    LinkedIn Agent Lite
                </h1>
                <p style="margin: 0; color: rgba(255, 255, 255, 0.9); font-size: 16px;">
                    {email_data.date} &bull; {email_data.total_count} message{"s" if email_data.total_count != 1 else ""} processed
                </p>
            </div>

            <!-- Stats Bar -->
            <div style="background: #1f2937; padding: 16px 24px; display: flex; justify-content: space-around; flex-wrap: wrap;">
                <div style="text-align: center; padding: 8px 16px;">
                    <p style="margin: 0; color: #10b981; font-size: 24px; font-weight: 700;">{stats['processed']}</p>
                    <p style="margin: 0; color: #9ca3af; font-size: 12px;">Processed</p>
                </div>
                <div style="text-align: center; padding: 8px 16px;">
                    <p style="margin: 0; color: #ef4444; font-size: 24px; font-weight: 700;">{stats['declined']}</p>
                    <p style="margin: 0; color: #9ca3af; font-size: 12px;">Declined</p>
                </div>
                <div style="text-align: center; padding: 8px 16px;">
                    <p style="margin: 0; color: #f59e0b; font-size: 24px; font-weight: 700;">{stats['manual_review']}</p>
                    <p style="margin: 0; color: #9ca3af; font-size: 12px;">Review</p>
                </div>
                <div style="text-align: center; padding: 8px 16px;">
                    <p style="margin: 0; color: #3b82f6; font-size: 24px; font-weight: 700;">{stats['auto_responded']}</p>
                    <p style="margin: 0; color: #9ca3af; font-size: 12px;">Auto</p>
                </div>
            </div>

            <!-- Content -->
            <div style="background: #fafafa; padding: 32px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <!-- Result Cards -->
                {all_cards_html}

                <!-- Footer -->
                <div style="margin-top: 32px; padding-top: 24px; border-top: 2px solid #e5e7eb; text-align: center;">
                    <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 13px;">
                        LinkedIn AI Agent Lite &bull; No Database Required
                    </p>
                    <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                        Run again: python scripts/run_lite.py
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return html
