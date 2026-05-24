# Production Deployment Guide for Renia AI

This guide outlines the production deployment lifecycle for the Renia AI voice SaaS platform. It covers containerized local operations, AWS cloud infrastructure deployment, environment keys setup, third-party webhook routing, and scaling best practices.

---

## 1. Environment Configurations Reference

Create a production `.env` file containing the following variables. Ensure all keys are kept secure and never committed to source control.

```ini
# App Basics
APP_NAME="Renia AI"
DEBUG=False
SECRET_KEY="production-super-secret-jwt-key"
ENCRYPTION_KEY="production-aes-256-fernet-key-32-bytes"

# Database Configuration (SQLite in dev, PostgreSQL in production)
DATABASE_URL="postgresql://postgres:securepassword@db:5432/grokdent_prod"

# xAI Grok Voice API
XAI_API_KEY="xai-grok-voice-api-key"
XAI_BASE_URL="https://api.x.ai/v1"

# Twilio Telephony credentials
TWILIO_ACCOUNT_SID="ACtwilioaccountsid"
TWILIO_AUTH_TOKEN="twilioauthtoken"
TWILIO_PHONE_NUMBER="+14075550100"

# Stripe Billing credentials
STRIPE_SECRET_KEY="sk_live_stripesecretkey"
STRIPE_WEBHOOK_SECRET="whsec_stripewebhooksecret"

# SendGrid Email notifications
SENDGRID_API_KEY="SG.sendgridapikey"

# Google Calendar Integration (JSON Service Account credentials)
GOOGLE_CALENDAR_CREDENTIALS_JSON='{"type": "service_account", "project_id": ...}'
GOOGLE_CALENDAR_ID="clinic-calendar@gmail.com"
```

---

## 2. Docker & Multi-Container Deployment

For quick, reliable, and isolated production scaling, utilize the multi-container configuration defined in `docker-compose.yml` and `Dockerfile`.

### Build and Launch Instructions:
1. Clone the repository to your production server:
   ```bash
   git clone https://github.com/yourorg/renia-ai.git
   cd renia-ai
   ```
2. Create the production environment configurations:
   ```bash
   cp .env.example .env
   nano .env # Set your keys, secrets, and database passwords
   ```
3. Compile and boot the application stacks:
   ```bash
   docker-compose up -d --build
   ```
4. Verify the server health and database migrations:
   ```bash
   docker-compose exec backend alembic upgrade head
   docker-compose exec backend python scripts/seed_data.py
   ```

---

## 3. AWS Infrastructure Setup (EC2 + RDS + ALB)

To scale Renia AI with high availability, database replication, and automated SSL termination, deploy to Amazon Web Services (AWS).

```
               [ HTTPS / WSS Calls ]
                         |
                         v
           +-------------+-------------+
           |   Application Load Balancer | (Terminates SSL via ACM)
           +-------------+-------------+
                         |
        +----------------+----------------+
        |                                 |
        v                                 v
+-------+-------+                 +-------+-------+
|  EC2 Instance |                 |  EC2 Instance | (Running Docker container)
|  Availability |                 |  Availability |
|    Zone A     |                 |    Zone B     |
+-------+-------+                 +-------+-------+
        |                                 |
        +----------------+----------------+
                         |
                         v
           +-------------+-------------+
           |     Amazon RDS Postgres   | (Multi-AZ Deployment)
           +---------------------------+
```

### Infrastructure Components:
1. **Database Layer (Amazon RDS)**:
   - Create a Multi-AZ **PostgreSQL 15+** instance.
   - Restrict the security group to accept incoming traffic *only* from the EC2 application instances (Port 5432).
2. **Compute Layer (EC2 Autoscaling Group)**:
   - Provision EC2 instances using the Amazon Linux 2 AMI with Docker and Git installed.
   - Run the Renia AI container listening on port 8000.
3. **Routing Layer (Application Load Balancer - ALB)**:
   - Route traffic through an ALB with listener rules for HTTP (Port 80 redirect to 443) and HTTPS (Port 443).
   - Provision an SSL certificate using **AWS Certificate Manager (ACM)** for your custom domain (e.g., `dashboard.grokdent.fl`).
   - Configure health checks pointing to `/health` with a 200 OK expectation.

---

## 4. Third-Party API Webhooks Routing

Once the application is live under an HTTPS domain, configure third-party webhooks to link telephony and billing events.

### A. Twilio Voice Configuration
1. Log in to the [Twilio Console](https://console.twilio.com).
2. Navigate to **Develop** -> **Phone Numbers** -> **Active Numbers** and click on your Florida clinic phone number.
3. Scroll down to the **Voice & Fax** section.
4. Under **A Call Comes In**, select **Webhook** and set the URL to:
   `https://yourdomain.com/api/v1/webhooks/voice/incoming`
   Ensure the method is set to **HTTP POST**.
5. Under **Primary Handler Fails**, set the callback to your emergency voicemail.
6. Under **Call Status Changes**, set the status callback URL to:
   `https://yourdomain.com/api/v1/webhooks/voice/status`

### B. Stripe Webhook Configuration
1. Log in to the [Stripe Dashboard](https://dashboard.stripe.com).
2. Navigate to **Developers** -> **Webhooks** and click **Add Endpoint**.
3. Set the Endpoint URL to:
   `https://yourdomain.com/api/v1/billing/webhook`
4. Select the following events to listen to:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
5. Save the endpoint and copy the **Signing Secret** (`whsec_...`). Paste this value into your production `.env` under `STRIPE_WEBHOOK_SECRET`.

---

## 5. Security & Maintenance Auditing

- **Automated Backups**: Enable RDS daily snapshots with a 7-day retention period.
- **Log Management**: Forward Docker system logs to **AWS CloudWatch** or **Datadog** for centralized monitoring. Ensure no raw decrypted patient phone numbers or transcripts are leaked in text format log levels.
- **VPC Isolation**: Keep the RDS Postgres database and Redis cache inside private VPC subnets. Only the ALB should reside in public subnets.
