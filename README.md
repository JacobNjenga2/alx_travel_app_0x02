# ALX Travel App 0x02 - Payment Integration

## 🧭 Overview
This project demonstrates **Chapa Payment Gateway integration** into a Django-based travel booking application. Building upon the ALX Travel App 0x01, this version adds secure payment processing, transaction tracking, and automated email notifications. The app now provides a complete booking workflow from listing discovery to payment completion.

**Key Focus Areas:**
- 💳 **Payment Gateway Integration** with Chapa API
- 🔐 **Secure Credential Management** using environment variables
- 📊 **Transaction Tracking** with comprehensive payment models
- 📧 **Automated Email Notifications** using Celery background tasks
- ✅ **Payment Verification** and status handling

---

## ✨ Features

### 📦 Core Models
- **Listing**: Represents an accommodation or property
- **Booking**: Represents a reservation with automatic total calculation
- **Review**: Represents user feedback for a listing
- **Payment**: 🆕 Comprehensive payment tracking with Chapa integration

### 💳 Payment Integration
- **Chapa API Integration**: Secure payment processing using Chapa payment gateway
- **Multiple Payment States**: Pending, Processing, Completed, Failed, Cancelled, Refunded
- **Transaction Tracking**: Complete audit trail of payment transactions
- **Webhook Support**: Real-time payment status updates from Chapa
- **Error Handling**: Graceful handling of payment failures and timeouts

### 🔗 API Endpoints
- **ListingSerializer**: Converts `Listing` model to and from JSON
- **BookingSerializer**: Enhanced with payment integration
- **PaymentSerializer**: Complete payment transaction data
- **Payment APIs**: Initiation, verification, and status endpoints

### 📧 Background Tasks (Celery)
- **Payment Confirmation Emails**: Automated success notifications
- **Payment Failure Notifications**: Customer alerts for failed payments
- **Booking Reminders**: Pre-arrival notifications
- **Cleanup Tasks**: Automatic cleanup of expired payments

### 🌱 Data Seeder
Custom management command to generate sample listings, bookings, and reviews for development/testing.

> Run with:
```bash
python manage.py seed
```

## 🧩 Models

### Listing
- `id`: Auto-incrementing primary key
- `title`: Name of the property/listing
- `description`: Detailed property description
- `price_per_night`: Decimal price per night
- `address`: Property location/address
- `host`: ForeignKey to User (property owner)
- `created_at`: Timestamp of listing creation

### Booking
- `id`: Auto-incrementing primary key
- `listing`: ForeignKey to Listing
- `user`: ForeignKey to User (guest)
- `check_in`: Check-in date
- `check_out`: Check-out date
- `guests`: Number of guests
- `total_amount`: 🆕 Calculated total booking amount
- `created_at`: Timestamp of booking creation

### Review
- `id`: Auto-incrementing primary key
- `listing`: ForeignKey to Listing
- `user`: ForeignKey to User (reviewer)
- `rating`: Integer rating (1-5)
- `comment`: Text review content
- `created_at`: Review timestamp

### Payment 🆕
- `id`: UUID primary key for security
- `booking`: OneToOneField to Booking
- `amount`: Payment amount (Decimal)
- `currency`: Currency code (default: ETB)
- `status`: Payment status (pending/processing/completed/failed/cancelled/refunded)
- `chapa_transaction_id`: Chapa transaction reference
- `chapa_checkout_url`: Chapa payment page URL
- `chapa_reference`: Unique payment reference
- `payment_method`: Payment method used
- `customer_email`: Customer email address
- `customer_phone`: Customer phone number
- `customer_name`: Customer full name
- `failure_reason`: Reason for payment failure (if applicable)
- `created_at`: Payment initiation timestamp
- `updated_at`: Last update timestamp
- `paid_at`: Payment completion timestamp

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Django 5.2+
- MySQL Database
- Redis (for Celery background tasks)
- Chapa API Account

### 🔧 Environment Setup

1. **Clone and Setup Virtual Environment**
```bash
git clone https://github.com/JacobNjenga2/alx_travel_app_0x02.git
cd alx_travel_app_0x02
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**
```bash
pip install -r alx_travel_app/requirement.txt
```

3. **Configure Environment Variables**

Create a `.env` file in the project root:
```env
# Chapa Payment Gateway Configuration
CHAPA_SECRET_KEY=CHASECK_TEST-your-test-key-here

# Django Configuration
DEBUG=True
SECRET_KEY=your-secret-key-here

# Database Configuration
MYSQL_DB=alx_travel_db
MYSQL_USER=your_db_user
MYSQL_PASSWORD=your_db_password
MYSQL_HOST=localhost
MYSQL_PORT=3306

# Email Configuration (for payment confirmations)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=noreply@alxtravel.com

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

4. **Database Setup**
```bash
# Create database migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Seed the database with sample data
python manage.py seed

# Create superuser (optional)
python manage.py createsuperuser
```

5. **Start Services**

**Terminal 1 - Django Development Server:**
```bash
python manage.py runserver
```

**Terminal 2 - Celery Worker (for background tasks):**
```bash
celery -A alx_travel_app worker --loglevel=info
```

**Terminal 3 - Redis Server:**
```bash
redis-server
```

## 💳 Payment API Endpoints

The application provides RESTful API endpoints for complete payment workflow management.

### Base URL
```
http://localhost:8000/api/
```

### Authentication
All payment endpoints require authentication. Include the Authorization header:
```
Authorization: Bearer <your-token>
```

### 1. Initiate Payment
Create a payment for a booking and get Chapa checkout URL.

**Endpoint:** `POST /payments/initiate/`

**Request Body:**
```json
{
  "booking_id": 1,
  "customer_email": "customer@example.com",
  "customer_phone": "+251911123456",
  "customer_name": "John Doe",
  "return_url": "https://yourdomain.com/payment-success",
  "webhook_url": "https://yourdomain.com/payment-webhook"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Payment initiated successfully",
  "payment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "checkout_url": "https://checkout.chapa.co/checkout/payment/...",
  "reference": "TRV-ABC12345",
  "amount": "150.00",
  "currency": "ETB"
}
```

### 2. Verify Payment
Verify payment status after customer completes payment.

**Endpoint:** `POST /payments/verify/`

**Request Body:**
```json
{
  "transaction_id": "TRV-ABC12345"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Payment verification completed",
  "payment": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "completed",
    "amount": "150.00",
    "currency": "ETB",
    "chapa_reference": "TRV-ABC12345",
    "payment_method": "telebirr",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "paid_at": "2024-01-15T10:35:00Z",
    "booking_details": {
      "booking_id": 1,
      "listing_title": "Cozy Downtown Apartment",
      "check_in": "2024-02-01",
      "check_out": "2024-02-05",
      "guests": 2
    }
  }
}
```

### 3. Get Payment Status
Check current payment status by payment ID.

**Endpoint:** `GET /payments/{payment_id}/status/`

**Response:**
```json
{
  "success": true,
  "payment": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "completed",
    "amount": "150.00",
    "currency": "ETB",
    "chapa_reference": "TRV-ABC12345",
    "payment_method": "telebirr",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "paid_at": "2024-01-15T10:35:00Z",
    "booking_details": {
      "booking_id": 1,
      "listing_title": "Cozy Downtown Apartment",
      "check_in": "2024-02-01",
      "check_out": "2024-02-05",
      "guests": 2
    }
  }
}
```

### 4. Payment Webhook
Endpoint for Chapa to send payment status updates.

**Endpoint:** `POST /payments/webhook/`

**Note:** This endpoint is called automatically by Chapa when payment status changes.

## 🔄 Payment Workflow

### Complete Payment Flow

1. **Create Booking**
   ```
   POST /bookings/
   ```

2. **Initiate Payment**
   ```
   POST /payments/initiate/
   → Returns Chapa checkout URL
   ```

3. **Customer Pays**
   ```
   Customer completes payment on Chapa checkout page
   ```

4. **Webhook Notification**
   ```
   Chapa sends status update to /payments/webhook/
   → Payment status updated automatically
   → Email confirmation sent via Celery
   ```

5. **Verify Payment (Optional)**
   ```
   POST /payments/verify/
   → Manual verification if needed
   ```

### Payment Status Flow
```
pending → processing → completed ✅
   ↓         ↓           ↓
cancelled  failed    refunded
```

## 🔐 Security Features

- **Environment Variables**: All sensitive data stored in `.env` file
- **UUID Payment IDs**: Unpredictable payment identifiers
- **Webhook Verification**: All webhook data verified with Chapa API
- **Request Validation**: Comprehensive input validation and sanitization
- **Error Handling**: Graceful error handling with detailed logging
- **CORS Configuration**: Properly configured cross-origin requests

## 📧 Email Notifications

Automated email notifications are sent using Celery background tasks:

- ✅ **Payment Confirmation**: Sent immediately after successful payment
- ❌ **Payment Failure**: Sent when payment fails or is cancelled
- 📅 **Booking Reminders**: Sent 1 day before check-in (optional)
- 🧹 **Cleanup Notifications**: Automatic cleanup of expired payments

## 🧪 Testing with Chapa Sandbox

1. **Get Test Credentials**
   - Sign up at [Chapa Developer Portal](https://developer.chapa.co/)
   - Get your test secret key (starts with `CHASECK_TEST-`)

2. **Test Payment Flow**
   ```bash
   # Use test credentials in .env
   CHAPA_SECRET_KEY=CHASECK_TEST-your-test-key
   
   # Test with sandbox URLs
   # Chapa provides test card numbers and phone numbers
   ```

3. **Sample Test Data**
   ```json
   {
     "customer_email": "test@example.com",
     "customer_phone": "+251911000000",
     "customer_name": "Test Customer"
   }
   ```

## 📊 Monitoring and Logging

- **Payment Logging**: All payment operations logged with transaction IDs
- **Error Tracking**: Failed payments logged with detailed error messages
- **Webhook Logging**: All webhook events tracked and verified
- **Email Logging**: Email sending status and failures logged

## 🤝 Contributing
Pull requests are welcome!
For major changes, please open an issue first to discuss what you'd like to improve.

## 📄 License
This project is licensed for ALX learning purposes.

## 🏗️ Architecture Overview

The payment integration follows a microservices-inspired architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Django API     │    │  Chapa API      │
│   (React/Vue)   │◄──►│  (REST APIs)    │◄──►│  (Payment       │
│                 │    │                 │    │   Gateway)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Database      │    │   Webhooks      │
                    │   (MySQL)       │    │   (Real-time    │
                    │                 │    │    Updates)     │
                    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │  Celery Worker  │◄──►│  Email Service  │
                    │  (Background    │    │  (SMTP)         │
                    │   Tasks)        │    │                 │
                    └─────────────────┘    └─────────────────┘
```

## 📈 Key Implementation Highlights

### ✅ Completed Features

1. **💳 Payment Model Integration**
   - Comprehensive Payment model with UUID primary keys
   - OneToOne relationship with Booking model
   - Multiple payment states and status tracking
   - Automatic payment reference generation

2. **🔗 Chapa API Service**
   - Dedicated service class for Chapa interactions
   - Payment initiation and verification methods
   - Robust error handling and logging
   - HTTP request management with proper timeouts

3. **🌐 RESTful API Endpoints**
   - Payment initiation endpoint (`/payments/initiate/`)
   - Payment verification endpoint (`/payments/verify/`)
   - Payment status endpoint (`/payments/{id}/status/`)
   - Webhook endpoint for real-time updates (`/payments/webhook/`)

4. **📧 Background Email System**
   - Celery integration for asynchronous tasks
   - Payment confirmation emails
   - Payment failure notifications
   - Booking reminder system
   - Automated cleanup tasks

5. **🔐 Security Implementation**
   - Environment variable configuration
   - Webhook verification with Chapa API
   - Input validation and sanitization
   - UUID-based payment identifiers
   - Comprehensive error handling

### 🎯 Business Logic Implementation

- **Automatic Total Calculation**: Booking totals calculated based on nights × price_per_night
- **Payment State Management**: Clear state transitions from pending to completed
- **Idempotent Operations**: Prevent duplicate payments for same booking
- **Graceful Error Handling**: Failed payments properly logged and customers notified
- **Real-time Updates**: Webhook integration for instant payment status updates

## 🚀 Production Readiness

This implementation includes several production-ready features:

- **Scalable Architecture**: Celery workers can be scaled horizontally
- **Database Optimization**: Proper indexing and relationships
- **Monitoring**: Comprehensive logging throughout the payment flow
- **Error Recovery**: Retry mechanisms for failed operations
- **Security**: All sensitive data properly secured

## 📝 Development Notes

- **Test Environment**: Use Chapa sandbox for development and testing
- **Database**: MySQL for production, SQLite for local development
- **Caching**: Redis used for Celery message broker
- **Email**: SMTP configuration for transactional emails
- **Deployment**: Docker-ready with environment configuration

## ✍️ Author
**Jacob N.** / ALX Student

*Specialized in backend development, payment gateway integration, and Django REST API development.*

---

**🎉 Successfully implemented a complete payment processing system with Chapa integration, including secure transaction handling, real-time status updates, and automated customer communications.**
