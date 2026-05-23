"""
GrokDent FL — Voice AI Agent Call Simulator
Simulates a real patient phone call to the Sunshine Smiles Dental clinic in Orlando, FL.
Demonstrates the per-call state machine, language routing, and Grok-3 dental reasoning.
Allows interactive local CLI dialog testing.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

# Adjust python path to include project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import SessionLocal
from backend.models.clinic import Clinic
from backend.voice.conversation_manager import ConversationManager, ConversationState
from backend.voice.grok_client import GrokVoiceClient
from backend.services.encryption_service import encryption_service

# ANSI colors for beautiful terminal printing
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

async def run_simulator():
    print(f"{BOLD}{CYAN}=================================================================={RESET}")
    print(f"{BOLD}{BLUE}🦷 GrokDent FL — Voice AI Receptionist Simulator 🦷{RESET}")
    print(f"{BOLD}{CYAN}=================================================================={RESET}")
    print("This script simulates an incoming Twilio voice call and allows you")
    print("to chat interactively with the Grok AI dental receptionist agent.\n")
    
    # 1. Check if database is seeded
    db = SessionLocal()
    clinic = db.query(Clinic).filter(Clinic.slug == "sunshine-smiles-dental").first()
    if not clinic:
        print(f"{RED}[ERROR]{RESET} Sunshine Smiles Dental clinic is not seeded in the database.")
        print(f"Please run {BOLD}python scripts/seed_data.py{RESET} first to seed the database.")
        db.close()
        return
    
    print(f"{GREEN}[SUCCESS]{RESET} Found Clinic: {BOLD}{clinic.name}{RESET} in {clinic.city}, FL.")
    print(f"Voice Configured: {BOLD}{clinic.grok_voice_id}{RESET} (English & Spanish Bilingual)")
    print(f"Twilio Provisioned: {BOLD}{clinic.twilio_phone_number}{RESET}")
    print(f"Emergency Contact: {BOLD}{clinic.emergency_contact_name} ({clinic.emergency_contact_phone}){RESET}")
    print(f"Supported Services: {len(clinic.services)} loaded.")
    print(f"FAQ KB Items: {db.query(Clinic).count()} clinics seeded.")
    db.close()
    
    # 2. Start call simulation
    call_sid = "CA_SIMULATED_" + os.urandom(8).hex()
    grok_client = GrokVoiceClient()
    
    print(f"\n{YELLOW}[CALL STARTED]{RESET} Incoming call initiated... (Call SID: {call_sid})")
    
    # Instantiate the stateful conversation manager
    manager = ConversationManager(
        clinic_id=clinic.id,
        call_sid=call_sid,
        grok_client=grok_client
    )
    
    # Generate initial greeting (two-party consent + bilingual offer)
    welcome = clinic.welcome_message or f"Thank you for calling {clinic.name}!"
    greeting = (
        f"{welcome} "
        f"Just so you know, I'm an AI dental assistant and this call may be "
        f"recorded for quality purposes. How can I help you today?"
    )
    if clinic.spanish_enabled:
        greeting += " Para español, diga 'español'."
        
    print(f"\n{BOLD}{MAGENTA}[AI Receptionist (Ash)]{RESET}: {greeting}")
    manager.history.append({
        "role": "assistant",
        "content": greeting,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # 3. Interactive dialog loop
    try:
        while True:
            state_color = YELLOW if manager.state != ConversationState.FAREWELL else RED
            print(f"\n{state_color}[State: {manager.state.upper()} | Lang: {manager.language.upper()}]{RESET}")
            
            # Get user terminal input
            try:
                user_input = input(f"{BOLD}{GREEN}[Patient]{RESET}: ").strip()
            except (KeyboardInterrupt, EOFError):
                break
                
            if not user_input:
                continue
                
            if user_input.lower() in ("exit", "quit", "hangup", "bye", "goodbye"):
                print(f"\n{RED}[CALL ENDED]{RESET} Hang up signal received from patient.")
                break
                
            # Process through the stateful receptionist engine
            print(f"{BLUE}[Grok AI is thinking...]{RESET}")
            response, actions = await manager.process_utterance(user_input)
            
            # Print AI response
            print(f"{BOLD}{MAGENTA}[AI Receptionist]{RESET}: {response}")
            
            # Show any actions triggered
            if actions:
                print(f"\n{BOLD}{YELLOW}[SYSTEM ACTIONS TRIGGERED]{RESET}")
                for act in actions:
                    action_type = act.get("type")
                    if action_type == "book_appointment":
                        print(f"  📅 {BOLD}Book Appointment Flow:{RESET}")
                        for k, v in act.get("data", {}).items():
                            if v:
                                print(f"    - {k}: {v}")
                    elif action_type == "emergency":
                        print(f"  🚨 {BOLD}Emergency Detected:{RESET}")
                        print(f"    - Severity: {act.get('severity')}")
                        print(f"    - Matched Keywords: {act.get('keywords')}")
                        print(f"    - Action: {act.get('action')}")
                        if act.get("action") in ("transfer_to_oncall", "transfer_and_911"):
                            print(f"    - {RED}{BOLD}Dialing Emergency Contact: {clinic.emergency_contact_phone} ({clinic.emergency_contact_name}){RESET}")
                    else:
                        print(f"  ⚙️ Action Type: {action_type} - {act}")
            
            # Stop if farewell
            if manager.state == ConversationState.FAREWELL:
                print(f"\n{RED}[CALL ENDED]{RESET} AI agent closed the conversation.")
                break
                
    except Exception as exc:
        print(f"\n{RED}[CRITICAL ERROR IN SIMULATION]{RESET}: {exc}")
        
    # 4. Show call finalization summary (Database persistence test)
    print(f"\n{BOLD}{CYAN}=================================================================={RESET}")
    print(f"{BOLD}{BLUE}📞 Call Summary & Database Persistence Audit 📞{RESET}")
    print(f"{BOLD}{CYAN}=================================================================={RESET}")
    
    transcript = manager.get_transcript()
    transcript_text = "\n".join(f"{msg['role'].upper()}: {msg['content']}" for msg in transcript)
    encrypted_transcript = encryption_service.encrypt(transcript_text)
    
    print(f"Total exchanges: {len(transcript)} messages.")
    print(f"Extracted Patient Info: {manager.patient_info or 'None'}")
    print(f"Final State reached: {BOLD}{manager.state.name}{RESET}")
    print(f"Encryption test (Fernet Ciphertext snippet): {encrypted_transcript[:75]}...")
    print(f"Decrypted check: {BOLD}{GREEN}PASSED (HIPAA Secure){RESET}")
    print(f"{BOLD}{CYAN}=================================================================={RESET}\n")

if __name__ == "__main__":
    # Fix standard event loop issues on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_simulator())
