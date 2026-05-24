/* ============================================
   Renia AI — WebSocket Client
   ============================================ */

class WebSocketClient {
  constructor() {
    this.socket = null;
    this.callbacks = {
      message: [],
      callUpdate: [],
      appointmentUpdate: [],
      statusChange: []
    };
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
    this.clinicId = null;
    this.isConnected = false;
    this._heartbeatTimer = null;
    this._intentionalClose = false;
  }

  /**
   * Connect to the WebSocket server
   */
  connect(clinicId) {
    this.clinicId = clinicId;
    this._intentionalClose = false;

    const token = localStorage.getItem('renia_token');
    if (!token || token.startsWith('demo_token_')) {
      this.updateStatus(false);
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/${clinicId}?token=${token}`;

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this.updateStatus(true);
        this.callbacks.statusChange.forEach(cb => cb(true));
        this._startHeartbeat();
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (e) {
          console.warn('Failed to parse WebSocket message:', e);
        }
      };

      this.socket.onclose = (event) => {
        this._stopHeartbeat();
        this.isConnected = false;
        this.updateStatus(false);
        this.callbacks.statusChange.forEach(cb => cb(false));

        if (!this._intentionalClose && event.code !== 1000) {
          this.reconnect();
        }
      };

      this.socket.onerror = (error) => {
        this._stopHeartbeat();
        this.isConnected = false;
        this.updateStatus(false);
        if (!this._intentionalClose) {
          this.reconnect();
        }
      };
    } catch (error) {
      console.warn('WebSocket connection failed:', error);
      this.updateStatus(false);
    }
  }

  /**
   * Handle incoming messages and route to callbacks
   */
  handleMessage(data) {
    // Notify all general message callbacks
    this.callbacks.message.forEach(cb => cb(data));

    // Route by message type
    switch (data.type) {
      case 'call_started':
      case 'call_ended':
      case 'call_update':
        this.callbacks.callUpdate.forEach(cb => cb(data));
        break;

      case 'appointment_created':
      case 'appointment_updated':
      case 'appointment_cancelled':
        this.callbacks.appointmentUpdate.forEach(cb => cb(data));
        break;

      case 'ping':
        this.send({ type: 'pong' });
        break;
    }
  }

  /**
   * Register a callback for all messages
   */
  onMessage(callback) {
    this.callbacks.message.push(callback);
  }

  /**
   * Register a callback for call updates
   */
  onCallUpdate(callback) {
    this.callbacks.callUpdate.push(callback);
  }

  /**
   * Register a callback for appointment updates
   */
  onAppointmentUpdate(callback) {
    this.callbacks.appointmentUpdate.push(callback);
  }

  /**
   * Register a callback for connection status changes
   */
  onStatusChange(callback) {
    this.callbacks.statusChange.push(callback);
  }

  /**
   * Send data through the WebSocket
   */
  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }

  _startHeartbeat() {
    this._stopHeartbeat();
    this._heartbeatTimer = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  _stopHeartbeat() {
    if (this._heartbeatTimer) {
      clearInterval(this._heartbeatTimer);
      this._heartbeatTimer = null;
    }
  }

  /**
   * Auto-reconnect with exponential backoff
   */
  reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.reconnectAttempts = 0;
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);

    setTimeout(() => {
      if (this.clinicId) {
        this.connect(this.clinicId);
      }
    }, delay);
  }

  /**
   * Update the UI connection indicator
   */
  updateStatus(connected) {
    const indicator = document.querySelector('.live-indicator');
    if (!indicator) return;

    if (connected) {
      indicator.style.display = 'flex';
      indicator.textContent = '';
      indicator.innerHTML = '<span></span> Live';
      indicator.style.color = '#10b981';
    } else {
      indicator.style.color = '#ef4444';
      indicator.textContent = '';
      indicator.innerHTML = '<span></span> Disconnected';
    }
  }

  /**
   * Disconnect the WebSocket
   */
  disconnect() {
    this._intentionalClose = true;
    this._stopHeartbeat();
    if (this.socket) {
      this.socket.close(1000, 'User disconnected');
      this.socket = null;
    }
  }
}

// Global instance
const wsClient = new WebSocketClient();
