# Bitespeed Identity Reconciliation Service

## Overview

This service identifies and consolidates customer contacts across multiple purchases.

If a request shares either email or phoneNumber with an existing contact, 
the records are linked together.

Oldest contact remains primary. Others become secondary.

---

## Tech Stack

- FastAPI (Python)
- SQLAlchemy
- SQLite
- Uvicorn

---

## Endpoint

POST /identify

### Request Body

```json
{
  "email": "string",
  "phoneNumber": "string"
}
```

### Response Format

```json
{
  "contact": {
    "primaryContatctId": number,
    "emails": [],
    "phoneNumbers": [],
    "secondaryContactIds": []
  }
}
```

---

## Local Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app
```

Visit:
http://127.0.0.1:8000/docs# bitespeed-identity-service
## Hosted API

Base URL:
https://bitespeed-identity-service-ss6w.onrender.com

Swagger Docs:
https://bitespeed-identity-service-ss6w.onrender.com/docs

Github Repo:
https://github.com/daiviksinha2004-pixel/bitespeed-identity-service

Endpoint:
POST /identify

