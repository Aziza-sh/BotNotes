from datetime import datetime, time
from unittest.mock import patch

import pytest

from functions.greeting import send_greeting


class _FixedDateTime(datetime):
    """Позволяет подменить datetime.now() внутри functions.greeting."""

    _fixed_hour = 0

    @classmethod
    def now(cls, tz=None):
        return cls(2024, 1, 1, cls._fixed_hour, 0, 0)


def _greeting_at(hour: int, username: str | None = None) -> str:
    fixed = type("_Fixed", (_FixedDateTime,), {"_fixed_hour": hour})
    with patch("functions.greeting.datetime", fixed):
        return send_greeting(username)


@pytest.mark.parametrize(
    "hour, expected_word",
    [
        (4, "Доброе утро"),
        (11, "Доброе утро"),
        (12, "Добрый день"),
        (17, "Добрый день"),
        (18, "Добрый вечер"),
        (22, "Добрый вечер"),
        (23, "Доброй ночи"),
        (3, "Доброй ночи"),
        (0, "Доброй ночи"),
    ],
)
def test_send_greeting_time_bands(hour, expected_word):
    result = _greeting_at(hour)
    assert expected_word in result


def test_send_greeting_uses_username_when_given():
    result = _greeting_at(10, username="Redd")
    assert "Redd" in result
    assert "дорогой пользователь" not in result


def test_send_greeting_falls_back_without_username():
    result = _greeting_at(10, username=None)
    assert "дорогой пользователь" in result


def test_send_greeting_returns_html_bold_tags():
    result = _greeting_at(10)
    assert result.startswith("🌄")
    assert "<b>" in result and "</b>" in result
