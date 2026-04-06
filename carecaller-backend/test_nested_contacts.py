#!/usr/bin/env python
"""Test script for nested contacts endpoint"""

import json
import httpx
import asyncio

async def test_nested_contacts():
    """Test the nested contacts format from n8n"""
    
    # Test data matching n8n format
    nested_data = [
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
    print("Testing Nested Contacts Format (n8n style)")
    print("=" * 70)
    print(f"\nSending {len(nested_data[0]['contacts'])} contacts in nested format...\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/webhook/contacts",
            json=nested_data,
            timeout=10.0
        )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 200 and result.get("success"):
        print(f"\n✅ SUCCESS: Imported {result.get('count')} contacts!")
    else:
        print("\n❌ FAILED to import contacts")
    
    # Test retrieval
    print("\n" + "=" * 70)
    print("Verifying Contacts Were Stored")
    print("=" * 70 + "\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/contacts")
    
    contacts = response.json()
    print(f"Total contacts in system: {len(contacts)}")
    print(f"Last contact stored:")
    if contacts:
        print(json.dumps(contacts[-1], indent=2))

if __name__ == "__main__":
    asyncio.run(test_nested_contacts())
