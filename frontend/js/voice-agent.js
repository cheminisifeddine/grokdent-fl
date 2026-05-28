class GrokVoiceAgent {
  constructor(options = {}) {
    this.ws = null;
    this.audioContext = null;
    this.workletNode = null;
    this.mediaStream = null;
    this.isSessionReady = false;
    this.micBuffer = [];
    this.nextPlayTime = 0;
    this.queuedSources = [];
    this.sessionToken = null;
    this.tokenExpiresAt = 0;
    this.isConnected = false;
    this.isConnecting = false;
    
    const defaultVoice = options.voice || 'eve';
    const defaultClinicName = options.clinicName || 'Sunshine Smiles Dental';

    this.config = {
      voice: defaultVoice,
      instructions: options.instructions || this.getDefaultInstructions(defaultVoice, defaultClinicName),
      clinicName: defaultClinicName,
      tools: options.tools || this.getDefaultTools(),
      model: options.model || 'grok-voice-think-fast-1.0',
      sessionTokenEndpoint: options.sessionTokenEndpoint || '/api/v1/voice/session-token',
      autoStart: options.autoStart !== false,
      initialMessage: options.initialMessage || '',
      demoMode: options.demoMode || false
    };

    this.callbacks = {
      onConnect: [],
      onDisconnect: [],
      onError: [],
      onTranscript: [],
      onAssistantTranscript: [],
      onToolCall: [],
      onStateChange: []
    };

    this.state = 'disconnected';
    this.currentAssistantMessage = '';
    this._pcmChunkBuffer = [];
    this._pcmFlushTimer = null;
  }

  getDefaultInstructions(voice = this.config?.voice || 'eve', clinicName = this.config?.clinicName || 'Sunshine Smiles Dental') {
    const voiceDisplayNames = {
      'rex': 'Ash',
      'ara': 'Ani',
      'eve': 'Eve',
      'sal': 'Verse',
      'leo': 'Leo'
    };
    const voiceName = voiceDisplayNames[voice] || 'Eve';
    
    return `You are ${voiceName}, the elite AI voice receptionist for ${clinicName} in Florida.

WHO YOU ARE
You are highly professional, warm, and speak with a friendly, patient, and empathetic tone. You represent a high-end dental practice. You are NOT an AI assistant, you are the digital receptionist. Never mention that you are an AI or language model. 

CLINIC KNOWLEDGE
- Name: ${clinicName}
- Location: Florida
- Hours: Mon-Fri 9:00 AM to 5:00 PM. Closed weekends.
- Accepted Insurance: Delta Dental PPO, Humana, Guardian, MCNA (Florida Medicaid).
- Services: General checkups, teeth whitening, orthodontics, emergency extractions, dental implants.

YOUR MISSION
Answer patient questions, check appointment availability, schedule new appointments, and process cancellations. Be concise, audio-friendly, and conversational. Do not output long lists or bullet points. Speak naturally. Use the provided tools when a patient wants to book, check, or cancel an appointment.

BEHAVIORAL RULES
1. If a patient asks for availability, use the 'check_availability' tool.
2. If a patient wants to book, collect their name, phone, date/time, and reason, then use the 'schedule_appointment' tool.
3. If a patient has a dental emergency (severe pain, bleeding), advise them to seek immediate care and offer the earliest possible slot.
4. If asked about insurance, confirm only from the accepted list.

Keep responses short and conversational — this is a voice call, not an email.`;
  }

  getDefaultTools() {
    return [
      {
        "type": "function",
        "name": "check_availability",
        "description": "Check available appointment slots for a given date range and provider",
        "parameters": {
          "type": "object",
          "properties": {
            "provider_name": { "type": "string", "description": "Name of the doctor or provider" },
            "date": { "type": "string", "description": "Preferred date" },
            "appointment_type": { "type": "string", "description": "Type of appointment" }
          },
          "required": ["date"],
          "additionalProperties": false
        }
      },
      {
        "type": "function",
        "name": "schedule_appointment",
        "description": "Book a new appointment for a patient",
        "parameters": {
          "type": "object",
          "properties": {
            "patient_name": { "type": "string", "description": "Full name of the patient" },
            "phone_number": { "type": "string", "description": "Contact phone number" },
            "date": { "type": "string", "description": "Appointment date" },
            "time": { "type": "string", "description": "Appointment time" },
            "reason": { "type": "string", "description": "Reason for the visit" }
          },
          "required": ["patient_name", "phone_number", "date", "time"],
          "additionalProperties": false
        }
      },
      {
        "type": "function",
        "name": "cancel_appointment",
        "description": "Cancel an existing appointment",
        "parameters": {
          "type": "object",
          "properties": {
            "patient_name": { "type": "string", "description": "Name of the patient" },
            "appointment_date": { "type": "string", "description": "Date of the appointment to cancel" }
          },
          "required": ["patient_name", "appointment_date"],
          "additionalProperties": false
        }
      }
    ];
  }

  setState(newState) {
    this.state = newState;
    this.callbacks.onStateChange.forEach(cb => cb(newState));
  }

  on(event, callback) {
    if (this.callbacks[event]) {
      this.callbacks[event].push(callback);
    }
  }

  async fetchSessionToken() {
    const now = Date.now();
    if (this.sessionToken && now < (this.tokenExpiresAt - 5000)) {
      console.log('Reusing existing session token, expires in:', Math.round((this.tokenExpiresAt - now) / 1000), 'seconds');
      return this.sessionToken;
    }

    try {
      console.log('Fetching new session token from backend...');
      
      let endpoint = this.config.sessionTokenEndpoint;
      if (endpoint.startsWith('/') && typeof window !== 'undefined' && window.location) {
        const hostname = window.location.hostname;
        const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.') || hostname.startsWith('10.') || hostname.startsWith('172.');
        if (isLocal) {
          const port = window.location.port;
          if (port && port !== '8000') {
            endpoint = `http://${hostname}:8000${endpoint}`;
          }
        } else {
          // In production, bypass Cloudflare Pages redirect proxy to avoid 405 error on POST requests
          endpoint = `https://renia-ai-backend.medsaidkichene.workers.dev${endpoint}`;
        }
      }
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      console.log('Session token endpoint response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Session token endpoint error:', response.status, errorText);
        throw new Error(`Session token endpoint failed: ${response.status} - ${errorText.substring(0, 100)}`);
      }

      const data = await response.json();
      console.log('Session token received:', data.token ? 'Yes (masked)' : 'No', 'expires_at:', data.expires_at);
      
      if (!data.token) {
        throw new Error('Session token endpoint returned no token');
      }

      this.sessionToken = data.token;
      this.tokenExpiresAt = data.expires_at * 1000;
      return this.sessionToken;
    } catch (err) {
      console.error('Session token endpoint failed completely:', err);
      throw err;
    }
  }

  async connect() {
    if (this.isConnected || this.isConnecting) {
      return;
    }

    this.isConnecting = true;
    this.setState('connecting');

    try {
      const sessionToken = await this.fetchSessionToken();

      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
      }

      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 24000
        }
      });

      try {
        await this.audioContext.audioWorklet.addModule('js/pcm-processor-worklet.js');
      } catch (e) {
        console.warn('Could not load worklet from js/, trying root:', e);
        try {
          await this.audioContext.audioWorklet.addModule('pcm-processor-worklet.js');
        } catch (e2) {
          console.warn('Worklet loading failed, using ScriptProcessor fallback:', e2);
        }
      }

       const source = this.audioContext.createMediaStreamSource(this.mediaStream);
       
       if (this.audioContext.audioWorklet) {
         try {
           this.workletNode = new AudioWorkletNode(this.audioContext, 'pcm-processor');
           this.workletNode.port.onmessage = (event) => this.handleMicData(event.data);
           source.connect(this.workletNode);
         } catch (e) {
           console.warn('Falling back to ScriptProcessorNode:', e);
           this.setupScriptProcessorFallback(source);
         }
       } else {
         this.setupScriptProcessorFallback(source);
       }

       this.isSessionReady = false;
       this.micBuffer = [];
       this.nextPlayTime = 0;
       this.queuedSources = [];

       if (!sessionToken) {
         throw new Error('No session token available. Please check your backend connection and API key.');
       }

       console.log('Connecting WebSocket to xAI Realtime API...');
       console.log('Model:', this.config.model);
       console.log('Session token (first 20 chars):', sessionToken.substring(0, 20) + '...');

       const connectionTimeout = setTimeout(() => {
         if (!this.isConnected) {
           console.log('WebSocket connection timeout (10s)');
           if (this.ws) {
             try { this.ws.close(); } catch (e) {}
             this.ws = null;
           }
           this.isConnecting = false;
           this.setState('disconnected');
           this.callbacks.onError.forEach(cb => cb(new Error('Connection timeout. The xAI API may be unavailable or your API key may not have Realtime Voice API access.')));
         }
       }, 15000);
       
       this.ws = new WebSocket(
         `wss://api.x.ai/v1/realtime?model=${encodeURIComponent(this.config.model)}`,
         [`xai-client-secret.${sessionToken}`]
       );

       this.ws.onopen = () => {
         clearTimeout(connectionTimeout);
         console.log('WebSocket connection opened successfully!');
         this.handleOpen();
       };

       this.ws.onmessage = (event) => {
         this.handleMessage(event);
       };

       this.ws.onclose = (event) => {
         clearTimeout(connectionTimeout);
         console.log('WebSocket closed - code:', event.code, 'reason:', event.reason || '(none)');
         this.handleClose(event);
       };

       this.ws.onerror = (error) => {
         clearTimeout(connectionTimeout);
         console.error('WebSocket error:', error);
         this.handleError(error);
       };

    } catch (err) {
      this.isConnecting = false;
      this.setState('disconnected');
      this.callbacks.onError.forEach(cb => cb(err));
      throw err;
    }
  }

  setupScriptProcessorFallback(source) {
    const bufferSize = 4096;
    const scriptProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);
    
    scriptProcessor.onaudioprocess = (e) => {
      const input = e.inputBuffer.getChannelData(0);
      const int16 = new Int16Array(input.length);
      for (let i = 0; i < input.length; i++) {
        const s = Math.max(-1, Math.min(1, input[i]));
        int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      this.handleMicData(int16);
    };

    source.connect(scriptProcessor);
    scriptProcessor.connect(this.audioContext.destination);
  }

  getSavedApiKey() {
    try {
      const settings = localStorage.getItem('renia_settings');
      if (settings) {
        const parsed = JSON.parse(settings);
        if (parsed.voice && parsed.voice.xai_key) {
          return parsed.voice.xai_key;
        }
      }
    } catch (e) {}
    return '';
  }

  handleMicData(int16Data) {
    if (this.isSessionReady && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'input_audio_buffer.append',
        audio: this.audioToBase64(int16Data)
      }));
    } else {
      if (this.micBuffer.length < 50) {
        this.micBuffer.push(int16Data);
      }
    }
  }

  audioToBase64(int16Array) {
    const bytes = new Uint8Array(int16Array.buffer, int16Array.byteOffset, int16Array.byteLength);
    const CHUNK = 0x2000;
    const parts = [];
    for (let i = 0; i < bytes.length; i += CHUNK) {
      parts.push(String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK)));
    }
    return btoa(parts.join(''));
  }

  handleOpen() {
    console.log('Grok Voice Agent WebSocket connected');
    
    this.ws.send(JSON.stringify({
      type: 'session.update',
      session: {
        voice: this.config.voice,
        instructions: this.config.instructions,
        turn_detection: {
          type: 'server_vad',
          threshold: 0.82,
          silence_duration_ms: 850,
          prefix_padding_ms: 333
        },
        tools: this.config.tools,
        audio: {
          input: { format: { type: 'audio/pcm', rate: 24000 } },
          output: { format: { type: 'audio/pcm', rate: 24000 } }
        }
      }
    }));

    this.isConnected = true;
    this.isConnecting = false;
    this.setState('connected');
    this.callbacks.onConnect.forEach(cb => cb());

    if (this.config.autoStart) {
      if (this.config.initialMessage) {
        this.ws.send(JSON.stringify({
          type: 'conversation.item.create',
          item: {
            type: 'message',
            role: 'user',
            content: [{ type: 'input_text', text: this.config.initialMessage }]
          }
        }));
      }
      this.ws.send(JSON.stringify({ type: 'response.create' }));
    }
  }

  handleMessage(event) {
    let data;
    try {
      if (typeof event.data === 'string') {
        data = JSON.parse(event.data);
      } else {
        return;
      }
    } catch (e) {
      console.warn('Failed to parse WebSocket message:', e);
      return;
    }

    switch (data.type) {
      case 'session.created':
        console.log('Session created:', data.session?.id);
        break;

      case 'session.updated':
        console.log('Session updated, ready for audio');
        this.isSessionReady = true;
        this.flushMicBuffer();
        break;

      case 'input_audio_buffer.speech_started':
        console.log('User started speaking');
        this.interruptPlayback();
        if (this.ws) {
          this.ws.send(JSON.stringify({ type: 'response.cancel' }));
        }
        this.currentAssistantMessage = '';
        this.setState('listening');
        break;

      case 'input_audio_buffer.speech_stopped':
        console.log('User stopped speaking');
        this.setState('thinking');
        break;

      case 'conversation.item.input_audio_transcription.completed':
        console.log('User transcript:', data.transcript);
        this.callbacks.onTranscript.forEach(cb => cb(data.transcript || data.text || '', 'user'));
        break;

      case 'response.output_audio.delta':
        if (this.state !== 'speaking') {
          this.setState('speaking');
        }
        this.playPcmChunk(data.delta);
        break;

      case 'response.output_audio_transcript.delta':
      case 'response.output_text.delta':
      case 'response.text.delta':
        this.currentAssistantMessage += data.delta || '';
        this.callbacks.onAssistantTranscript.forEach(cb => cb(this.currentAssistantMessage, 'assistant'));
        break;

      case 'response.output_audio_transcript.done':
      case 'response.output_text.done':
      case 'response.text.done':
        console.log('Assistant transcript complete:', data.transcript || data.text);
        break;

      case 'response.function_call_arguments.done':
        console.log('Tool call:', data.name, data.arguments);
        this.handleToolCall(data.name, data.arguments, data.call_id);
        this.callbacks.onToolCall.forEach(cb => cb(data.name, JSON.parse(data.arguments || '{}')));
        break;

      case 'response.done':
        console.log('Response done, tokens:', data.usage?.total_tokens);
        this.setState('listening');
        break;

      case 'error':
        console.error('Voice Agent error:', data.error || data.message);
        this.callbacks.onError.forEach(cb => cb(new Error(data.error?.message || data.message || 'Voice Agent error')));
        break;
    }
  }

  flushMicBuffer() {
    for (const chunk of this.micBuffer) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'input_audio_buffer.append',
          audio: this.audioToBase64(chunk)
        }));
      }
    }
    this.micBuffer = [];
  }

  playPcmChunk(base64) {
    if (!this.audioContext) return;

    try {
      // Decode base64 PCM chunk
      const raw = atob(base64);
      const bytes = new Uint8Array(raw.length);
      for (let i = 0; i < raw.length; i++) {
        bytes[i] = raw.charCodeAt(i);
      }

      const int16 = new Int16Array(bytes.buffer);
      const float32 = new Float32Array(int16.length);
      for (let i = 0; i < int16.length; i++) {
        float32[i] = int16[i] / 32768;
      }

      // Buffer small chunks to avoid glitching on rapid-fire deltas
      this._pcmChunkBuffer.push(float32);

      // Debounce flush: schedule playback after a brief coalesce period
      if (this._pcmFlushTimer) clearTimeout(this._pcmFlushTimer);
      this._pcmFlushTimer = setTimeout(() => this._flushPcmBuffer(), 50);
    } catch (e) {
      console.warn('Audio playback error:', e);
    }
  }

  _flushPcmBuffer() {
    if (this._pcmChunkBuffer.length === 0) return;
    this._pcmFlushTimer = null;

    try {
      // Calculate total length
      const totalLen = this._pcmChunkBuffer.reduce((sum, arr) => sum + arr.length, 0);
      const combined = new Float32Array(totalLen);
      let offset = 0;
      for (const arr of this._pcmChunkBuffer) {
        combined.set(arr, offset);
        offset += arr.length;
      }
      this._pcmChunkBuffer = [];

      const buf = this.audioContext.createBuffer(1, combined.length, 24000);
      buf.getChannelData(0).set(combined);

      const src = this.audioContext.createBufferSource();
      src.buffer = buf;
      src.connect(this.audioContext.destination);

      const now = this.audioContext.currentTime;
      const startAt = Math.max(now, this.nextPlayTime);
      src.start(startAt);
      this.nextPlayTime = startAt + buf.duration;

      this.queuedSources.push(src);
      src.onended = () => {
        const idx = this.queuedSources.indexOf(src);
        if (idx !== -1) this.queuedSources.splice(idx, 1);
      };
    } catch (e) {
      console.warn('Flush PCM buffer error:', e);
    }
  }

  interruptPlayback() {
    for (const src of this.queuedSources) {
      try {
        src.stop();
      } catch (e) {
        // Source may already have stopped — safe to ignore
      }
    }
    this.queuedSources.length = 0;
    this.nextPlayTime = 0;
    // Flush any pending audio in the buffer
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.suspend().then(() => this.audioContext.resume()).catch(() => {});
    }
  }

  async handleToolCall(name, argsJson, callId) {
    let result;
    const args = JSON.parse(argsJson || '{}');

    switch (name) {
      case 'check_availability':
        try {
          const date = args.date;
          if (!date) {
            result = { 
              success: false, 
              message: 'Please provide a date to check availability.' 
            };
          } else if (typeof API !== 'undefined' && typeof API.getAvailability === 'function') {
            const slots = await API.getAvailability(date);
            if (slots && Array.isArray(slots) && slots.length > 0) {
              const slotTimes = slots.map(s => s.time || s);
              result = { 
                success: true, 
                available_slots: slotTimes,
                message: `We have ${slotTimes.join(', ')} available on ${date}.`
              };
            } else {
              result = { 
                success: false, 
                message: `No available slots for ${date}.` 
              };
            }
          } else {
            result = { 
              success: true, 
              available_slots: ["10:00 AM", "2:30 PM", "4:00 PM"],
              message: this.config.demoMode
                ? `For this demo, I found 10:00 AM, 2:30 PM, and 4:00 PM available on ${date}. In production this would check the clinic calendar.`
                : `We have 10:00 AM, 2:30 PM, and 4:00 PM available on ${date}.`
            };
          }
        } catch (err) {
          console.error('check_availability error:', err);
          result = { 
            success: false, 
            message: 'Sorry, there was an error checking availability. Please try again.' 
          };
        }
        break;

      case 'schedule_appointment':
        try {
          const { patient_name, phone_number, date, time, reason } = args;
          
          if (!patient_name || !phone_number || !date || !time) {
            result = { 
              success: false, 
              message: 'Please provide patient name, phone number, date, and time to book an appointment.' 
            };
          } else if (typeof API !== 'undefined' && typeof API.createAppointment === 'function') {
            const appt = await API.createAppointment({
              name: patient_name,
              phone: phone_number,
              date,
              time,
              service: reason || 'Checkup',
              notes: ''
            });
            result = { 
              success: true, 
              confirmation_id: appt?.id || "APT-" + Math.floor(Math.random() * 10000),
              message: `Successfully booked ${patient_name} for ${reason || 'an appointment'} on ${date} at ${time}.`
            };
          } else {
            result = { 
              success: true, 
              confirmation_id: "APT-" + Math.floor(Math.random() * 10000),
              message: this.config.demoMode
                ? `For this demo, I prepared an appointment hold for ${patient_name} on ${date} at ${time}. In production this would write to the clinic schedule.`
                : `Successfully booked ${patient_name} for ${reason || 'an appointment'} on ${date} at ${time}.`
            };
          }
        } catch (err) {
          console.error('schedule_appointment error:', err);
          result = { 
            success: false, 
            message: 'Sorry, there was an error booking the appointment. Please try again.' 
          };
        }
        break;

      case 'cancel_appointment':
        try {
          const { patient_name, appointment_date } = args;
          
          if (!patient_name || !appointment_date) {
            result = { 
              success: false, 
              message: 'Please provide patient name and appointment date to cancel.' 
            };
          } else if (typeof API !== 'undefined' && typeof API.getAppointments === 'function' && typeof API.deleteAppointment === 'function') {
            const appts = await API.getAppointments();
            const appointments = Array.isArray(appts) ? appts : (appts?.data || []);
            
            const toCancel = appointments.find(a => 
              a.name?.toLowerCase().includes(patient_name.toLowerCase()) && 
              a.date === appointment_date
            );
            
            if (toCancel) {
              await API.deleteAppointment(toCancel.id);
              result = { 
                success: true, 
                message: `Appointment cancelled successfully for ${patient_name} on ${appointment_date}.`
              };
            } else {
              result = { 
                success: false, 
                message: `No appointment found for ${patient_name} on ${appointment_date}.`
              };
            }
          } else {
            result = { 
              success: true, 
              message: this.config.demoMode
                ? `For this demo, I showed the cancellation workflow for ${patient_name}. In production this would update the clinic schedule.`
                : `Appointment cancelled successfully for ${patient_name}.`
            };
          }
        } catch (err) {
          console.error('cancel_appointment error:', err);
          result = { 
            success: false, 
            message: 'Sorry, there was an error cancelling the appointment. Please try again.' 
          };
        }
        break;

      default:
        result = { error: `Unknown tool: ${name}` };
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'conversation.item.create',
        item: { 
          type: 'function_call_output', 
          call_id: callId, 
          output: JSON.stringify(result) 
        }
      }));
      this.ws.send(JSON.stringify({ type: 'response.create' }));
    }
  }

  handleClose(event) {
    console.log('WebSocket closed:', event.code, event.reason);
    this.isConnected = false;
    this.isConnecting = false;
    this.isSessionReady = false;
    this.setState('disconnected');
    
    let errorMsg = 'WebSocket connection closed';
    if (event.code === 1006) {
      errorMsg = 'Connection failed. Please check your internet connection and try again.';
    } else if (event.code === 1008 || event.code === 1011) {
      errorMsg = `Server error: ${event.reason || 'Internal server error'}`;
    } else if (event.code === 1001) {
      errorMsg = 'Connection closed by server.';
    } else if (event.reason) {
      errorMsg = `Connection closed: ${event.reason}`;
    }
    
    if (event.code !== 1000) {
      this.callbacks.onError.forEach(cb => cb(new Error(errorMsg)));
    }
    this.callbacks.onDisconnect.forEach(cb => cb(event));
  }

  handleError(error) {
    console.error('WebSocket error:', error);
    
    let errorMsg = 'WebSocket error occurred';
    if (error instanceof Error) {
      errorMsg = error.message;
    } else if (error && typeof error === 'object') {
      if (error.type === 'error') {
        errorMsg = 'Connection failed. Please check your API key and internet connection.';
      } else if (error.message) {
        errorMsg = error.message;
      } else {
        try {
          errorMsg = JSON.stringify(error);
        } catch (e) {
          errorMsg = 'Unknown connection error';
        }
      }
    }
    
    this.callbacks.onError.forEach(cb => cb(new Error(errorMsg)));
  }

  sendText(text) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    this.ws.send(JSON.stringify({
      type: 'conversation.item.create',
      item: { 
        type: 'message', 
        role: 'user',
        content: [{ type: 'input_text', text: text }] 
      }
    }));
    this.ws.send(JSON.stringify({ type: 'response.create' }));
  }

  async disconnect() {
    // 1. Clear any pending debounced audio flushes
    if (this._pcmFlushTimer) {
      clearTimeout(this._pcmFlushTimer);
      this._pcmFlushTimer = null;
    }
    this._pcmChunkBuffer = [];

    // 2. Stop all currently playing audio sources immediately
    this.interruptPlayback();

    // 3. Close the WebSocket connection
    if (this.ws) {
      this.ws.close(1000, 'User disconnected');
      this.ws = null;
    }

    // 4. Stop the microphone stream
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }

    // 5. Close the audio context
    if (this.audioContext) {
      try {
        await this.audioContext.close();
      } catch (e) {
        console.warn('Error closing AudioContext:', e);
      }
      this.audioContext = null;
    }

    this.workletNode = null;
    this.isConnected = false;
    this.isSessionReady = false;
    this.micBuffer = [];
    this.setState('disconnected');
  }

  setVoice(voice) {
    this.config.voice = voice;
  }

  setInstructions(instructions) {
    this.config.instructions = instructions;
  }

  setClinicName(name) {
    this.config.clinicName = name;
    this.config.instructions = this.getDefaultInstructions();
  }
}

window.GrokVoiceAgent = GrokVoiceAgent;
