import WebSocket from 'ws';
import dotenv from 'dotenv';

// Load environment variables if present
dotenv.config();

// Export your API key in the terminal or .env file before running
// export XAI_API_KEY="xai-..."
const API_KEY = process.env.XAI_API_KEY || 'xai-YOUR_API_KEY_HERE';

if (!API_KEY || API_KEY === 'xai-YOUR_API_KEY_HERE') {
  console.error("❌ ERROR: Please set your XAI_API_KEY environment variable.");
  process.exit(1);
}

console.log("🦷 Initializing Renia AI Dentist Voice Agent (Grok Realtime API)...");

// Use the fast Grok Voice model
const ws = new WebSocket('wss://api.x.ai/v1/realtime?model=grok-voice-latest', {
  headers: { Authorization: `Bearer ${API_KEY}` },
});

ws.on('open', () => {
  console.log("✅ Connected to Grok Realtime Voice API.");
  
  // Configure the Agent for a Standard Dentist
  ws.send(JSON.stringify({
    type: 'session.update',
    session: {
      voice: 'eve', // Fast, clear, professional voice
      instructions: `You are Ash, the elite AI voice receptionist for Sunshine Smiles Dental in Florida. 

---
WHO YOU ARE
You are highly professional, warm, and speak with a friendly, patient, and empathetic tone. You represent a high-end dental practice. You are NOT an AI assistant, you are the digital receptionist. Never mention that you are an AI or language model. 

---
CLINIC KNOWLEDGE
- Name: Sunshine Smiles Dental
- Location: Orlando, Florida
- Hours: Mon-Fri 9:00 AM to 5:00 PM. Closed weekends.
- Accepted Insurance: Delta Dental PPO, Humana, Guardian, MCNA (Florida Medicaid).
- Services: General checkups, teeth whitening, orthodontics, emergency extractions, dental implants.

---
YOUR MISSION
Answer patient questions, check appointment availability, schedule new appointments, and process cancellations. Be concise, audio-friendly, and conversational. Do not output long lists or bullet points. Speak naturally. Use the provided tools when a patient wants to book, check, or cancel an appointment.

---
BEHAVIORAL RULES
1. If a patient asks for availability, use the 'check_availability' tool.
2. If a patient wants to book, collect their name, phone, date/time, and reason, then use the 'schedule_appointment' tool.
3. If a patient has a dental emergency (severe pain, bleeding), advise them to seek immediate care and offer the earliest possible slot.
4. If asked about insurance, confirm only from the accepted list.`,
      turn_detection: { type: 'server_vad' },
      tools: [
        {
          "type": "function",
          "name": "check_availability",
          "description": "Check available appointment slots for a given date range and provider",
          "parameters": {
            "type": "object",
            "properties": {
              "provider_name": { "type": "string", "description": "Name of the doctor or provider (e.g. Dr. Smith)" },
              "date": { "type": "string", "description": "Preferred date (e.g., 'next Tuesday', 'March 15th')" },
              "appointment_type": { "type": "string", "description": "Type of appointment (e.g., 'checkup', 'consultation')" }
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
      ],
      input_audio_transcription: { model: 'grok-2-audio' },
      audio: {
        input:  { format: { type: 'audio/pcm', rate: 24000 } },
        output: { format: { type: 'audio/pcm', rate: 24000 } },
      },
    },
  }));
  
  // Kick off the conversation
  console.log("🎙️ Initiating call simulation... Sending greeting request.");
  ws.send(JSON.stringify({
    type: 'conversation.item.create',
    item: { 
      type: 'message', 
      role: 'user',
      content: [{ type: 'input_text', text: 'Hello, I am calling Sunshine Smiles Dental.' }] 
    },
  }));
  ws.send(JSON.stringify({ type: 'response.create' }));
});

ws.on('message', async (raw) => {
  const event = JSON.parse(raw.toString());

  switch (event.type) {
    case 'session.created':
      console.log('🔗 Session Created:', event.session.id);
      break;

    case 'input_audio_buffer.speech_started':
      // User started talking — interrupt playback
      console.log(">> [User speaking... interrupting AI]");
      ws.send(JSON.stringify({ type: 'response.cancel' }));
      break;

    case 'response.output_audio.delta':
      // Base64-encoded PCM audio chunk → decode and play
      // const pcm = Buffer.from(event.delta, 'base64');
      // In a real voice app, you would pipe this to the speaker (e.g., using 'speaker' package)
      break;

    case 'response.output_audio_transcript.delta':
      // Print the transcript of what the AI is speaking
      process.stdout.write(event.delta);
      break;

    case 'response.function_call_arguments.done': {
      console.log(`\n\n⚙️ [TOOL CALL DETECTED]: ${event.name}`);
      console.log(`📋 Arguments:`, event.arguments);
      
      // Custom tool call completed — execute handler and send result
      const result = await handleToolCall(event.name, event.arguments);
      
      console.log(`📤 [TOOL RESULT]:`, result);
      
      ws.send(JSON.stringify({
        type: 'conversation.item.create',
        item: { 
          type: 'function_call_output', 
          call_id: event.call_id, 
          output: JSON.stringify(result) 
        },
      }));
      // Request AI to continue speaking after receiving the tool data
      ws.send(JSON.stringify({ type: 'response.create' }));
      break;
    }

    case 'response.done':
      console.log('\n\n✅ [Response Done] — Tokens used:', event.usage?.total_tokens);
      break;

    case 'error':
      console.error('\n❌ [API Error]:', event.error || event.message);
      break;
  }
});

ws.on('close', () => {
  console.log("Connection closed.");
});

// ── Tool Handlers ────────────────────────────────────────────────────────────

async function handle_check_availability(args) {
  console.log(`Checking PMS for availability on ${args.date}...`);
  // Mock logic
  return { 
    success: true, 
    available_slots: ["10:00 AM", "2:30 PM", "4:00 PM"],
    message: `We have 10:00 AM, 2:30 PM, and 4:00 PM available on ${args.date}.`
  };
}

async function handle_schedule_appointment(args) {
  console.log(`Scheduling appointment for ${args.patient_name} on ${args.date} at ${args.time}...`);
  // Mock logic
  return { 
    success: true, 
    confirmation_id: "APT-" + Math.floor(Math.random() * 10000),
    message: `Successfully booked ${args.patient_name} for ${args.reason} on ${args.date} at ${args.time}.`
  };
}

async function handle_cancel_appointment(args) {
  console.log(`Cancelling appointment for ${args.patient_name} on ${args.appointment_date}...`);
  // Mock logic
  return { 
    success: true, 
    message: `Appointment cancelled successfully for ${args.patient_name}.`
  };
}

async function handleToolCall(name, argsJson) {
  const args = JSON.parse(argsJson || '{}');
  switch (name) {
    case 'check_availability': return handle_check_availability(args);
    case 'schedule_appointment': return handle_schedule_appointment(args);
    case 'cancel_appointment': return handle_cancel_appointment(args);
    default: return { error: `Unknown tool: ${name}` };
  }
}
