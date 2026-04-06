#!/usr/bin/env python
"""Test backward compatibility with direct contacts format"""

import json
import httpx
import asyncio

async def test_direct_contacts():
    """Test the direct contacts format (old format)"""
    
    # Test data in direct format (old style)
    direct_data = [
        {
            "call_id": "direct_1",
            "patient_name": "John Direct",
            "phone_number": "9191111111",
            "medication": "Lisinopril",
            "dosage": "10mg",
            "status": "pending"
        },
        {
            "call_id": "direct_2",
            "patient_name": "Jane Direct",
            "phone_number": "9192222222",
            "medication": "Atorvastatin",
            "dosage": "20mg",
            "status": "completed"
        },
        {
            "call_id": "direct_3",
            "patient_name": "Bob Direct",
            "phone_number": "9193333333",
            "medication": "Metformin",
            "dosage": "500mg",
            "status": "pending"
        }
    ]
    
    print("=" * 70)
    print("Testing Direct Contacts Format (Backward Compatibility)")
    print("=" * 70)
    print(f"\nSending {len(direct_data)} contacts in direct format...\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/webhook/contacts",
            json=direct_data,
            timeout=10.0
        )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 200 and result.get("success"):
        print(f"\n✅ SUCCESS: Imported {result.get('count')} contacts in direct format!")
    else:
        print("\n❌ FAILED to import contacts")
    
    # Test retrieval
    print("\n" + "=" * 70)
    print("Verifying Direct Format Contacts Were Stored")
    print("=" * 70 + "\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/contacts")
    
    contacts = response.json()
    print(f"Total contacts in system: {len(contacts)}")
    
    # Find and display the direct contacts
    direct_contacts = [c for c in contacts if c.get("call_id", "").startswith("direct")]
    if direct_contacts:
        print(f"\nDirect format contacts stored ({len(direct_contacts)}):")
        for contact in direct_contacts:
            print(f"  - {contact['patient_name']}: {contact['phone_number']}")

if __name__ == "__main__":
    asyncio.run(test_direct_contacts())
