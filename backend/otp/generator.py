import datetime
import warnings

from backend.app import db
from backend.models.otp import OTPRecord


class OTPService:
    """Manages one-time password generation, verification, and lifecycle."""

    def generate_otp(
        self, user_id: int, purpose: str = 'login', expiry_minutes: int = 5
    ) -> dict:
        """Create a new OTP for a user, invalidating any prior unused OTPs with same purpose."""
        OTPRecord.query.filter_by(user_id=user_id, purpose=purpose, is_used=False).update(
            {'is_used': True}
        )
        db.session.commit()

        code = OTPRecord.generate_code()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            now_utc = datetime.datetime.utcnow()
        expires_at = now_utc + datetime.timedelta(minutes=expiry_minutes)

        otp = OTPRecord(
            user_id=user_id,
            code=code,
            purpose=purpose,
            expires_at=expires_at,
        )
        db.session.add(otp)
        db.session.commit()

        expires_in_seconds = int(expiry_minutes * 60)

        return {
            'otp_id': otp.id,
            'code': code,
            'expires_at': expires_at.isoformat(),
            'expires_in_seconds': expires_in_seconds,
            'message': 'OTP generated successfully',
        }

    def verify_otp(self, user_id: int, submitted_code: str, purpose: str = 'login') -> dict:
        """Validate a submitted OTP code against stored records with attempt tracking."""
        otp = (
            OTPRecord.query.filter_by(user_id=user_id, purpose=purpose, is_used=False)
            .order_by(OTPRecord.created_at.desc())
            .first()
        )

        if not otp:
            return {'success': False, 'reason': 'no_otp_found'}

        otp.attempts = (otp.attempts or 0) + 1
        db.session.commit()

        if otp.attempts > 3:
            return {'success': False, 'reason': 'too_many_attempts'}

        if otp.is_expired():
            return {'success': False, 'reason': 'otp_expired'}

        if submitted_code != otp.code:
            return {'success': False, 'reason': 'invalid_code'}

        otp.is_used = True
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            otp.used_at = datetime.datetime.utcnow()
        db.session.commit()

        return {'success': True, 'reason': 'verified', 'otp_id': otp.id}

    def cleanup_expired_otps(self, user_id: int = None) -> int:
        """Delete all expired or used OTPs, optionally scoped to a single user."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            now_utc = datetime.datetime.utcnow()
        query = OTPRecord.query.filter(
            (OTPRecord.is_used == True) | (OTPRecord.expires_at < now_utc)
        )

        if user_id is not None:
            query = query.filter_by(user_id=user_id)

        count = query.delete()
        db.session.commit()
        return count
