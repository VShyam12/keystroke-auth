from backend.features.device_fingerprint import DeviceFingerprintAnalyzer
from backend.risk.context import LoginContextAnalyzer


BIOMETRIC_WEIGHT = 0.40
DEVICE_WEIGHT = 0.40
CONTEXT_WEIGHT = 0.20
LOW_RISK_THRESHOLD = 25.0
HIGH_RISK_THRESHOLD = 60.0

RISK_LOW = 'LOW'
RISK_MEDIUM = 'MEDIUM'
RISK_HIGH = 'HIGH'


class RiskScorer:
    """Combines biometric, device, and context signals into a final access risk score."""

    def __init__(self):
        """Initialize dependent analyzers used in composite risk scoring."""
        self.context_analyzer = LoginContextAnalyzer()
        self.device_analyzer = DeviceFingerprintAnalyzer()

    def normalize_biometric_score(self, raw_score: float, threshold: float) -> float:
        """Normalize raw biometric distance into a clamped 0.0-1.0 risk signal."""
        if raw_score <= 0:
            return 0.0

        safe_threshold = threshold if threshold and threshold > 0 else 1.0
        normalized = raw_score / (safe_threshold * 3)
        return float(max(0.0, min(1.0, normalized)))

    def calculate_risk(
        self,
        user_id: int,
        biometric_score: float,
        biometric_threshold: float,
        fingerprint_data: dict,
    ) -> dict:
        """Calculate weighted final risk, risk level, and action recommendation for a login attempt."""
        biometric_risk = self.normalize_biometric_score(biometric_score, biometric_threshold)

        device_risk = self.device_analyzer.calculate_device_risk(user_id, fingerprint_data)

        context_data = self.context_analyzer.calculate_context_risk(user_id)
        context_risk = context_data['context_risk_score']

        final_score = (
            biometric_risk * BIOMETRIC_WEIGHT * 100
            + device_risk * DEVICE_WEIGHT * 100
            + context_risk * CONTEXT_WEIGHT * 100
        )

        if final_score < LOW_RISK_THRESHOLD:
            risk_level = RISK_LOW
            recommendation = 'grant_access'
        elif final_score < HIGH_RISK_THRESHOLD:
            risk_level = RISK_MEDIUM
            recommendation = 'require_otp'
        else:
            risk_level = RISK_HIGH
            recommendation = 'deny_access'

        return {
            'risk_level': risk_level,
            'final_score': float(final_score),
            'biometric_risk': float(biometric_risk),
            'biometric_score': float(biometric_score),
            'device_risk': float(device_risk),
            'context_risk': float(context_risk),
            'is_new_device': bool(device_risk >= 0.6),
            'is_unusual_time': bool(context_data.get('is_unusual_time', False)),
            'is_high_frequency': bool(context_data.get('is_high_frequency', False)),
            'recommendation': recommendation,
        }

    def get_risk_summary(self, risk_result: dict) -> str:
        """Build a human-readable summary that highlights elevated contributing signals."""
        risk_level = risk_result.get('risk_level', RISK_LOW)
        final_score = float(risk_result.get('final_score', 0.0))

        reasons = []
        if risk_result.get('is_new_device'):
            reasons.append('new device detected')
        if risk_result.get('is_unusual_time'):
            reasons.append('unusual login time')
        if risk_result.get('is_high_frequency'):
            reasons.append('high login attempt frequency')
        if float(risk_result.get('biometric_risk', 0.0)) >= 0.5:
            reasons.append('biometric mismatch risk elevated')

        recommendation = risk_result.get('recommendation', 'grant_access')
        if recommendation == 'grant_access':
            action_text = 'access granted'
        elif recommendation == 'require_otp':
            action_text = 'OTP verification required'
        else:
            action_text = 'access denied'

        if reasons:
            return f"{risk_level} risk (score: {final_score:.1f}) - {', '.join(reasons)}, {action_text}"

        return f"{risk_level} risk (score: {final_score:.1f}) - no elevated signals, {action_text}"