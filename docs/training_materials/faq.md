# FAQ
Source: https://docs.trade.mudrex.com/docs/faq
Date Scraped: 2026-01-24

---

What does

offset

mean on list endpoints?

End-time boundary in Unix ms. Results are returned up to that time. If omitted, current server time is used.

Which leverage wins if I set it via Leverage API and in Order Create?

The leverage value in Order Create overrides and updates leverage for that asset/position.

MARKET vs LIMIT orders

Set

trigger_type

to

"MARKET"

or

"LIMIT"

. For

"LIMIT"

, include

order_price

.

Decimal inputs

Send decimals as strings (e.g.,

"0.001"

,

"107526"

) to avoid precision issues.

Do I need public endpoints or HMAC headers?

No. All

/fapi/v1

endpoints require

X-Authentication

. Public endpoints and HMAC are not part of MVP.

Updated

2 days ago

Ask AI
