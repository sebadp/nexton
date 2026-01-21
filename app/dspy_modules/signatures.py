"""
DSPy Signatures - Define input/output types for LLM modules.

Signatures describe what the LLM should do and what format
it should return data in.
"""
import dspy


class ConversationStateSignature(dspy.Signature):
    """
    Analyze the conversation context to determine the type of message.

    This signature identifies whether a message is a new job opportunity,
    a follow-up to previous communication, or a simple courtesy/closing message
    that doesn't require a response.

    IMPORTANT: Be conservative. Only classify as NEW_OPPORTUNITY if the message
    clearly contains a job offer or recruitment pitch with substantive details.
    """

    # Input
    message: str = dspy.InputField(
        desc="Raw LinkedIn message from recruiter"
    )

    # Outputs
    conversation_state: str = dspy.OutputField(
        desc="""Classify the message into ONE of these categories:
        - NEW_OPPORTUNITY: A recruiter is presenting a new job/role with details (company, position, requirements). Must contain substantive job information.
        - FOLLOW_UP: The recruiter is responding to something the candidate previously said or asked. Includes answers to questions, clarifications, or continuing a discussion.
        - COURTESY_CLOSE: Simple acknowledgment or closing messages like "Gracias", "Perfecto", "Ok", "Dale", "Quedamos así", "Suerte", "Éxitos". These are polite endings, NOT new opportunities.

        CRITICAL: Short messages without job details (even if from recruiters) should be COURTESY_CLOSE, not NEW_OPPORTUNITY.
        A message saying just "Ok" or "Gracias" is NEVER a new opportunity, even if it's about a job conversation."""
    )

    confidence: str = dspy.OutputField(
        desc="Confidence level: HIGH, MEDIUM, or LOW"
    )

    reasoning: str = dspy.OutputField(
        desc="Brief explanation of why this classification was chosen"
    )

    contains_job_details: str = dspy.OutputField(
        desc="YES if the message contains actual job information (company name, role title, tech stack, salary, etc.). NO if it's just a short reply or acknowledgment."
    )


class FollowUpAnalysisSignature(dspy.Signature):
    """
    Analyze a FOLLOW_UP message to determine if it contains a clear question
    that can be answered automatically using the candidate's profile data.

    IMPORTANT: Be very conservative. Only mark as auto-respondable if the question
    is extremely clear and can be answered with profile data alone.
    """

    # Input
    message: str = dspy.InputField(
        desc="The follow-up message from recruiter"
    )
    candidate_profile_summary: str = dspy.InputField(
        desc="Summary of candidate's profile including: salary expectations, experience, preferred technologies, availability, etc."
    )

    # Outputs
    question_type: str = dspy.OutputField(
        desc="""Classify the type of question (if any) in the message:
        - SALARY: Asking about salary expectations (e.g., "What's your salary expectation?", "What rate are you looking for?")
        - AVAILABILITY: Asking about availability or start date (e.g., "When can you start?", "What's your availability?")
        - EXPERIENCE: Asking about specific experience or skills (e.g., "How many years with Python?")
        - INTEREST: Asking if candidate is interested (e.g., "Are you interested?", "Would you like to proceed?")
        - SCHEDULING: Trying to schedule a call (e.g., "Can we talk tomorrow?", "When are you free?")
        - NONE: No clear question, just a statement or acknowledgment
        - OTHER: Question that doesn't fit above categories or requires conversation context"""
    )

    detected_question: str = dspy.OutputField(
        desc="The exact question found in the message, or 'N/A' if no question"
    )

    can_auto_respond: str = dspy.OutputField(
        desc="""YES or NO. Mark YES ONLY if ALL of these are true:
        1. There is a clear, direct question (not just a statement)
        2. The question can be answered using ONLY the candidate's profile data
        3. Answering does NOT require knowledge of previous conversation context
        4. The question type is SALARY, AVAILABILITY, or EXPERIENCE

        Mark NO if:
        - The message is vague (e.g., "Sure, Sebastian!")
        - The message references something we don't have context for
        - The question type is SCHEDULING (requires human judgment on timing)
        - The question type is NONE or OTHER"""
    )

    requires_context: str = dspy.OutputField(
        desc="YES if answering the message properly requires knowledge of previous conversation that we don't have. NO if it can be answered standalone."
    )

    reasoning: str = dspy.OutputField(
        desc="Brief explanation of the decision"
    )


class MessageAnalysisSignature(dspy.Signature):
    """
    Analyze a LinkedIn recruiter message and extract key information.

    This signature tells the LLM to extract structured data from
    unstructured recruiter messages.
    """

    # Input
    message: str = dspy.InputField(
        desc="Raw LinkedIn message from recruiter"
    )

    # Outputs
    company: str = dspy.OutputField(
        desc="Company name mentioned in the message"
    )
    role: str = dspy.OutputField(
        desc="Job role/title mentioned (e.g., 'Senior Backend Engineer')"
    )
    seniority: str = dspy.OutputField(
        desc="Seniority level: Junior, Mid, Senior, Staff, Principal, or Unknown"
    )
    tech_stack: str = dspy.OutputField(
        desc="Comma-separated list of technologies mentioned (e.g., 'Python,FastAPI,PostgreSQL')"
    )
    salary_range: str = dspy.OutputField(
        desc="Salary range if mentioned (e.g., '100000-150000 USD') or 'Not mentioned'"
    )
    remote_policy: str = dspy.OutputField(
        desc="Remote work policy: Remote, Hybrid, Onsite, or Unknown"
    )
    location: str = dspy.OutputField(
        desc="Job location if mentioned, or 'Not specified'"
    )


class ScoringSignature(dspy.Signature):
    """
    Score an opportunity based on candidate profile and extracted information.

    Uses structured data to calculate relevance scores.
    """

    # Inputs
    extracted_data: str = dspy.InputField(
        desc="JSON string with extracted job information (company, role, tech_stack, etc.)"
    )
    candidate_profile: str = dspy.InputField(
        desc="JSON string with candidate's preferences, skills, and requirements"
    )

    # Outputs
    tech_stack_score: int = dspy.OutputField(
        desc="Tech stack match score (0-40 points). 40 = perfect match, 0 = no match"
    )
    tech_stack_reasoning: str = dspy.OutputField(
        desc="Brief explanation of tech stack score"
    )

    salary_score: int = dspy.OutputField(
        desc="Salary adequacy score (0-30 points). 30 = excellent, 0 = too low"
    )
    salary_reasoning: str = dspy.OutputField(
        desc="Brief explanation of salary score"
    )

    seniority_score: int = dspy.OutputField(
        desc="Seniority match score (0-20 points). 20 = perfect fit, 0 = mismatch"
    )
    seniority_reasoning: str = dspy.OutputField(
        desc="Brief explanation of seniority score"
    )

    company_score: int = dspy.OutputField(
        desc="Company attractiveness score (0-10 points). 10 = top company, 0 = unknown"
    )
    company_reasoning: str = dspy.OutputField(
        desc="Brief explanation of company score"
    )


class ResponseGenerationSignature(dspy.Signature):
    """
    Generate a professional response to the recruiter.

    Creates personalized, context-aware responses based on
    the opportunity score, details, and candidate's current professional situation.

    IMPORTANT: Be conservative and "shy" - don't oversell or push for calls unless
    the opportunity is truly exceptional AND meets all critical requirements.
    """

    # Inputs
    recruiter_name: str = dspy.InputField(
        desc="Recruiter's name"
    )
    company: str = dspy.InputField(
        desc="Company name"
    )
    role: str = dspy.InputField(
        desc="Job role"
    )
    total_score: int = dspy.InputField(
        desc="Total opportunity score (0-100)"
    )
    tier: str = dspy.InputField(
        desc="Opportunity tier: HIGH_PRIORITY, INTERESANTE, POCO_INTERESANTE, NO_INTERESA"
    )
    salary_range: str = dspy.InputField(
        desc="Salary range if mentioned"
    )
    tech_stack: str = dspy.InputField(
        desc="Technologies mentioned"
    )
    candidate_name: str = dspy.InputField(
        desc="Candidate's name"
    )
    candidate_context: str = dspy.InputField(
        desc="Candidate's current professional situation, job search status, must-have requirements, and deal-breakers. Use this to personalize the response appropriately."
    )
    candidate_status: str = dspy.InputField(
        desc="Candidate's job search status: ACTIVE_SEARCH, PASSIVE, SELECTIVE, NOT_LOOKING"
    )
    failed_hard_filters: str = dspy.InputField(
        desc="Comma-separated list of hard requirements that this opportunity FAILED to meet (e.g., '4-day work week not mentioned, salary below minimum'). Empty string if all filters passed."
    )
    work_week_mentioned: str = dspy.InputField(
        desc="YES if 4-day work week is explicitly mentioned in the job, NO if not mentioned or 5-day week, UNKNOWN if unclear"
    )

    # Output
    response: str = dspy.OutputField(
        desc="""Generate a professional, CONSERVATIVE response (50-150 words) following these STRICT rules:

        ## RESPONSE RULES BY STATUS:

        IF candidate_status == "PASSIVE" or "SELECTIVE":
        - NEVER propose scheduling a call in your response
        - Instead say: "Gracias por contactarme. Actualmente no estoy buscando activamente, pero para posiciones con [CRITICAL_REQUIREMENT] podría considerar hacer un espacio. ¿Este rol cuenta con eso?"
        - Ask about the specific missing requirement (4-day work week, remote policy, etc.)

        IF candidate_status == "ACTIVE_SEARCH" AND tier == "HIGH_PRIORITY" AND failed_hard_filters is empty:
        - Only then can you express strong interest
        - Can propose availability for a call

        ## HARD FILTER RULES:

        IF failed_hard_filters is NOT empty:
        - MUST generate a POLITE DECLINE response
        - Thank the recruiter
        - Mention the specific failed requirement(s)
        - Example: "Gracias por pensar en mí. Actualmente solo estoy considerando posiciones con semana laboral de 4 días, que es un requisito indispensable para mí."

        IF work_week_mentioned == "NO" and candidate requires 4-day week:
        - Ask specifically about work week before showing interest
        - Do NOT propose a call

        ## GENERAL RULES:
        1. NEVER say "esta tarde podemos hablar" unless ALL conditions for ACTIVE_SEARCH + HIGH_PRIORITY + no failed filters are met
        2. Be honest and direct about requirements
        3. MUST end with: '*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad.'
        4. Use professional Spanish
        5. For tech_stack_score < 50%: politely decline mentioning skill mismatch
        """
    )