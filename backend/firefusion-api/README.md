# 🔐 FireFusion API – Auth0 JWT Authentication

## 📌 Overview

This project implements secure authentication and authorization for the FireFusion API using Auth0 and JWT (JSON Web Tokens).

The solution demonstrates:
- Auth0 integration with backend APIs
- JWT access token validation using JWKS
- Protected API endpoints
- Scope-based authorization
- Backend-only testing using curl/Postman (no frontend dependency)

---

## ⚙️ Technologies Used

- FastAPI
- Auth0
- JWT (RS256)
- PyJWT
- Uvicorn
- Python 3.9+

---

## 🔑 Auth0 Configuration

### API Setup

- Name: FireFusion API  
- Identifier (Audience): https://firefusion-api  
- Signing Algorithm: RS256  

---

### Permission (Scope)

read:fire-data

Used to restrict access to sensitive endpoints.

---

### Machine-to-Machine Application

A Machine-to-Machine (M2M) application was created to generate access tokens using:

grant_type: client_credentials

This allows backend testing without a frontend.

---

## 🔄 JWT Authentication Flow

1. Client requests an access token from Auth0  
2. Auth0 issues a JWT access token  
3. Client sends request with header:  
   Authorization: Bearer <access_token>  
4. FireFusion API:
   - Validates JWT signature using Auth0 JWKS
   - Verifies issuer and audience
   - Checks required scope (if needed)
5. Access is granted or denied  

---

## 📂 API Endpoints

### Public Endpoint

GET /auth-demo/public  

✔ No authentication required  

---

### Protected Endpoint

GET /auth-demo/protected  

✔ Requires a valid JWT access token  

---

### Scoped Endpoint

GET /auth-demo/fire-data  

✔ Requires scope: read:fire-data  

---

## 🧪 Testing (Using curl)

### Public Endpoint

curl http://localhost:8000/auth-demo/public

---

### Protected Endpoint (Without Token)

curl http://localhost:8000/auth-demo/protected

Expected:

{
  "detail": "Authorization header is missing"
}

---

### Protected Endpoint (With Token)

curl http://localhost:8000/auth-demo/protected \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

---

### Scoped Endpoint

curl http://localhost:8000/auth-demo/fire-data \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

---

## 📊 Sample Responses

### Protected Endpoint

{
  "message": "Access granted. Auth0 JWT token is valid.",
  "user": "client-id",
  "audience": "https://firefusion-api",
  "issuer": "https://firefusion-dev-demo.au.auth0.com/"
}

---

### Scoped Endpoint

{
  "message": "Scope validation successful",
  "sample_data": {
    "region": "Victoria",
    "risk_level": "High",
    "temperature": "32°C",
    "wind_speed": "28 km/h"
  },
  "scope": "read:fire-data"
}

---

## 🔐 Security Implementation

- JWT validation using Auth0 JWKS
- RS256 signature verification
- Audience validation (https://firefusion-api)
- Issuer validation
- Scope-based authorization
- Protected API endpoints

---

## ⚠️ Important Notes

- Existing FireFusion API endpoints were not modified  
- Authentication is implemented in isolated routes (/auth-demo)  
- Backend tested independently without frontend dependency  
- Compatible with Python 3.9 (uses Optional instead of modern union syntax)  

---

## ▶️ How to Run Locally

### 1. Navigate to backend

cd backend/firefusion-api

---

### 2. Install dependencies

pip install -r requirements.txt

---

### 3. Configure environment variables

Create a `.env` file:

AUTH0_DOMAIN=your-auth0-domain.au.auth0.com  
AUTH0_AUDIENCE=https://firefusion-api  

---

### 4. Run server

python3 -m uvicorn app.main:app --reload --port 8000

---

### 5. Access API

http://localhost:8000

---

## 👨‍💻 Contribution

- Implemented Auth0 JWT authentication in FastAPI backend  
- Developed protected and scoped API endpoints  
- Integrated JWKS-based token validation  
- Implemented scope-based access control (read:fire-data)  
- Performed backend testing using curl/Postman  

---

## 🚀 Outcome

✔ Secure authentication using Auth0  
✔ JWT validation fully functional  
✔ Scope-based authorization enforced  
✔ End-to-end backend testing completed  
✔ Ready for frontend integration  

---

## 📚 References

- https://auth0.com/docs  
- https://fastapi.tiangolo.com/  
- https://jwt.io/  