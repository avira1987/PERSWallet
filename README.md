# Account Charging System / سیستم اکانتی با قابلیت شارژ

A full-stack account management system with wallet charging, payment gateway integration, user transfers, affiliate program, and admin dashboard.

## Features

- **Company Landing Page** - Beautiful RTL website with company introduction and E-Namad badge
- **Authentication** - Registration, login with Argon2 password hashing and JWT tokens
- **Two-Factor Authentication** - TOTP-based 2FA compatible with Google Authenticator & Microsoft Authenticator
- **Wallet System** - Digital wallet with balance tracking and transaction history
- **Multi-Gateway Payments** - Shaparak payment via ZarinPal, IDPay, Pay.ir, NextPay (switchable)
- **User Transfers** - Send balance between users by username or phone number
- **Pro Account Charging** - Dedicated page for sending charges to pro accounts
- **Affiliate Program** - Referral system with automatic commission on transactions
- **Admin Dashboard** - Manage users, transactions, and refund requests
- **Banking API** - Refund to bank accounts via Paya/Satna (IBAN-based)
- **Security** - Rate limiting, audit logs, CORS, CSRF protection

## Tech Stack

- **Backend**: Django 4.2 + Django REST Framework + PostgreSQL
- **Frontend**: React 18 + Vite + Tailwind CSS (RTL)
- **Auth**: Argon2 + JWT (SimpleJWT) + TOTP (pyotp)
- **Payments**: Shaparak gateways (Strategy Pattern)

## Project Structure

```
presWebsit/
├── backend/          # Django REST API
│   ├── config/       # Django settings, URLs
│   ├── accounts/     # User management, 2FA
│   ├── wallet/       # Wallet & transactions
│   ├── payments/     # Payment gateway integration
│   │   └── gateways/ # ZarinPal, IDPay, Pay.ir, NextPay
│   ├── transfers/    # User-to-user transfers
│   ├── affiliates/   # Affiliate/referral program
│   ├── banking/      # Refund API
│   └── tests/        # Test suite
├── frontend/         # React + Vite app
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── contexts/
│       └── api/
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
copy .env.example .env
# Edit .env with your database and gateway credentials

# Create database
# CREATE DATABASE account_system; (in PostgreSQL)

# Run migrations
python manage.py makemigrations accounts wallet payments transfers affiliates banking
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Running Tests

```bash
cd backend
python manage.py test tests
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/accounts/register/` | Register new user |
| POST | `/api/accounts/login/` | Login (with optional 2FA) |
| POST | `/api/accounts/token/refresh/` | Refresh JWT token |
| GET/PATCH | `/api/accounts/profile/` | View/update profile |
| POST | `/api/accounts/change-password/` | Change password |
| GET/POST | `/api/accounts/2fa/setup/` | Setup 2FA (QR code) |
| POST | `/api/accounts/2fa/disable/` | Disable 2FA |

### Wallet
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wallet/` | Get wallet balance |
| GET | `/api/wallet/transactions/` | List transactions |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/request/` | Initiate payment |
| POST | `/api/payments/verify/` | Verify payment callback |
| GET | `/api/payments/history/` | Payment history |

### Transfers
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/transfers/send/` | Send transfer |
| GET | `/api/transfers/history/` | Transfer history |
| GET | `/api/transfers/pro-accounts/` | List pro accounts |

### Affiliates
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/affiliates/profile/` | Affiliate profile & code |
| GET | `/api/affiliates/referrals/` | List referrals |
| GET | `/api/affiliates/commissions/` | List commissions |

### Banking (Refunds)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/banking/refund/` | Request refund |
| GET | `/api/banking/refunds/` | List user's refunds |
| GET | `/api/banking/admin/refunds/` | Admin: all refunds |
| PATCH | `/api/banking/admin/refunds/<id>/` | Admin: process refund |

## Payment Gateway Configuration

Set the active gateway in `.env`:

```env
ACTIVE_GATEWAY=zarinpal  # zarinpal, idpay, payir, nextpay
```

Each gateway can be configured independently:

```env
ZARINPAL_MERCHANT_ID=your-merchant-id
ZARINPAL_SANDBOX=True

IDPAY_API_KEY=your-api-key
IDPAY_SANDBOX=True

PAYIR_API_KEY=your-api-key
NEXTPAY_API_KEY=your-api-key
```

## Security Features

- **Argon2** password hashing (primary hasher)
- **TOTP 2FA** with Google/Microsoft Authenticator
- **JWT** with access/refresh token rotation
- **Rate limiting** on sensitive endpoints (30 req/min anon, 100 req/min auth)
- **Atomic transactions** with `select_for_update()` for financial operations
- **CORS** configured for frontend origin
- **Audit logs** for all sensitive operations
- **Input validation** on all endpoints
- **IBAN validation** for refund requests

## License

All rights reserved.
