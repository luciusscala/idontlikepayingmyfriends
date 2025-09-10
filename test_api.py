#!/usr/bin/env python3
"""
Test script for the Trip Commitment System API
This script demonstrates the complete flow using Stripe test cards.
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"

# Stripe test payment method IDs (these work with Stripe test mode)
TEST_PAYMENT_METHODS = {
    "visa_success": "pm_card_visa",  # Visa card that will succeed
    "visa_declined": "pm_card_chargeDeclined",  # Visa card that will be declined
    "mastercard_success": "pm_card_mastercard",  # Mastercard that will succeed
    "amex_success": "pm_card_amex",  # American Express that will succeed
}

def create_trip(threshold_amount_cents):
    """Create a new trip"""
    print(f"\n🏖️  Creating trip with threshold ${threshold_amount_cents/100:.2f}")
    
    response = requests.post(f"{BASE_URL}/trips", json={
        "threshold_amount": threshold_amount_cents
    })
    
    if response.status_code == 200:
        trip_data = response.json()
        print(f"✅ Trip created: {trip_data['trip_id']}")
        return trip_data['trip_id']
    else:
        print(f"❌ Failed to create trip: {response.text}")
        return None

def commit_to_trip(trip_id, traveler_name, amount_cents, payment_method_key):
    """Commit a traveler to a trip"""
    print(f"\n💳 {traveler_name} committing ${amount_cents/100:.2f}")
    
    response = requests.post(f"{BASE_URL}/trips/{trip_id}/commit", json={
        "traveler_name": traveler_name,
        "committed_amount": amount_cents,
        "payment_method_id": TEST_PAYMENT_METHODS[payment_method_key]
    })
    
    if response.status_code == 200:
        commit_data = response.json()
        print(f"✅ Commitment created: {commit_data['commitment_id']}")
        print(f"   Status: {commit_data['status']}")
        return commit_data
    else:
        print(f"❌ Failed to commit: {response.text}")
        return None

def get_trip_status(trip_id):
    """Get trip status"""
    print(f"\n📊 Getting status for trip {trip_id}")
    
    response = requests.get(f"{BASE_URL}/trips/{trip_id}/status")
    
    if response.status_code == 200:
        status_data = response.json()
        print(f"✅ Trip Status:")
        print(f"   Threshold: ${status_data['threshold_amount']/100:.2f}")
        print(f"   Total Committed: ${status_data['total_committed']/100:.2f}")
        print(f"   Threshold Met: {status_data['threshold_met']}")
        print(f"   Travelers: {len(status_data['travelers'])}")
        
        for traveler in status_data['travelers']:
            print(f"     - {traveler['traveler_name']}: ${traveler['committed_amount']/100:.2f} ({traveler['status']})")
        
        return status_data
    else:
        print(f"❌ Failed to get status: {response.text}")
        return None

def test_successful_flow():
    """Test the complete successful flow"""
    print("=" * 60)
    print("🧪 TESTING SUCCESSFUL FLOW")
    print("=" * 60)
    
    # Create a trip with $100 threshold
    trip_id = create_trip(10000)  # $100.00 in cents
    if not trip_id:
        return
    
    # First traveler commits $30
    commit_to_trip(trip_id, "Alice", 3000, "visa_success")
    get_trip_status(trip_id)
    
    # Second traveler commits $40
    commit_to_trip(trip_id, "Bob", 4000, "mastercard_success")
    get_trip_status(trip_id)
    
    # Third traveler commits $50 (this should trigger the threshold)
    commit_to_trip(trip_id, "Charlie", 5000, "amex_success")
    get_trip_status(trip_id)

def test_failed_payment_flow():
    """Test flow with a failed payment"""
    print("\n" + "=" * 60)
    print("🧪 TESTING FAILED PAYMENT FLOW")
    print("=" * 60)
    
    # Create a trip with $50 threshold
    trip_id = create_trip(5000)  # $50.00 in cents
    if not trip_id:
        return
    
    # First traveler commits $30 (success)
    commit_to_trip(trip_id, "David", 3000, "visa_success")
    get_trip_status(trip_id)
    
    # Second traveler commits $20 with a card that will be declined
    commit_to_trip(trip_id, "Eve", 2000, "visa_declined")
    get_trip_status(trip_id)

def test_partial_threshold():
    """Test when threshold is not met"""
    print("\n" + "=" * 60)
    print("🧪 TESTING PARTIAL THRESHOLD")
    print("=" * 60)
    
    # Create a trip with $200 threshold
    trip_id = create_trip(20000)  # $200.00 in cents
    if not trip_id:
        return
    
    # First traveler commits $50
    commit_to_trip(trip_id, "Frank", 5000, "visa_success")
    get_trip_status(trip_id)
    
    # Second traveler commits $75
    commit_to_trip(trip_id, "Grace", 7500, "mastercard_success")
    get_trip_status(trip_id)
    
    print("ℹ️  Threshold not met yet - no payments captured")

if __name__ == "__main__":
    print("🚀 Starting Trip Commitment System API Tests")
    print("Make sure the API server is running on http://localhost:8000")
    print("Press Enter to continue...")
    input()
    
    try:
        # Test health endpoint
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print("❌ API is not responding")
            exit(1)
        
        # Run tests
        test_successful_flow()
        test_failed_payment_flow()
        test_partial_threshold()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
