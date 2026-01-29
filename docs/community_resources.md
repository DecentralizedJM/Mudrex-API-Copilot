# Community resources and common questions

This document covers: Mudrex SDKs, fee structure, and trade ideas/signals. Use it when users ask about these topics.

---

## SDKs for Mudrex

When users ask about **SDKs**, **Python SDK**, **client library**, or **how to trade programmatically with Mudrex**:

- **Unofficial community Python SDK (works):** https://github.com/DecentralizedJM/mudrex-api-trading-python-sdk  
- Tell users: This is an **unofficial** repo created for the community; it **works** and supports symbol-first trading, 500+ pairs, orders, positions, leverage, and MCP.  
- **Official SDK:** An official SDK will be released by Mudrex soon; until then, the community SDK is a working option.

Keywords: SDK, Python SDK, client library, programmatic trading, mudrex sdk, library for Mudrex.

---

## Fee structure and how to see fees

When users ask about **fees**, **fee structure**, **trading fees**, or **what are the charges**:

- **Current fee (as of now):** Futures fee is **0.05%** (confirm on the link below for latest tiers).  
- **Full fee structure and Alpha tiers:** https://mudrex.com/blog/new-mudrex-alpha/  
- **How to see fees deducted (API):** Use the fee history endpoint so users can list fees charged on their account.

**Endpoint:** `GET /fapi/v1/futures/fee/history`  
- Docs: https://docs.trade.mudrex.com/docs/fees  
- Parameters: `limit`, `offset`  
- Response includes: `symbol`, `fee_amount`, `fee_perc`, `fee_type` (TRANSACTION or FUNDING), `created_at`, `transaction_amount`

**Example (Python) – list recent fees:**

```python
import requests

BASE_URL = "https://trade.mudrex.com/fapi/v1"
headers = {"X-Authentication": "your_api_secret"}

resp = requests.get(f"{BASE_URL}/futures/fee/history", headers=headers, params={"limit": 20})
data = resp.json()
if data.get("success") and data.get("data"):
    for fee in data["data"]:
        print(f"{fee['created_at']} | {fee['symbol']} | {fee['fee_type']} | {fee['fee_perc']}% | {fee['fee_amount']}")
```

Keywords: fees, fee structure, 0.05%, trading charges, fee history, how to see fees deducted, Alpha tiers.

---

## Trade ideas and signals

When users ask about **trade ideas**, **signals**, **signal broadcasting**, **TIA**, or **automated signals**:

- **Signal broadcasting service (community):** https://github.com/DecentralizedJM/TIA-Service-Broadcaster  
- Tell users: When signals are **published**, a **WebSocket** streams them in real time. Install and use the **SDK/service** to **receive** and **execute** those signals (e.g. on your own machine with your API key).  
- The broadcaster does not store your API keys; execution is local/decentralized.

Keywords: trade ideas, signals, TIA, signal broadcasting, WebSocket signals, receive signals, execute signals, Trade Ideas Automation.
