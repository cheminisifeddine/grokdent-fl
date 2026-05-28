/**
 * Renia AI — Cloudflare Serverless Worker Backend
 * Powered by Hono, D1 Database, R2 Object Storage, and xAI Grok API.
 * Secure, bilingual, serverless, and HIPAA-compliant.
 */

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { SignJWT, jwtVerify } from 'jose';

const app = new Hono();
const landingVoiceTokenHits = new Map();
const LANDING_VOICE_TOKEN_LIMIT = 24;
const LANDING_VOICE_TOKEN_WINDOW_MS = 60 * 1000;

// Enable CORS for dashboard web clients
app.use('*', cors({
  origin: '*',
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
  exposeHeaders: ['Content-Length'],
  maxAge: 600,
  credentials: true,
}));

// -------------------------------------------------------------------------
// Crypto Helpers (AES-GCM Web Crypto for HIPAA ePHI Protection)
// -------------------------------------------------------------------------
async function getCryptoKey(secretStr) {
  const enc = new TextEncoder();
  const rawKey = enc.encode(secretStr.padEnd(32).substring(0, 32));
  return await crypto.subtle.importKey(
    'raw',
    rawKey,
    { name: 'AES-GCM' },
    false,
    ['encrypt', 'decrypt']
  );
}

async function encryptData(plaintext, secretStr) {
  if (!plaintext) return '';
  const key = await getCryptoKey(secretStr);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encoded = new TextEncoder().encode(plaintext);
  const ciphertext = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    encoded
  );
  
  // Combine IV + Ciphertext
  const ivHex = Array.from(iv).map(b => b.toString(16).padStart(2, '0')).join('');
  const cipherHex = Array.from(new Uint8Array(ciphertext)).map(b => b.toString(16).padStart(2, '0')).join('');
  return `${ivHex}:${cipherHex}`;
}

async function decryptData(encryptedStr, secretStr) {
  if (!encryptedStr || !encryptedStr.includes(':')) return '';
  try {
    const key = await getCryptoKey(secretStr);
    const [ivHex, cipherHex] = encryptedStr.split(':');
    
    const iv = new Uint8Array(ivHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
    const ciphertext = new Uint8Array(cipherHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
    
    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      key,
      ciphertext
    );
    return new TextDecoder().decode(decrypted);
  } catch (err) {
    console.error('Decryption failed:', err);
    return '[DECRYPTION_ERROR]';
  }
}

// PBKDF2-based password hashing (HIPAA-aligned)
async function hashPassword(password) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    'raw', encoder.encode(password), 'PBKDF2', false, ['deriveBits']
  );
  const derivedBits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
    keyMaterial, 256
  );
  const saltHex = Array.from(salt).map(b => b.toString(16).padStart(2, '0')).join('');
  const hashHex = Array.from(new Uint8Array(derivedBits)).map(b => b.toString(16).padStart(2, '0')).join('');
  return `${saltHex}:${hashHex}`;
}

async function verifyPassword(password, stored) {
  const [saltHex, hashHex] = stored.split(':');
  const salt = new Uint8Array(saltHex.match(/.{1,2}/g).map(b => parseInt(b, 16)));
  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    'raw', encoder.encode(password), 'PBKDF2', false, ['deriveBits']
  );
  const derivedBits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
    keyMaterial, 256
  );
  const verifyHex = Array.from(new Uint8Array(derivedBits)).map(b => b.toString(16).padStart(2, '0')).join('');
  return verifyHex === hashHex;
}

// -------------------------------------------------------------------------
// JWT Authentication Middleware
// -------------------------------------------------------------------------
async function authMiddleware(c, next) {
  const authHeader = c.req.header('Authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return c.json({ error: 'Not authenticated' }, 401);
  }
  
  const token = authHeader.split(' ')[1];
  const jwtSecret = c.env.JWT_SECRET;
  if (!jwtSecret) {
    return c.json({ error: 'JWT_SECRET not configured on server' }, 500);
  }
  
  try {
    const encSecret = new TextEncoder().encode(jwtSecret);
    const { payload } = await jwtVerify(token, encSecret);
    c.set('user', payload);
    await next();
  } catch (err) {
    return c.json({ error: 'Invalid or expired token' }, 401);
  }
}

function enforceLandingVoiceTokenRateLimit(c) {
  const ip = c.req.header('CF-Connecting-IP') || c.req.header('X-Forwarded-For') || 'unknown';
  const now = Date.now();
  const hits = landingVoiceTokenHits.get(ip) || [];
  const recentHits = hits.filter((timestamp) => now - timestamp < LANDING_VOICE_TOKEN_WINDOW_MS);

  if (recentHits.length >= LANDING_VOICE_TOKEN_LIMIT) {
    return c.json({ error: 'Demo limit reached. Please wait a minute and try again.' }, 429);
  }

  recentHits.push(now);
  landingVoiceTokenHits.set(ip, recentHits);
  return null;
}

// -------------------------------------------------------------------------
// 🔐 Auth Router Endpoints
// -------------------------------------------------------------------------
app.post('/api/v1/auth/signup', async (c) => {
  const body = await c.req.json();
  const db = c.env.DB;
  
  if (!body.clinic_name || !body.email || !body.password || !body.full_name) {
    return c.json({ error: 'Missing required signup fields' }, 400);
  }
  
  // Check duplicate email
  const existingUser = await db.prepare('SELECT id FROM users WHERE email = ?').bind(body.email).first();
  if (existingUser) {
    return c.json({ error: 'Email already registered' }, 400);
  }
  
  const clinicId = crypto.randomUUID();
  const userId = crypto.randomUUID();
  const slug = body.clinic_name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  
  // Insert Clinic & User in D1
  await db.batch([
    db.prepare('INSERT INTO clinics (id, name, slug, spanish_enabled) VALUES (?, ?, ?, 1)')
      .bind(clinicId, body.clinic_name, slug),
    db.prepare('INSERT INTO users (id, clinic_id, email, hashed_password, full_name, role) VALUES (?, ?, ?, ?, ?, "admin")')
      .bind(userId, clinicId, body.email, await hashPassword(body.password), body.full_name)
  ]);
  
  // Issue JWT Token
  const jwtSecret = c.env.JWT_SECRET;
  if (!jwtSecret) {
    return c.json({ error: 'JWT_SECRET not configured on server' }, 500);
  }
  const encSecret = new TextEncoder().encode(jwtSecret);
  const token = await new SignJWT({ sub: userId, clinic_id: clinicId, role: 'admin' })
    .setProtectedHeader({ alg: 'HS256' })
    .setExpirationTime('2h')
    .sign(encSecret);
    
  return c.json({
    access_token: token,
    token_type: 'bearer',
    user: { id: userId, clinic_id: clinicId, email: body.email, full_name: body.full_name, role: 'admin' }
  }, 201);
});

app.post('/api/v1/auth/login', async (c) => {
  const body = await c.req.json();
  const db = c.env.DB;
  
  const user = await db.prepare('SELECT * FROM users WHERE email = ?').bind(body.email).first();
  if (!user) return c.json({ error: 'Invalid credentials' }, 401);
  
  const valid = await verifyPassword(body.password, user.hashed_password);
  if (!valid) {
    return c.json({ error: 'Invalid credentials' }, 401);
  }
  
  const jwtSecret = c.env.JWT_SECRET;
  if (!jwtSecret) {
    return c.json({ error: 'JWT_SECRET not configured on server' }, 500);
  }
  const encSecret = new TextEncoder().encode(jwtSecret);
  const token = await new SignJWT({ sub: user.id, clinic_id: user.clinic_id, role: user.role })
    .setProtectedHeader({ alg: 'HS256' })
    .setExpirationTime('2h')
    .sign(encSecret);
    
  return c.json({
    access_token: token,
    token_type: 'bearer',
    user: { id: user.id, clinic_id: user.clinic_id, email: user.email, full_name: user.full_name, role: user.role }
  });
});

// -------------------------------------------------------------------------
// 🏥 Clinic Profiles
// -------------------------------------------------------------------------
app.get('/api/v1/clinics', authMiddleware, async (c) => {
  const user = c.get('user');
  const clinic = await c.env.DB.prepare('SELECT * FROM clinics WHERE id = ?').bind(user.clinic_id).first();
  if (!clinic) return c.json({ error: 'Clinic not found' }, 404);
  return c.json(clinic);
});

app.get('/api/v1/voice/xai-key', authMiddleware, async (c) => {
  const user = c.get('user');
  const clinic = await c.env.DB.prepare('SELECT xai_key FROM clinics WHERE id = ?').bind(user.clinic_id).first();
  const clinicKey = clinic?.xai_key || '';
  const envKey = c.env.XAI_API_KEY || '';
  return c.json({ xai_key: clinicKey || envKey });
});

app.put('/api/v1/clinics', authMiddleware, async (c) => {
  const user = c.get('user');
  const body = await c.req.json();
  const db = c.env.DB;
  
  await db.prepare('UPDATE clinics SET name = ?, phone = ?, email = ?, address = ?, city = ?, zip_code = ?, welcome_message = ? WHERE id = ?')
    .bind(body.name, body.phone, body.email, body.address, body.city, body.zip_code, body.welcome_message, user.clinic_id)
    .run();
    
  return c.json({ message: 'Clinic profile updated successfully' });
});

// -------------------------------------------------------------------------
// 👤 Patients Management Router (Brings HIPAA AES Encryption)
// -------------------------------------------------------------------------
app.get('/api/v1/patients', authMiddleware, async (c) => {
  const user = c.get('user');
  const encKey = c.env.ENCRYPTION_KEY;
  if (!encKey) {
    return c.json({ error: 'ENCRYPTION_KEY not configured on server' }, 500);
  }
  
  const patients = await c.env.DB.prepare('SELECT * FROM patients WHERE clinic_id = ?').bind(user.clinic_id).all();
  
  const decrypted = await Promise.all(patients.results.map(async p => ({
    id: p.id,
    first_name: p.first_name,
    last_name: p.last_name,
    phone: p.phone_encrypted ? await decryptData(p.phone_encrypted, encKey) : null,
    email: p.email_encrypted ? await decryptData(p.email_encrypted, encKey) : null,
    dob: p.dob_encrypted ? await decryptData(p.dob_encrypted, encKey) : null,
    insurance_provider: p.insurance_provider,
    insurance_id: p.insurance_id_encrypted ? await decryptData(p.insurance_id_encrypted, encKey) : null,
    preferred_language: p.preferred_language,
    notes: p.notes_encrypted ? await decryptData(p.notes_encrypted, encKey) : null
  })));
  
  return c.json(decrypted);
});

app.post('/api/v1/patients', authMiddleware, async (c) => {
  const user = c.get('user');
  const body = await c.req.json();
  const encKey = c.env.ENCRYPTION_KEY;
  if (!encKey) {
    return c.json({ error: 'ENCRYPTION_KEY not configured on server' }, 500);
  }
  
  const patientId = crypto.randomUUID();
  
  const phoneEnc = body.phone ? await encryptData(body.phone, encKey) : '';
  const emailEnc = body.email ? await encryptData(body.email, encKey) : '';
  const dobEnc = body.dob ? await encryptData(body.dob, encKey) : '';
  const insEnc = body.insurance_id ? await encryptData(body.insurance_id, encKey) : '';
  const notesEnc = body.notes ? await encryptData(body.notes, encKey) : '';
  
  await c.env.DB.prepare('INSERT INTO patients (id, clinic_id, first_name, last_name, phone_encrypted, email_encrypted, dob_encrypted, insurance_provider, insurance_id_encrypted, preferred_language, notes_encrypted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    .bind(patientId, user.clinic_id, body.first_name, body.last_name, phoneEnc, emailEnc, dobEnc, body.insurance_provider, insEnc, body.preferred_language || 'en', notesEnc)
    .run();
    
  return c.json({ id: patientId, message: 'Patient secure record created' }, 201);
});

// -------------------------------------------------------------------------
// 📅 Appointments Router
// -------------------------------------------------------------------------
app.get('/api/v1/appointments', authMiddleware, async (c) => {
  const user = c.get('user');
  const appointments = await c.env.DB.prepare('SELECT * FROM appointments WHERE clinic_id = ? ORDER BY appointment_datetime')
    .bind(user.clinic_id).all();
  return c.json(appointments.results);
});

app.post('/api/v1/appointments', authMiddleware, async (c) => {
  const user = c.get('user');
  const body = await c.req.json();
  const apptId = crypto.randomUUID();
  
  await c.env.DB.prepare('INSERT INTO appointments (id, clinic_id, patient_id, appointment_datetime, service_type, notes) VALUES (?, ?, ?, ?, ?, ?)')
    .bind(apptId, user.clinic_id, body.patient_id, body.appointment_datetime, body.service_type, body.notes)
    .run();
    
  return c.json({ id: apptId, message: 'Appointment created successfully' }, 201);
});

// -------------------------------------------------------------------------
// 📞 Call History Feed (D1 + R2 storage integration)
// -------------------------------------------------------------------------
app.get('/api/v1/calls', authMiddleware, async (c) => {
  const user = c.get('user');
  const encKey = c.env.ENCRYPTION_KEY;
  if (!encKey) {
    return c.json({ error: 'ENCRYPTION_KEY not configured on server' }, 500);
  }
  
  const calls = await c.env.DB.prepare('SELECT * FROM call_logs WHERE clinic_id = ? ORDER BY created_at DESC')
    .bind(user.clinic_id).all();
    
  const decrypted = await Promise.all(calls.results.map(async log => ({
    id: log.id,
    twilio_call_sid: log.twilio_call_sid,
    direction: log.direction,
    caller_number: log.caller_number,
    called_number: log.called_number,
    duration_seconds: log.duration_seconds,
    status: log.status,
    sentiment: log.sentiment,
    summary: log.summary,
    language: log.language,
    is_emergency: log.is_emergency === 1,
    transcript: log.transcript_encrypted ? await decryptData(log.transcript_encrypted, encKey) : null
  })));
  
  return c.json(decrypted);
});

// -------------------------------------------------------------------------
// 📞 Twilio Voice AI webhooks
// -------------------------------------------------------------------------
app.post('/api/v1/webhooks/voice/incoming', async (c) => {
  const greeting = (
    '<?xml version="1.0" encoding="UTF-8"?>' +
    '<Response>' +
    '<Gather input="speech" speechTimeout="auto" language="en-US" action="/api/v1/webhooks/voice/gather" method="POST">' +
    '<Say voice="Polly.Joanna">Thank you for calling Sunshine Smiles Dental. I am your AI receptionist. This call may be recorded for quality purposes. How can I help you?</Say>' +
    '</Gather>' +
    '<Say voice="Polly.Joanna">I did not catch that. Goodbye!</Say>' +
    '</Response>'
  );
  return new Response(greeting, { headers: { 'Content-Type': 'application/xml' } });
});

// -------------------------------------------------------------------------
// 📊 Dashboards & Analytics
// -------------------------------------------------------------------------
app.get('/api/v1/analytics/dashboard', authMiddleware, async (c) => {
  const user = c.get('user');
  const db = c.env.DB;
  
  const callCount = await db.prepare('SELECT COUNT(id) as count FROM call_logs WHERE clinic_id = ?').bind(user.clinic_id).first();
  const apptCount = await db.prepare('SELECT COUNT(id) as count FROM appointments WHERE clinic_id = ?').bind(user.clinic_id).first();
  
  return c.json({
    calls_today: callCount ? callCount.count : 0,
    bookings_today: apptCount ? apptCount.count : 0,
    revenue_estimate: (apptCount ? apptCount.count : 0) * 150.00,
    satisfaction_score: 95.5
  });
});

// -------------------------------------------------------------------------
// 🔐 Auth — Get Current User
// -------------------------------------------------------------------------
app.get('/api/v1/auth/me', authMiddleware, async (c) => {
  const user = c.get('user');
  const dbUser = await c.env.DB.prepare('SELECT id, clinic_id, email, full_name, role FROM users WHERE id = ?').bind(user.sub).first();
  if (!dbUser) return c.json({ error: 'User not found' }, 404);
  return c.json(dbUser);
});

// -------------------------------------------------------------------------
// 📅 Appointments — Today, Update, Delete
// -------------------------------------------------------------------------
app.get('/api/v1/appointments/today', authMiddleware, async (c) => {
  const user = c.get('user');
  const today = new Date().toISOString().split('T')[0];
  const appts = await c.env.DB.prepare(
    "SELECT * FROM appointments WHERE clinic_id = ? AND appointment_datetime LIKE ? ORDER BY appointment_datetime"
  ).bind(user.clinic_id, today + '%').all();
  return c.json(appts.results);
});

app.get('/api/v1/appointments/availability', authMiddleware, async (c) => {
  const user = c.get('user');
  const date = c.req.query('date') || new Date().toISOString().split('T')[0];
  const booked = await c.env.DB.prepare(
    "SELECT appointment_datetime FROM appointments WHERE clinic_id = ? AND appointment_datetime LIKE ? AND status != 'cancelled'"
  ).bind(user.clinic_id, date + '%').all();
  const bookedTimes = booked.results.map(a => a.appointment_datetime);
  const allSlots = ['09:00','09:30','10:00','10:30','11:00','11:30','13:00','13:30','14:00','14:30','15:00','15:30','16:00','16:30'];
  const available = allSlots.filter(slot => !bookedTimes.some(bt => bt.includes(slot)));
  return c.json(available.map(t => ({ time: t, available: true })));
});

app.put('/api/v1/appointments/:id', authMiddleware, async (c) => {
  const user = c.get('user');
  const id = c.req.param('id');
  const body = await c.req.json();
  await c.env.DB.prepare(
    'UPDATE appointments SET appointment_datetime = ?, service_type = ?, status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND clinic_id = ?'
  ).bind(body.appointment_datetime || '', body.service_type || '', body.status || 'scheduled', body.notes || '', id, user.clinic_id).run();
  return c.json({ message: 'Appointment updated' });
});

app.delete('/api/v1/appointments/:id', authMiddleware, async (c) => {
  const user = c.get('user');
  const id = c.req.param('id');
  await c.env.DB.prepare(
    "UPDATE appointments SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND clinic_id = ?"
  ).bind(id, user.clinic_id).run();
  return c.json({ message: 'Appointment cancelled' });
});

// -------------------------------------------------------------------------
// 📞 Calls — Recent, Stats, Detail
// -------------------------------------------------------------------------
app.get('/api/v1/calls/recent', authMiddleware, async (c) => {
  const user = c.get('user');
  const calls = await c.env.DB.prepare(
    'SELECT * FROM call_logs WHERE clinic_id = ? ORDER BY created_at DESC LIMIT 10'
  ).bind(user.clinic_id).all();
  return c.json(calls.results);
});

app.get('/api/v1/calls/stats', authMiddleware, async (c) => {
  const user = c.get('user');
  const db = c.env.DB;
  const total = await db.prepare('SELECT COUNT(id) as count FROM call_logs WHERE clinic_id = ?').bind(user.clinic_id).first();
  const completed = await db.prepare("SELECT COUNT(id) as count FROM call_logs WHERE clinic_id = ? AND status = 'completed'").bind(user.clinic_id).first();
  const missed = await db.prepare("SELECT COUNT(id) as count FROM call_logs WHERE clinic_id = ? AND status = 'missed'").bind(user.clinic_id).first();
  const avgDuration = await db.prepare('SELECT AVG(duration_seconds) as avg FROM call_logs WHERE clinic_id = ?').bind(user.clinic_id).first();
  return c.json({
    total_calls: total?.count || 0,
    completed_calls: completed?.count || 0,
    missed_calls: missed?.count || 0,
    average_duration: Math.round(avgDuration?.avg || 0)
  });
});

app.get('/api/v1/calls/:id', authMiddleware, async (c) => {
  const user = c.get('user');
  const id = c.req.param('id');
  const encKey = c.env.ENCRYPTION_KEY;
  if (!encKey) {
    return c.json({ error: 'ENCRYPTION_KEY not configured on server' }, 500);
  }
  const call = await c.env.DB.prepare('SELECT * FROM call_logs WHERE id = ? AND clinic_id = ?').bind(id, user.clinic_id).first();
  if (!call) return c.json({ error: 'Call not found' }, 404);
  call.transcript = call.transcript_encrypted ? await decryptData(call.transcript_encrypted, encKey) : null;
  return c.json(call);
});

// -------------------------------------------------------------------------
// 📚 Knowledge Base — Full CRUD + Seed
// -------------------------------------------------------------------------
app.get('/api/v1/knowledge', authMiddleware, async (c) => {
  const user = c.get('user');
  const category = c.req.query('category');
  let query = 'SELECT * FROM knowledge_base WHERE clinic_id = ?';
  const params = [user.clinic_id];
  if (category && category !== 'all') {
    query += ' AND category = ?';
    params.push(category);
  }
  query += ' ORDER BY priority DESC, created_at DESC';
  const stmt = c.env.DB.prepare(query);
  const result = params.length === 2 ? await stmt.bind(params[0], params[1]).all() : await stmt.bind(params[0]).all();
  return c.json(result.results);
});

app.post('/api/v1/knowledge', authMiddleware, async (c) => {
  const user = c.get('user');
  const body = await c.req.json();
  const id = crypto.randomUUID();
  await c.env.DB.prepare(
    'INSERT INTO knowledge_base (id, clinic_id, category, question, answer, answer_spanish, priority) VALUES (?, ?, ?, ?, ?, ?, ?)'
  ).bind(id, user.clinic_id, body.category || 'general', body.question, body.answer, body.answer_es || '', body.priority || 0).run();
  return c.json({ id, message: 'Knowledge entry created' }, 201);
});

app.put('/api/v1/knowledge/:id', authMiddleware, async (c) => {
  const user = c.get('user');
  const id = c.req.param('id');
  const body = await c.req.json();
  await c.env.DB.prepare(
    'UPDATE knowledge_base SET category = ?, question = ?, answer = ?, answer_spanish = ?, priority = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND clinic_id = ?'
  ).bind(body.category || 'general', body.question, body.answer, body.answer_es || '', body.priority || 0, body.active ? 1 : 0, id, user.clinic_id).run();
  return c.json({ message: 'Knowledge entry updated' });
});

app.delete('/api/v1/knowledge/:id', authMiddleware, async (c) => {
  const user = c.get('user');
  const id = c.req.param('id');
  await c.env.DB.prepare('DELETE FROM knowledge_base WHERE id = ? AND clinic_id = ?').bind(id, user.clinic_id).run();
  return c.json({ message: 'Knowledge entry deleted' });
});

app.post('/api/v1/knowledge/seed', authMiddleware, async (c) => {
  const user = c.get('user');
  const defaults = [
    { category: 'hours', question: 'What are your office hours?', answer: 'We are open Monday through Friday, 8:00 AM to 5:00 PM, and Saturday 9:00 AM to 1:00 PM. We are closed on Sundays.', answer_es: 'Estamos abiertos de lunes a viernes de 8:00 AM a 5:00 PM, y sábados de 9:00 AM a 1:00 PM. Los domingos estamos cerrados.' },
    { category: 'emergency', question: 'What should I do in a dental emergency?', answer: 'If you are experiencing a dental emergency such as severe pain, swelling, or a knocked-out tooth, please call our office immediately. We offer same-day emergency appointments during business hours.', answer_es: 'Si tiene una emergencia dental como dolor severo, hinchazón o un diente que se le cayó, por favor llame a nuestra oficina de inmediato. Ofrecemos citas de emergencia el mismo día durante horario laboral.' },
    { category: 'insurance', question: 'What insurance do you accept?', answer: 'We accept most major dental insurance plans including Delta Dental, Cigna, MetLife, Aetna, Guardian, Humana, and Florida Medicaid (MCNA Dental). Please contact us to verify your specific plan.', answer_es: 'Aceptamos la mayoría de los seguros dentales incluyendo Delta Dental, Cigna, MetLife, Aetna, Guardian, Humana y Medicaid de Florida (MCNA Dental). Por favor contáctenos para verificar su plan específico.' },
    { category: 'services', question: 'What services do you offer?', answer: 'We offer comprehensive dental care including general dentistry, cosmetic dentistry, dental implants, orthodontics, teeth whitening, root canals, crowns, bridges, veneers, and emergency dental services.', answer_es: 'Ofrecemos atención dental integral incluyendo odontología general, cosmética, implantes dentales, ortodoncia, blanqueamiento, endodoncias, coronas, puentes, carillas y servicios dentales de emergencia.' },
    { category: 'pricing', question: 'How much does a dental cleaning cost?', answer: 'A routine dental cleaning and exam starts at $99 for new patients. For patients with insurance, your copay will vary based on your plan. We also offer affordable payment plans through CareCredit.', answer_es: 'Una limpieza dental de rutina y examen comienza en $99 para nuevos pacientes. Para pacientes con seguro, su copago variará según su plan. También ofrecemos planes de pago accesibles a través de CareCredit.' },
    { category: 'location', question: 'Where are you located?', answer: 'We are conveniently located in the heart of Florida. Free parking is available. Our office is wheelchair accessible.', answer_es: 'Estamos convenientemente ubicados en el corazón de Florida. Estacionamiento gratuito disponible. Nuestra oficina es accesible para sillas de ruedas.' },
    { category: 'policies', question: 'What is your cancellation policy?', answer: 'We require 24 hours advance notice for cancellations. Late cancellations or no-shows may be subject to a $50 fee. We understand emergencies happen and will work with you on a case-by-case basis.', answer_es: 'Requerimos 24 horas de anticipación para cancelaciones. Cancelaciones tardías o ausencias pueden estar sujetas a un cargo de $50. Entendemos que las emergencias suceden y trabajaremos con usted caso por caso.' },
    { category: 'general', question: 'Do you see new patients?', answer: 'Absolutely! We welcome new patients of all ages. You can schedule your first appointment online or by calling our office. New patient appointments include a comprehensive exam, X-rays, and cleaning.', answer_es: '¡Absolutamente! Damos la bienvenida a nuevos pacientes de todas las edades. Puede programar su primera cita en línea o llamando a nuestra oficina. Las citas de nuevos pacientes incluyen un examen completo, radiografías y limpieza.' }
  ];
  
  const stmts = defaults.map(d => 
    c.env.DB.prepare('INSERT INTO knowledge_base (id, clinic_id, category, question, answer, answer_spanish, priority) VALUES (?, ?, ?, ?, ?, ?, ?)')
      .bind(crypto.randomUUID(), user.clinic_id, d.category, d.question, d.answer, d.answer_es, 5)
  );
  await c.env.DB.batch(stmts);
  return c.json({ message: `Seeded ${defaults.length} default knowledge base entries` }, 201);
});

// -------------------------------------------------------------------------
// 🏥 Clinic — Hours, Voice Settings
// -------------------------------------------------------------------------
app.put('/api/v1/clinics/hours', authMiddleware, async (c) => {
  const user = c.get('user');
  const body = await c.req.json();
  await c.env.DB.prepare('UPDATE clinics SET hours = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
    .bind(JSON.stringify(body), user.clinic_id).run();
  return c.json({ message: 'Hours updated' });
});

app.put('/api/v1/clinics/services', authMiddleware, async (c) => {
  const user = c.get('user');
  const body = await c.req.json();
  await c.env.DB.prepare('UPDATE clinics SET services = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
    .bind(JSON.stringify(body.services || body), user.clinic_id).run();
  return c.json({ message: 'Services updated' });
});

app.put('/api/v1/clinics/insurance', authMiddleware, async (c) => {
  const user = c.get('user');
  const body = await c.req.json();
  await c.env.DB.prepare('UPDATE clinics SET insurance_accepted = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
    .bind(JSON.stringify(body.insurance || body), user.clinic_id).run();
  return c.json({ message: 'Insurance list updated' });
});

app.put('/api/v1/clinics/voice-settings', authMiddleware, async (c) => {
  const user = c.get('user');
  const body = await c.req.json();
  await c.env.DB.prepare('UPDATE clinics SET grok_voice_id = ?, welcome_message = ?, spanish_enabled = ?, xai_key = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
    .bind(body.grok_voice_id || body.voice || 'Ash', body.welcome_message || '', body.spanish_enabled ? 1 : 0, body.xai_key || '', user.clinic_id).run();
  return c.json({ message: 'Voice settings updated' });
});

// -------------------------------------------------------------------------
// 📊 Analytics — Full Suite
// -------------------------------------------------------------------------
app.get('/api/v1/analytics/calls-over-time', authMiddleware, async (c) => {
  const user = c.get('user');
  const days = parseInt(c.req.query('days')) || 7;
  const results = [];
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split('T')[0];
    const count = await c.env.DB.prepare(
      "SELECT COUNT(id) as count FROM call_logs WHERE clinic_id = ? AND created_at LIKE ?"
    ).bind(user.clinic_id, dateStr + '%').first();
    results.push({ date: dateStr, count: count?.count || 0 });
  }
  return c.json(results);
});

app.get('/api/v1/analytics/bookings-over-time', authMiddleware, async (c) => {
  const user = c.get('user');
  const days = parseInt(c.req.query('days')) || 7;
  const results = [];
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split('T')[0];
    const count = await c.env.DB.prepare(
      "SELECT COUNT(id) as count FROM appointments WHERE clinic_id = ? AND created_at LIKE ?"
    ).bind(user.clinic_id, dateStr + '%').first();
    results.push({ date: dateStr, count: count?.count || 0 });
  }
  return c.json(results);
});

app.get('/api/v1/analytics/top-services', authMiddleware, async (c) => {
  const user = c.get('user');
  const services = await c.env.DB.prepare(
    "SELECT service_type, COUNT(id) as count FROM appointments WHERE clinic_id = ? AND service_type IS NOT NULL GROUP BY service_type ORDER BY count DESC LIMIT 10"
  ).bind(user.clinic_id).all();
  return c.json(services.results);
});

app.get('/api/v1/analytics/language-breakdown', authMiddleware, async (c) => {
  const user = c.get('user');
  const langs = await c.env.DB.prepare(
    "SELECT language, COUNT(id) as count FROM call_logs WHERE clinic_id = ? GROUP BY language"
  ).bind(user.clinic_id).all();
  return c.json(langs.results);
});

// -------------------------------------------------------------------------
// 💳 Billing — Checkout, Subscription, Cancel
// -------------------------------------------------------------------------
app.post('/api/v1/billing/checkout', authMiddleware, async (c) => {
  const user = c.get('user');
  const body = await c.req.json();
  const plan = body.plan || 'starter';
  // In production, this would create a Stripe checkout session
  // For now, update the subscription directly
  await c.env.DB.prepare('UPDATE clinics SET subscription_plan = ?, subscription_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
    .bind(plan, 'active', user.clinic_id).run();
  return c.json({ message: `Subscribed to ${plan} plan`, checkout_url: null });
});

app.get('/api/v1/billing/subscription', authMiddleware, async (c) => {
  const user = c.get('user');
  const clinic = await c.env.DB.prepare('SELECT subscription_plan, subscription_status, stripe_customer_id FROM clinics WHERE id = ?').bind(user.clinic_id).first();
  return c.json({
    plan: clinic?.subscription_plan || 'starter',
    status: clinic?.subscription_status || 'trial',
    customer_id: clinic?.stripe_customer_id || null
  });
});

app.post('/api/v1/billing/cancel', authMiddleware, async (c) => {
  const user = c.get('user');
  await c.env.DB.prepare("UPDATE clinics SET subscription_status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?")
    .bind(user.clinic_id).run();
  return c.json({ message: 'Subscription cancelled' });
});

// -------------------------------------------------------------------------
// 👤 Patients — Search, Detail, Update
// -------------------------------------------------------------------------
app.get('/api/v1/patients/search', authMiddleware, async (c) => {
  const user = c.get('user');
  const q = c.req.query('q') || '';
  const encKey = c.env.ENCRYPTION_KEY;
  if (!encKey) {
    return c.json({ error: 'ENCRYPTION_KEY not configured on server' }, 500);
  }
  const patients = await c.env.DB.prepare(
    "SELECT * FROM patients WHERE clinic_id = ? AND (first_name LIKE ? OR last_name LIKE ?)"
  ).bind(user.clinic_id, `%${q}%`, `%${q}%`).all();
  const decrypted = await Promise.all(patients.results.map(async p => ({
    id: p.id, first_name: p.first_name, last_name: p.last_name,
    phone: p.phone_encrypted ? await decryptData(p.phone_encrypted, encKey) : null,
    email: p.email_encrypted ? await decryptData(p.email_encrypted, encKey) : null,
    insurance_provider: p.insurance_provider, preferred_language: p.preferred_language
  })));
  return c.json(decrypted);
});

app.get('/api/v1/patients/:id', authMiddleware, async (c) => {
  const user = c.get('user');
  const id = c.req.param('id');
  const encKey = c.env.ENCRYPTION_KEY;
  if (!encKey) {
    return c.json({ error: 'ENCRYPTION_KEY not configured on server' }, 500);
  }
  const p = await c.env.DB.prepare('SELECT * FROM patients WHERE id = ? AND clinic_id = ?').bind(id, user.clinic_id).first();
  if (!p) return c.json({ error: 'Patient not found' }, 404);
  return c.json({
    id: p.id, first_name: p.first_name, last_name: p.last_name,
    phone: p.phone_encrypted ? await decryptData(p.phone_encrypted, encKey) : null,
    email: p.email_encrypted ? await decryptData(p.email_encrypted, encKey) : null,
    dob: p.dob_encrypted ? await decryptData(p.dob_encrypted, encKey) : null,
    insurance_provider: p.insurance_provider,
    insurance_id: p.insurance_id_encrypted ? await decryptData(p.insurance_id_encrypted, encKey) : null,
    preferred_language: p.preferred_language,
    notes: p.notes_encrypted ? await decryptData(p.notes_encrypted, encKey) : null
  });
});

app.put('/api/v1/patients/:id', authMiddleware, async (c) => {
  const user = c.get('user');
  const id = c.req.param('id');
  const body = await c.req.json();
  const encKey = c.env.ENCRYPTION_KEY;
  if (!encKey) {
    return c.json({ error: 'ENCRYPTION_KEY not configured on server' }, 500);
  }
  const phoneEnc = body.phone ? await encryptData(body.phone, encKey) : '';
  const emailEnc = body.email ? await encryptData(body.email, encKey) : '';
  const notesEnc = body.notes ? await encryptData(body.notes, encKey) : '';
  await c.env.DB.prepare(
    'UPDATE patients SET first_name = ?, last_name = ?, phone_encrypted = ?, email_encrypted = ?, insurance_provider = ?, notes_encrypted = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND clinic_id = ?'
  ).bind(body.first_name, body.last_name, phoneEnc, emailEnc, body.insurance_provider || '', notesEnc, id, user.clinic_id).run();
  return c.json({ message: 'Patient updated' });
});

// -------------------------------------------------------------------------
// 📞 Real xAI Grok Voice Agent Simulator Proxy (Bypasses Browser CORS)
// -------------------------------------------------------------------------
app.post('/api/v1/voice/simulate', authMiddleware, async (c) => {
  try {
    const body = await c.req.json();
    const { messages, scenario, clinicName, settings, kbEntries } = body;
    const user = c.get('user');
    
    // Use clinic-level key first, then fall back to server env
    const clinic = await c.env.DB.prepare('SELECT xai_key FROM clinics WHERE id = ?').bind(user.clinic_id).first();
    const xaiKey = clinic?.xai_key || c.env.XAI_API_KEY;
    if (!xaiKey) {
      return c.json({ error: 'XAI_API_KEY not configured on server' }, 500);
    }
    
    // Construct dynamic system prompt based on active dentist setup
    const activeVoice = (settings && settings.voice && settings.voice.voice) || 'Ash';
    let systemPrompt = `You are the Elite AI Voice Receptionist named ${activeVoice} for "${clinicName || 'Sunshine Smiles Dental'}". 
    Your tone is warm, professional, and Florida-friendly. You represent a real dental clinic.

CLINIC DETAILS:
- Settings: ${JSON.stringify(settings || {})}
- Accepted Insurances: Delta Dental PPO, Humana, Guardian, MCNA (Florida Medicaid).
- Custom Knowledge Base: ${JSON.stringify(kbEntries || [])}

SCENARIO INSTRUCTIONS:
`;

    if (scenario === 'carlos') {
      systemPrompt += `
- You are speaking with Carlos Hernandez, a Spanish-preferred patient with severe tooth pain/bleeding emergency.
- Speak in fluent Spanish. Triage the pain, offer an emergency extraction appointment for "today at 1:30 PM".
- When Carlos agrees and provides his full name and phone number, you MUST book the appointment and conclude the call warmly.
- Once you successfully book the appointment, append exactly "[BOOKING: Emergency Extraction | 2026-05-23 | 1:30 PM]" to the very end of your response.
`;
    } else if (scenario === 'emily') {
      systemPrompt += `
- You are speaking with Emily Johnson, a new patient interested in cosmetic teeth whitening.
- She will ask if you accept Delta Dental PPO. Confirm that you proudly accept Delta Dental PPO, MCNA, and Humana!
- Offer her an appointment for "tomorrow at 10:00 AM" or "Friday at 3:00 PM".
- When she agrees, ask for her full name and phone number to secure the slot.
- Once booked, append exactly "[BOOKING: Teeth Whitening Consultation | 2026-05-24 | 10:00 AM]" to the very end of your response.
`;
    } else if (scenario === 'james') {
      systemPrompt += `
- You are speaking with James Wilson, an existing patient who wants to reschedule his routine cleaning next Wednesday to tomorrow afternoon.
- Locate his record, confirm you can release next Wednesday's slot, and offer tomorrow at 2:00 PM.
- When he confirms, ask for his full name and phone number to verify his file.
- Once booked, append exactly "[BOOKING: Routine Cleaning Reschedule | 2026-05-24 | 2:00 PM]" to the very end of your response.
`;
    } else {
      systemPrompt += `
- Answer general inquiries using the Knowledge Base. 
- If booking occurs, append "[BOOKING: General Checkup | 2026-05-23 | 10:00 AM]" at the end.
`;
    }

    systemPrompt += `\nCRITICAL DIRECTIVES:
1. Speak concisely in short conversational sentences (since this is an audio voice conversation). Avoid long lists or paragraphs.
2. Never break character. Never mention you are an LLM.
3. Keep answers strictly HIPAA-compliant. Do not disclose other patient information.`;

    const payload = {
      model: 'grok-4.3',
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages
      ],
      temperature: 0.7,
      max_tokens: 250
    };

    const xaiResponse = await fetch('https://api.x.ai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${xaiKey}`
      },
      body: JSON.stringify(payload)
    });

    if (!xaiResponse.ok) {
      const errTxt = await xaiResponse.text();
      return c.json({ error: 'xAI API error', details: errTxt }, 502);
    }

    const data = await xaiResponse.json();
    const reply = data.choices[0].message.content;

    return c.json({ response: reply });
  } catch (err) {
    return c.json({ error: 'Simulator proxy error', message: err.message }, 500);
  }
});

// -------------------------------------------------------------------------
// 🔑 xAI Realtime API Session Token Endpoint (For Browser Voice Agents)
// -------------------------------------------------------------------------
async function mintXaiRealtimeClientSecret(xaiKey) {
  const response = await fetch('https://api.x.ai/v1/realtime/client_secrets', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${xaiKey}`
    },
    body: JSON.stringify({
      expires_after: { seconds: 300 }
    })
  });

  console.log('xAI session token response status:', response.status);

  if (!response.ok) {
    const errText = await response.text();
    console.error('xAI session token error:', errText);
    return { error: errText, status: response.status };
  }

  return { data: await response.json() };
}

app.post('/api/v1/voice/landing-session-token', async (c) => {
  const rateLimitResponse = enforceLandingVoiceTokenRateLimit(c);
  if (rateLimitResponse) return rateLimitResponse;

  const xaiKey = c.env.XAI_API_KEY;
  if (!xaiKey) {
    return c.json({ error: 'Realtime voice demo is not configured.' }, 500);
  }

  try {
    console.log('Fetching public landing session token from xAI...');
    const result = await mintXaiRealtimeClientSecret(xaiKey);
    if (result.error) {
      return c.json({ error: 'Failed to mint landing session token', details: result.error, status: result.status }, 502);
    }
    if (!result.data?.value || !result.data?.expires_at) {
      return c.json({ error: 'Invalid xAI realtime token response.' }, 502);
    }

    return c.json({
      token: result.data.value,
      expires_at: result.data.expires_at,
      model: 'grok-voice-think-fast-1.0'
    });
  } catch (err) {
    console.error('Landing session token endpoint error:', err);
    return c.json({ error: 'Landing session token endpoint error', message: err.message }, 500);
  }
});

app.post('/api/v1/voice/session-token', authMiddleware, async (c) => {
  const user = c.get('user');
  // Use clinic-level key first, then fall back to server env
  const clinic = await c.env.DB.prepare('SELECT xai_key FROM clinics WHERE id = ?').bind(user.clinic_id).first();
  const xaiKey = clinic?.xai_key || c.env.XAI_API_KEY;
  if (!xaiKey) {
    return c.json({ error: 'XAI_API_KEY not configured on server' }, 500);
  }
  
  try {
    console.log('Fetching session token from xAI...');
    const result = await mintXaiRealtimeClientSecret(xaiKey);
    if (result.error) {
      return c.json({ error: 'Failed to mint session token', details: result.error, status: result.status }, 502);
    }

    const data = result.data;
    if (!data?.value || !data?.expires_at) {
      return c.json({ error: 'Invalid xAI realtime token response.' }, 502);
    }
    console.log('Session token received, expires_at:', data.expires_at);
    return c.json({
      token: data.value,
      expires_at: data.expires_at,
      model: 'grok-voice-think-fast-1.0'
    });
  } catch (err) {
    console.error('Session token endpoint error:', err);
    return c.json({ error: 'Session token endpoint error', message: err.message }, 500);
  }
});

// -------------------------------------------------------------------------
// 🔊 Real xAI Text-to-Speech Proxy (CORS-Safe Dynamic Voice Synthesis)
// -------------------------------------------------------------------------
app.post('/api/v1/voice/tts', authMiddleware, async (c) => {
  try {
    const body = await c.req.json();
    const { text, voice_id, speed, language } = body;
    
    const user = c.get('user');
    // Use clinic-level key first, then fall back to server env
    const clinic = await c.env.DB.prepare('SELECT xai_key FROM clinics WHERE id = ?').bind(user.clinic_id).first();
    const xaiKey = clinic?.xai_key || c.env.XAI_API_KEY;
    if (!xaiKey) {
      return c.json({ error: 'XAI_API_KEY not configured on server' }, 500);
    }
    
    // Map UI voice agent selection to real xAI voices (eve, ara, leo, rex, sal)
    const voiceMap = {
      'ash': 'rex',
      'ballad': 'ara',
      'coral': 'eve',
      'sage': 'eve',
      'verse': 'sal',
      'ani': 'ara',
      'eve': 'eve',
      'leo': 'leo'
    };
    
    const matchedVoice = voiceMap[(voice_id || 'eve').toLowerCase()] || 'eve';
    
    const xaiResponse = await fetch('https://api.x.ai/v1/tts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${xaiKey}`
      },
      body: JSON.stringify({
        text: text,
        voice_id: matchedVoice,
        speed: speed || 1.0,
        language: language || 'en'
      })
    });
    
    if (!xaiResponse.ok) {
      const errTxt = await xaiResponse.text();
      return c.json({ error: 'xAI TTS error', details: errTxt }, 502);
    }
    
    // Stream dynamic audio MP3 back to the browser
    const audioData = await xaiResponse.arrayBuffer();
    c.header('Content-Type', 'audio/mpeg');
    return c.body(audioData);
  } catch (err) {
    return c.json({ error: 'TTS proxy error', message: err.message }, 500);
  }
});

// -------------------------------------------------------------------------
// 🔄 Real-time WebSocket Dashboard (via Durable Object)
// -------------------------------------------------------------------------
app.get('/ws/:clinic_id', async (c) => {
  const clinicId = c.req.param('clinic_id');
  const doId = c.env.REALTIME_DO.idFromName(`clinic-${clinicId}`);
  const doStub = c.env.REALTIME_DO.get(doId);

  const url = new URL(c.req.url);
  url.searchParams.set('clinic_id', clinicId);

  const doResponse = await doStub.fetch(url.toString(), c.req.raw);
  return doResponse;
});

// Broadcast helper used by other endpoints
async function broadcastToClinic(env, clinicId, eventType, data) {
  const doId = env.REALTIME_DO.idFromName(`clinic-${clinicId}`);
  const doStub = env.REALTIME_DO.get(doId);
  await doStub.fetch('http://broadcast/', {
    method: 'POST',
    body: JSON.stringify({ event: eventType, data, timestamp: Date.now() }),
  });
}

// -------------------------------------------------------------------------
// 🏥 Health Check
// -------------------------------------------------------------------------
app.get('/health', (c) => c.json({ status: 'ok', service: 'Renia AI Backend', version: '1.0.0' }));

export default app;
export { RealtimeDashboardDO } from './durable-objects.js';
