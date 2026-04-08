import datetime

from backend.models.login_log import LoginLog


class LoginContextAnalyzer:
    """Evaluates contextual login risk from historical behavior and recent activity."""

    def get_login_hour_risk(self, user_id: int) -> float:
        """Return risk based on how unusual the current UTC login hour is for the user."""
        current_hour = datetime.datetime.now(datetime.timezone.utc).hour

        historical_logins = (
            LoginLog.query.filter_by(user_id=user_id, outcome='granted')
            .order_by(LoginLog.timestamp.desc())
            .limit(30)
            .all()
        )

        if len(historical_logins) < 5:
            return 0.3

        normal_hours = {log.timestamp.hour for log in historical_logins if log.timestamp is not None}
        if not normal_hours:
            return 0.3

        hour_diffs = [min(abs(current_hour - hour), 24 - abs(current_hour - hour)) for hour in normal_hours]
        min_diff = min(hour_diffs)

        if min_diff <= 2:
            return 0.1
        if min_diff <= 4:
            return 0.3
        return 0.7

    def get_day_of_week_risk(self, user_id: int) -> float:
        """Return risk based on whether the current UTC weekday matches prior successful logins."""
        current_day = datetime.datetime.now(datetime.timezone.utc).weekday()

        historical_logins = (
            LoginLog.query.filter_by(user_id=user_id, outcome='granted')
            .order_by(LoginLog.timestamp.desc())
            .limit(30)
            .all()
        )

        if len(historical_logins) < 5:
            return 0.2

        normal_days = {log.timestamp.weekday() for log in historical_logins if log.timestamp is not None}
        if current_day in normal_days:
            return 0.1
        return 0.4

    def get_frequency_risk(self, user_id: int) -> float:
        """Return risk from the number of login attempts in the past 10 UTC minutes."""
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        window_start = now_utc - datetime.timedelta(minutes=10)

        attempt_count = (
            LoginLog.query.filter(LoginLog.user_id == user_id, LoginLog.timestamp >= window_start)
            .count()
        )

        if attempt_count >= 10:
            return 1.0
        if attempt_count >= 5:
            return 0.6
        if attempt_count >= 3:
            return 0.3
        return 0.0

    def calculate_context_risk(self, user_id: int) -> dict:
        """Compute weighted context risk and return component scores plus flags."""
        hour_risk = self.get_login_hour_risk(user_id)
        day_risk = self.get_day_of_week_risk(user_id)
        frequency_risk = self.get_frequency_risk(user_id)

        context_risk_score = (hour_risk * 0.4) + (day_risk * 0.3) + (frequency_risk * 0.3)

        return {
            'context_risk_score': float(context_risk_score),
            'hour_risk': float(hour_risk),
            'day_risk': float(day_risk),
            'frequency_risk': float(frequency_risk),
            'is_unusual_time': hour_risk >= 0.5,
            'is_high_frequency': frequency_risk >= 0.6,
        }