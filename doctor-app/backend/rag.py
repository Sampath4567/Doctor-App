import requests
import json
import logging
from sqlalchemy.orm import Session, joinedload
import models
from config import settings


logger = logging.getLogger(__name__)


def get_context(db: Session, user: models.User = None):
    # Fetch doctors with their specialization and user details
    doctors = db.query(models.Doctor).options(
        joinedload(models.Doctor.user),
        joinedload(models.Doctor.specialization)
    ).filter(models.Doctor.is_available == True).all()
    
    specializations = db.query(models.Specialization).all()
    
    context_text = "Here is the current data for the DoctorBook app:\n\n"
    
    context_text += "Available Specializations:\n"
    for s in specializations:
        context_text += f"- {s.name}: {s.description}\n"
        
    context_text += "\nAvailable Doctors:\n"
    for d in doctors:
        context_text += f"- Dr. {d.user.full_name} ({d.specialization.name}). Bio: {d.bio}. Fee: {d.consultation_fee}\n"
        
    if user:
        context_text += f"\n\n--- CURRENT USER CONTEXT ---\n"
        context_text += f"User: {user.full_name} (Role: {user.role})\n"
        
        if user.role == "patient":
            appts = db.query(models.Appointment).filter(models.Appointment.patient_id == user.id).all()
            if appts:
                context_text += "My Appointments:\n"
                for a in appts:
                    context_text += f"- {a.slot.slot_date} at {a.slot.start_time} with Dr. {a.slot.doctor.user.full_name} (Status: {a.status})\n"
            else:
                context_text += "I have no upcoming appointments.\n"

        elif user.role == "doctor":
            doc = db.query(models.Doctor).filter(models.Doctor.user_id == user.id).first()
            if doc:
                appts = db.query(models.Appointment).join(models.Slot).filter(models.Slot.doctor_id == doc.id).all()
                context_text += "My Schedule/Appointments:\n"
                for a in appts:
                    context_text += f"- {a.slot.slot_date} at {a.slot.start_time}: Patient {a.patient.full_name} (Reason: {a.reason}, Status: {a.status})\n"
        
        elif user.role == "admin":
            user_count = db.query(models.User).count()
            appt_count = db.query(models.Appointment).count()
            context_text += f"System Stats: {user_count} total users, {appt_count} total appointments.\n"

    return context_text


def extract_booking_intent(message: str) -> dict:
    """
    Use the LLM strictly as an intent extractor.

    Expected JSON format:
    {
      "intent": "book_appointment" | "none",
      "doctor_name": null | string,
      "specialization": null | string,
      "date": null | "YYYY-MM-DD",
      "day_of_week": null | string,
      "time": null | "HH:MM",
      "part_of_day": null | "morning" | "afternoon" | "evening"
    }
    """
    OLLAMA_URL = "http://localhost:11434/api/chat"
    MODEL = "gemma3:4b"

    system_prompt = """
You are an intent extraction engine for a doctor appointment chatbot.

Your ONLY task is to analyse the user's single message and extract structured intent.

Very important rules:
- You MUST respond with JSON ONLY. No explanations, no prose, no markdown.
- Use EXACTLY this JSON shape with all keys present:
  {
    "intent": "book_appointment" | "none",
    "doctor_name": null | string,
    "specialization": null | string,
    "date": null | "YYYY-MM-DD",
    "day_of_week": null | string,
    "time": null | "HH:MM",
    "part_of_day": null | "morning" | "afternoon" | "evening"
  }
- If the user clearly wants to book a medical appointment, set "intent" to "book_appointment".
- Otherwise set "intent" to "none".
- NEVER make up or guess doctors, specializations, dates or times.
  - Only use a doctor or specialization name if the user explicitly mentioned it.
  - Only use a date or time if the user explicitly mentioned it.
  - If you are not sure about a field, set it to null.
- If the user says things like "tomorrow", "next Monday", "today", set "day_of_week" accordingly, not "date".
- If the user mentions morning/afternoon/evening, set "part_of_day" accordingly.
"""

    default = {
        "intent": "none",
        "doctor_name": None,
        "specialization": None,
        "date": None,
        "day_of_week": None,
        "time": None,
        "part_of_day": None,
    }

    try:
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "stream": False,
        }
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        body = response.json()
        content = body.get("message", {}).get("content", "")
        intent_data = json.loads(content)
        # Ensure all required keys exist, fall back to defaults if not.
        merged = {**default, **{k: intent_data.get(k) for k in default.keys() if isinstance(intent_data, dict)}}
        logger.info("Extracted booking intent: %s", merged)
        return merged
    except Exception as e:  # pragma: no cover - safety net
        logger.error("Intent extraction error: %s", e)
        return default


def ask_bot(query: str, db: Session, user: models.User = None):
    # Ollama settings
    OLLAMA_URL = "http://localhost:11434/api/chat"
    # You can change this to "gemma3:4b", "qwen2:7b", etc. based on your 'ollama list'
    MODEL = "gemma3:4b" 
    
    db_context = get_context(db, user)
    
    instruction = "If the user is a patient, you may recommend suitable doctors from the list based on their symptoms and encourage them to book an appointment."
    if user and user.role in ["doctor", "admin"]:
        instruction = "Do not suggest booking an appointment as this user is a staff member. Focus on answering their query."
    
    system_prompt = f"""You are a helpful medical assistant for the DoctorBook app.
        Your goal is to help users find the right doctor and answer their questions using the provided context.
        
        You are chatting with {user.full_name if user else 'a guest'}. Use the provided context to answer questions about their specific appointments or schedule if available.
        
        Use the following information about available doctors and specializations to answer the user's question.
        If the user asks about medical advice, give a standard disclaimer that you are an AI, but try to recommend a relevant doctor from the list based on their symptoms if possible.
        
        {instruction}
        
        Keep answers concise and friendly.
        
        Context:
        {db_context}
        """

    try:
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "stream": False
        }
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json()['message']['content']
    except Exception as e:
        print(f"Ollama Error: {e}")
        return "Sorry, I'm having trouble connecting to the local Ollama service. Please ensure Ollama is running."


def ask_bot_stream(query: str, db: Session, user: models.User = None):
    # Ollama settings
    OLLAMA_URL = "http://localhost:11434/api/chat"
    # You can change this to "gemma3:4b", "qwen2:7b", etc. based on your 'ollama list'
    MODEL = "gemma3:4b" 
    
    db_context = get_context(db, user)
    
    instruction = "If the user is a patient, you may recommend suitable doctors from the list based on their symptoms and encourage them to book an appointment."
    if user and user.role in ["doctor", "admin"]:
        instruction = "Do not suggest booking an appointment as this user is a staff member. Focus on answering their query."
    
    system_prompt = f"""You are a helpful medical assistant for the DoctorBook app.
        Your goal is to help users find the right doctor and answer their questions using the provided context.
        
        You are chatting with {user.full_name if user else 'a guest'}. Use the provided context to answer questions about their specific appointments or schedule if available.
        
        Use the following information about available doctors and specializations to answer the user's question.
        If the user asks about medical advice, give a standard disclaimer that you are an AI, but try to recommend a relevant doctor from the list based on their symptoms if possible.
        
        {instruction}
        
        Keep answers concise and friendly.
        
        Context:
        {db_context}
        """

    try:
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "stream": True
        }
        with requests.post(OLLAMA_URL, json=payload, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    body = json.loads(line)
                    if 'message' in body and 'content' in body['message']:
                        yield body['message']['content']
    except Exception as e:
        print(f"Ollama Error: {e}")
        yield "Sorry, I'm having trouble connecting to the local Ollama service. Please ensure Ollama is running."
