class KeystrokeCollector {
	constructor() {
		this.events = [];
		this.keyDownTimes = {};
		this.startTime = null;
		this.isAttached = false;
		this._inputElement = null;
		this._handleKeyDown = null;
		this._handleKeyUp = null;
		this._ignoredKeys = new Set([
			'Shift',
			'CapsLock',
			'Backspace',
			'Delete',
			'Tab',
			'Enter',
			'Alt',
			'Control',
			'Meta',
			'ArrowLeft',
			'ArrowRight',
			'ArrowUp',
			'ArrowDown'
		]);
	}

	/**
	 * Attaches key listeners to an input element and begins event capture.
	 * @param {HTMLElement} inputElement - The input element to monitor.
	 */
	attach(inputElement) {
		if (!inputElement || this.isAttached) {
			return;
		}

		this._inputElement = inputElement;

		this._handleKeyDown = (e) => {
			if (this._ignoredKeys.has(e.key)) {
				return;
			}

			const now = performance.now();
			this.keyDownTimes[e.key] = now;

			if (this.startTime === null) {
				this.startTime = now;
			}

			this.events.push({ type: 'down', key: e.key, t: now });
		};

		this._handleKeyUp = (e) => {
			if (this._ignoredKeys.has(e.key)) {
				return;
			}

			const now = performance.now();
			this.events.push({ type: 'up', key: e.key, t: now });
		};

		inputElement.addEventListener('keydown', this._handleKeyDown);
		inputElement.addEventListener('keyup', this._handleKeyUp);
		this.isAttached = true;
	}

	/**
	 * Computes keystroke features from captured events.
	 * @returns {object|null} Feature object or null when data is insufficient.
	 */
	getFeatures() {
		const downEvents = this.events.filter((event) => event.type === 'down');
		if (downEvents.length < 3) {
			return null;
		}

		const upEvents = this.events.filter((event) => event.type === 'up');
		const pendingDowns = {};
		const dwell = [];

		for (let i = 0; i < this.events.length; i += 1) {
			const event = this.events[i];
			if (event.type === 'down') {
				if (!pendingDowns[event.key]) {
					pendingDowns[event.key] = [];
				}
				pendingDowns[event.key].push(event.t);
			} else if (event.type === 'up' && pendingDowns[event.key] && pendingDowns[event.key].length > 0) {
				const downTime = pendingDowns[event.key].shift();
				dwell.push(event.t - downTime);
			}
		}

		const flight = [];
		const comparableFlightCount = Math.min(upEvents.length, downEvents.length - 1);
		for (let i = 0; i < comparableFlightCount; i += 1) {
			flight.push(downEvents[i + 1].t - upEvents[i].t);
		}

		const digraph = [];
		for (let i = 0; i < downEvents.length - 1; i += 1) {
			digraph.push(downEvents[i + 1].t - downEvents[i].t);
		}

		const firstTime = this.startTime !== null ? this.startTime : downEvents[0].t;
		const lastTime = this.events.length > 0 ? this.events[this.events.length - 1].t : firstTime;
		const durationSeconds = Math.max((lastTime - firstTime) / 1000, 0);
		const typingSpeed = durationSeconds > 0 ? downEvents.length / durationSeconds : 0;

		const mean = (arr) => (arr.length ? arr.reduce((sum, v) => sum + v, 0) / arr.length : 0);
		const std = (arr) => {
			if (!arr.length) {
				return 0;
			}
			const m = mean(arr);
			const variance = arr.reduce((sum, v) => sum + (v - m) * (v - m), 0) / arr.length;
			return Math.sqrt(variance);
		};

		return {
			dwell,
			flight,
			digraph,
			typing_speed: typingSpeed,
			mean_dwell: mean(dwell),
			std_dwell: std(dwell),
			mean_flight: mean(flight),
			mean_digraph: mean(digraph)
		};
	}

	/**
	 * Resets all captured keystroke state without removing listeners.
	 */
	reset() {
		this.events = [];
		this.keyDownTimes = {};
		this.startTime = null;
	}

	/**
	 * Detaches key listeners from an input element.
	 * @param {HTMLElement} inputElement - The input element to stop monitoring.
	 */
	detach(inputElement) {
		const target = inputElement || this._inputElement;
		if (!target) {
			this.isAttached = false;
			return;
		}

		if (this._handleKeyDown) {
			target.removeEventListener('keydown', this._handleKeyDown);
		}
		if (this._handleKeyUp) {
			target.removeEventListener('keyup', this._handleKeyUp);
		}

		this._inputElement = null;
		this._handleKeyDown = null;
		this._handleKeyUp = null;
		this.isAttached = false;
	}

	/**
	 * Returns a debug summary of the most recent capture.
	 * @returns {string} Human-readable capture summary.
	 */
	getSummary() {
		const features = this.getFeatures();
		if (!features) {
			const keyCount = this.events.filter((event) => event.type === 'down').length;
			return `Capture summary: keys=${keyCount}, mean dwell=0.00 ms, mean flight=0.00 ms`;
		}

		const keyCount = this.events.filter((event) => event.type === 'down').length;
		return `Capture summary: keys=${keyCount}, mean dwell=${features.mean_dwell.toFixed(2)} ms, mean flight=${features.mean_flight.toFixed(2)} ms`;
	}
}

if (typeof module !== 'undefined') module.exports = KeystrokeCollector;
