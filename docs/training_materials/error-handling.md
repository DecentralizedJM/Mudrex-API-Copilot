# Errors
Source: https://docs.trade.mudrex.com/docs/error-handling
Date Scraped: 2026-01-24

---

Error Response

JSON

{
  "success": false,
  "code": "ERROR_CODE",
  "message": "Human readable message",
  "requestId": "b7b2c2e5-8b8a-4e2a-9a4b-5f5b1f5d2e2a",
  "ts": 1737665012345
}

Errors Codes

Status code

Error Code

Description

400

INVALID_REQUEST

Bad or missing parameter

401

UNAUTHORIZED

Invalid or missing

X-Authentication

403

FORBIDDEN

Scope/IP not allowed

404

NOT_FOUND

Resource not found

409

CONFLICT

Conflicting or duplicate action

429

RATE_LIMIT_EXCEEDED

Throttled by rate limiter

5xx

SERVER_ERROR

Internal error; retry with backoff

Updated

2 days ago

Wallet

Ask AI
