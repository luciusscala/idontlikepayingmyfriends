import os
import uuid
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

import stripe
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    raise ValueError("STRIPE_SECRET_KEY environment variable is required")

app = FastAPI(title="Trip Commitment System", version="1.0.0")

# In-memory storage (in production, use a proper database)
trips_db: List['Trip'] = []
travelers_db: List['TravelerCommitment'] = []

class CommitmentStatus(str, Enum):
    PENDING = "pending"
    CAPTURED = "captured"
    FAILED = "failed"

@dataclass
class Trip:
    trip_id: str
    threshold_amount: int  # Amount in cents
    total_committed: int = 0  # Amount in cents
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class TravelerCommitment:
    commitment_id: str
    trip_id: str
    payment_intent_id: str
    committed_amount: int  # Amount in cents
    status: CommitmentStatus
    traveler_name: str
    created_at: datetime = field(default_factory=datetime.now)

# Pydantic models for API requests/responses
class CreateTripRequest(BaseModel):
    threshold_amount: int  # Amount in cents

class CreateTripResponse(BaseModel):
    trip_id: str
    threshold_amount: int
    total_committed: int
    created_at: datetime

class CommitToTripRequest(BaseModel):
    traveler_name: str
    committed_amount: int  # Amount in cents
    payment_method_id: str  # Stripe payment method ID

class CommitToTripResponse(BaseModel):
    commitment_id: str
    payment_intent_id: str
    status: CommitmentStatus
    committed_amount: int

class TripStatusResponse(BaseModel):
    trip_id: str
    threshold_amount: int
    total_committed: int
    threshold_met: bool
    travelers: List[dict]

# Helper functions
def find_trip(trip_id: str) -> Optional[Trip]:
    """Find a trip by ID"""
    for trip in trips_db:
        if trip.trip_id == trip_id:
            return trip
    return None

def get_trip_travelers(trip_id: str) -> List[TravelerCommitment]:
    """Get all travelers for a specific trip"""
    return [t for t in travelers_db if t.trip_id == trip_id]

def update_trip_total_committed(trip_id: str):
    """Update the total committed amount for a trip"""
    trip = find_trip(trip_id)
    if trip:
        trip.total_committed = sum(
            t.committed_amount for t in get_trip_travelers(trip_id) 
            if t.status == CommitmentStatus.PENDING or t.status == CommitmentStatus.CAPTURED
        )

def check_and_capture_payments(trip_id: str):
    """Check if threshold is met and capture all pending payments"""
    trip = find_trip(trip_id)
    if not trip:
        return
    
    if trip.total_committed >= trip.threshold_amount:
        print(f"🎉 Threshold reached for trip {trip_id}! Total: ${trip.total_committed/100:.2f}, Threshold: ${trip.threshold_amount/100:.2f}")
        
        # Get all pending commitments for this trip
        pending_commitments = [
            t for t in get_trip_travelers(trip_id) 
            if t.status == CommitmentStatus.PENDING
        ]
        
        # Capture each pending payment
        for commitment in pending_commitments:
            try:
                # Capture the payment intent
                payment_intent = stripe.PaymentIntent.capture(commitment.payment_intent_id)
                
                if payment_intent.status == 'succeeded':
                    commitment.status = CommitmentStatus.CAPTURED
                    print(f"✅ Successfully captured ${commitment.committed_amount/100:.2f} from {commitment.traveler_name}")
                else:
                    commitment.status = CommitmentStatus.FAILED
                    print(f"❌ Failed to capture payment from {commitment.traveler_name}")
                    
            except stripe.error.StripeError as e:
                commitment.status = CommitmentStatus.FAILED
                print(f"❌ Stripe error capturing payment from {commitment.traveler_name}: {str(e)}")

# API Endpoints
@app.post("/trips", response_model=CreateTripResponse)
async def create_trip(request: CreateTripRequest):
    """Create a new trip with a threshold amount"""
    trip_id = str(uuid.uuid4())
    trip = Trip(
        trip_id=trip_id,
        threshold_amount=request.threshold_amount
    )
    trips_db.append(trip)
    
    print(f"🏖️  Created new trip {trip_id} with threshold ${trip.threshold_amount/100:.2f}")
    
    return CreateTripResponse(
        trip_id=trip.trip_id,
        threshold_amount=trip.threshold_amount,
        total_committed=trip.total_committed,
        created_at=trip.created_at
    )

@app.post("/trips/{trip_id}/commit", response_model=CommitToTripResponse)
async def commit_to_trip(trip_id: str, request: CommitToTripRequest):
    """A traveler commits to a trip with payment info"""
    # Check if trip exists
    trip = find_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Create payment intent with manual capture
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=request.committed_amount,
            currency='usd',
            payment_method=request.payment_method_id,
            confirmation_method='manual',
            capture_method='manual',
            confirm=True,
            return_url='https://example.com/return'  # Not used in this flow
        )
        
        # Create commitment record
        commitment_id = str(uuid.uuid4())
        commitment = TravelerCommitment(
            commitment_id=commitment_id,
            trip_id=trip_id,
            payment_intent_id=payment_intent.id,
            committed_amount=request.committed_amount,
            status=CommitmentStatus.PENDING,
            traveler_name=request.traveler_name
        )
        travelers_db.append(commitment)
        
        # Update trip's total committed amount
        update_trip_total_committed(trip_id)
        
        print(f"💳 {request.traveler_name} committed ${request.committed_amount/100:.2f} to trip {trip_id}")
        print(f"   Payment Intent: {payment_intent.id}")
        print(f"   Total committed so far: ${trip.total_committed/100:.2f}")
        
        # Check if threshold is met and capture payments
        check_and_capture_payments(trip_id)
        
        return CommitToTripResponse(
            commitment_id=commitment_id,
            payment_intent_id=payment_intent.id,
            status=commitment.status,
            committed_amount=request.committed_amount
        )
        
    except stripe.error.StripeError as e:
        print(f"❌ Stripe error creating payment intent: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")

@app.get("/trips/{trip_id}/status", response_model=TripStatusResponse)
async def get_trip_status(trip_id: str):
    """Get trip status including total committed and threshold status"""
    trip = find_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Update total committed amount
    update_trip_total_committed(trip_id)
    
    # Get all travelers for this trip
    travelers = get_trip_travelers(trip_id)
    travelers_info = [
        {
            "traveler_name": t.traveler_name,
            "committed_amount": t.committed_amount,
            "status": t.status,
            "created_at": t.created_at
        }
        for t in travelers
    ]
    
    threshold_met = trip.total_committed >= trip.threshold_amount
    
    return TripStatusResponse(
        trip_id=trip.trip_id,
        threshold_amount=trip.threshold_amount,
        total_committed=trip.total_committed,
        threshold_met=threshold_met,
        travelers=travelers_info
    )

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Trip Commitment System API", "status": "running"}

@app.get("/test")
async def test_page():
    """Serve the test page"""
    return FileResponse("test_page.html")

@app.get("/config")
async def get_config():
    """Get frontend configuration including Stripe keys"""
    return {
        "stripe_publishable_key": os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_mock_key"),
        "api_base": "http://localhost:8000"
    }

@app.get("/trips", response_model=List[CreateTripResponse])
async def list_trips():
    """List all trips"""
    return [
        CreateTripResponse(
            trip_id=trip.trip_id,
            threshold_amount=trip.threshold_amount,
            total_committed=trip.total_committed,
            created_at=trip.created_at
        )
        for trip in trips_db
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
