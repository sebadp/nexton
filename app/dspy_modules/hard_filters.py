"""
Hard Filters - Veto filters that must be passed before generating an acceptance response.

These filters implement strict requirements that, if not met, should result in
a polite decline rather than expressing interest.
"""

from app.core.logging import get_logger
from app.dspy_modules.models import (
    CandidateStatus,
    ExtractedData,
    HardFilterResult,
    ScoringResult,
)

logger = get_logger(__name__)


def get_candidate_status_from_profile(profile_dict: dict) -> CandidateStatus:
    """
    Determine candidate status from profile configuration.

    Args:
        profile_dict: Full profile dictionary including job_search_status

    Returns:
        CandidateStatus enum value
    """
    job_search = profile_dict.get("job_search_status", {})
    urgency = job_search.get("urgency", "moderate").lower()
    actively_looking = job_search.get("actively_looking", True)

    if not actively_looking or urgency == "not_looking":
        return CandidateStatus.NOT_LOOKING
    elif urgency == "selective":
        return CandidateStatus.SELECTIVE
    elif urgency == "urgent":
        return CandidateStatus.ACTIVE_SEARCH
    else:  # moderate
        return CandidateStatus.PASSIVE


def check_work_week_requirement(
    extracted: ExtractedData,
    raw_message: str,
    preferred_work_week: str,
) -> tuple[bool, str]:
    """
    Check if the job meets work week requirements.

    Args:
        extracted: Extracted job data
        raw_message: Original message text
        preferred_work_week: Candidate's preferred work week (e.g., "4-days")

    Returns:
        tuple: (passes_filter, work_week_status)
        - work_week_status: CONFIRMED, NOT_MENTIONED, FIVE_DAY, UNKNOWN
    """
    if preferred_work_week != "4-days":
        # Candidate doesn't require 4-day week
        return True, "NOT_REQUIRED"

    message_lower = raw_message.lower()
    extracted_week = extracted.work_week.lower() if extracted.work_week else ""

    # Check for explicit 4-day week mentions
    four_day_patterns = [
        "4 días",
        "4 day",
        "four day",
        "4-day",
        "cuatro días",
        "semana de 4",
        "4 day week",
        "32 hour",
        "32 horas",
        "semana laboral reducida",
        "compressed week",
    ]

    for pattern in four_day_patterns:
        if pattern in message_lower or pattern in extracted_week:
            return True, "CONFIRMED"

    # Check for explicit 5-day week mentions (disqualifying)
    five_day_patterns = [
        "5 días",
        "5 day",
        "five day",
        "5-day",
        "cinco días",
        "semana de 5",
        "5 day week",
        "40 hour",
        "40 horas",
        "full time standard",
        "standard work week",
    ]

    for pattern in five_day_patterns:
        if pattern in message_lower:
            return False, "FIVE_DAY"

    # Work week not mentioned - this should trigger a question, not acceptance
    return False, "NOT_MENTIONED"


def check_salary_requirement(
    extracted: ExtractedData,
    minimum_salary_usd: int,
) -> tuple[bool, str | None]:
    """
    Check if salary meets minimum requirements.

    Args:
        extracted: Extracted job data
        minimum_salary_usd: Candidate's minimum salary requirement

    Returns:
        tuple: (passes_filter, failure_reason or None)
    """
    if not extracted.salary_min and not extracted.salary_max:
        # Salary not mentioned - this is OK, we can ask
        return True, None

    # Get the higher bound if available, otherwise use min
    offered_salary = extracted.salary_max or extracted.salary_min

    # Validate offered_salary is a number
    if not isinstance(offered_salary, int | float):
        logger.warning("invalid_salary_extracted", salary=offered_salary)
        # If we extracted something but it's not a number, we shouldn't filter based on it
        # We assume it's valid to proceed and let human verify
        return True, None

    try:
        # Convert to USD if needed (simple conversion for common currencies)
        if extracted.currency == "EUR" and offered_salary:
            offered_salary = int(offered_salary * 1.1)  # Approximate EUR to USD
        elif extracted.currency == "ARS" and offered_salary:
            offered_salary = int(offered_salary / 1000)  # Very rough ARS to USD
    except Exception as e:
        logger.error("salary_conversion_error", error=str(e), currency=extracted.currency)
        # If conversion fails, we skip the filter
        return True, None

    if offered_salary and offered_salary < minimum_salary_usd:
        return False, f"Salary ({offered_salary:,} USD) below minimum ({minimum_salary_usd:,} USD)"

    return True, None


def check_tech_stack_match(
    scoring: ScoringResult,
    min_tech_match_percent: int = 50,
) -> tuple[bool, str | None]:
    """
    Check if tech stack match is above threshold.

    Args:
        scoring: Scoring results
        min_tech_match_percent: Minimum tech match percentage (0-100)

    Returns:
        tuple: (passes_filter, failure_reason or None)
    """
    # Tech stack score is 0-40, convert to percentage
    tech_match_percent = (scoring.tech_stack_score / 40) * 100

    if tech_match_percent < min_tech_match_percent:
        return (
            False,
            f"Tech stack match ({tech_match_percent:.0f}%) below threshold ({min_tech_match_percent}%)",
        )

    return True, None


def check_remote_policy(
    extracted: ExtractedData,
    preferred_policy: str,
) -> tuple[bool, str | None]:
    """
    Check if remote policy matches requirements.

    Args:
        extracted: Extracted job data
        preferred_policy: Candidate's preferred remote policy

    Returns:
        tuple: (passes_filter, failure_reason or None)
    """
    if preferred_policy.lower() != "remote":
        # Candidate is flexible on remote policy
        return True, None

    if extracted.remote_policy.lower() == "onsite":
        return False, "Position requires on-site work, candidate requires remote"

    # Unknown or hybrid are acceptable for now - can ask later
    return True, None


def check_reject_criteria(
    extracted: ExtractedData,
    raw_message: str,
    reject_if: list[str],
) -> tuple[bool, str | None]:
    """
    Check against automatic rejection criteria.

    Args:
        extracted: Extracted job data
        raw_message: Original message
        reject_if: List of rejection criteria from profile

    Returns:
        tuple: (passes_filter, failure_reason or None)
    """
    message_lower = raw_message.lower()
    company_lower = extracted.company.lower()

    for criterion in reject_if:
        criterion_lower = criterion.lower()

        # Check for common rejection patterns
        if "agency" in criterion_lower or "consulting" in criterion_lower:
            agency_patterns = ["agency", "agencia", "consulting", "consultora", "staffing"]
            for pattern in agency_patterns:
                if pattern in message_lower or pattern in company_lower:
                    return False, f"Matched rejection criterion: {criterion}"

        elif "crypto" in criterion_lower or "blockchain" in criterion_lower:
            crypto_patterns = ["crypto", "blockchain", "web3", "defi", "nft"]
            for pattern in crypto_patterns:
                if pattern in message_lower or pattern in company_lower:
                    return False, f"Matched rejection criterion: {criterion}"

        elif "early-stage" in criterion_lower or "pre-seed" in criterion_lower:
            early_patterns = ["pre-seed", "preseed", "early stage", "early-stage", "seed round"]
            for pattern in early_patterns:
                if pattern in message_lower:
                    return False, f"Matched rejection criterion: {criterion}"

        elif "5-day" in criterion_lower or "5 day" in criterion_lower:
            # This is handled by check_work_week_requirement
            pass

        elif "on-site" in criterion_lower or "onsite" in criterion_lower:
            # This is handled by check_remote_policy
            pass

    return True, None


def apply_hard_filters(
    extracted: ExtractedData,
    scoring: ScoringResult,
    raw_message: str,
    profile_dict: dict,
) -> HardFilterResult:
    """
    Apply all hard filters and return aggregated result.

    Args:
        extracted: Extracted job data
        scoring: Scoring results
        raw_message: Original message
        profile_dict: Full profile dictionary

    Returns:
        HardFilterResult: Aggregated filter results
    """
    failed_filters: list[str] = []
    score_penalty = 0
    work_week_status = "UNKNOWN"

    # Get configuration from profile
    job_search = profile_dict.get("job_search_status", {})
    reject_if = job_search.get("reject_if", [])
    preferred_work_week = profile_dict.get("preferred_work_week", "5-days")
    minimum_salary = profile_dict.get("minimum_salary_usd", 0)
    preferred_remote = profile_dict.get("preferred_remote_policy", "Remote")

    logger.debug(
        "applying_hard_filters",
        preferred_work_week=preferred_work_week,
        minimum_salary=minimum_salary,
        preferred_remote=preferred_remote,
    )

    # 1. Check work week requirement (critical for 4-day week seekers)
    work_week_pass, work_week_status = check_work_week_requirement(
        extracted, raw_message, preferred_work_week
    )
    if not work_week_pass:
        if work_week_status == "FIVE_DAY":
            failed_filters.append("5-day work week explicitly required")
            score_penalty += 50
        elif work_week_status == "NOT_MENTIONED":
            failed_filters.append("4-day work week not mentioned")
            score_penalty += 30  # Penalty but not as severe

    # 2. Check salary requirement
    salary_pass, salary_reason = check_salary_requirement(extracted, minimum_salary)
    if not salary_pass and salary_reason:
        failed_filters.append(salary_reason)
        score_penalty += 40

    # 3. Check tech stack match
    tech_pass, tech_reason = check_tech_stack_match(scoring, min_tech_match_percent=50)
    if not tech_pass and tech_reason:
        failed_filters.append(tech_reason)
        score_penalty += 30

    # 4. Check remote policy
    remote_pass, remote_reason = check_remote_policy(extracted, preferred_remote)
    if not remote_pass and remote_reason:
        failed_filters.append(remote_reason)
        score_penalty += 40

    # 5. Check rejection criteria
    reject_pass, reject_reason = check_reject_criteria(extracted, raw_message, reject_if)
    if not reject_pass and reject_reason:
        failed_filters.append(reject_reason)
        score_penalty += 50

    # Determine if we should decline
    # Decline if any critical filter failed or if penalty is too high
    should_decline = len(failed_filters) > 0 and (
        score_penalty >= 40  # High penalty
        or any("5-day work week" in f for f in failed_filters)  # 5-day week required
        or any("on-site" in f.lower() for f in failed_filters)  # On-site required
        or any("rejection criterion" in f.lower() for f in failed_filters)  # Matched rejection
    )

    result = HardFilterResult(
        passed=len(failed_filters) == 0,
        failed_filters=failed_filters,
        score_penalty=min(score_penalty, 100),
        should_decline=should_decline,
        work_week_status=work_week_status,
    )

    logger.info(
        "hard_filters_applied",
        passed=result.passed,
        failed_count=len(failed_filters),
        score_penalty=result.score_penalty,
        should_decline=result.should_decline,
        work_week_status=work_week_status,
    )

    return result
