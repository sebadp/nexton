# Sprint 3 - Planning Document

**Version**: 1.2.0 (Planned)
**Duration**: 14 days (estimated)
**Start Date**: January 18, 2024
**Target Release**: February 1, 2024
**Status**: 📋 **PLANNING**

---

## 🎯 Sprint Goals

Sprint 3 focuses on **intelligent automation and integration**, building on the solid foundation of Sprint 2 to deliver:

1. **Multi-Model LLM Support** - Flexibility to use OpenAI, Anthropic Claude, or local models
2. **Advanced Search & Filtering** - Full-text search and complex filtering
3. **Smart Notifications** - Email/Slack alerts for high-tier opportunities
4. **Response Automation** - AI-powered response generation and sending
5. **Job Board Integration** - Pull opportunities from Indeed, Glassdoor, etc.

---

## 📊 Priority Matrix

| Feature | Business Value | Complexity | Dependencies | Priority |
|---------|---------------|------------|--------------|----------|
| Multi-Model LLM | High | Medium | None | **P0** |
| Advanced Search | High | Low | None | **P0** |
| Email/Slack Notifications | Medium | Low | Celery (✅) | **P1** |
| Response Automation | High | High | LinkedIn API | **P1** |
| Job Board Integration | Medium | Medium | Scraper pattern (✅) | **P2** |

**Sprint 3 Scope**: P0 + P1 features (5 features)

---

## 🚀 Feature Breakdown

### Feature 3.1: Multi-Model LLM Support ⭐ **P0**

**Business Value**: Cost optimization, vendor flexibility, performance improvement

**User Story**:
> "As a platform admin, I want to choose between different LLM providers (OpenAI, Anthropic, local Ollama) so that I can optimize for cost, latency, and quality."

#### Current State
- ✅ Ollama integration working
- ✅ DSPy pipeline architecture
- ❌ Locked to single provider

#### Target State
- ✅ Abstract LLM interface
- ✅ OpenAI GPT-4/GPT-3.5 support
- ✅ Anthropic Claude 3 support
- ✅ Ollama (existing) support
- ✅ Model selection via config
- ✅ Automatic fallback logic
- ✅ Per-module model configuration
- ✅ Cost tracking per provider

#### Technical Design

```python
# app/llm/base.py
class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embeddings."""
        pass

    @property
    @abstractmethod
    def cost_per_1k_tokens(self) -> float:
        """Cost per 1K tokens."""
        pass

# app/llm/openai_provider.py
class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def complete(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content

# app/llm/anthropic_provider.py
class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, prompt: str, **kwargs) -> str:
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.content[0].text

# app/llm/factory.py
class LLMFactory:
    """Factory for creating LLM providers."""

    @staticmethod
    def create_provider(provider_type: str, **kwargs) -> LLMProvider:
        providers = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "ollama": OllamaProvider,
        }
        return providers[provider_type](**kwargs)

# Configuration
LLM_PROVIDER=openai  # or anthropic, ollama
LLM_MODEL=gpt-4      # or claude-3-sonnet, llama2
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Per-module configuration (optional)
ANALYZER_LLM_PROVIDER=openai
ANALYZER_LLM_MODEL=gpt-3.5-turbo
SCORER_LLM_PROVIDER=anthropic
SCORER_LLM_MODEL=claude-3-sonnet
RESPONSE_LLM_PROVIDER=openai
RESPONSE_LLM_MODEL=gpt-4
```

#### Tasks
- [ ] **3.1.1** Create `app/llm/` module structure
- [ ] **3.1.2** Implement `LLMProvider` abstract base class
- [ ] **3.1.3** Implement `OpenAIProvider` with async support
- [ ] **3.1.4** Implement `AnthropicProvider` with async support
- [ ] **3.1.5** Refactor `OllamaProvider` to match interface
- [ ] **3.1.6** Create `LLMFactory` with provider selection
- [ ] **3.1.7** Add cost tracking per provider
- [ ] **3.1.8** Implement fallback logic (try primary, fallback to secondary)
- [ ] **3.1.9** Update DSPy modules to use LLM factory
- [ ] **3.1.10** Add configuration for per-module models
- [ ] **3.1.11** Update metrics to track provider usage
- [ ] **3.1.12** Write tests (10+ tests for each provider)
- [ ] **3.1.13** Update documentation

**Estimated Effort**: 3 days
**Dependencies**: None
**Risk**: Medium (API rate limits, different response formats)

---

### Feature 3.2: Advanced Search & Filtering ⭐ **P0**

**Business Value**: Better opportunity discovery, improved user experience

**User Story**:
> "As a user, I want to search opportunities by keywords and apply complex filters so that I can quickly find relevant opportunities."

#### Current State
- ✅ Basic filtering by tier, status
- ✅ Pagination
- ❌ No full-text search
- ❌ No complex filters (salary range, tech stack)
- ❌ No sorting options

#### Target State
- ✅ Full-text search across all fields
- ✅ PostgreSQL `tsvector` full-text search
- ✅ Complex filters:
  - Salary range (min/max)
  - Tech stack (any/all match)
  - Company name
  - Date range
  - Score range
- ✅ Multiple sort options
- ✅ Search suggestions/autocomplete
- ✅ Search result highlighting

#### Technical Design

```python
# app/database/models.py
class Opportunity(Base):
    # ... existing fields ...

    # Add full-text search column
    search_vector = Column(
        TSVector(),
        Computed(
            "to_tsvector('english', coalesce(company, '') || ' ' || "
            "coalesce(position, '') || ' ' || coalesce(raw_message, ''))",
            persisted=True
        )
    )

    __table_args__ = (
        Index('idx_opportunity_search', search_vector, postgresql_using='gin'),
    )

# app/api/v1/schemas.py
class OpportunitySearchRequest(BaseModel):
    """Search and filter request."""

    # Search
    query: Optional[str] = None  # Full-text search

    # Filters
    tier: Optional[list[str]] = None  # ["A", "B"]
    status: Optional[list[str]] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    tech_stack: Optional[list[str]] = None  # Match any of these
    tech_stack_match_all: bool = False  # Require all techs
    company: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    # Sorting
    sort_by: str = "created_at"  # created_at, score, salary_max
    sort_order: str = "desc"  # asc, desc

    # Pagination
    page: int = 1
    limit: int = 10

# app/database/repositories.py
class OpportunityRepository:
    async def search(
        self,
        search_request: OpportunitySearchRequest
    ) -> tuple[list[Opportunity], int]:
        """Advanced search with filters."""

        query = select(Opportunity)

        # Full-text search
        if search_request.query:
            search_query = func.plainto_tsquery('english', search_request.query)
            query = query.where(
                Opportunity.search_vector.op('@@')(search_query)
            ).order_by(
                func.ts_rank(Opportunity.search_vector, search_query).desc()
            )

        # Filters
        if search_request.tier:
            query = query.where(Opportunity.tier.in_(search_request.tier))

        if search_request.min_salary:
            query = query.where(Opportunity.salary_min >= search_request.min_salary)

        if search_request.tech_stack:
            if search_request.tech_stack_match_all:
                # All techs must be present
                query = query.where(
                    Opportunity.tech_stack.contains(search_request.tech_stack)
                )
            else:
                # Any tech matches
                query = query.where(
                    Opportunity.tech_stack.overlap(search_request.tech_stack)
                )

        # ... more filters ...

        # Sorting
        sort_column = getattr(Opportunity, search_request.sort_by)
        if search_request.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        # Pagination
        offset = (search_request.page - 1) * search_request.limit
        query = query.offset(offset).limit(search_request.limit)

        result = await self.session.execute(query)
        opportunities = result.scalars().all()

        return opportunities, total

# API Endpoint
@router.post("/opportunities/search")
async def search_opportunities(
    search_request: OpportunitySearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """Advanced search endpoint."""
    repo = OpportunityRepository(db)
    opportunities, total = await repo.search(search_request)

    return {
        "items": [OpportunityResponse.from_orm(o) for o in opportunities],
        "total": total,
        "page": search_request.page,
        "pages": (total + search_request.limit - 1) // search_request.limit
    }
```

#### Tasks
- [ ] **3.2.1** Add `search_vector` column to Opportunity model
- [ ] **3.2.2** Create migration for full-text search
- [ ] **3.2.3** Add GIN index for search performance
- [ ] **3.2.4** Create `OpportunitySearchRequest` schema
- [ ] **3.2.5** Implement `search()` method in repository
- [ ] **3.2.6** Add salary range filtering
- [ ] **3.2.7** Add tech stack filtering (any/all match)
- [ ] **3.2.8** Add date range filtering
- [ ] **3.2.9** Add score range filtering
- [ ] **3.2.10** Implement sorting logic
- [ ] **3.2.11** Add search result highlighting
- [ ] **3.2.12** Create search API endpoint
- [ ] **3.2.13** Add caching for popular searches
- [ ] **3.2.14** Write tests (15+ tests)
- [ ] **3.2.15** Update API documentation

**Estimated Effort**: 2 days
**Dependencies**: None
**Risk**: Low

---

### Feature 3.3: Email/Slack Notifications 🔔 **P1**

**Business Value**: Instant alerts for high-value opportunities

**User Story**:
> "As a user, I want to receive email/Slack notifications for A-tier opportunities so that I don't miss high-value opportunities."

#### Current State
- ✅ Celery background jobs working
- ✅ Opportunity tier classification
- ❌ No notification system

#### Target State
- ✅ Email notifications via SMTP
- ✅ Slack notifications via webhooks
- ✅ Configurable notification rules:
  - Tier threshold (notify for A-tier only, or A+B)
  - Score threshold (notify if score > 80)
  - Tech stack match (notify if matches preferred techs)
  - Salary threshold (notify if salary > $150k)
- ✅ Notification templates
- ✅ Rate limiting (max X notifications per day)
- ✅ Digest mode (daily summary)

#### Technical Design

```python
# app/notifications/base.py
class NotificationChannel(ABC):
    """Abstract notification channel."""

    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Send notification."""
        pass

# app/notifications/email.py
class EmailNotification(NotificationChannel):
    """Email notification channel."""

    def __init__(self):
        self.smtp_client = aiosmtplib.SMTP(
            hostname=settings.MAIL_SERVER,
            port=settings.MAIL_PORT,
            use_tls=settings.MAIL_USE_TLS
        )

    async def send(self, notification: Notification) -> bool:
        """Send email notification."""
        message = EmailMessage()
        message["From"] = settings.MAIL_FROM
        message["To"] = notification.recipient
        message["Subject"] = notification.subject
        message.set_content(notification.body_text)
        message.add_alternative(notification.body_html, subtype="html")

        await self.smtp_client.connect()
        await self.smtp_client.send_message(message)
        await self.smtp_client.quit()

        return True

# app/notifications/slack.py
class SlackNotification(NotificationChannel):
    """Slack notification channel."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient()

    async def send(self, notification: Notification) -> bool:
        """Send Slack notification."""
        payload = {
            "text": notification.subject,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": notification.subject}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": notification.body_text}
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Details"},
                            "url": notification.action_url
                        }
                    ]
                }
            ]
        }

        response = await self.client.post(self.webhook_url, json=payload)
        return response.status_code == 200

# app/notifications/rules.py
class NotificationRule:
    """Notification rule configuration."""

    def __init__(
        self,
        enabled: bool = True,
        channels: list[str] = ["email"],
        tier_threshold: list[str] = ["A"],
        score_threshold: Optional[int] = None,
        tech_stack_match: Optional[list[str]] = None,
        salary_threshold: Optional[int] = None,
        rate_limit: int = 10,  # max per day
        digest_mode: bool = False,
        digest_time: str = "09:00"  # UTC
    ):
        self.enabled = enabled
        self.channels = channels
        self.tier_threshold = tier_threshold
        self.score_threshold = score_threshold
        self.tech_stack_match = tech_stack_match
        self.salary_threshold = salary_threshold
        self.rate_limit = rate_limit
        self.digest_mode = digest_mode
        self.digest_time = digest_time

    def should_notify(self, opportunity: Opportunity) -> bool:
        """Check if opportunity matches notification rules."""
        if not self.enabled:
            return False

        # Tier check
        if opportunity.tier not in self.tier_threshold:
            return False

        # Score check
        if self.score_threshold and opportunity.total_score < self.score_threshold:
            return False

        # Tech stack check
        if self.tech_stack_match:
            if not any(tech in opportunity.tech_stack for tech in self.tech_stack_match):
                return False

        # Salary check
        if self.salary_threshold and opportunity.salary_max < self.salary_threshold:
            return False

        return True

# app/tasks/notification_tasks.py
@celery_app.task(name="send_opportunity_notification")
async def send_opportunity_notification(opportunity_id: int):
    """Send notification for new opportunity."""
    # Get opportunity
    # Check notification rules
    # Send to configured channels
    # Track in database
    pass

# Integration in OpportunityService
class OpportunityService:
    async def create_opportunity(self, ...):
        # ... existing code ...

        # Trigger notification if rules match
        if notification_rule.should_notify(opportunity):
            send_opportunity_notification.delay(opportunity.id)

        return opportunity
```

#### Tasks
- [ ] **3.3.1** Create `app/notifications/` module
- [ ] **3.3.2** Implement `NotificationChannel` base class
- [ ] **3.3.3** Implement `EmailNotification` with templates
- [ ] **3.3.4** Implement `SlackNotification` with blocks
- [ ] **3.3.5** Create `NotificationRule` configuration
- [ ] **3.3.6** Create notification database models
- [ ] **3.3.7** Implement rule matching logic
- [ ] **3.3.8** Add rate limiting (max per day)
- [ ] **3.3.9** Implement digest mode (daily summary)
- [ ] **3.3.10** Create Celery task for notifications
- [ ] **3.3.11** Integrate with OpportunityService
- [ ] **3.3.12** Add notification history tracking
- [ ] **3.3.13** Create notification settings API
- [ ] **3.3.14** Add metrics for notifications sent
- [ ] **3.3.15** Write tests (12+ tests)
- [ ] **3.3.16** Create HTML email templates

**Estimated Effort**: 2 days
**Dependencies**: Celery (✅ from Sprint 2)
**Risk**: Low

---

### Feature 3.4: Automated Response Sending 🤖 **P1**

**Business Value**: Save time, respond faster, maintain professionalism

**User Story**:
> "As a user, I want the system to automatically generate and send responses to recruiters based on opportunity tier so that I can respond quickly and professionally."

#### Current State
- ✅ Response generation in DSPy pipeline
- ✅ LinkedIn scraper working
- ❌ No automated sending
- ❌ No response approval workflow

#### Target State
- ✅ AI-generated response review UI (or API)
- ✅ Automatic response sending via LinkedIn
- ✅ Response templates by tier
- ✅ User approval workflow:
  - Auto-send for D-tier (decline)
  - Review required for A/B/C-tier
- ✅ Response scheduling (don't send at 3am)
- ✅ Rate limiting (don't spam)
- ✅ Response tracking

#### Technical Design

```python
# app/responses/generator.py
class ResponseGenerator:
    """Generate contextual responses based on opportunity."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def generate_response(
        self,
        opportunity: Opportunity,
        user_profile: CandidateProfile,
        response_type: str = "interested"  # interested, not_interested, more_info
    ) -> str:
        """Generate personalized response."""

        prompt = self._build_prompt(opportunity, user_profile, response_type)
        response = await self.llm.complete(prompt)

        return response

    def _build_prompt(self, ...):
        """Build prompt for response generation."""
        if response_type == "interested":
            return f"""
            Generate a professional, interested response to this recruiter message.

            Recruiter: {opportunity.recruiter_name}
            Company: {opportunity.company}
            Position: {opportunity.position}
            Original Message: {opportunity.raw_message}

            Candidate Profile:
            - Experience: {user_profile.years_of_experience} years
            - Skills: {', '.join(user_profile.tech_stack)}
            - Current Role: {user_profile.current_seniority}

            Guidelines:
            - Express genuine interest
            - Mention 1-2 relevant skills that match
            - Ask about next steps
            - Keep it concise (3-4 sentences)
            - Professional but friendly tone
            """
        # ... other response types ...

# app/responses/sender.py
class ResponseSender:
    """Send responses via LinkedIn."""

    def __init__(self, scraper: LinkedInScraper):
        self.scraper = scraper

    async def send_response(
        self,
        opportunity_id: int,
        message: str,
        scheduled_at: Optional[datetime] = None
    ) -> bool:
        """Send response to recruiter."""

        # Check rate limits
        if await self._is_rate_limited():
            raise RateLimitError("Too many responses sent today")

        # Schedule if needed
        if scheduled_at:
            send_linkedin_response.apply_async(
                args=[opportunity_id, message],
                eta=scheduled_at
            )
            return True

        # Send immediately
        success = await self.scraper.send_message(
            recruiter_profile_url=opportunity.recruiter_url,
            message=message
        )

        # Track response
        await self._track_response(opportunity_id, message, success)

        return success

# app/responses/workflow.py
class ResponseWorkflow:
    """Manage response approval workflow."""

    def __init__(self):
        self.rules = self._load_rules()

    async def process_opportunity(self, opportunity: Opportunity):
        """Process opportunity and handle response workflow."""

        # Generate response
        response = await self.generator.generate_response(opportunity)

        # Determine if auto-send or review required
        if self._requires_review(opportunity):
            # Create pending response for review
            await self._create_pending_response(opportunity, response)
            # Trigger notification for review
            await self._notify_review_required(opportunity)
        else:
            # Auto-send (typically for D-tier declines)
            scheduled_time = self._get_optimal_send_time()
            await self.sender.send_response(
                opportunity.id,
                response,
                scheduled_at=scheduled_time
            )

    def _requires_review(self, opportunity: Opportunity) -> bool:
        """Check if response requires manual review."""
        # D-tier: auto-decline
        if opportunity.tier == "D":
            return False
        # A/B/C-tier: review required
        return True

    def _get_optimal_send_time(self) -> datetime:
        """Get optimal time to send (business hours)."""
        now = datetime.now(tz=pytz.UTC)

        # If it's business hours, send now
        if 9 <= now.hour <= 17:
            return now

        # Otherwise, schedule for 9am next business day
        next_day = now + timedelta(days=1)
        send_time = next_day.replace(hour=9, minute=0, second=0)

        # Skip weekends
        while send_time.weekday() >= 5:  # Saturday or Sunday
            send_time += timedelta(days=1)

        return send_time

# Database models
class PendingResponse(Base):
    """Pending response awaiting approval."""
    __tablename__ = "pending_responses"

    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    generated_response = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected, sent
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)

# API endpoints
@router.get("/responses/pending")
async def get_pending_responses(...):
    """Get responses awaiting approval."""
    pass

@router.post("/responses/{response_id}/approve")
async def approve_response(...):
    """Approve and send response."""
    pass

@router.post("/responses/{response_id}/edit")
async def edit_response(...):
    """Edit response before sending."""
    pass

@router.post("/responses/{response_id}/reject")
async def reject_response(...):
    """Reject response (don't send)."""
    pass
```

#### Tasks
- [ ] **3.4.1** Create `app/responses/` module
- [ ] **3.4.2** Implement `ResponseGenerator` with LLM
- [ ] **3.4.3** Create response templates by tier
- [ ] **3.4.4** Implement `ResponseSender` with LinkedIn integration
- [ ] **3.4.5** Add rate limiting for sending
- [ ] **3.4.6** Implement optimal send time calculation
- [ ] **3.4.7** Create `PendingResponse` database model
- [ ] **3.4.8** Implement `ResponseWorkflow` with approval logic
- [ ] **3.4.9** Create API endpoints for response management
- [ ] **3.4.10** Add LinkedIn message sending to scraper
- [ ] **3.4.11** Implement response tracking and history
- [ ] **3.4.12** Create Celery task for scheduled sending
- [ ] **3.4.13** Add metrics for response tracking
- [ ] **3.4.14** Write tests (15+ tests)
- [ ] **3.4.15** Add response analytics dashboard

**Estimated Effort**: 3 days
**Dependencies**: LinkedIn scraper (✅), LLM provider (3.1)
**Risk**: High (LinkedIn API limitations, anti-bot detection)

---

### Feature 3.5: Job Board Integration 🔍 **P2** (Stretch Goal)

**Business Value**: More opportunities, automated sourcing

**User Story**:
> "As a user, I want the system to automatically pull relevant job postings from Indeed and Glassdoor so that I have more opportunities to evaluate."

#### Current State
- ✅ Scraper pattern established
- ✅ Background job processing
- ❌ No job board integration

#### Target State
- ✅ Indeed job scraper
- ✅ Glassdoor job scraper
- ✅ Periodic polling (daily/weekly)
- ✅ Job deduplication
- ✅ Automatic opportunity creation
- ✅ Source tracking

#### Technical Design

```python
# app/scrapers/indeed_scraper.py
class IndeedScraper:
    """Scrape jobs from Indeed."""

    async def search_jobs(
        self,
        keywords: list[str],
        location: str = "Remote",
        salary_min: Optional[int] = None
    ) -> list[JobPosting]:
        """Search Indeed for matching jobs."""

        # Build search URL
        url = self._build_search_url(keywords, location, salary_min)

        # Fetch with Playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)

            # Extract job listings
            jobs = await self._extract_jobs(page)

            await browser.close()

        return jobs

    async def _extract_jobs(self, page) -> list[JobPosting]:
        """Extract job data from page."""
        job_cards = await page.query_selector_all(".job_seen_beacon")

        jobs = []
        for card in job_cards:
            job = JobPosting(
                source="indeed",
                title=await card.query_selector(".jobTitle").text_content(),
                company=await card.query_selector(".companyName").text_content(),
                location=await card.query_selector(".companyLocation").text_content(),
                description=await self._get_job_description(card),
                url=await card.query_selector("a").get_attribute("href"),
                posted_date=await self._parse_date(card)
            )
            jobs.append(job)

        return jobs

# app/scrapers/glassdoor_scraper.py
class GlassdoorScraper:
    """Similar implementation for Glassdoor."""
    pass

# app/tasks/job_board_tasks.py
@celery_app.task(name="scrape_job_boards")
async def scrape_job_boards():
    """Periodic task to scrape job boards."""

    # Get user search criteria from profile
    profile = await get_profile()

    # Scrape Indeed
    indeed = IndeedScraper()
    indeed_jobs = await indeed.search_jobs(
        keywords=profile.tech_stack,
        salary_min=profile.minimum_salary_usd
    )

    # Scrape Glassdoor
    glassdoor = GlassdoorScraper()
    glassdoor_jobs = await glassdoor.search_jobs(
        keywords=profile.tech_stack,
        salary_min=profile.minimum_salary_usd
    )

    # Process all jobs
    all_jobs = indeed_jobs + glassdoor_jobs

    for job in all_jobs:
        # Check if already exists
        if await job_exists(job):
            continue

        # Create opportunity
        await opportunity_service.create_opportunity_from_job(job)

# Schedule task
celery_app.conf.beat_schedule = {
    'scrape-job-boards-daily': {
        'task': 'scrape_job_boards',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8am
    }
}
```

#### Tasks
- [ ] **3.5.1** Create `app/scrapers/indeed_scraper.py`
- [ ] **3.5.2** Create `app/scrapers/glassdoor_scraper.py`
- [ ] **3.5.3** Implement job search logic
- [ ] **3.5.4** Add job data extraction
- [ ] **3.5.5** Create `JobPosting` model
- [ ] **3.5.6** Implement deduplication logic
- [ ] **3.5.7** Add conversion from JobPosting to Opportunity
- [ ] **3.5.8** Create periodic Celery task
- [ ] **3.5.9** Add source tracking
- [ ] **3.5.10** Implement rate limiting
- [ ] **3.5.11** Add error handling and retries
- [ ] **3.5.12** Write tests (10+ tests)

**Estimated Effort**: 2 days
**Dependencies**: Scraper pattern (✅)
**Risk**: High (site structure changes, anti-scraping measures)

---

## 📅 Sprint Timeline

### Week 1 (Days 1-7)
- **Days 1-3**: Feature 3.1 - Multi-Model LLM Support
- **Days 4-5**: Feature 3.2 - Advanced Search & Filtering
- **Days 6-7**: Feature 3.3 - Email/Slack Notifications (start)

### Week 2 (Days 8-14)
- **Days 8-9**: Feature 3.3 - Email/Slack Notifications (complete)
- **Days 10-12**: Feature 3.4 - Response Automation
- **Days 13-14**: Testing, documentation, buffer

### Stretch (if time permits)
- Feature 3.5 - Job Board Integration

---

## 🎯 Success Criteria

### Functional
- [ ] Can switch between OpenAI, Anthropic, Ollama
- [ ] Full-text search returns relevant results
- [ ] Can filter by complex criteria (salary, tech stack, etc.)
- [ ] Email notifications sent for A-tier opportunities
- [ ] Slack notifications working with rich formatting
- [ ] Responses generated and require approval for A/B/C-tier
- [ ] Auto-decline working for D-tier
- [ ] Responses sent during business hours only

### Performance
- [ ] Search response time < 200ms
- [ ] Notification latency < 30s
- [ ] Response generation < 5s
- [ ] No impact on existing performance metrics

### Quality
- [ ] 80%+ test coverage for new features
- [ ] 50+ new tests written
- [ ] All integration tests passing
- [ ] Documentation complete

---

## 🔧 Technical Dependencies

### New Dependencies to Add

```toml
# pyproject.toml additions

# OpenAI
openai = "^1.10.0"

# Anthropic
anthropic = "^0.18.0"

# Email
aiosmtplib = "^3.0.1"
email-validator = "^2.1.0"

# Notifications
httpx = "^0.26.0"  # For Slack webhooks

# Full-text search (already have PostgreSQL)
# No new dependencies needed

# Testing
respx = "^0.20.0"  # For mocking HTTP
```

### Environment Variables

```bash
# LLM Providers
LLM_PROVIDER=openai  # openai, anthropic, ollama
LLM_MODEL=gpt-4
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Per-module LLM config (optional)
ANALYZER_LLM_PROVIDER=openai
ANALYZER_LLM_MODEL=gpt-3.5-turbo
SCORER_LLM_PROVIDER=anthropic
SCORER_LLM_MODEL=claude-3-sonnet
RESPONSE_LLM_PROVIDER=openai
RESPONSE_LLM_MODEL=gpt-4

# Notifications
NOTIFICATION_ENABLED=true
EMAIL_ENABLED=true
SLACK_ENABLED=true

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=LinkedIn Agent <noreply@linkedinagent.com>

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Notification Rules
NOTIFICATION_TIER_THRESHOLD=A,B
NOTIFICATION_SCORE_THRESHOLD=80
NOTIFICATION_RATE_LIMIT=10  # per day
NOTIFICATION_DIGEST_MODE=false

# Response Automation
RESPONSE_AUTO_SEND_D_TIER=true
RESPONSE_REQUIRE_APPROVAL_TIERS=A,B,C
RESPONSE_BUSINESS_HOURS_ONLY=true
RESPONSE_RATE_LIMIT=5  # per day

# Job Boards
JOB_BOARDS_ENABLED=true
JOB_BOARDS_SCRAPE_SCHEDULE=daily
INDEED_ENABLED=true
GLASSDOOR_ENABLED=true
```

---

## 🚨 Risks & Mitigations

### Risk 1: API Rate Limits (OpenAI/Anthropic)
**Severity**: Medium
**Mitigation**:
- Implement exponential backoff
- Use caching aggressively (already have from Sprint 2)
- Fallback to secondary provider
- Monitor usage with metrics

### Risk 2: LinkedIn Anti-Bot Detection
**Severity**: High
**Mitigation**:
- Use proper delays between actions
- Maintain realistic user behavior patterns
- Session persistence (already implemented)
- Manual fallback option
- Clear error messages to user

### Risk 3: Email Deliverability
**Severity**: Medium
**Mitigation**:
- Use proper SMTP authentication
- Implement SPF/DKIM (documentation)
- Rate limiting to avoid spam flags
- Allow users to test with their own email first

### Risk 4: Job Board Structure Changes
**Severity**: Medium
**Mitigation**:
- Robust error handling
- Regular monitoring
- Quick rollback capability
- Make job boards optional feature

### Risk 5: Scope Creep
**Severity**: Medium
**Mitigation**:
- Stick to P0 and P1 features
- Move P2 to Sprint 4 if needed
- Clear definition of done for each feature
- Daily progress tracking

---

## 📊 Metrics to Track

### New Metrics

```python
# LLM Provider Metrics
llm_provider_requests_total{provider, model, module}
llm_provider_errors_total{provider, error_type}
llm_provider_cost_usd{provider, model}
llm_provider_latency_seconds{provider, model}
llm_provider_tokens_used{provider, model, type}  # prompt, completion

# Search Metrics
search_requests_total{has_query, has_filters}
search_results_count{bucket}  # 0, 1-5, 6-20, 21+
search_latency_seconds
search_cache_hit_rate

# Notification Metrics
notifications_sent_total{channel, tier, status}  # sent, failed
notifications_rate_limited_total
notification_delivery_latency_seconds{channel}

# Response Metrics
responses_generated_total{tier, response_type}
responses_sent_total{tier, status}  # sent, failed
responses_approved_total
responses_rejected_total
response_generation_latency_seconds
response_approval_time_seconds  # time from generation to approval

# Job Board Metrics
job_boards_scrape_total{source, status}
job_boards_jobs_found{source}
job_boards_duplicates_total{source}
job_boards_scrape_latency_seconds{source}
```

---

## 📚 Documentation Plan

### New Documentation
- [ ] **Multi-LLM Configuration Guide** - How to configure different providers
- [ ] **Search API Documentation** - Search syntax and filter examples
- [ ] **Notification Setup Guide** - Email/Slack configuration
- [ ] **Response Workflow Guide** - How approval workflow works
- [ ] **Job Board Integration Guide** - Supported sites and configuration

### Updated Documentation
- [ ] **README.md** - Add Sprint 3 features
- [ ] **ARCHITECTURE.md** - LLM abstraction layer
- [ ] **DEPLOYMENT.md** - New environment variables
- [ ] **CHANGELOG.md** - v1.2.0 release notes

---

## 🧪 Testing Strategy

### Unit Tests (40+ new tests)
- LLM provider implementations (10 tests)
- Search query building (10 tests)
- Notification channel implementations (10 tests)
- Response generation (5 tests)
- Job board parsing (5 tests)

### Integration Tests (20+ new tests)
- End-to-end search with filters (5 tests)
- Notification delivery (5 tests)
- Response workflow (5 tests)
- Multi-provider LLM switching (5 tests)

### Manual Test Scenarios
- [ ] Switch between LLM providers and verify quality
- [ ] Search with complex filters
- [ ] Receive email notification
- [ ] Receive Slack notification
- [ ] Approve and send response
- [ ] Auto-decline D-tier opportunity
- [ ] Verify business hours scheduling

---

## 🎓 Lessons from Sprint 2 to Apply

### What Worked Well
✅ **Service layer pattern** - Continue using for new features
✅ **Comprehensive testing** - Write tests alongside features
✅ **Documentation as we go** - Don't save for end
✅ **Monitoring integration** - Add metrics for all new features
✅ **Incremental approach** - Build features in logical order

### What to Improve
⚠️ **API design upfront** - Design APIs before implementation
⚠️ **Mock external services early** - Don't wait for rate limits
⚠️ **Performance testing** - Test under load earlier
⚠️ **Error scenarios** - Test failure cases from start

---

## 🚀 Getting Started

### Day 1 Checklist
- [ ] Review this plan with team
- [ ] Set up OpenAI and Anthropic API keys
- [ ] Create feature branches
- [ ] Set up test email/Slack for notifications
- [ ] Run Sprint 2 smoke test to ensure stability
- [ ] Begin Feature 3.1 (Multi-Model LLM)

---

## 📝 Notes

- **MVP Focus**: P0 and P1 features are must-have. P2 is stretch.
- **Quality Over Speed**: Don't compromise on tests and documentation
- **User Feedback**: Get early feedback on response generation quality
- **Monitoring**: Track LLM costs carefully with new providers
- **Security**: Handle API keys securely, never commit them

---

**Next Steps**:
1. Review and approve this plan
2. Set up API keys for OpenAI/Anthropic
3. Create Sprint 3 branch
4. Begin Feature 3.1 implementation

---

*Last Updated: January 17, 2024*
*Status: 📋 PLANNING*
*Ready to Start: Pending Approval*
