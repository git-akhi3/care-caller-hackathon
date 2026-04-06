"""
Healthcare AI Voice Agent Analytics Dashboard Backend

Run with:
    uvicorn main.py:app --reload --port 8000

This FastAPI backend receives webhook calls from n8n, stores call data,
serves it to the React frontend, and generates clinical summaries using
the OpenAI ChatGPT API.
"""

import os
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from collections import defaultdict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", 8000))
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
CHATGPT_MODEL = "gpt-4o"  # Best model for complex clinical analysis

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class Contact(BaseModel):
    """Contact data from Google Sheets"""
    call_id: str
    patient_name: str
    phone_number: str
    medication: str
    dosage: str
    status: str = "pending"  # pending | in_progress | completed | failed


class ContactsWrapper(BaseModel):
    """Wrapper for batch contacts from n8n"""
    contacts: List['Contact']


class QAResponse(BaseModel):
    """Question-answer pair from call"""
    question: str
    answer: str


class CallPayload(BaseModel):
    """Structured data from n8n after call completes"""
    call_id: str
    patient_name: str
    phone_number: str
    outcome: str  # completed | incomplete | opted_out | scheduled | escalated | wrong_number | voicemail
    call_duration: int  # seconds
    cost: float
    transcript: str  # full raw transcript
    responses: List[QAResponse]  # Q&A pairs
    escalation_flag: bool = False
    escalation_reason: str = ""
    new_address: str = ""
    call_notes: str = ""
    started_at: str  # ISO timestamp
    ended_at: str  # ISO timestamp


class QualityBreakdown(BaseModel):
    """Breakdown of call quality metrics"""
    response_completeness: int  # 0-100
    conversation_flow: int  # 0-100
    data_accuracy: int  # 0-100
    guardrail_compliance: int  # 0-100


class Flags(BaseModel):
    """Clinical flags detected in call"""
    excessive_weight_loss: bool = False
    concerning_goal_weight: bool = False
    new_medications_reported: bool = False
    surgery_reported: bool = False
    escalation_needed: bool = False
    stt_issues_detected: bool = False


class AIAnalysis(BaseModel):
    """Claude AI analysis results"""
    clinical_summary: str
    needs_attention: bool
    attention_reasons: List[str] = []
    quality_score: int  # 0-100
    quality_breakdown: QualityBreakdown
    flags: Flags
    recommended_action: str  # routine_refill | needs_doctor_review | urgent_escalation | follow_up_required


class CallRecord(BaseModel):
    """Internal call record with analysis"""
    call_id: str
    patient_name: str
    phone_number: str
    outcome: str
    call_duration: int
    cost: float
    transcript: str
    responses: List[Dict[str, str]]
    escalation_flag: bool
    escalation_reason: str
    new_address: str
    call_notes: str
    started_at: str
    ended_at: str
    ai_analysis: Optional[Dict[str, Any]] = None
    created_at: str = None


# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="HealthCare AI Voice Agent Analytics",
    description="Backend for AI voice agent call analytics dashboard",
    version="1.0.0"
)

# Enable CORS for frontend on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for hackathon demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# IN-MEMORY STORAGE
# ============================================================================

calls: Dict[str, Dict[str, Any]] = {}  # keyed by call_id
contacts: Dict[str, Dict[str, Any]] = {}  # keyed by phone_number


# ============================================================================
# OPENAI CHATGPT INTEGRATION
# ============================================================================

async def call_openai_api(call_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Call OpenAI ChatGPT API to generate clinical analysis for a call.
    Uses gpt-4o for best clinical analysis quality.
    Returns parsed JSON response or None if error occurs.
    """
    if not OPENAI_API_KEY:
        print("⚠️  OPENAI_API_KEY not set - skipping AI analysis")
        return None

    try:
        # Build user prompt from call data
        responses_text = "\n".join(
            [f"{i+1}. Q: {r.get('question', 'N/A')} → A: {r.get('answer', 'N/A')}"
             for i, r in enumerate(call_data.get("responses", []))]
        )
        
        transcript_excerpt = call_data.get("transcript", "")[:800]
        
        user_prompt = f"""Analyze this medication refill check-in call and return a JSON object with exactly these fields:
{{
  clinical_summary: string (2-3 sentences plain english summary of patient status),
  needs_attention: boolean (true if any concerning flags),
  attention_reasons: list of strings (specific reasons why attention needed),
  quality_score: integer 0-100 (overall call quality),
  quality_breakdown: {{
    response_completeness: integer 0-100,
    conversation_flow: integer 0-100,
    data_accuracy: integer 0-100,
    guardrail_compliance: integer 0-100
  }},
  flags: {{
    excessive_weight_loss: boolean (true if lost > 15 lbs this month),
    concerning_goal_weight: boolean (true if goal weight seems dangerously low),
    new_medications_reported: boolean,
    surgery_reported: boolean,
    escalation_needed: boolean,
    stt_issues_detected: boolean (true if transcript has obvious speech-to-text errors like garbled words)
  }},
  recommended_action: string (one of: routine_refill | needs_doctor_review | urgent_escalation | follow_up_required)
}}

Call data:
Outcome: {call_data.get('outcome', 'unknown')}
Duration: {call_data.get('call_duration', 0)} seconds
Patient responses:
{responses_text}
Transcript excerpt: {transcript_excerpt}
Escalation flag: {call_data.get('escalation_flag', False)}
Escalation reason: {call_data.get('escalation_reason', '')}"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": CHATGPT_MODEL,
                    "temperature": 0.7,
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a clinical data analyst reviewing AI voice agent calls for a medication refill service. Analyze the call and return ONLY a JSON object, no markdown, no explanation."
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ]
                },
                timeout=30.0
            )
        
        if response.status_code != 200:
            print(f"❌ OpenAI API error: {response.status_code} - {response.text}")
            return None
        
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            print(f"❌ Failed to parse OpenAI response as JSON: {response.text[:200]}")
            return None
        
        # Extract text from OpenAI response
        choices = response_data.get("choices", [])
        if not choices:
            print(f"❌ No choices in OpenAI response: {response_data}")
            return None
            
        text_content = choices[0].get("message", {}).get("content", "").strip()
        
        if not text_content:
            print(f"❌ Empty content in OpenAI response: {response_data}")
            return None
        
        # Parse JSON from response - strip markdown code blocks if present
        if text_content.startswith("```"):
            text_content = text_content.split("```")[1]
            if text_content.startswith("json"):
                text_content = text_content[4:]
            text_content = text_content.strip()
        
        # Parse JSON from response
        analysis = json.loads(text_content)
        return analysis

    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error from OpenAI: {e} | Content: {text_content[:100] if 'text_content' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return None


async def analyze_call_background(call_id: str) -> None:
    """Background task to analyze call with ChatGPT AI"""
    if call_id not in calls:
        print(f"⚠️  Call {call_id} not found for analysis")
        return
    
    print(f"🤖 Processing AI analysis for call {call_id}...")
    analysis = await call_openai_api(calls[call_id])
    
    if analysis:
        calls[call_id]["ai_analysis"] = analysis
        print(f"✅ AI analysis complete for call {call_id}")
    else:
        print(f"⚠️  AI analysis skipped for call {call_id}")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_webhook(endpoint: str, call_id: str) -> None:
    """Log incoming webhook with timestamp"""
    timestamp = datetime.now().isoformat()
    print(f"📨 [{timestamp}] Webhook: {endpoint} | call_id: {call_id}")


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Print all available endpoints on startup"""
    print("\n" + "="*70)
    print("🏥 HEALTHCARE AI VOICE AGENT ANALYTICS BACKEND STARTED")
    print("="*70)
    print("\n📍 Available Endpoints:\n")
    print("  Webhooks:")
    print("    POST /webhook/call-started          - Receive call start notification")
    print("    POST /webhook/call-completed        - Receive completed call data")
    print("    POST /webhook/contacts              - Bulk upsert contacts from sheet\n")
    print("  Data Retrieval:")
    print("    GET  /calls                         - List all calls (newest first)")
    print("    GET  /calls/{call_id}               - Get single call detail")
    print("    GET  /contacts                      - List all contacts\n")
    print("  Analytics:")
    print("    GET  /stats                         - Aggregated statistics")
    print("    GET  /health                        - Health check\n")
    print("  Demo:")
    print("    POST /demo/seed                     - Seed with sample data\n")
    print("🚀 Run: uvicorn main.py:app --reload --port 8000")
    print("="*70 + "\n")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "ok",
        "calls_count": len(calls),
        "contacts_count": len(contacts)
    }


# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@app.post("/webhook/call-started")
async def call_started(contact: Contact) -> Dict[str, Any]:
    """Receive call start notification from n8n"""
    try:
        log_webhook("call-started", contact.call_id)
        
        # Upsert contact with status in_progress
        contact_data = contact.dict()
        contact_data["status"] = "in_progress"
        contacts[contact.phone_number] = contact_data
        
        print(f"✅ Contact {contact.patient_name} marked as in_progress")
        return {"success": True}
    
    except Exception as e:
        print(f"❌ Error in call-started: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/call-completed")
async def call_completed(payload: CallPayload, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Receive completed call data and trigger AI analysis"""
    try:
        log_webhook("call-completed", payload.call_id)
        
        # Store call in calls dict
        call_record = {
            "call_id": payload.call_id,
            "patient_name": payload.patient_name,
            "phone_number": payload.phone_number,
            "outcome": payload.outcome,
            "call_duration": payload.call_duration,
            "cost": payload.cost,
            "transcript": payload.transcript,
            "responses": [r.dict() for r in payload.responses],
            "escalation_flag": payload.escalation_flag,
            "escalation_reason": payload.escalation_reason,
            "new_address": payload.new_address,
            "call_notes": payload.call_notes,
            "started_at": payload.started_at,
            "ended_at": payload.ended_at,
            "ai_analysis": None,
            "created_at": datetime.now().isoformat()
        }
        
        calls[payload.call_id] = call_record
        
        # Update contact status
        if payload.phone_number in contacts:
            contacts[payload.phone_number]["status"] = payload.outcome
        
        # Trigger background AI analysis
        background_tasks.add_task(analyze_call_background, payload.call_id)
        
        print(f"✅ Call {payload.call_id} stored | outcome: {payload.outcome}")
        return {"success": True, "call_id": payload.call_id}
    
    except Exception as e:
        print(f"❌ Error in call-completed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/contacts")
async def bulk_contacts(data: Union[ContactsWrapper, List[Contact], List[ContactsWrapper]]) -> Dict[str, Any]:
    """
    Bulk upsert contacts from Google Sheets
    
    Accepts three formats:
    1. Single nested from n8n: {"contacts": [Contact, Contact, ...]}
    2. Direct list: [Contact, Contact, ...]
    3. List of nested: [{"contacts": [...]}, {"contacts": [...]}]
    """
    try:
        # Extract all contacts from any format
        all_contacts = []
        
        # Handle single ContactsWrapper object
        if isinstance(data, ContactsWrapper):
            all_contacts = data.contacts
            log_webhook("contacts", f"batch_of_{len(all_contacts)}_nested")
        
        # Handle list of Contacts or ContactsWrappers
        elif isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            
            # Check if it's a list of ContactsWrapper objects
            if isinstance(first_item, ContactsWrapper):
                # List of wrapped batches: extract from each
                for wrapper in data:
                    all_contacts.extend(wrapper.contacts)
                log_webhook("contacts", f"batch_of_{len(all_contacts)}_nested")
            else:
                # Direct list of Contacts
                all_contacts = data
                log_webhook("contacts", f"batch_of_{len(all_contacts)}")
        
        # Upsert all contacts
        for contact in all_contacts:
            if isinstance(contact, Contact):
                contact_data = contact.dict()
            else:
                contact_data = contact
            contacts[contact_data.get("phone_number", "")] = contact_data
        
        print(f"✅ Upserted {len(all_contacts)} contacts")
        return {"success": True, "count": len(all_contacts)}
    
    except Exception as e:
        print(f"❌ Error in bulk-contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DATA RETRIEVAL ENDPOINTS
# ============================================================================

@app.get("/calls")
async def get_calls() -> List[Dict[str, Any]]:
    """Get all calls sorted by creation date (newest first)"""
    try:
        call_list = list(calls.values())
        # Sort by created_at descending (newest first)
        call_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return call_list
    
    except Exception as e:
        print(f"❌ Error in get-calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/calls/{call_id}")
async def get_call(call_id: str) -> Dict[str, Any]:
    """Get single call with full detail"""
    try:
        if call_id not in calls:
            raise HTTPException(status_code=404, detail="Call not found")
        
        return calls[call_id]
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get-call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contacts")
async def get_contacts() -> List[Dict[str, Any]]:
    """Get all contacts with their current status"""
    try:
        return list(contacts.values())
    
    except Exception as e:
        print(f"❌ Error in get-contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get aggregated statistics across all calls"""
    try:
        if not calls:
            return {
                "total_calls": 0,
                "outcome_counts": {},
                "escalation_count": 0,
                "avg_call_duration": 0,
                "total_cost": 0,
                "avg_cost": 0,
                "response_completeness_avg": 0,
                "flagged_calls_count": 0
            }
        
        # Count outcomes
        outcome_counts = defaultdict(int)
        escalation_count = 0
        total_duration = 0
        total_cost = 0
        response_completeness_sum = 0
        flagged_calls_count = 0
        
        for call in calls.values():
            outcome_counts[call["outcome"]] += 1
            total_duration += call["call_duration"]
            total_cost += call["cost"]
            
            if call["escalation_flag"]:
                escalation_count += 1
            
            # Calculate response completeness (responses out of max 14)
            responses_count = len(call.get("responses", []))
            response_completeness_sum += (responses_count / 14) * 100
            
            # Count flagged calls
            if call.get("ai_analysis") and call["ai_analysis"].get("needs_attention"):
                flagged_calls_count += 1
        
        total_calls = len(calls)
        
        return {
            "total_calls": total_calls,
            "outcome_counts": dict(outcome_counts),
            "escalation_count": escalation_count,
            "avg_call_duration": round(total_duration / total_calls, 2) if total_calls > 0 else 0,
            "total_cost": round(total_cost, 2),
            "avg_cost": round(total_cost / total_calls, 2) if total_calls > 0 else 0,
            "response_completeness_avg": round(response_completeness_sum / total_calls, 2) if total_calls > 0 else 0,
            "flagged_calls_count": flagged_calls_count
        }
    
    except Exception as e:
        print(f"❌ Error in get-stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DEMO ENDPOINT
# ============================================================================

@app.post("/demo/seed")
async def demo_seed() -> Dict[str, Any]:
    """Seed database with realistic sample calls for demo"""
    try:
        print("🌱 Seeding demo data...")
        
        # Clear existing data for fresh demo
        calls.clear()
        contacts.clear()
        
        # Sample Call 1: Escalation (excessive weight loss)
        call1 = {
            "call_id": "demo-call-001",
            "patient_name": "John Smith",
            "phone_number": "+1-555-0101",
            "outcome": "escalated",
            "call_duration": 245,
            "cost": 1.25,
            "transcript": "Agent: Hello, this is a medication refill confirmation call from CareCaller. Are you John Smith? Patient: Yes, that's me. Agent: Great! I'm calling to confirm your lisinopril refill prescription. Have you experienced any side effects? Patient: Well, I've lost about 20 pounds this month and I'm feeling pretty weak. Agent: I see. That's important information. We'll note that for your doctor to review.",
            "responses": [
                {"question": "Name confirmation", "answer": "John Smith"},
                {"question": "Current medication", "answer": "Lisinopril 10mg"},
                {"question": "Dosage", "answer": "Once daily"},
                {"question": "Side effects", "answer": "Weight loss, weakness"},
                {"question": "Recent changes", "answer": "Lost 20 lbs this month"},
                {"question": "Allergies", "answer": "No allergies"},
                {"question": "Other medications", "answer": "Metformin"},
                {"question": "Diet changes", "answer": "No"},
                {"question": "Exercise level", "answer": "Minimal"},
                {"question": "Follow-up needed", "answer": "Yes"},
                {"question": "Contact preference", "answer": "Phone"},
                {"question": "Insurance check", "answer": "Active"},
                {"question": "Address confirmation", "answer": "123 Main St"},
                {"question": "Best time to call", "answer": "Morning"}
            ],
            "escalation_flag": True,
            "escalation_reason": "Excessive weight loss reported",
            "new_address": "",
            "call_notes": "Patient reported 20 lb weight loss in one month",
            "started_at": "2026-04-04T10:15:00Z",
            "ended_at": "2026-04-04T10:19:05Z",
            "created_at": "2026-04-04T10:19:05Z",
            "ai_analysis": {
                "clinical_summary": "62-year-old patient on lisinopril reports significant weight loss (20 lbs) and weakness over the past month. Escalation recommended for physician review due to concerning vital sign changes.",
                "needs_attention": True,
                "attention_reasons": [
                    "Excessive weight loss in short timeframe",
                    "Reported weakness suggesting potential deconditioning",
                    "Requires physician evaluation before refill"
                ],
                "quality_score": 92,
                "quality_breakdown": {
                    "response_completeness": 100,
                    "conversation_flow": 90,
                    "data_accuracy": 95,
                    "guardrail_compliance": 85
                },
                "flags": {
                    "excessive_weight_loss": True,
                    "concerning_goal_weight": False,
                    "new_medications_reported": False,
                    "surgery_reported": False,
                    "escalation_needed": True,
                    "stt_issues_detected": False
                },
                "recommended_action": "urgent_escalation"
            }
        }
        
        # Sample Call 2: Routine refill (successful)
        call2 = {
            "call_id": "demo-call-002",
            "patient_name": "Sarah Johnson",
            "phone_number": "+1-555-0102",
            "outcome": "completed",
            "call_duration": 180,
            "cost": 0.95,
            "transcript": "Agent: Hello Sarah, this is CareCaller calling about your atorvastatin prescription. Patient: Hi, yes I'm ready. Agent: Perfect. Have you had any issues with your current medication? Patient: No, everything has been fine. My cholesterol levels were good at my last checkup.",
            "responses": [
                {"question": "Name confirmation", "answer": "Sarah Johnson"},
                {"question": "Current medication", "answer": "Atorvastatin 20mg"},
                {"question": "Dosage", "answer": "Once daily at night"},
                {"question": "Side effects", "answer": "None reported"},
                {"question": "Recent changes", "answer": "No changes"},
                {"question": "Allergies", "answer": "Penicillin"},
                {"question": "Other medications", "answer": "Aspirin"},
                {"question": "Diet changes", "answer": "Eating healthier"},
                {"question": "Exercise level", "answer": "3x weekly"},
                {"question": "Follow-up needed", "answer": "No"},
                {"question": "Contact preference", "answer": "Email"},
                {"question": "Insurance check", "answer": "Active"},
                {"question": "Address confirmation", "answer": "456 Oak Ave"},
                {"question": "Best time to call", "answer": "Evening"}
            ],
            "escalation_flag": False,
            "escalation_reason": "",
            "new_address": "",
            "call_notes": "Routine refill, patient compliant and doing well",
            "started_at": "2026-04-04T11:30:00Z",
            "ended_at": "2026-04-04T11:33:00Z",
            "created_at": "2026-04-04T11:33:00Z",
            "ai_analysis": {
                "clinical_summary": "47-year-old patient on stable atorvastatin therapy with excellent medication adherence and reported good cholesterol control. Patient maintains healthy lifestyle with regular exercise.",
                "needs_attention": False,
                "attention_reasons": [],
                "quality_score": 95,
                "quality_breakdown": {
                    "response_completeness": 100,
                    "conversation_flow": 95,
                    "data_accuracy": 100,
                    "guardrail_compliance": 90
                },
                "flags": {
                    "excessive_weight_loss": False,
                    "concerning_goal_weight": False,
                    "new_medications_reported": False,
                    "surgery_reported": False,
                    "escalation_needed": False,
                    "stt_issues_detected": False
                },
                "recommended_action": "routine_refill"
            }
        }
        
        # Sample Call 3: Opted out
        call3 = {
            "call_id": "demo-call-003",
            "patient_name": "Michael Chen",
            "phone_number": "+1-555-0103",
            "outcome": "opted_out",
            "call_duration": 45,
            "cost": 0.30,
            "transcript": "Agent: Hello, is this Michael Chen? Patient: Yes, but I don't want to participate in call programs. Please remove me from your list.",
            "responses": [
                {"question": "Name confirmation", "answer": "Michael Chen"},
                {"question": "Current medication", "answer": "Not provided"},
                {"question": "Dosage", "answer": "Not provided"},
                {"question": "Side effects", "answer": "Not provided"},
                {"question": "Recent changes", "answer": "Not provided"},
                {"question": "Allergies", "answer": "Not provided"},
                {"question": "Other medications", "answer": "Not provided"},
                {"question": "Diet changes", "answer": "Not provided"},
                {"question": "Exercise level", "answer": "Not provided"},
                {"question": "Follow-up needed", "answer": "Patient opted out"},
                {"question": "Contact preference", "answer": "Not provided"},
                {"question": "Insurance check", "answer": "Not provided"},
                {"question": "Address confirmation", "answer": "Not provided"},
                {"question": "Best time to call", "answer": "Not provided"}
            ],
            "escalation_flag": False,
            "escalation_reason": "",
            "new_address": "",
            "call_notes": "Patient opted out of program",
            "started_at": "2026-04-04T13:00:00Z",
            "ended_at": "2026-04-04T13:00:45Z",
            "created_at": "2026-04-04T13:00:45Z",
            "ai_analysis": {
                "clinical_summary": "Patient declined participation in medication refill program. No clinical data available.",
                "needs_attention": False,
                "attention_reasons": [],
                "quality_score": 0,
                "quality_breakdown": {
                    "response_completeness": 0,
                    "conversation_flow": 50,
                    "data_accuracy": 0,
                    "guardrail_compliance": 100
                },
                "flags": {
                    "excessive_weight_loss": False,
                    "concerning_goal_weight": False,
                    "new_medications_reported": False,
                    "surgery_reported": False,
                    "escalation_needed": False,
                    "stt_issues_detected": False
                },
                "recommended_action": "follow_up_required"
            }
        }
        
        # Store all calls
        calls[call1["call_id"]] = call1
        calls[call2["call_id"]] = call2
        calls[call3["call_id"]] = call3
        
        # Seed contacts
        contacts["+1-555-0101"] = {
            "call_id": "demo-call-001",
            "patient_name": "John Smith",
            "phone_number": "+1-555-0101",
            "medication": "Lisinopril",
            "dosage": "10mg once daily",
            "status": "escalated"
        }
        
        contacts["+1-555-0102"] = {
            "call_id": "demo-call-002",
            "patient_name": "Sarah Johnson",
            "phone_number": "+1-555-0102",
            "medication": "Atorvastatin",
            "dosage": "20mg once daily",
            "status": "completed"
        }
        
        contacts["+1-555-0103"] = {
            "call_id": "demo-call-003",
            "patient_name": "Michael Chen",
            "phone_number": "+1-555-0103",
            "medication": "Unknown",
            "dosage": "Unknown",
            "status": "opted_out"
        }
        
        print("✅ Demo seeded with 3 sample calls and 3 contacts")
        return {
            "success": True,
            "calls_created": 3,
            "contacts_created": 3,
            "message": "Demo data seeded successfully"
        }
    
    except Exception as e:
        print(f"❌ Error in demo-seed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True
    )
