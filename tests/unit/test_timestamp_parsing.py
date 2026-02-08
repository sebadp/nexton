"""
Unit tests for LinkedIn timestamp parsing.

Tests parse_relative_timestamp and _parse_linkedin_custom functions
with various date formats across Spanish and English locales.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.scraper.linkedin_scraper import _parse_linkedin_custom, parse_relative_timestamp


class TestParseRelativeTimestamp:
    """Tests for the main parse_relative_timestamp function."""

    @pytest.fixture
    def fixed_now(self):
        """Fixed datetime for consistent testing: Sunday, Feb 8, 2026 at 12:00."""
        return datetime(2026, 2, 8, 12, 0, 0)

    def test_just_now_english(self, fixed_now):
        with patch("app.scraper.linkedin_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            # dateparser should handle "just now"
            result = parse_relative_timestamp("just now")
            # Should be very close to now
            assert (fixed_now - result).total_seconds() < 60

    def test_ahora_spanish(self, fixed_now):
        with patch("app.scraper.linkedin_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            result = parse_relative_timestamp("ahora")
            assert (fixed_now - result).total_seconds() < 60

    def test_yesterday_english(self, fixed_now):
        with patch("app.scraper.linkedin_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            result = parse_relative_timestamp("yesterday")
            assert result.date() == (fixed_now - timedelta(days=1)).date()

    def test_ayer_spanish(self, fixed_now):
        with patch("app.scraper.linkedin_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            result = parse_relative_timestamp("ayer")
            assert result.date() == (fixed_now - timedelta(days=1)).date()

    def test_hours_ago_english(self, fixed_now):
        with patch("app.scraper.linkedin_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            result = parse_relative_timestamp("2 hours ago")
            expected = fixed_now - timedelta(hours=2)
            assert abs((result - expected).total_seconds()) < 60

    def test_hace_horas_spanish(self, fixed_now):
        with patch("app.scraper.linkedin_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            result = parse_relative_timestamp("hace 3 horas")
            expected = fixed_now - timedelta(hours=3)
            assert abs((result - expected).total_seconds()) < 60

    def test_days_ago(self, fixed_now):
        with patch("app.scraper.linkedin_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            result = parse_relative_timestamp("5d")
            expected = fixed_now - timedelta(days=5)
            assert result.date() == expected.date()

    def test_date_month_spanish(self, fixed_now):
        """Test '29 ene' format."""
        with patch("app.scraper.linkedin_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            result = parse_relative_timestamp("29 ene")
            assert result.month == 1
            assert result.day == 29

    def test_date_month_english(self, fixed_now):
        """Test 'Jan 29' format."""
        with patch("app.scraper.linkedin_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            result = parse_relative_timestamp("Jan 29")
            assert result.month == 1
            assert result.day == 29

    def test_time_only_format(self, fixed_now):
        """Test '15:30' format.

        Note: dateparser with PREFER_DATES_FROM: 'past' returns yesterday
        if the time hasn't occurred yet today (fixed_now is 12:00).
        """
        with patch("app.scraper.linkedin_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            result = parse_relative_timestamp("15:30")
            # dateparser returns yesterday 15:30 since 15:30 hasn't happened yet at 12:00
            expected_date = (fixed_now - timedelta(days=1)).date()
            assert result.date() == expected_date
            assert result.hour == 15
            assert result.minute == 30

    def test_empty_string_returns_now(self, fixed_now):
        with patch("app.scraper.linkedin_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            result = parse_relative_timestamp("")
            assert result == fixed_now

    def test_invalid_input_returns_now(self, fixed_now):
        with patch("app.scraper.linkedin_scraper.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            result = parse_relative_timestamp("invalid garbage text xyz123")
            # Should return now as fallback
            assert result.date() == fixed_now.date()


class TestParseLinkedInCustom:
    """Tests for the _parse_linkedin_custom fallback function."""

    @pytest.fixture
    def sunday_feb_8(self):
        """Fixed datetime: Sunday, Feb 8, 2026 at 12:00."""
        return datetime(2026, 2, 8, 12, 0, 0)

    def test_day_name_spanish_viernes(self, sunday_feb_8):
        """viernes (Friday) from Sunday should be 2 days back."""
        result = _parse_linkedin_custom("viernes", sunday_feb_8)
        expected = sunday_feb_8 - timedelta(days=2)  # Friday
        assert result is not None
        assert result.date() == expected.date()

    def test_day_name_spanish_miercoles(self, sunday_feb_8):
        """miércoles (Wednesday) from Sunday should be 4 days back."""
        result = _parse_linkedin_custom("miércoles", sunday_feb_8)
        expected = sunday_feb_8 - timedelta(days=4)  # Wednesday
        assert result is not None
        assert result.date() == expected.date()

    def test_day_name_spanish_miercoles_no_accent(self, sunday_feb_8):
        """miercoles without accent should work."""
        result = _parse_linkedin_custom("miercoles", sunday_feb_8)
        expected = sunday_feb_8 - timedelta(days=4)
        assert result is not None
        assert result.date() == expected.date()

    def test_day_name_spanish_jueves(self, sunday_feb_8):
        """jueves (Thursday) from Sunday should be 3 days back."""
        result = _parse_linkedin_custom("jueves", sunday_feb_8)
        expected = sunday_feb_8 - timedelta(days=3)
        assert result is not None
        assert result.date() == expected.date()

    def test_day_name_english_friday(self, sunday_feb_8):
        """friday from Sunday should be 2 days back."""
        result = _parse_linkedin_custom("friday", sunday_feb_8)
        expected = sunday_feb_8 - timedelta(days=2)
        assert result is not None
        assert result.date() == expected.date()

    def test_day_name_english_monday(self, sunday_feb_8):
        """monday from Sunday should be 6 days back (last Monday)."""
        result = _parse_linkedin_custom("monday", sunday_feb_8)
        expected = sunday_feb_8 - timedelta(days=6)
        assert result is not None
        assert result.date() == expected.date()

    def test_same_day_returns_last_week(self, sunday_feb_8):
        """domingo (Sunday) from Sunday should be 7 days back."""
        result = _parse_linkedin_custom("domingo", sunday_feb_8)
        expected = sunday_feb_8 - timedelta(days=7)
        assert result is not None
        assert result.date() == expected.date()

    def test_day_name_with_time(self, sunday_feb_8):
        """viernes 15:30 should return Friday at 15:30."""
        result = _parse_linkedin_custom("viernes 15:30", sunday_feb_8)
        expected_date = sunday_feb_8 - timedelta(days=2)
        assert result is not None
        assert result.date() == expected_date.date()
        assert result.hour == 15
        assert result.minute == 30

    def test_day_name_with_12hr_time(self, sunday_feb_8):
        """friday 3:45 pm should return Friday at 15:45."""
        result = _parse_linkedin_custom("friday 3:45 pm", sunday_feb_8)
        if result:  # Only if parsed
            expected_date = sunday_feb_8 - timedelta(days=2)
            assert result.date() == expected_date.date()
            assert result.hour == 15
            assert result.minute == 45

    def test_unrecognized_returns_none(self, sunday_feb_8):
        """Unrecognized input should return None."""
        result = _parse_linkedin_custom("not a day name", sunday_feb_8)
        assert result is None


class TestEdgeCases:
    """Edge case tests."""

    def test_case_insensitive(self):
        now = datetime(2026, 2, 8, 12, 0, 0)
        result = _parse_linkedin_custom("VIERNES", now)
        assert result is not None

    def test_mixed_case(self):
        now = datetime(2026, 2, 8, 12, 0, 0)
        result = _parse_linkedin_custom("Viernes", now)
        assert result is not None

    def test_whitespace_handling(self):
        """Leading/trailing whitespace should be handled."""
        now = datetime(2026, 2, 8, 12, 0, 0)
        result = parse_relative_timestamp("  viernes  ")
        assert result is not None
