#!/usr/bin/env python
"""Test the exact n8n payload format"""
import httpx
import json

BASE_URL = "http://localhost:8000"

# Exact payload from n8n
n8n_payload = [
    {
        "contacts": [
            {
                "call_id": "row_2",
                "patient_name": "Akhil Mulagada",
                "phone_number": "919346315817",
                "medication": "Ozempic",
                "dosage": "1mg",
                "status": "pending"
            },
            {
                "call_id": "row_4",
                "patient_name": "Shreyak Bannisetti",
                "phone_number": "919346315817",
                "medication": "Ozempic",
                "dosage": "1mg",
                "status": "pending"
            },
            {
                "call_id": "row_5",
                "patient_name": "Mahi Rasagyna",
                "phone_number": "919346315817",
                "medication": "Ozempic",
                "dosage": "1mg",
                "status": "pending"
            },
            {
                "call_id": "row_6",
                "patient_name": "Sudhiksha",
                "phone_number": "919346315817",
                "medication": "Ozempic",
                "dosage": "1mg",
                "status": "pending"
            },
            {
                "call_id": "row_7",
                "patient_name": "Rishav V",
                "phone_number": "919346315817",
                "medication": "Ozempic",
                "dosage": "1mg",
                "status": "pending"
            }
        ]
    }
]

print("=" * 70)
print("🧪 Test 1: N8N List Format (what n8n actually sends)")
print("=" * 70)

try:
    response = httpx.post(
        f"{BASE_URL}/webhook/contacts",
        json=n8n_payload
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    if response.status_code == 200:
        print("✅ PASS - N8N format accepted!")
    else:
        print("❌ FAIL - N8N format rejected!")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("🧪 Test 2: Single ContactsWrapper (if n8n sends object directly)")
print("=" * 70)

single_wrapper = {
    "contacts": [
        {
            "call_id": "test_1",
            "patient_name": "Test User",
            "phone_number": "+1-555-9999",
            "medication": "TestMed",
            "dosage": "10mg",
            "status": "pending"
        }
    ]
}

try:
    response = httpx.post(
        f"{BASE_URL}/webhook/contacts",
        json=single_wrapper
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    if response.status_code == 200:
        print("✅ PASS - Single wrapper format accepted!")
    else:
        print("❌ FAIL - Single wrapper format rejected!")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("🧪 Test 3: Verify contacts were stored")
print("=" * 70)

try:
    response = httpx.get(f"{BASE_URL}/contacts")
    contacts = response.json()
    print(f"Total contacts stored: {len(contacts)}")
    if contacts:
        print("\nContacts:")
        for contact in contacts[:3]:
            print(f"  - {contact.get('patient_name')} ({contact.get('phone_number')})")
        if len(contacts) > 3:
            print(f"  ... and {len(contacts) - 3} more")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
