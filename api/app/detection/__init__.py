from app.detection.engine import DetectionEngine, default_engine, default_rules
from app.detection.rules.brute_force import (
    BRUTE_FORCE_MIN_FAILURES,
    BRUTE_FORCE_WINDOW_MINUTES,
    BruteForceRule,
)
from app.detection.rules.credential_spray import (
    SPRAY_MIN_USERNAMES,
    SPRAY_WINDOW_MINUTES,
    CredentialSprayRule,
)
from app.detection.rules.impossible_travel import (
    IMPOSSIBLE_TRAVEL_MIN_LOCATIONS,
    IMPOSSIBLE_TRAVEL_WINDOW_MINUTES,
    ImpossibleTravelRule,
)
from app.detection.rules.request_frequency import (
    REQUEST_FREQUENCY_MIN_REQUESTS,
    REQUEST_FREQUENCY_WINDOW_MINUTES,
    RequestFrequencyRule,
)
from app.detection.rules.restricted_access import (
    RESTRICTED_ACCESS_MIN_DENIALS,
    RESTRICTED_RESOURCE_PREFIXES,
    RestrictedAccessRule,
)
from app.detection.rules.unusual_login import (
    UNUSUAL_LOGIN_HOURS_END_UTC,
    UNUSUAL_LOGIN_HOURS_START_UTC,
    UNUSUAL_LOGIN_MIN_SUCCESSES,
    UNUSUAL_LOGIN_WINDOW_MINUTES,
    UnusualLoginRule,
)

__all__ = [
    "BRUTE_FORCE_MIN_FAILURES",
    "BRUTE_FORCE_WINDOW_MINUTES",
    "BruteForceRule",
    "CredentialSprayRule",
    "DetectionEngine",
    "IMPOSSIBLE_TRAVEL_MIN_LOCATIONS",
    "IMPOSSIBLE_TRAVEL_WINDOW_MINUTES",
    "ImpossibleTravelRule",
    "REQUEST_FREQUENCY_MIN_REQUESTS",
    "REQUEST_FREQUENCY_WINDOW_MINUTES",
    "RESTRICTED_ACCESS_MIN_DENIALS",
    "RESTRICTED_RESOURCE_PREFIXES",
    "RequestFrequencyRule",
    "RestrictedAccessRule",
    "SPRAY_MIN_USERNAMES",
    "SPRAY_WINDOW_MINUTES",
    "UNUSUAL_LOGIN_HOURS_END_UTC",
    "UNUSUAL_LOGIN_HOURS_START_UTC",
    "UNUSUAL_LOGIN_MIN_SUCCESSES",
    "UNUSUAL_LOGIN_WINDOW_MINUTES",
    "UnusualLoginRule",
    "default_engine",
    "default_rules",
]
