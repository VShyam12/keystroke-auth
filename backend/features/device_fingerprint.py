import datetime

from backend.app import db
from backend.models.device import Device


class DeviceFingerprintAnalyzer:
    """Analyzes and manages trusted state for user devices."""

    def get_or_create_device(self, user_id: int, fingerprint_data: dict) -> tuple:
        """Fetch an existing device for a user or create a new untrusted one."""
        device = Device.query.filter_by(
            user_id=user_id,
            device_id=fingerprint_data["device_id"],
        ).first()

        if device:
            device.update_last_seen()
            db.session.commit()
            return device, False

        device = Device(
            user_id=user_id,
            device_id=fingerprint_data.get("device_id"),
            user_agent=fingerprint_data.get("user_agent"),
            platform=fingerprint_data.get("platform"),
            screen_resolution=fingerprint_data.get("screen_resolution"),
            timezone_offset=fingerprint_data.get("timezone_offset"),
            is_trusted=False,
            first_seen=datetime.datetime.now(datetime.timezone.utc),
            last_seen=datetime.datetime.now(datetime.timezone.utc),
            login_count=1,
        )
        db.session.add(device)
        db.session.commit()
        return device, True

    def calculate_device_risk(self, user_id: int, fingerprint_data: dict) -> float:
        """Calculate risk score for a device based on familiarity and trust state."""
        device, is_new = self.get_or_create_device(user_id, fingerprint_data)

        if is_new:
            return 0.7

        if device.is_trusted:
            return 0.1

        if device.login_count >= 3:
            return 0.2

        return 0.4

    def get_user_devices(self, user_id: int) -> list:
        """Return all devices associated with a user as dictionaries."""
        devices = Device.query.filter_by(user_id=user_id).all()
        return [device.to_dict() for device in devices]

    def trust_device(self, user_id: int, device_id: str) -> bool:
        """Mark a user device as trusted if it exists."""
        device = Device.query.filter_by(user_id=user_id, device_id=device_id).first()
        if not device:
            return False

        device.mark_trusted()
        db.session.commit()
        return True