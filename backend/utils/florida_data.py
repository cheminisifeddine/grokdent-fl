"""
GrokDent FL — Florida-Specific Reference Data
Cities, insurance providers, dental services, sample clinic config,
and a comprehensive sample knowledge base for seeding new clinics.
"""

from typing import Dict, List


# ---------------------------------------------------------------------------
# Florida cities served by GrokDent FL
# ---------------------------------------------------------------------------
FL_CITIES: List[Dict] = [
    {"name": "Miami", "area_code": "305", "county": "Miami-Dade"},
    {"name": "Orlando", "area_code": "407", "county": "Orange"},
    {"name": "Tampa", "area_code": "813", "county": "Hillsborough"},
    {"name": "Jacksonville", "area_code": "904", "county": "Duval"},
    {"name": "Fort Lauderdale", "area_code": "954", "county": "Broward"},
    {"name": "St. Petersburg", "area_code": "727", "county": "Pinellas"},
    {"name": "Naples", "area_code": "239", "county": "Collier"},
    {"name": "Sarasota", "area_code": "941", "county": "Sarasota"},
    {"name": "Gainesville", "area_code": "352", "county": "Alachua"},
    {"name": "Tallahassee", "area_code": "850", "county": "Leon"},
]


# ---------------------------------------------------------------------------
# Florida dental insurance providers
# ---------------------------------------------------------------------------
FL_INSURANCE_PROVIDERS: List[Dict] = [
    {
        "name": "Delta Dental of Florida",
        "type": "PPO",
        "phone": "(800) 521-2651",
        "website": "https://www.deltadentalins.com",
        "florida_specific": False,
    },
    {
        "name": "Humana Dental (Florida DHMO)",
        "type": "DHMO",
        "phone": "(800) 233-4013",
        "website": "https://www.humana.com/dental-insurance",
        "florida_specific": False,
    },
    {
        "name": "MCNA Dental (Florida Medicaid)",
        "type": "Medicaid",
        "phone": "(855) 776-6262",
        "website": "https://www.mcnafl.net",
        "florida_specific": True,
    },
    {
        "name": "Guardian Dental",
        "type": "PPO",
        "phone": "(888) 482-7342",
        "website": "https://www.guardiandirect.com",
        "florida_specific": False,
    },
    {
        "name": "Cigna Dental PPO",
        "type": "PPO",
        "phone": "(800) 244-6224",
        "website": "https://www.cigna.com/dental",
        "florida_specific": False,
    },
    {
        "name": "MetLife Preferred Dentist Program",
        "type": "PPO",
        "phone": "(800) 275-4638",
        "website": "https://www.metlife.com/dental",
        "florida_specific": False,
    },
    {
        "name": "Aetna Dental",
        "type": "PPO",
        "phone": "(877) 238-6200",
        "website": "https://www.aetna.com/dental",
        "florida_specific": False,
    },
    {
        "name": "DentaQuest (Florida Healthy Kids)",
        "type": "Medicaid",
        "phone": "(888) 830-5620",
        "website": "https://www.dentaquest.com",
        "florida_specific": True,
    },
]


# ---------------------------------------------------------------------------
# Dental services with ADA codes, pricing, and durations
# ---------------------------------------------------------------------------
FL_DENTAL_SERVICES: List[Dict] = [
    {"name": "New Patient Exam", "code": "D0150", "avg_price": 95.00, "duration_minutes": 60, "category": "diagnostic"},
    {"name": "Periodic Exam", "code": "D0120", "avg_price": 65.00, "duration_minutes": 30, "category": "diagnostic"},
    {"name": "Full Mouth X-rays", "code": "D0210", "avg_price": 150.00, "duration_minutes": 30, "category": "diagnostic"},
    {"name": "Bitewing X-rays", "code": "D0274", "avg_price": 65.00, "duration_minutes": 15, "category": "diagnostic"},
    {"name": "Adult Cleaning", "code": "D1110", "avg_price": 125.00, "duration_minutes": 45, "category": "preventive"},
    {"name": "Child Cleaning", "code": "D1120", "avg_price": 85.00, "duration_minutes": 30, "category": "preventive"},
    {"name": "Deep Cleaning (per quad)", "code": "D4341", "avg_price": 275.00, "duration_minutes": 60, "category": "periodontics"},
    {"name": "Fluoride Treatment", "code": "D1206", "avg_price": 40.00, "duration_minutes": 15, "category": "preventive"},
    {"name": "Dental Sealant (per tooth)", "code": "D1351", "avg_price": 55.00, "duration_minutes": 15, "category": "preventive"},
    {"name": "Composite Filling (1 surface)", "code": "D2330", "avg_price": 195.00, "duration_minutes": 30, "category": "restorative"},
    {"name": "Composite Filling (2 surfaces)", "code": "D2331", "avg_price": 250.00, "duration_minutes": 45, "category": "restorative"},
    {"name": "Amalgam Filling (1 surface)", "code": "D2140", "avg_price": 175.00, "duration_minutes": 30, "category": "restorative"},
    {"name": "Porcelain Crown", "code": "D2740", "avg_price": 1200.00, "duration_minutes": 90, "category": "restorative"},
    {"name": "Root Canal — Anterior", "code": "D3310", "avg_price": 850.00, "duration_minutes": 60, "category": "endodontics"},
    {"name": "Root Canal — Molar", "code": "D3330", "avg_price": 1200.00, "duration_minutes": 90, "category": "endodontics"},
    {"name": "Simple Extraction", "code": "D7140", "avg_price": 225.00, "duration_minutes": 30, "category": "oral_surgery"},
    {"name": "Surgical Extraction", "code": "D7210", "avg_price": 350.00, "duration_minutes": 45, "category": "oral_surgery"},
    {"name": "Dental Implant", "code": "D6010", "avg_price": 2500.00, "duration_minutes": 120, "category": "implantology"},
    {"name": "Teeth Whitening", "code": "D9972", "avg_price": 350.00, "duration_minutes": 60, "category": "cosmetic"},
    {"name": "Porcelain Veneer", "code": "D2962", "avg_price": 1100.00, "duration_minutes": 60, "category": "cosmetic"},
    {"name": "Complete Denture (upper)", "code": "D5110", "avg_price": 1800.00, "duration_minutes": 60, "category": "prosthodontics"},
    {"name": "Night Guard", "code": "D9944", "avg_price": 450.00, "duration_minutes": 30, "category": "preventive"},
    {"name": "Emergency Exam", "code": "D0140", "avg_price": 85.00, "duration_minutes": 30, "category": "emergency"},
    {"name": "Palliative Treatment", "code": "D9110", "avg_price": 150.00, "duration_minutes": 30, "category": "emergency"},
]


# ---------------------------------------------------------------------------
# Sample clinic configuration for seeding / demo
# ---------------------------------------------------------------------------
SAMPLE_CLINIC_DATA: Dict = {
    "name": "Sunshine Smiles Dental",
    "slug": "sunshine-smiles-dental",
    "phone": "(407) 555-0100",
    "email": "info@sunshinesmilesdental.com",
    "address": "1234 Orange Blossom Trail, Suite 200",
    "city": "Orlando",
    "state": "FL",
    "zip_code": "32801",
    "timezone": "US/Eastern",
    "services": [
        "General Dentistry", "Cosmetic Dentistry", "Orthodontics",
        "Dental Implants", "Teeth Whitening", "Root Canal Therapy",
        "Crowns & Bridges", "Pediatric Dentistry", "Emergency Dental Care",
        "Periodontics", "Oral Surgery", "Dentures & Partials",
    ],
    "hours": {
        "monday": {"open": "08:00", "close": "17:00"},
        "tuesday": {"open": "08:00", "close": "17:00"},
        "wednesday": {"open": "08:00", "close": "17:00"},
        "thursday": {"open": "08:00", "close": "18:00"},
        "friday": {"open": "08:00", "close": "16:00"},
        "saturday": {"open": "09:00", "close": "14:00"},
    },
    "insurance_accepted": [
        "Delta Dental", "Cigna", "Aetna", "MetLife", "Guardian",
        "Humana", "MCNA Dental (Medicaid)", "United Healthcare Dental",
    ],
    "emergency_contact_name": "Dr. Priya Patel",
    "emergency_contact_phone": "(407) 555-0199",
    "grok_voice_id": "Ash",
    "twilio_phone_number": "+14075550100",
    "subscription_plan": "professional",
    "subscription_status": "active",
    "policies": (
        "Cancellation Policy: Please provide at least 24 hours notice for cancellations. "
        "Late cancellations or no-shows may incur a $50 fee.\n\n"
        "Payment Policy: Payment is due at the time of service. We accept cash, credit cards, "
        "and CareCredit financing. We file insurance on your behalf.\n\n"
        "Late Arrival: If you arrive more than 15 minutes late, we may need to reschedule "
        "your appointment."
    ),
    "welcome_message": (
        "Thank you for calling Sunshine Smiles Dental in Orlando! "
        "I'm your AI dental assistant powered by Grok. "
        "I can help you schedule appointments, answer questions about our services, "
        "check insurance information, and more. How can I help you today?"
    ),
    "spanish_enabled": True,
    "is_active": True,
}


# ---------------------------------------------------------------------------
# Comprehensive sample knowledge base  (30+ Q&A entries)
# ---------------------------------------------------------------------------
SAMPLE_KNOWLEDGE_BASE: List[Dict] = [
    # === HOURS ===
    {
        "category": "hours",
        "question": "What are your office hours?",
        "answer": (
            "We're open Monday through Wednesday from 8 AM to 5 PM, "
            "Thursday from 8 AM to 6 PM (our extended-hours day), "
            "Friday from 8 AM to 4 PM, and Saturday from 9 AM to 2 PM. "
            "We're closed on Sundays."
        ),
        "answer_spanish": (
            "Estamos abiertos de lunes a miércoles de 8 AM a 5 PM, "
            "jueves de 8 AM a 6 PM (nuestro día de horario extendido), "
            "viernes de 8 AM a 4 PM, y sábados de 9 AM a 2 PM. "
            "Los domingos estamos cerrados."
        ),
        "priority": 10,
    },
    {
        "category": "hours",
        "question": "Are you open on weekends?",
        "answer": "Yes! We're open on Saturdays from 9 AM to 2 PM. We're closed on Sundays.",
        "answer_spanish": "¡Sí! Abrimos los sábados de 9 AM a 2 PM. Los domingos estamos cerrados.",
        "priority": 9,
    },
    {
        "category": "hours",
        "question": "Do you have evening appointments?",
        "answer": "Yes, on Thursdays we have extended hours until 6 PM. Our last appointment slot is at 5:30 PM.",
        "answer_spanish": "Sí, los jueves tenemos horario extendido hasta las 6 PM. Nuestra última cita disponible es a las 5:30 PM.",
        "priority": 8,
    },

    # === LOCATION ===
    {
        "category": "location",
        "question": "Where are you located?",
        "answer": (
            "We're located at 1234 Orange Blossom Trail, Suite 200, Orlando, FL 32801. "
            "We're near the intersection of Orange Blossom Trail and Colonial Drive, "
            "across from the Orlando Regional Medical Center. Free parking is available in front of the building."
        ),
        "answer_spanish": (
            "Estamos ubicados en 1234 Orange Blossom Trail, Suite 200, Orlando, FL 32801. "
            "Estamos cerca de la intersección de Orange Blossom Trail y Colonial Drive, "
            "frente al Orlando Regional Medical Center. Hay estacionamiento gratuito frente al edificio."
        ),
        "priority": 10,
    },
    {
        "category": "location",
        "question": "Do you have parking?",
        "answer": "Yes, we have free parking in front of our building. There are also accessible parking spots available.",
        "answer_spanish": "Sí, tenemos estacionamiento gratuito frente a nuestro edificio. También hay espacios de estacionamiento accesibles.",
        "priority": 5,
    },

    # === SERVICES ===
    {
        "category": "services",
        "question": "What services do you offer?",
        "answer": (
            "We offer a full range of dental services including general dentistry (exams, cleanings, fillings), "
            "cosmetic dentistry (whitening, veneers, bonding), restorative dentistry (crowns, bridges, dentures), "
            "orthodontics, dental implants, root canal therapy, oral surgery, periodontics (gum treatment), "
            "pediatric dentistry, and emergency dental care."
        ),
        "answer_spanish": (
            "Ofrecemos una gama completa de servicios dentales incluyendo odontología general (exámenes, limpiezas, rellenos), "
            "odontología cosmética (blanqueamiento, carillas, bonding), odontología restaurativa (coronas, puentes, dentaduras), "
            "ortodoncia, implantes dentales, endodoncia, cirugía oral, periodoncia (tratamiento de encías), "
            "odontología pediátrica y atención dental de emergencia."
        ),
        "priority": 10,
    },
    {
        "category": "services",
        "question": "Do you do teeth whitening?",
        "answer": (
            "Yes! We offer both in-office professional teeth whitening ($350) and custom take-home whitening trays ($250). "
            "In-office whitening takes about one hour and results are immediate. Take-home trays are custom-made for "
            "your teeth and you wear them for 30 minutes a day for about two weeks."
        ),
        "answer_spanish": (
            "¡Sí! Ofrecemos blanqueamiento dental profesional en oficina ($350) y bandejas de blanqueamiento para llevar a casa ($250). "
            "El blanqueamiento en oficina toma aproximadamente una hora y los resultados son inmediatos."
        ),
        "priority": 7,
    },
    {
        "category": "services",
        "question": "Do you do dental implants?",
        "answer": (
            "Yes, we provide dental implant services. A single implant starts at around $2,500 for the implant post, "
            "plus $1,800 for the implant crown. We offer free implant consultations. "
            "Dr. Patel has over 15 years of implant experience."
        ),
        "answer_spanish": (
            "Sí, ofrecemos servicios de implantes dentales. Un implante individual comienza alrededor de $2,500 "
            "para el poste del implante, más $1,800 para la corona. Ofrecemos consultas gratuitas de implantes."
        ),
        "priority": 7,
    },
    {
        "category": "services",
        "question": "Do you treat children?",
        "answer": (
            "Yes! We welcome patients of all ages, including children. We recommend bringing your child for their "
            "first dental visit by age 1 or when their first tooth comes in. Our team is great with kids and "
            "we make the experience fun and comfortable."
        ),
        "answer_spanish": (
            "¡Sí! Recibimos pacientes de todas las edades, incluyendo niños. Recomendamos traer a su hijo "
            "para su primera visita dental antes del primer año o cuando aparezca su primer diente."
        ),
        "priority": 6,
    },
    {
        "category": "services",
        "question": "Do you offer Invisalign or braces?",
        "answer": (
            "Yes, we offer both traditional braces and Invisalign clear aligners. Invisalign treatment starts "
            "at around $4,500. We offer free orthodontic consultations to determine the best option for you. "
            "We also have flexible payment plans available."
        ),
        "answer_spanish": (
            "Sí, ofrecemos brackets tradicionales e Invisalign. El tratamiento con Invisalign comienza "
            "alrededor de $4,500. Ofrecemos consultas ortodónticas gratuitas."
        ),
        "priority": 6,
    },
    {
        "category": "services",
        "question": "Do you do emergency dental work?",
        "answer": (
            "Absolutely! We see dental emergencies the same day whenever possible. "
            "If you're experiencing severe pain, a knocked-out tooth, heavy bleeding, or facial swelling, "
            "call us immediately. After hours, our on-call dentist Dr. Patel can be reached at (407) 555-0199."
        ),
        "answer_spanish": (
            "¡Por supuesto! Atendemos emergencias dentales el mismo día siempre que sea posible. "
            "Si experimenta dolor severo, un diente caído, sangrado abundante o hinchazón facial, "
            "llámenos inmediatamente. Fuera de horario, puede comunicarse con la Dra. Patel al (407) 555-0199."
        ),
        "priority": 10,
    },

    # === INSURANCE ===
    {
        "category": "insurance",
        "question": "What insurance do you accept?",
        "answer": (
            "We accept most major dental insurance plans including Delta Dental, Cigna, Aetna, MetLife, "
            "Guardian, Humana, United Healthcare Dental, and MCNA Dental (Florida Medicaid). "
            "We also accept patients without insurance and offer affordable self-pay rates and payment plans."
        ),
        "answer_spanish": (
            "Aceptamos la mayoría de los planes de seguro dental incluyendo Delta Dental, Cigna, Aetna, MetLife, "
            "Guardian, Humana, United Healthcare Dental y MCNA Dental (Medicaid de Florida). "
            "También aceptamos pacientes sin seguro y ofrecemos tarifas accesibles y planes de pago."
        ),
        "priority": 10,
    },
    {
        "category": "insurance",
        "question": "Do you accept Medicaid?",
        "answer": (
            "Yes, we accept Florida Medicaid dental coverage through MCNA Dental. "
            "We see both children and adults covered under Medicaid. "
            "Please bring your Medicaid card to your appointment."
        ),
        "answer_spanish": (
            "Sí, aceptamos la cobertura dental de Medicaid de Florida a través de MCNA Dental. "
            "Atendemos tanto a niños como a adultos cubiertos por Medicaid."
        ),
        "priority": 9,
    },
    {
        "category": "insurance",
        "question": "Do you accept patients without insurance?",
        "answer": (
            "Yes! We welcome patients without insurance. We offer competitive self-pay rates and a "
            "membership plan that includes 2 cleanings, 2 exams, and all necessary x-rays per year for $299. "
            "Members also receive 15% off all other treatments. We accept CareCredit for financing."
        ),
        "answer_spanish": (
            "¡Sí! Recibimos pacientes sin seguro. Ofrecemos tarifas competitivas y un plan de membresía "
            "que incluye 2 limpiezas, 2 exámenes y todas las radiografías necesarias por año por $299. "
            "Los miembros también reciben 15% de descuento en todos los demás tratamientos."
        ),
        "priority": 9,
    },
    {
        "category": "insurance",
        "question": "Can you verify my insurance before my appointment?",
        "answer": (
            "Yes! We verify insurance benefits before your appointment so you know exactly what's covered. "
            "Just provide your insurance company name, member ID, and date of birth when you schedule, "
            "and we'll take care of the rest."
        ),
        "answer_spanish": (
            "¡Sí! Verificamos los beneficios de su seguro antes de su cita para que sepa exactamente qué está cubierto. "
            "Solo proporcione el nombre de su compañía de seguros, su número de miembro y fecha de nacimiento."
        ),
        "priority": 7,
    },

    # === PRICING ===
    {
        "category": "pricing",
        "question": "How much does a cleaning cost?",
        "answer": (
            "A regular adult cleaning (prophylaxis) is $125 without insurance. "
            "With most PPO insurance plans, preventive cleanings are covered at 100%, meaning no out-of-pocket cost. "
            "Deep cleanings (scaling & root planing) are $275 per quadrant."
        ),
        "answer_spanish": (
            "Una limpieza dental regular para adultos es $125 sin seguro. "
            "Con la mayoría de los planes PPO, las limpiezas preventivas están cubiertas al 100%."
        ),
        "priority": 8,
    },
    {
        "category": "pricing",
        "question": "How much do fillings cost?",
        "answer": (
            "Composite (tooth-colored) fillings start at $195 for a single surface and $250 for two surfaces. "
            "Amalgam (silver) fillings start at $175. Most insurance plans cover fillings at 80%. "
            "We'll always give you a cost estimate before starting any treatment."
        ),
        "answer_spanish": (
            "Los rellenos de composite (color diente) comienzan en $195 para una superficie y $250 para dos. "
            "Los rellenos de amalgama (plata) comienzan en $175. La mayoría de los seguros cubren rellenos al 80%."
        ),
        "priority": 7,
    },
    {
        "category": "pricing",
        "question": "Do you offer payment plans?",
        "answer": (
            "Yes! We offer several flexible payment options: CareCredit financing (0% interest for 6-12 months "
            "on qualifying purchases), in-house payment plans for treatments over $500, "
            "and our dental membership plan for patients without insurance ($299/year)."
        ),
        "answer_spanish": (
            "¡Sí! Ofrecemos varias opciones de pago flexibles: financiamiento CareCredit "
            "(0% de interés por 6-12 meses en compras elegibles), planes de pago internos "
            "para tratamientos mayores de $500, y nuestro plan de membresía dental ($299/año)."
        ),
        "priority": 8,
    },
    {
        "category": "pricing",
        "question": "How much does a crown cost?",
        "answer": (
            "Porcelain crowns are $1,200 per tooth. With dental insurance, crowns are typically covered at 50% "
            "after your deductible, so your out-of-pocket cost could be around $600. "
            "We offer payment plans for major treatments like crowns."
        ),
        "answer_spanish": (
            "Las coronas de porcelana son $1,200 por diente. Con seguro dental, las coronas generalmente "
            "están cubiertas al 50% después de su deducible."
        ),
        "priority": 6,
    },

    # === POLICIES ===
    {
        "category": "policies",
        "question": "What is your cancellation policy?",
        "answer": (
            "We ask for at least 24 hours notice for cancellations. Late cancellations or no-shows "
            "may incur a $50 fee. We understand emergencies happen, so if something comes up "
            "please call us as soon as possible and we'll do our best to accommodate you."
        ),
        "answer_spanish": (
            "Pedimos al menos 24 horas de anticipación para cancelaciones. Las cancelaciones tardías "
            "o las ausencias pueden incurrir en un cargo de $50. Entendemos que surgen emergencias, "
            "así que llámenos lo antes posible."
        ),
        "priority": 8,
    },
    {
        "category": "policies",
        "question": "What forms of payment do you accept?",
        "answer": (
            "We accept cash, all major credit cards (Visa, MasterCard, American Express, Discover), "
            "debit cards, personal checks, CareCredit, and most dental insurance. "
            "Payment is due at the time of service."
        ),
        "answer_spanish": (
            "Aceptamos efectivo, todas las tarjetas de crédito principales, tarjetas de débito, "
            "cheques personales, CareCredit y la mayoría de los seguros dentales. "
            "El pago se debe al momento del servicio."
        ),
        "priority": 7,
    },
    {
        "category": "policies",
        "question": "Do I need to arrive early for my first visit?",
        "answer": (
            "Yes, please arrive 15 minutes early for your first appointment to complete new patient paperwork. "
            "You can also save time by filling out our forms online before your visit. "
            "Please bring your insurance card, photo ID, and a list of any medications you take."
        ),
        "answer_spanish": (
            "Sí, por favor llegue 15 minutos antes de su primera cita para completar los formularios de nuevo paciente. "
            "Traiga su tarjeta de seguro, identificación con foto y una lista de medicamentos."
        ),
        "priority": 8,
    },

    # === EMERGENCY ===
    {
        "category": "emergency",
        "question": "What should I do if I have a dental emergency?",
        "answer": (
            "Call us immediately at (407) 555-0100! We see dental emergencies the same day whenever possible. "
            "If it's after hours, our on-call dentist Dr. Patel can be reached at (407) 555-0199. "
            "For life-threatening emergencies, call 911 first."
        ),
        "answer_spanish": (
            "¡Llámenos inmediatamente al (407) 555-0100! Atendemos emergencias dentales el mismo día siempre que sea posible. "
            "Fuera de horario, comuníquese con la Dra. Patel al (407) 555-0199. "
            "Para emergencias que amenazan la vida, llame al 911 primero."
        ),
        "priority": 10,
    },
    {
        "category": "emergency",
        "question": "My tooth was knocked out, what should I do?",
        "answer": (
            "This is a time-sensitive emergency! 1) Pick up the tooth by the crown (top), not the root. "
            "2) Gently rinse with milk or saline — don't scrub. "
            "3) Try to place it back in the socket, or put it in a cup of milk. "
            "4) Call us immediately — we need to see you within 30 minutes for the best chance of saving it. "
            "Call (407) 555-0100 now."
        ),
        "answer_spanish": (
            "¡Esta es una emergencia urgente! 1) Recoja el diente por la corona, no por la raíz. "
            "2) Enjuáguelo suavemente con leche o solución salina. "
            "3) Intente colocarlo de nuevo en la encía, o póngalo en un vaso de leche. "
            "4) Llámenos inmediatamente — necesitamos verle dentro de 30 minutos."
        ),
        "priority": 10,
    },
    {
        "category": "emergency",
        "question": "I have severe tooth pain, what should I do?",
        "answer": (
            "I'm sorry you're in pain! Here's what to do right now: "
            "1) Take ibuprofen (Advil) 400-600mg for pain relief. "
            "2) Apply a cold compress to the outside of your cheek. "
            "3) Rinse with warm salt water. "
            "4) Call us to schedule an emergency appointment — we see same-day emergencies. "
            "Call (407) 555-0100."
        ),
        "answer_spanish": (
            "¡Lamento que tenga dolor! Esto es lo que puede hacer ahora: "
            "1) Tome ibuprofeno (Advil) 400-600mg para el dolor. "
            "2) Aplique una compresa fría en la mejilla. "
            "3) Enjuague con agua tibia con sal. "
            "4) Llámenos para una cita de emergencia el mismo día."
        ),
        "priority": 10,
    },

    # === GENERAL ===
    {
        "category": "general",
        "question": "Who are your dentists?",
        "answer": (
            "Our lead dentist is Dr. Priya Patel, DDS, who has over 15 years of experience in general "
            "and cosmetic dentistry. She graduated from the University of Florida College of Dentistry "
            "and is a member of the American Dental Association and the Florida Dental Association. "
            "We also have Dr. Michael Chen, DMD, who specializes in orthodontics and implants."
        ),
        "answer_spanish": (
            "Nuestra dentista principal es la Dra. Priya Patel, DDS, con más de 15 años de experiencia. "
            "Se graduó de la Universidad de Florida y es miembro de la Asociación Dental Americana."
        ),
        "priority": 7,
    },
    {
        "category": "general",
        "question": "Do you speak Spanish?",
        "answer": (
            "¡Sí! Tenemos personal bilingüe que habla español e inglés. "
            "We have bilingual staff who speak both Spanish and English. "
            "You're welcome to communicate in whichever language is most comfortable for you."
        ),
        "answer_spanish": (
            "¡Sí! Tenemos personal bilingüe que habla español e inglés. "
            "Puede comunicarse en el idioma que le sea más cómodo."
        ),
        "priority": 8,
    },
    {
        "category": "general",
        "question": "How do I schedule an appointment?",
        "answer": (
            "You can schedule an appointment by: 1) Calling us at (407) 555-0100, "
            "2) Using our online booking system at our website, or "
            "3) I can help you schedule one right now! Just let me know what service you need "
            "and your preferred date and time."
        ),
        "answer_spanish": (
            "Puede programar una cita: 1) Llamándonos al (407) 555-0100, "
            "2) Usando nuestro sistema de reservas en línea, o "
            "3) ¡Puedo ayudarle a programar una ahora mismo!"
        ),
        "priority": 9,
    },
    {
        "category": "general",
        "question": "Is it safe to visit the dentist?",
        "answer": (
            "Absolutely! Your safety is our top priority. We follow all CDC and ADA infection control guidelines. "
            "We use hospital-grade sterilization equipment, EPA-approved disinfectants, "
            "and maintain the highest standards of cleanliness throughout our office."
        ),
        "answer_spanish": (
            "¡Absolutamente! Su seguridad es nuestra máxima prioridad. Seguimos todas las pautas de "
            "control de infecciones de los CDC y la ADA."
        ),
        "priority": 5,
    },
    {
        "category": "general",
        "question": "Do you offer sedation dentistry?",
        "answer": (
            "Yes! We understand dental anxiety is common. We offer nitrous oxide (laughing gas) "
            "and oral sedation for patients who need extra comfort. Let us know when scheduling "
            "and we'll make sure you're comfortable throughout your visit."
        ),
        "answer_spanish": (
            "¡Sí! Entendemos que la ansiedad dental es común. Ofrecemos óxido nitroso (gas de la risa) "
            "y sedación oral para pacientes que necesitan mayor comodidad."
        ),
        "priority": 6,
    },
    {
        "category": "general",
        "question": "What COVID-19 precautions do you take?",
        "answer": (
            "We take comprehensive safety measures including enhanced sterilization protocols, "
            "air purification systems, pre-appointment health screenings, and follow all "
            "CDC, ADA, and Florida Department of Health guidelines for dental offices."
        ),
        "answer_spanish": (
            "Tomamos medidas de seguridad integrales incluyendo protocolos de esterilización mejorados, "
            "sistemas de purificación de aire y seguimos todas las pautas de los CDC, ADA y el "
            "Departamento de Salud de Florida."
        ),
        "priority": 5,
    },
    {
        "category": "general",
        "question": "How often should I visit the dentist?",
        "answer": (
            "We recommend visiting the dentist every 6 months for a routine exam and cleaning. "
            "Some patients with gum disease or other conditions may need to come in every 3-4 months. "
            "Regular visits help catch problems early when they're easier and less expensive to treat."
        ),
        "answer_spanish": (
            "Recomendamos visitar al dentista cada 6 meses para un examen y limpieza de rutina. "
            "Las visitas regulares ayudan a detectar problemas temprano."
        ),
        "priority": 5,
    },
]
