"""
GrokDent FL — Database Seeding Script
Populates the SQLite or PostgreSQL database with realistic sample Florida dental clinic data:
Sunshine Smiles Dental clinic profile, admin user, 5 patients with AES-encrypted PII,
10 appointments (historical & upcoming), 20 call logs, and 30+ FAQ knowledge base items.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta, timezone
import bcrypt

# Adjust python path to include project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import engine, Base, SessionLocal
from backend.models.clinic import Clinic
from backend.models.user import User
from backend.models.patient import Patient
from backend.models.appointment import Appointment
from backend.models.call_log import CallLog
from backend.models.knowledge_base import KnowledgeBase
from backend.models.insurance import Insurance
from backend.services.encryption_service import encryption_service
from backend.utils.florida_data import (
    SAMPLE_CLINIC_DATA,
    FL_INSURANCE_PROVIDERS,
    SAMPLE_KNOWLEDGE_BASE,
    FL_DENTAL_SERVICES
)

# Use bcrypt directly (compatible with bcrypt >= 5.0)

def seed_database():
    logger = SessionLocal()
    print("Starting database seeding process...")
    
    # 1. Ensure tables exist
    print("Recreating database schema...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Check if clinic already exists
    existing_clinic = logger.query(Clinic).filter(Clinic.slug == SAMPLE_CLINIC_DATA["slug"]).first()
    if existing_clinic:
        print("Sunshine Smiles Dental clinic already seeded. Skipping clinic and admin seeding...")
        clinic = existing_clinic
    else:
        # Create clinic
        print("Creating Sunshine Smiles Dental clinic...")
        clinic = Clinic(
            name=SAMPLE_CLINIC_DATA["name"],
            slug=SAMPLE_CLINIC_DATA["slug"],
            phone=SAMPLE_CLINIC_DATA["phone"],
            email=SAMPLE_CLINIC_DATA["email"],
            address=SAMPLE_CLINIC_DATA["address"],
            city=SAMPLE_CLINIC_DATA["city"],
            state=SAMPLE_CLINIC_DATA["state"],
            zip_code=SAMPLE_CLINIC_DATA["zip_code"],
            timezone=SAMPLE_CLINIC_DATA["timezone"],
            services=SAMPLE_CLINIC_DATA["services"],
            hours=SAMPLE_CLINIC_DATA["hours"],
            insurance_accepted=SAMPLE_CLINIC_DATA["insurance_accepted"],
            emergency_contact_name=SAMPLE_CLINIC_DATA["emergency_contact_name"],
            emergency_contact_phone=SAMPLE_CLINIC_DATA["emergency_contact_phone"],
            grok_voice_id=SAMPLE_CLINIC_DATA["grok_voice_id"],
            twilio_phone_number=SAMPLE_CLINIC_DATA["twilio_phone_number"],
            subscription_plan=SAMPLE_CLINIC_DATA["subscription_plan"],
            subscription_status=SAMPLE_CLINIC_DATA["subscription_status"],
            policies=SAMPLE_CLINIC_DATA["policies"],
            welcome_message=SAMPLE_CLINIC_DATA["welcome_message"],
            spanish_enabled=SAMPLE_CLINIC_DATA["spanish_enabled"],
            xai_key=SAMPLE_CLINIC_DATA.get("xai_key", ""),
            is_active=True
        )
        logger.add(clinic)
        logger.flush()  # get clinic.id
        
        # Create admin user
        print("Creating administrator user...")
        admin_user = User(
            clinic_id=clinic.id,
            email="admin@sunshinesmiles.com",
            hashed_password=bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
            full_name="Dr. Priya Patel",
            role="admin",
            is_active=True
        )
        logger.add(admin_user)
        logger.flush()

    # 3. Seed Insurance Providers
    print("Checking insurance providers...")
    if logger.query(Insurance).count() == 0:
        print("Seeding Florida dental insurance providers...")
        for ins_data in FL_INSURANCE_PROVIDERS:
            ins = Insurance(
                name=ins_data["name"],
                type=ins_data["type"],
                florida_specific=ins_data["florida_specific"],
                phone=ins_data["phone"],
                website=ins_data["website"],
                is_active=True
            )
            logger.add(ins)
        logger.flush()

    # 4. Seed Clinic Knowledge Base
    print("Checking knowledge base...")
    if logger.query(KnowledgeBase).filter(KnowledgeBase.clinic_id == clinic.id).count() == 0:
        print("Seeding Sunshine Smiles Dental FAQ knowledge base...")
        for kb_item in SAMPLE_KNOWLEDGE_BASE:
            entry = KnowledgeBase(
                clinic_id=clinic.id,
                category=kb_item["category"],
                question=kb_item["question"],
                answer=kb_item["answer"],
                answer_spanish=kb_item.get("answer_spanish"),
                priority=kb_item.get("priority", 0),
                is_active=True
            )
            logger.add(entry)
        logger.flush()

    # 5. Seed Patients with HIPAA-compliant encrypted fields
    print("Checking patient list...")
    patients_list = logger.query(Patient).filter(Patient.clinic_id == clinic.id).all()
    if len(patients_list) == 0:
        print("Seeding sample patient database...")
        patients_to_seed = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "(407) 555-0123",
                "email": "john.doe@gmail.com",
                "dob": "1985-05-15",
                "insurance_provider": "Delta Dental of Florida",
                "insurance_id": "DD9876543",
                "preferred_language": "en",
                "notes": "Patient suffers from slight dental anxiety. Prefers morning appointments."
            },
            {
                "first_name": "Maria",
                "last_name": "Rodriguez",
                "phone": "(305) 555-0456",
                "email": "maria.rodriguez@yahoo.com",
                "dob": "1990-09-20",
                "insurance_provider": "MCNA Dental (Florida Medicaid)",
                "insurance_id": "MED-MCNA-8812",
                "preferred_language": "es",
                "notes": "Prefiere hablar en español. Tiene dos niños pequeños."
            },
            {
                "first_name": "Robert",
                "last_name": "Smith",
                "phone": "(813) 555-0789",
                "email": "robert.smith@outlook.com",
                "dob": "1972-11-08",
                "insurance_provider": "Self-Pay (No Insurance)",
                "insurance_id": None,
                "preferred_language": "en",
                "notes": "Interested in joining our Dental Membership plan. Needs filling quote."
            },
            {
                "first_name": "Emily",
                "last_name": "Davis",
                "phone": "(954) 555-0321",
                "email": "emily.davis@gmail.com",
                "dob": "2005-02-14",
                "insurance_provider": "Guardian Dental",
                "insurance_id": "GD-55431",
                "preferred_language": "en",
                "notes": "High school student. Mother handles billing."
            },
            {
                "first_name": "Carlos",
                "last_name": "Gomez",
                "phone": "(305) 555-0987",
                "email": "carlos.gomez@gmail.com",
                "dob": "1963-07-22",
                "insurance_provider": "Humana Dental (Florida DHMO)",
                "insurance_id": "HUM-DHMO-9910",
                "preferred_language": "es",
                "notes": "Has sensitive teeth. Needs deep cleaning next."
            }
        ]
        
        patients_list = []
        for p_data in patients_to_seed:
            patient = Patient(
                clinic_id=clinic.id,
                first_name=p_data["first_name"],
                last_name=p_data["last_name"],
                phone_encrypted=encryption_service.encrypt(p_data["phone"]),
                email_encrypted=encryption_service.encrypt(p_data["email"]),
                dob_encrypted=encryption_service.encrypt(p_data["dob"]),
                insurance_provider=p_data["insurance_provider"],
                insurance_id_encrypted=encryption_service.encrypt(p_data["insurance_id"]) if p_data["insurance_id"] else None,
                preferred_language=p_data["preferred_language"],
                notes_encrypted=encryption_service.encrypt(p_data["notes"]) if p_data["notes"] else None
            )
            logger.add(patient)
            patients_list.append(patient)
        logger.flush()

    # 6. Seed Appointments (upcoming & historical)
    print("Checking appointments...")
    if logger.query(Appointment).filter(Appointment.clinic_id == clinic.id).count() == 0:
        print("Seeding sample appointments timeline...")
        base_time = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0)
        
        appointments_to_seed = [
            {
                "patient_idx": 0,  # John Doe
                "offset_days": 2,  # 2 days from now
                "hour": 10,
                "duration": 60,
                "service": "New Patient Exam",
                "status": "confirmed",
                "notes": "First exam, full mouth x-rays scheduled.",
                "created_via": "web_dashboard"
            },
            {
                "patient_idx": 1,  # Maria Rodriguez
                "offset_days": 3,  # 3 days from now
                "hour": 14,
                "duration": 60,
                "service": "Deep Cleaning (per quad)",
                "status": "scheduled",
                "notes": "Medicaid verification complete. Patient requested Spanish speaker.",
                "created_via": "ai_voice"
            },
            {
                "patient_idx": 2,  # Robert Smith
                "offset_days": 4,  # 4 days from now
                "hour": 9,
                "duration": 45,
                "service": "Composite Filling (1 surface)",
                "status": "scheduled",
                "notes": "Patient self-pay. $195 quote confirmed.",
                "created_via": "ai_voice"
            },
            {
                "patient_idx": 3,  # Emily Davis
                "offset_days": 5,  # 5 days from now
                "hour": 15,
                "duration": 60,
                "service": "Teeth Whitening",
                "status": "confirmed",
                "notes": "Prom prep. Professional in-office whitening.",
                "created_via": "web_dashboard"
            },
            {
                "patient_idx": 4,  # Carlos Gomez
                "offset_days": -4,  # 4 days ago
                "hour": 11,
                "duration": 45,
                "service": "Adult Cleaning",
                "status": "completed",
                "notes": "Routine recall cleaning completed.",
                "created_via": "manual"
            },
            {
                "patient_idx": 0,  # John Doe
                "offset_days": -12,  # 12 days ago
                "hour": 9,
                "duration": 30,
                "service": "Emergency Exam",
                "status": "completed",
                "notes": "Chipped tooth exam completed. Scheduled for crown next week.",
                "created_via": "ai_voice"
            }
        ]
        
        for appt_data in appointments_to_seed:
            patient = patients_list[appt_data["patient_idx"]]
            target_date = base_time + timedelta(days=appt_data["offset_days"])
            appt_time = target_date.replace(hour=appt_data["hour"], minute=0, second=0)
            
            appt = Appointment(
                clinic_id=clinic.id,
                patient_id=patient.id,
                appointment_datetime=appt_time,
                duration_minutes=appt_data["duration"],
                service_type=appt_data["service"],
                status=appt_data["status"],
                notes=appt_data["notes"],
                created_via=appt_data["created_via"]
            )
            logger.add(appt)
        logger.flush()

    # 7. Seed Call Logs representing rich real-world dental clinic operations
    print("Checking call history...")
    if logger.query(CallLog).filter(CallLog.clinic_id == clinic.id).count() == 0:
        print("Seeding mock call history with transcripts and sentiment analysis...")
        
        # Helper logs data
        call_scenarios = [
            {
                "patient_idx": 0,  # John Doe
                "direction": "inbound",
                "phone": "(407) 555-0123",
                "duration": 182,
                "status": "completed",
                "sentiment": "positive",
                "language": "en",
                "actions": ["book_appointment", "verify_insurance"],
                "summary": "Patient John Doe booked a new patient comprehensive dental exam. Insurance benefits verified successfully.",
                "transcript": (
                    "AI: Thank you for calling Sunshine Smiles Dental in Orlando! I'm your AI dental assistant. This call may be recorded. How can I help you today?\n"
                    "PATIENT: Hi, I'm new to the area and need to schedule a new patient exam.\n"
                    "AI: Welcome to Orlando! We'd love to help you. Do you have dental insurance?\n"
                    "PATIENT: Yes, I have Delta Dental PPO.\n"
                    "AI: Excellent, we accept Delta Dental! I can schedule that new patient exam for you. It typically takes about an hour. Would next Monday at 10 AM work for you?\n"
                    "PATIENT: Yes, that is perfect!\n"
                    "AI: Great. I have booked your appointment for next Monday, at 10:00 AM. I will send you a confirmation text. Have a wonderful day!"
                ),
                "is_emergency": False,
                "ago_days": 1
            },
            {
                "patient_idx": 1,  # Maria Rodriguez
                "direction": "inbound",
                "phone": "(305) 555-0456",
                "duration": 210,
                "status": "completed",
                "sentiment": "positive",
                "language": "es",
                "actions": ["book_appointment"],
                "summary": "Reserva de limpieza profunda en español para María Rodríguez. Confirmación enviada.",
                "transcript": (
                    "AI: Gracias por llamar a Sunshine Smiles Dental. Soy su asistente de inteligencia artificial. ¿En qué puedo ayudarle hoy?\n"
                    "PATIENT: Hola, hablo español. ¿Tienen citas para limpieza?\n"
                    "AI: ¡Hola! Sí, hablo español y con gusto le ayudo. ¿Es usted un paciente existente?\n"
                    "PATIENT: Sí, soy María Rodríguez.\n"
                    "AI: Hola María. Veo que el doctor recomendó una limpieza profunda para usted. ¿Le gustaría reservar para el próximo martes a las 2 de la tarde?\n"
                    "PATIENT: Sí, ese horario está muy bien para mí.\n"
                    "AI: Perfecto. Su cita está reservada para el martes a las 2 PM. Le envié un mensaje de texto de confirmación."
                ),
                "is_emergency": False,
                "ago_days": 2
            },
            {
                "patient_idx": 2,  # Robert Smith
                "direction": "inbound",
                "phone": "(813) 555-0789",
                "duration": 140,
                "status": "completed",
                "sentiment": "neutral",
                "language": "en",
                "actions": ["answer_faq", "book_appointment"],
                "summary": "Uninsured patient inquired about filling prices. Booked a composite filling appointment. $195 estimate provided.",
                "transcript": (
                    "AI: Thank you for calling Sunshine Smiles. How can I help you today?\n"
                    "PATIENT: Hi, I don't have insurance. How much does a composite filling cost?\n"
                    "AI: No problem at all! For self-pay patients, a composite tooth-colored filling starts at $195. We also offer a dental membership plan for $299 a year which gives you 15% off all treatments.\n"
                    "PATIENT: Okay, that's reasonable. Can I book an appointment to get a filling done next Wednesday?\n"
                    "AI: Sure! I have Wednesday morning available at 9:00 AM. Would that work?\n"
                    "PATIENT: Yes, lock that in please."
                ),
                "is_emergency": False,
                "ago_days": 3
            },
            {
                "patient_idx": None,
                "direction": "inbound",
                "phone": "(407) 555-9000",
                "duration": 85,
                "status": "completed",
                "sentiment": "neutral",
                "language": "en",
                "actions": ["answer_faq"],
                "summary": "Anonymous caller asked about office location, parking options, and hours of operation.",
                "transcript": (
                    "AI: Thank you for calling Sunshine Smiles Dental. How can I help you?\n"
                    "PATIENT: Hey, where are you guys located? And do you have parking?\n"
                    "AI: We are located at 1234 Orange Blossom Trail, Suite 200, Orlando. We are right across from the Orlando Regional Medical Center, and free parking is available in front of the building!\n"
                    "PATIENT: Oh perfect! What are your hours today?\n"
                    "AI: We are open today until 5:00 PM.\n"
                    "PATIENT: Awesome, thanks!"
                ),
                "is_emergency": False,
                "ago_days": 4
            },
            {
                "patient_idx": 4,  # Carlos Gomez
                "direction": "inbound",
                "phone": "(305) 555-0987",
                "duration": 115,
                "status": "completed",
                "sentiment": "negative",
                "language": "es",
                "actions": ["emergency_transfer"],
                "summary": "Llamada de dolor dental severo en español. Identificada como urgencia clínica. Transferencia exitosa a la Dra. Patel.",
                "transcript": (
                    "AI: Gracias por llamar a Sunshine Smiles. ¿Cómo puedo ayudarle hoy?\n"
                    "PATIENT: Hola, me duele muchísimo una muela, no puedo dormir del dolor. Ayúdeme por favor.\n"
                    "AI: Siento mucho que tenga ese dolor. Esto califica como una emergencia dental. ¿Está experimentando alguna hinchazón o sangrado?\n"
                    "PATIENT: Sí, mi mejilla derecha está un poco hinchada.\n"
                    "AI: Entendido. Voy a transferir su llamada de inmediato con nuestra dentista de guardia, la Dra. Priya Patel, a su teléfono de emergencia para que le atienda de inmediato. Por favor manténgase en la línea..."
                ),
                "is_emergency": True,
                "ago_days": 5
            }
        ]
        
        # Add some historical random logs to reach 20 call logs
        for i in range(15):
            call_scenarios.append({
                "patient_idx": i % 5,
                "direction": "inbound" if i % 3 != 0 else "outbound",
                "phone": f"(407) 555-010{i%5}",
                "duration": 45 + (i * 12),
                "status": "completed" if i % 8 != 0 else "missed",
                "sentiment": "positive" if i % 2 == 0 else "neutral",
                "language": "en" if i % 4 != 0 else "es",
                "actions": ["answer_faq"] if i % 3 != 0 else ["reschedule_appointment"],
                "summary": f"Routine dental clinic operational call log #{i+6}. Patient called to verify details.",
                "transcript": "AI: Thank you for calling Sunshine Smiles. How can I assist you?\nPATIENT: Just calling to verify my appointment time.\nAI: Your appointment is verified successfully.",
                "is_emergency": False,
                "ago_days": 6 + i
            })
            
        for c_sec in call_scenarios:
            patient_id = None
            if c_sec["patient_idx"] is not None:
                patient_id = patients_list[c_sec["patient_idx"]].id
                
            log = CallLog(
                clinic_id=clinic.id,
                patient_id=patient_id,
                twilio_call_sid=f"CA{uuid.uuid4().hex[:30]}",
                direction=c_sec["direction"],
                caller_number=c_sec["phone"],
                called_number=clinic.twilio_phone_number or "+14075550100",
                duration_seconds=c_sec["duration"],
                status=c_sec["status"],
                transcript_encrypted=encryption_service.encrypt(c_sec["transcript"]),
                summary=c_sec["summary"],
                sentiment=c_sec["sentiment"],
                language=c_sec["language"],
                actions_taken=c_sec["actions"],
                is_emergency=c_sec["is_emergency"],
                created_at=datetime.now(timezone.utc) - timedelta(days=c_sec["ago_days"])
            )
            logger.add(log)
        logger.flush()

    logger.commit()
    print("Database seeding completed successfully!")
    print(f"Default Clinic: {SAMPLE_CLINIC_DATA['name']} ({SAMPLE_CLINIC_DATA['city']}, FL)")
    print("Default Admin User: admin@sunshinesmiles.com / password123")
    print(f"Seeded: {logger.query(Patient).count()} Patients, {logger.query(Appointment).count()} Appointments, {logger.query(CallLog).count()} Call Logs.")
    logger.close()

if __name__ == "__main__":
    seed_database()
