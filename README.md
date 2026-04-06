# 🤖 TrimRX Voice AI Agent — Automated Medication Refill System

> An end-to-end production-ready voice AI pipeline that calls patients, conducts structured medication refill check-ins, and generates clean JSON summaries — powered by **Vapi**, **n8n**, and **Claude (Anthropic)**.

---

## 📋 Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Agent Identity](#agent-identity)
- [Call Flow](#call-flow)
- [Questionnaire Structure](#questionnaire-structure)
- [Call Outcomes](#call-outcomes)
- [Output Schema](#output-schema)
- [n8n Workflow Architecture](#n8n-workflow-architecture)
- [Vapi Configuration](#vapi-configuration)
- [Setup & Installation](#setup--installation)
- [Input Data Format](#input-data-format)
- [Edge Case Handling](#edge-case-handling)
- [Escalation Logic](#escalation-logic)
- [Security & Privacy](#security--privacy)

---

## Overview

TrimRX Voice AI is an outbound calling agent that automates medication refill check-ins for patients. The agent — named **Jessica** — calls patients from a dataset, conducts a structured 14-question health questionnaire, and upon call completion, generates a structured JSON record per patient that is stored back to Google Sheets.

The system handles the full call lifecycle:
- Identity verification
- Refill interest routing
- 14-question health questionnaire
- Shipping address update (conditional slot-filling)
- Escalation for medical concerns
- Voicemail detection and delivery
- Structured JSON output generation

---

## How It Works

```
Google Sheets (Patient Data)
        ↓
    n8n Workflow
        ↓
  Loop per Patient Row
        ↓
  HTTP Request → Vapi Outbound Call API
        ↓
  Vapi Executes Jessica AI Agent
        ↓
  Webhook captures call result + transcript
        ↓
  Claude AI Node → Structures transcript into JSON
        ↓
  Set Node → Cleans & maps final output
        ↓
  Google Sheets → Appends result row per patient
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Voice AI Agent | [Vapi](https://vapi.ai) |
| LLM (Agent Brain) | Anthropic Claude (via Vapi) |
| Voice Synthesis | ElevenLabs |
| Speech Recognition | Deepgram |
| Workflow Automation | n8n |
| Structured Output | Claude (via native n8n connector) |
| Data Source | Google Sheets |
| Data Storage | Google Sheets |

---

## Agent Identity

| Field | Value |
|---|---|
| **Name** | Jessica |
| **Company** | TrimRX |
| **Role** | Medication Refill Check-in Agent |
| **Tone** | Warm, professional, efficient |
| **Language** | English |
| **Call Type** | Outbound |

Jessica is designed to behave like a real outbound healthcare refill coordinator — calm, privacy-aware, structured, and decisive. She never gives medical advice, never skips a mandatory question on a completed call, and never speaks the internal JSON output aloud.

---

## Call Flow

```
OPENING
  └─ Greeting + Identity Confirmation
  └─ Refill Interest Check
  └─ Availability Check (2 minutes?)

ROUTING
  ├─ Busy         → outcome: scheduled   → capture callback time + timezone → CLOSING
  ├─ Not Interested → outcome: opted_out → confirm → CLOSING
  ├─ Wrong Person  → outcome: wrong_number → apologize → CLOSING
  └─ Agrees        → begin QUESTIONNAIRE

QUESTIONNAIRE (14 questions — strict order)

CLOSING
  └─ Deliver outcome-specific closing script

TERMINATED
  └─ Trigger end_call function
  └─ Generate internal JSON summary (never spoken)
```

---

## Questionnaire Structure

The agent asks exactly **14 questions** in strict order. No question is repeated, skipped, or reordered on a completed call.

| # | Question |
|---|---|
| Q1 | How have you been feeling overall? |
| Q2 | What is your current weight in pounds? |
| Q3 | What is your height in feet and inches? |
| Q4 | How much weight have you lost this past month in pounds? |
| Q5 | Any side effects from your medication this month? |
| Q6 | Are you satisfied with your rate of weight loss? |
| Q7 | What is your goal weight in pounds? |
| Q8 | Any requests about your dosage? |
| Q9 | Have you started any new medications or supplements since last month? |
| Q10 | Do you have any new medical conditions since your last check-in? |
| Q11 | Any new allergies? |
| Q12 | Any surgeries since your last check-in? |
| Q13 | Any questions for your doctor? |
| Q14 | Has your shipping address changed? |

> **Q14 Special Logic:** If patient answers Yes, the agent collects the new address via structured slot-filling (Pincode → Landmark → Street → House/Apartment) and confirms the assembled address before proceeding to closing.

---

## Call Outcomes

The system strictly maps every call to one of **7 outcome ENUMs**:

| Outcome | Trigger Condition |
|---|---|
| `completed` | All 14 questions answered successfully |
| `escalated` | Patient reports serious medical symptom or concern |
| `opted_out` | Patient not interested in refill |
| `scheduled` | Patient busy — callback time captured |
| `wrong_number` | Identity mismatch confirmed |
| `voicemail` | No human response after greeting retries |
| `incomplete` | Call dropped, silence timeout, or early disconnect |

---

## Output Schema

After every call, one clean structured JSON object is generated per patient:

```json
{
  "patient_name": "vighnesh",
  "number": "919398952819",
  "status": "completed",
  "summary": "Patient completed full check-in. Reported 4 lbs weight loss, mild nausea side effect noted.",
  "transcript": "<full raw call transcript>",
  "call_duration": "187",
  "action_required": "Follow-up needed — side effect flagged for clinical review",
  "timestamp": "2026-04-06T17:30:00Z"
}
```

**Field Rules:**
- `status` — strictly one of the 7 ENUM values
- `summary` — 1–2 sentences, concise
- `transcript` — full raw transcript passed through from Vapi
- `call_duration` — in seconds, from Vapi webhook payload
- `action_required` — meaningful next step (e.g. "No action required", "Reschedule call", "Escalate to clinical team")
- `timestamp` — ISO 8601 format
- No extra fields allowed
- Valid JSON only — no markdown, no comments

---

## n8n Workflow Architecture

The n8n workflow consists of **9 nodes** executed in sequence:

### Node 1 — Manual Trigger
Starts the workflow on demand. Can be swapped for a Cron trigger for scheduled daily runs.

### Node 2 — Google Sheets (Read)
Reads all patient rows from the configured Google Sheet. Each row contains: `patient_name`, `number`, `medication`, `dosage`.

### Node 3 — Loop Over Items
Iterates one patient row at a time, ensuring calls are made sequentially and not in parallel.

### Node 4 — HTTP Request (Vapi Outbound Call)
Calls Vapi's outbound call API with the patient's number and assistant configuration. Passes `patient_name`, `medication`, and `dosage` as dynamic variables.

```
POST https://api.vapi.ai/call/phone
Authorization: Bearer <VAPI_API_KEY>
```

```json
{
  "assistantId": "4e61e788-d0bd-4e95-b351-7b864ccf3556",
  "phoneNumberId": "5a232df4-1694-447b-aba9-631ff4262fa3",
  "customer": {
    "number": "+{{ $json.number }}"
  },
  "assistantOverrides": {
    "variableValues": {
      "patient_name": "{{ $json.patient_name }}",
      "medication": "{{ $json.medication }}",
      "dosage": "{{ $json.dosage }}"
    }
  }
}
```

### Node 5 — Wait Node
Pauses workflow execution and waits for Vapi's webhook to fire with the post-call payload (transcript, duration, end reason).

### Node 6 — Webhook Node
Receives Vapi's `end-of-call-report` server message. Captures: transcript, call duration, end reason, and call metadata.

### Node 7 — Claude AI Node (native n8n connector)
Sends the raw transcript and call metadata to Claude. Receives structured JSON back. See **Claude Node Prompt** section below.

### Node 8 — Set Node
Maps Claude's output to the final clean JSON schema. Ensures no extra fields slip through and all values are correctly typed.

### Node 9 — Google Sheets (Append)
Appends the final JSON as a new row in the results sheet — one row per patient call.

---

## Claude Node Prompt

### System Prompt

```
You are a structured data extraction assistant for a healthcare voice AI system called TrimRX.

Your ONLY job is to read a raw call transcript and call metadata, then return a single valid JSON object.

STRICT RULES:
- Output ONLY raw valid JSON. No markdown. No code fences. No commentary. No explanation.
- The JSON must contain exactly these fields and no others:
  patient_name, number, status, summary, transcript, call_duration, action_required, timestamp

STATUS ENUM — you must select exactly ONE:
- completed    → full questionnaire was conducted and call ended normally
- escalated    → patient reported a serious medical concern (chest pain, breathing difficulty, severe symptoms)
- opted_out    → patient explicitly said they don't want the refill or ended the call early
- scheduled    → patient was busy and requested a callback; callback time was captured
- wrong_number → the person who answered confirmed they are not the intended patient
- voicemail    → no human responded; voicemail message was delivered
- incomplete   → call dropped mid-conversation, patient went silent, or call ended before questionnaire finished

FIELD RULES:
- status: Must be exactly one of the 7 values above. Never invent a new status.
- summary: 1–2 sentences. Describe what actually happened on the call. Do not hallucinate.
- transcript: Copy the full raw transcript string exactly as provided. Do not modify or summarize it.
- call_duration: Use the value provided in seconds. If not available, use "unknown".
- action_required: Choose a meaningful next step. Examples:
    "No action required"
    "Follow-up needed — side effect reported"
    "Escalate to clinical team — serious symptom mentioned"
    "Schedule callback — patient unavailable"
    "Verify number — wrong person answered"
- timestamp: Use the provided end timestamp in ISO 8601 format. If not available, use current UTC time.

EDGE CASE HANDLING:
- If transcript is empty or null → status = voicemail or incomplete (use end_reason to decide)
- If transcript shows no human voice → status = voicemail
- If call dropped mid-questionnaire → status = incomplete
- If patient said "not interested" or "remove me" → status = opted_out
- If a family member answered but patient never came to phone → status = incomplete
- If number was invalid or not in service → status = wrong_number
- Never guess or infer medical information not present in the transcript

ANTI-HALLUCINATION RULE:
Only use information explicitly present in the transcript or metadata provided. If a field value cannot be determined, use "unknown" — never invent a value.
```

### User Prompt

```
Here is the call data. Extract and return the structured JSON.

Patient Name: {{ $json.patient_name }}
Phone Number: {{ $json.number }}
Call Duration (seconds): {{ $json.call_duration }}
Call End Reason: {{ $json.end_reason }}
Call End Timestamp: {{ $json.ended_at }}

Raw Transcript:
{{ $json.transcript }}

Return ONLY the JSON object. Nothing else.
```

---

## Vapi Configuration

| Field | Value |
|---|---|
| Assistant ID | `4e61e788-d0bd-4e95-b351-7b864ccf3556` |
| Phone Number ID | `5a232df4-1694-447b-aba9-631ff4262fa3` |
| LLM Provider | Anthropic (Claude) |
| Voice Provider | ElevenLabs |
| Transcriber | Deepgram |
| Start Speaking Wait | 1.3 seconds |
| Smart Endpointing | Vapi |
| Voicemail Detection | Enabled |

> ⚠️ **Security Note:** Do not commit your Vapi API key to the repository. Store it in n8n credentials or as an environment variable.

---

## Setup & Installation

### Prerequisites

- [n8n](https://n8n.io) instance (self-hosted or cloud)
- [Vapi](https://vapi.ai) account with a published assistant
- Anthropic API access (Claude connected in n8n)
- Google Sheets with patient data
- Google Sheets API credentials configured in n8n

### Steps

**1. Clone this repository**
```bash
git clone https://github.com/your-org/trimrx-voice-agent.git
cd trimrx-voice-agent
```

**2. Import the n8n workflow**
- Open your n8n instance
- Go to **Workflows → Import from File**
- Select `workflow/trimrx_workflow.json`

**3. Configure credentials in n8n**
- Add your **Vapi API Key** as a Header Auth credential
- Connect your **Google Sheets** account
- Ensure the **Claude (Anthropic)** node is connected via the native n8n connector

**4. Set up Google Sheets**
- Create a sheet with columns: `patient_name`, `number`, `medication`, `dosage`
- Create a results sheet for output storage

**5. Configure the Webhook URL**
- Copy the Webhook node URL from n8n
- Paste it into your Vapi assistant's **Server URL** under Advanced settings
- Enable `end-of-call-report` in Server Messages

**6. Test**
- Add one patient row to your Google Sheet
- Run the workflow manually
- Check the results sheet for the structured JSON output

---

## Input Data Format

Google Sheet columns (exact names required):

| Column | Type | Example |
|---|---|---|
| `patient_name` | String | `vighnesh` |
| `number` | String (with country code) | `919398952819` |
| `medication` | String | `Tirzepatide` |
| `dosage` | String | `2.5mg` |

---

## Edge Case Handling

| Scenario | Agent Behaviour |
|---|---|
| Patient silent after greeting (×2) | Deliver voicemail → terminate |
| Patient busy | Capture callback time + timezone → `scheduled` |
| Wrong person answers | Apologize → terminate immediately |
| Patient gives out-of-order answer | Store silently → use when correct question is reached |
| Background noise/interference | Ask to move to quieter spot or offer callback |
| Unrealistic health value | Confirm once → accept → flag internally |
| Patient mentions new medication | Confirm name once → record verbatim |
| Patient refuses to answer a question | Note as "Patient declined" → proceed |
| Call exceeds expected duration | Continue calmly — never rush patient |
| Patient tries to restart after closing | Do not re-engage → terminate |

---

## Escalation Logic

Escalation is triggered when the patient mentions any serious medical concern during the call, including but not limited to:

- Chest pain
- Severe nausea
- Breathing difficulty
- Worsening symptoms
- Blood pressure issues

**What happens:**
1. Agent acknowledges the concern clearly
2. Informs patient it will be escalated
3. Continues remaining questionnaire questions
4. Uses escalation closing script at the end
5. Sets `escalation_flag: true` in internal JSON
6. Stores exact symptom phrase in `escalation_reason`

> Escalation is **never** triggered mid-questionnaire unless the concern is immediately life-threatening.

---

## Security & Privacy

- Patient medication details are **never disclosed** to anyone except the confirmed patient
- If identity cannot be confirmed, the call ends immediately without sharing any health data
- Internal JSON output is **never spoken aloud** during the call
- Proxy responses (family members answering on behalf) are rejected — agent requests to speak directly with the patient
- No patient data is logged beyond what is written to the designated Google Sheet

---

## License

This project is proprietary to TrimRX. Unauthorized distribution or use is prohibited.

---

## Contact

For integration support or configuration questions, contact your TrimRX automation team.
