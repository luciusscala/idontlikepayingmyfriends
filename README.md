# Trip Commitment System

A minimal backend prototype that implements a Stripe-based trip commitment system. Travelers can commit to trips with their payment information, and when the total committed amount reaches a threshold, all payments are automatically captured.

## Features

- **Trip Management**: Create trips with configurable threshold amounts
- **Traveler Commitments**: Travelers can commit to trips with payment information
- **Automatic Payment Capture**: When threshold is met, all pending payments are captured
- **Stripe Integration**: Uses Stripe PaymentIntents with manual capture
- **Real-time Status**: Check trip status and commitment details

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Stripe

1. Copy the environment example file:
   ```bash
   cp env.example .env
   ```

2. Get your Stripe API keys from the [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys)

3. Update `.env` with your test keys:
   ```
   STRIPE_SECRET_KEY=sk_test_your_actual_secret_key_here
   STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key_here
   ```

### 3. Run the Server

```bash
python app.py
```

The API will be available at `http://localhost:8000`

### 4. Test the API

Run the test script to see the system in action:

```bash
python test_api.py
```

## API Endpoints

### Create a Trip
```http
POST /trips
Content-Type: application/json

{
  "threshold_amount": 10000
}
```

### Commit to a Trip
```http
POST /trips/{trip_id}/commit
Content-Type: application/json

{
  "traveler_name": "Alice",
  "committed_amount": 3000,
  "payment_method_id": "pm_card_visa"
}
```

### Get Trip Status
```http
GET /trips/{trip_id}/status
```

## Testing with Stripe Test Cards

The system uses Stripe test payment methods. Here are some test payment method IDs you can use:

- `pm_card_visa` - Visa card that will succeed
- `pm_card_mastercard` - Mastercard that will succeed  
- `pm_card_amex` - American Express that will succeed
- `pm_card_chargeDeclined` - Card that will be declined

## Example Flow

1. **Create a trip** with a $100 threshold
2. **Alice commits** $30 (payment authorized but not captured)
3. **Bob commits** $40 (payment authorized but not captured)
4. **Charlie commits** $50 (total now $120, threshold met!)
5. **All payments are automatically captured** and statuses updated

## Architecture

### Data Models

- **Trip**: `trip_id`, `threshold_amount`, `total_committed`
- **TravelerCommitment**: `commitment_id`, `trip_id`, `payment_intent_id`, `committed_amount`, `status`

### Payment Flow

1. Traveler provides payment method ID
2. Stripe PaymentIntent created with `capture_method=manual`
3. Payment is authorized but not charged
4. When threshold is met, all pending PaymentIntents are captured
5. Status updated based on capture results

### Status Values

- `pending`: Payment authorized but not captured
- `captured`: Payment successfully captured
- `failed`: Payment capture failed

## Development Notes

- Uses in-memory storage (trips_db, travelers_db)
- No user authentication required
- Minimal error handling focused on core functionality
- All amounts stored in cents to avoid floating-point issues
- Console logging shows key events and status changes

## Stripe Test Mode

This system is designed to work with Stripe test mode. Make sure you're using test API keys (starting with `sk_test_` and `pk_test_`). No real money will be charged.

## Error Handling

The system includes basic error handling for:
- Stripe API errors
- Invalid trip IDs
- Payment method validation
- Payment capture failures

## Next Steps

This is a minimal prototype. For production, consider:
- Database persistence (PostgreSQL, MongoDB)
- User authentication and authorization
- Webhook handling for payment status updates
- Email notifications
- Trip management UI
- Refund capabilities
- Multi-currency support
