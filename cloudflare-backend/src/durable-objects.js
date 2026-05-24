export class RealtimeDashboardDO {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.sessions = new Map();
    this.heartbeatInterval = 30000;
  }

  async fetch(request) {
    const url = new URL(request.url);

    // Handle broadcast POST requests from server-side endpoints
    if (url.pathname === '/broadcast' && request.method === 'POST') {
      const body = await request.json();
      const clinicId = body.clinic_id || url.searchParams.get('clinic_id');
      if (clinicId) {
        await this.broadcast(clinicId, body);
      }
      return new Response('OK');
    }

    const clinicId = url.searchParams.get('clinic_id');

    if (request.headers.get('Upgrade') !== 'websocket') {
      return new Response('Expected WebSocket upgrade', { status: 426 });
    }

    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);

    this.sessions.set(server, {
      clinicId,
      connectedAt: Date.now(),
    });

    server.accept();

    server.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'ping') {
          server.send(JSON.stringify({ type: 'pong' }));
        }
      } catch (e) {
        // ignore malformed messages
      }
    });

    server.addEventListener('close', () => {
      this.sessions.delete(server);
    });

    server.addEventListener('error', () => {
      this.sessions.delete(server);
    });

    return new Response(null, { status: 101, webSocket: client });
  }

  async broadcast(clinicId, message) {
    const payload = JSON.stringify(message);
    const disconnected = [];

    for (const [ws, session] of this.sessions) {
      if (session.clinicId === clinicId) {
        try {
          ws.send(payload);
        } catch (e) {
          disconnected.push(ws);
        }
      }
    }

    for (const ws of disconnected) {
      this.sessions.delete(ws);
    }
  }

  async alarm() {
    for (const [ws, session] of this.sessions) {
      try {
        ws.send(JSON.stringify({ type: 'heartbeat', timestamp: Date.now() }));
      } catch (e) {
        this.sessions.delete(ws);
      }
    }
    await this.state.storage.setAlarm(Date.now() + this.heartbeatInterval);
  }
}
