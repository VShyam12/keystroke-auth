import datetime
import warnings

from backend.extensions import db
from backend.models.login_log import LoginLog


def log_security_event(event_type, user_id, details, ip_address=None):
    """Log a formatted security event entry to stdout."""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        timestamp = datetime.datetime.utcnow().isoformat()

    ip = ip_address if ip_address is not None else '-'
    print(f"[SECURITY] {timestamp} | {event_type} | {user_id} | {details} | {ip}")
    return None


def log_failed_login(user_id, reason, ip_address):
    """Log a failed login security event."""
    return log_security_event(
        event_type='FAILED_LOGIN',
        user_id=user_id,
        details=reason,
        ip_address=ip_address,
    )


def log_successful_login(user_id, risk_level, ip_address):
    """Log a successful login security event."""
    return log_security_event(
        event_type='SUCCESSFUL_LOGIN',
        user_id=user_id,
        details=f"risk_level={risk_level}",
        ip_address=ip_address,
    )


def log_otp_failure(user_id, reason, ip_address):
    """Log an OTP failure security event."""
    return log_security_event(
        event_type='OTP_FAILURE',
        user_id=user_id,
        details=reason,
        ip_address=ip_address,
    )


def log_suspicious_session(user_id, session_id, anomaly_score):
    """Log a suspicious session security event."""
    return log_security_event(
        event_type='SUSPICIOUS_SESSION',
        user_id=user_id,
        details=f"session={session_id} score={anomaly_score}",
    )
