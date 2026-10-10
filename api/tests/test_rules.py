from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.rules import validate_minimum_lead_time

TZ = ZoneInfo("America/Mexico_City")


def test_three_hour_rule_blocks_too_soon():
    now = datetime(2026, 10, 3, 10, 0, tzinfo=TZ)
    starts = now + timedelta(hours=2, minutes=59)
    assert validate_minimum_lead_time(starts, now=now) is False


def test_three_hour_rule_allows_exact_boundary():
    now = datetime(2026, 10, 3, 10, 0, tzinfo=TZ)
    starts = now + timedelta(hours=3)
    assert validate_minimum_lead_time(starts, now=now) is True
