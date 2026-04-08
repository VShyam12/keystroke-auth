class DeviceFingerprint {
  /**
   * Collects browser and device fingerprint attributes.
   * @returns {Promise<object>} Collected fingerprint fields.
   */
  async collect() {
    const screenWidth = screen.width;
    const screenHeight = screen.height;

    return {
      user_agent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      screen_width: screenWidth,
      screen_height: screenHeight,
      screen_resolution: screenWidth + 'x' + screenHeight,
      timezone_offset: new Date().getTimezoneOffset(),
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      color_depth: screen.colorDepth,
      pixel_ratio: window.devicePixelRatio || 1,
      hardware_concurrency: navigator.hardwareConcurrency || 0,
      touch_support: 'ontouchstart' in window,
      cookie_enabled: navigator.cookieEnabled
    };
  }

  /**
   * Generates a SHA-256 device ID from selected fingerprint fields.
   * @param {object} fingerprintData - Fingerprint object returned by collect().
   * @returns {Promise<string>} Hex-encoded SHA-256 hash string.
   */
  async generateId(fingerprintData) {
    const payload = [
      fingerprintData.user_agent,
      fingerprintData.platform,
      fingerprintData.screen_resolution,
      fingerprintData.timezone_offset,
      fingerprintData.color_depth,
      fingerprintData.pixel_ratio
    ].join('|');

    const encoded = new TextEncoder().encode(payload);
    const digestBuffer = await crypto.subtle.digest('SHA-256', encoded);
    const digestBytes = new Uint8Array(digestBuffer);
    const hex = Array.from(digestBytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
    return hex;
  }

  /**
   * Collects fingerprint fields and returns them with a generated device ID.
   * @returns {Promise<object>} Fingerprint fields including device_id.
   */
  async getFingerprint() {
    const fingerprintData = await this.collect();
    const deviceId = await this.generateId(fingerprintData);

    return {
      ...fingerprintData,
      device_id: deviceId
    };
  }
}

if (typeof module !== 'undefined') module.exports = DeviceFingerprint;