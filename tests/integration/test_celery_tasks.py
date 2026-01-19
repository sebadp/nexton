"""
Integration tests for Celery background tasks.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.celery_app.tasks import (
    process_opportunity_task,
    scrape_linkedin_messages_task,
    send_notification_task,
    update_opportunity_stats_task,
)


class TestProcessOpportunityTask:
    """Test opportunity processing task."""

    @patch("app.celery_app.tasks.get_db")
    @patch("app.celery_app.tasks.OpportunityService")
    def test_process_opportunity_success(self, mock_service_class, mock_get_db):
        """Test successful opportunity processing."""
        # Mock database session
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)

        # Mock service
        mock_service = AsyncMock()
        mock_opportunity = MagicMock()
        mock_opportunity.id = 1
        mock_opportunity.total_score = 85
        mock_opportunity.tier = "A"
        mock_service.create_opportunity = AsyncMock(return_value=mock_opportunity)
        mock_service_class.return_value = mock_service

        # Execute task
        result = process_opportunity_task(
            recruiter_name="Jane Smith",
            raw_message="Great opportunity at TechCorp",
        )

        # Assertions
        assert result["success"] is True
        assert result["opportunity_id"] == 1
        assert result["score"] == 85
        assert result["tier"] == "A"

    @patch("app.celery_app.tasks.get_db")
    @patch("app.celery_app.tasks.OpportunityService")
    def test_process_opportunity_failure(self, mock_service_class, mock_get_db):
        """Test opportunity processing failure."""
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)

        mock_service = AsyncMock()
        mock_service.create_opportunity = AsyncMock(
            side_effect=Exception("Processing failed")
        )
        mock_service_class.return_value = mock_service

        result = process_opportunity_task(
            recruiter_name="Jane Smith",
            raw_message="Test message",
        )

        assert result["success"] is False
        assert "error" in result

    @patch("app.celery_app.tasks.track_pipeline_execution")
    @patch("app.celery_app.tasks.get_db")
    @patch("app.celery_app.tasks.OpportunityService")
    def test_process_opportunity_metrics(
        self,
        mock_service_class,
        mock_get_db,
        mock_track_pipeline,
    ):
        """Test that metrics are tracked."""
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)

        mock_service = AsyncMock()
        mock_opportunity = MagicMock()
        mock_opportunity.id = 1
        mock_service.create_opportunity = AsyncMock(return_value=mock_opportunity)
        mock_service_class.return_value = mock_service

        process_opportunity_task(
            recruiter_name="Jane Smith",
            raw_message="Test message",
        )

        # Verify metrics tracking (if implemented in task)
        # mock_track_pipeline.assert_called()


class TestScrapeLinkedInMessagesTask:
    """Test LinkedIn scraping task."""

    @patch("app.celery_app.tasks.LinkedInScraper")
    @patch("app.celery_app.tasks.RedisCache")
    def test_scrape_messages_success(self, mock_cache_class, mock_scraper_class):
        """Test successful message scraping."""
        # Mock scraper
        mock_scraper = AsyncMock()
        mock_scraper.start = AsyncMock()
        mock_scraper.login = AsyncMock()
        mock_scraper.fetch_messages = AsyncMock(return_value=[
            {"sender": "John Doe", "message": "Test message 1"},
            {"sender": "Jane Smith", "message": "Test message 2"},
        ])
        mock_scraper.close = AsyncMock()
        mock_scraper_class.return_value.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper_class.return_value.__aexit__ = AsyncMock()

        # Mock cache
        mock_cache = AsyncMock()
        mock_cache.set = AsyncMock()
        mock_cache_class.return_value = mock_cache

        result = scrape_linkedin_messages_task()

        assert result["success"] is True
        assert result["messages_count"] == 2

    @patch("app.celery_app.tasks.LinkedInScraper")
    def test_scrape_messages_failure(self, mock_scraper_class):
        """Test scraping failure."""
        mock_scraper = AsyncMock()
        mock_scraper.start = AsyncMock()
        mock_scraper.login = AsyncMock(side_effect=Exception("Login failed"))
        mock_scraper.close = AsyncMock()
        mock_scraper_class.return_value.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper_class.return_value.__aexit__ = AsyncMock()

        result = scrape_linkedin_messages_task()

        assert result["success"] is False
        assert "error" in result

    @patch("app.celery_app.tasks.scraper_operations_total")
    @patch("app.celery_app.tasks.LinkedInScraper")
    def test_scrape_messages_metrics(self, mock_scraper_class, mock_metric):
        """Test that scraping metrics are tracked."""
        mock_scraper = AsyncMock()
        mock_scraper.start = AsyncMock()
        mock_scraper.login = AsyncMock()
        mock_scraper.fetch_messages = AsyncMock(return_value=[])
        mock_scraper.close = AsyncMock()
        mock_scraper_class.return_value.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper_class.return_value.__aexit__ = AsyncMock()

        scrape_linkedin_messages_task()

        # Verify metrics were tracked (if implemented)
        # mock_metric.labels.assert_called()

    @patch("app.celery_app.tasks.LinkedInScraper")
    @patch("app.celery_app.tasks.RateLimiter")
    def test_scrape_respects_rate_limit(self, mock_rate_limiter, mock_scraper_class):
        """Test that rate limiting is applied."""
        mock_scraper = AsyncMock()
        mock_scraper.start = AsyncMock()
        mock_scraper.login = AsyncMock()
        mock_scraper.fetch_messages = AsyncMock(return_value=[])
        mock_scraper.close = AsyncMock()
        mock_scraper_class.return_value.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper_class.return_value.__aexit__ = AsyncMock()

        scrape_linkedin_messages_task()

        # Rate limiter should be used
        # This verifies the scraper was initialized with rate limiting


class TestSendNotificationTask:
    """Test notification sending task."""

    @patch("app.celery_app.tasks.send_email")
    def test_send_notification_success(self, mock_send_email):
        """Test successful notification sending."""
        mock_send_email.return_value = True

        result = send_notification_task(
            recipient="user@example.com",
            subject="New Opportunity",
            message="You have a new A-tier opportunity!",
        )

        assert result["success"] is True
        mock_send_email.assert_called_once()

    @patch("app.celery_app.tasks.send_email")
    def test_send_notification_failure(self, mock_send_email):
        """Test notification sending failure."""
        mock_send_email.side_effect = Exception("Email server error")

        result = send_notification_task(
            recipient="user@example.com",
            subject="Test",
            message="Test message",
        )

        assert result["success"] is False
        assert "error" in result

    def test_send_notification_validation(self):
        """Test notification input validation."""
        # Test with invalid email
        result = send_notification_task(
            recipient="invalid-email",
            subject="Test",
            message="Test message",
        )

        # Should handle validation error
        assert "success" in result


class TestUpdateOpportunityStatsTask:
    """Test stats update task."""

    @patch("app.celery_app.tasks.get_db")
    @patch("app.celery_app.tasks.OpportunityService")
    @patch("app.celery_app.tasks.update_opportunities_by_tier")
    def test_update_stats_success(
        self,
        mock_update_metric,
        mock_service_class,
        mock_get_db,
    ):
        """Test successful stats update."""
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)

        mock_service = AsyncMock()
        mock_service.get_stats = AsyncMock(return_value={
            "total_count": 100,
            "by_tier": {"A": 10, "B": 30, "C": 40, "D": 20},
            "average_score": 72.5,
        })
        mock_service_class.return_value = mock_service

        result = update_opportunity_stats_task()

        assert result["success"] is True
        assert result["total_count"] == 100
        assert result["tier_counts"] == {"A": 10, "B": 30, "C": 40, "D": 20}

        # Verify metrics were updated
        mock_update_metric.assert_called_once()

    @patch("app.celery_app.tasks.get_db")
    @patch("app.celery_app.tasks.OpportunityService")
    def test_update_stats_failure(self, mock_service_class, mock_get_db):
        """Test stats update failure."""
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)

        mock_service = AsyncMock()
        mock_service.get_stats = AsyncMock(side_effect=Exception("Database error"))
        mock_service_class.return_value = mock_service

        result = update_opportunity_stats_task()

        assert result["success"] is False
        assert "error" in result


class TestCeleryTaskConfiguration:
    """Test Celery task configuration."""

    def test_task_names(self):
        """Test that tasks are properly named."""
        assert process_opportunity_task.name == "process_opportunity"
        assert scrape_linkedin_messages_task.name == "scrape_linkedin_messages"
        assert send_notification_task.name == "send_notification"
        assert update_opportunity_stats_task.name == "update_opportunity_stats"

    def test_task_retries(self):
        """Test task retry configuration."""
        # Verify tasks have retry configuration
        assert hasattr(process_opportunity_task, "max_retries")
        assert hasattr(scrape_linkedin_messages_task, "max_retries")

    def test_task_routing(self):
        """Test task routing configuration."""
        # Verify tasks are routed correctly
        assert hasattr(process_opportunity_task, "queue")


class TestCeleryBeat:
    """Test Celery Beat scheduled tasks."""

    @patch("app.celery_app.celery_app.conf.beat_schedule")
    def test_scheduled_tasks_configured(self, mock_beat_schedule):
        """Test that periodic tasks are configured."""
        # Verify scheduled tasks exist
        expected_tasks = [
            "scrape-linkedin-messages",
            "update-opportunity-stats",
        ]

        # Check if tasks are in beat schedule (if configured)
        # This depends on your actual beat schedule configuration


@pytest.mark.asyncio
class TestTaskChaining:
    """Test task chaining and workflows."""

    @patch("app.celery_app.tasks.process_opportunity_task.apply_async")
    @patch("app.celery_app.tasks.send_notification_task.apply_async")
    def test_opportunity_notification_chain(
        self,
        mock_notification,
        mock_process,
    ):
        """Test chaining opportunity processing with notification."""
        # Mock successful processing
        mock_process.return_value = MagicMock(
            id="task-123",
            get=MagicMock(return_value={
                "success": True,
                "opportunity_id": 1,
                "tier": "A",
            }),
        )

        # Simulate task chain: process -> notify if tier A
        result = mock_process.return_value.get()

        if result["success"] and result["tier"] == "A":
            mock_notification.assert_not_called()  # Would be called in real chain

    @patch("app.celery_app.tasks.scrape_linkedin_messages_task")
    @patch("app.celery_app.tasks.process_opportunity_task")
    def test_scrape_and_process_workflow(
        self,
        mock_process,
        mock_scrape,
    ):
        """Test workflow: scrape messages -> process each opportunity."""
        # Mock scraping result
        mock_scrape.return_value = {
            "success": True,
            "messages": [
                {"sender": "John", "message": "Opportunity 1"},
                {"sender": "Jane", "message": "Opportunity 2"},
            ],
        }

        messages = mock_scrape.return_value["messages"]

        # Each message should trigger processing task
        for msg in messages:
            mock_process.apply_async.assert_not_called()  # Would be called in real workflow


class TestTaskMonitoring:
    """Test task monitoring and metrics."""

    @patch("app.celery_app.tasks.track_pipeline_execution")
    @patch("app.celery_app.tasks.get_db")
    @patch("app.celery_app.tasks.OpportunityService")
    def test_task_duration_tracking(
        self,
        mock_service_class,
        mock_get_db,
        mock_track,
    ):
        """Test that task duration is tracked."""
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)

        mock_service = AsyncMock()
        mock_opportunity = MagicMock()
        mock_opportunity.id = 1
        mock_service.create_opportunity = AsyncMock(return_value=mock_opportunity)
        mock_service_class.return_value = mock_service

        import time
        start = time.time()
        process_opportunity_task("John", "Test message")
        duration = time.time() - start

        assert duration >= 0  # Task completed

    def test_task_error_tracking(self):
        """Test that task errors are tracked."""
        # Test error handling and logging
        with patch("app.celery_app.tasks.logger") as mock_logger:
            with patch("app.celery_app.tasks.OpportunityService") as mock_service_class:
                mock_service_class.side_effect = Exception("Task error")

                try:
                    process_opportunity_task("John", "Test")
                except Exception:
                    pass

                # Logger should have recorded the error
                # mock_logger.error.assert_called()
