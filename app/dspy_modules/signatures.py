"""
DSPy Signatures - Define input/output types for LLM modules.

Signatures describe what the LLM should do and what format
it should return data in.
"""
import dspy


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

    # Output
    response: str = dspy.OutputField(
        desc="""Generate a professional, contextual response (50-150 words) that:
        1. Thanks the recruiter by name
        2. CONSIDERS the candidate's current situation and requirements from candidate_context
        3. For HIGH_PRIORITY: Express interest IF it aligns with candidate's must-haves. If not, politely decline mentioning specific requirements.
        4. For INTERESANTE: Express moderate interest and ask about specific must-have requirements (e.g., work week, remote policy)
        5. For POCO_INTERESANTE/NO_INTERESA: Politely decline, mentioning 1-2 specific reasons from candidate_context
        6. If the opportunity doesn't meet deal-breakers (e.g., no 4-day work week mentioned), politely decline and mention this requirement
        7. MUST end with: '*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad.'
        8. Use a professional but friendly tone in Spanish
        9. Be honest about requirements - don't waste anyone's time with opportunities that don't match
        """
    )