"""Exceptions."""


class SentryException(Exception):
    """All sentry related Exception."""


class SentryNoOutcomeException(Exception):
    """Exception Raised when sentry doesn't return any stats."""
