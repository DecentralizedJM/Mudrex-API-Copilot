"""
Deterministic troubleshooting tools for known Mudrex API issues.

These functions are registered as Gemini function-calling tools so the LLM
can invoke them when a user asks about a specific, well-understood error.
Each function returns a curated, step-by-step markdown guide — no
hallucination, no vector search required.

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""


def troubleshoot_500_error(context: str) -> str:
    """Returns exact debugging steps for Mudrex 500 Internal Server Errors, specifically addressing inline SL/TP issues, string precision, and bracket order structure."""
    return (
        "You're close - this 500 is usually a payload-shape issue, not a hard API outage.\n\n"
        "**Most common reasons on Mudrex:**\n"
        "1. **Inline SL/TP invalid:** `slTriggerPrice` / `tpTriggerPrice` sign or side is wrong.\n"
        "2. **Precision mismatch:** price/qty decimals don't match asset `tickSize`/`stepSize`.\n"
        "3. **Wrong order structure:** inline SL/TP for an existing position can fail; set risk order separately.\n"
        "4. **Missing required fields:** `symbol`, `side`, `type`, `quantity`.\n\n"
        "**Quick Python sanity-check pattern:**\n"
        "```python\n"
        "import requests\n"
        "\n"
        "BASE = \"https://trade.mudrex.com/fapi/v1\"\n"
        "headers = {\"X-Authentication\": \"YOUR_API_SECRET\", \"Content-Type\": \"application/json\"}\n"
        "\n"
        "# 1) Place order WITHOUT inline SL/TP first\n"
        "order_payload = {\n"
        "    \"side\": \"BUY\",\n"
        "    \"type\": \"MARKET\",\n"
        "    \"quantity\": \"0.010\",  # as string\n"
        "}\n"
        "r = requests.post(f\"{BASE}/futures/ETHUSDT/order?is_symbol=true\", headers=headers, json=order_payload)\n"
        "print(\"order:\", r.status_code, r.text)\n"
        "\n"
        "# 2) Then set SL/TP via riskorder endpoint\n"
        "# requests.post(f\"{BASE}/futures/positions/{position_id}/riskorder\", ...)\n"
        "```\n\n"
        "**Next best step:** share your exact request body (mask key) + response body, and I can pinpoint the exact field causing 500."
    )


def troubleshoot_pnl_discrepancy(context: str) -> str:
    """Returns exact debugging steps for PnL discrepancies on Mudrex/Bybit futures, including funding rate settlements and timestamp issues."""
    return (
        "**Troubleshooting PnL Discrepancies**\n\n"
        "1. **Funding Rates:** Check if funding-rate settlements occurred "
        "during the trade. Funding is settled every 8 hours and creates a "
        "difference between the unrealized PnL shown in the UI and the "
        "actual realized PnL.\n\n"
        "2. **Timestamps:** Make sure you are comparing the exact "
        "timestamps for entry, exit, and any funding settlements. Use "
        "`GET /fapi/v1/futures/orders/history` to get precise fill times.\n\n"
        "3. **Fee Deduction:** Trading fees (maker/taker) are deducted "
        "from PnL. Check `GET /fapi/v1/futures/funds` → `fee_history` "
        "for the fee breakdown on each trade.\n\n"
        "4. **Partial Fills:** If the order was partially filled at "
        "different prices, the average entry price may differ from the "
        "expected price. Verify via the order history endpoint.\n\n"
        "5. **Cross vs Isolated Margin:** In cross-margin mode, "
        "unrealized PnL from other positions affects available balance, "
        "which can look like a PnL mismatch."
    )


def troubleshoot_auth_error(context: str) -> str:
    """Returns exact debugging steps for Mudrex authentication errors including 401, 403, and -1022 error codes."""
    return (
        "**Troubleshooting Authentication Errors (401 / 403 / -1022)**\n\n"
        "1. **Header Name:** Mudrex uses `X-Authentication` (not "
        "`Authorization`). Example:\n"
        "   ```\n"
        "   headers = {\"X-Authentication\": \"your_api_secret\"}\n"
        "   ```\n\n"
        "2. **No HMAC / No Signing:** Mudrex does NOT use HMAC signing "
        "or timestamps. Just pass the API secret as a plain string in "
        "the header. If you copied Binance-style signing code, remove it.\n\n"
        "3. **Key Rotation:** If you recently regenerated your API key "
        "in the dashboard (`www.mudrex.com/pro-trading`), the old key is "
        "immediately invalidated. Update your `.env` / config.\n\n"
        "4. **Whitespace / Encoding:** Ensure the secret has no leading "
        "or trailing whitespace. Copy-paste from the dashboard carefully.\n\n"
        "5. **403 — IP / Permission:** A 403 may indicate the key lacks "
        "trading permissions or IP restrictions are active. Check your "
        "API key settings in the dashboard."
    )


def troubleshoot_rate_limit(context: str) -> str:
    """Returns exact debugging steps for Mudrex API rate limiting (429) errors, including the 2 req/sec limit and backoff strategies."""
    return (
        "**Troubleshooting Rate Limiting (429)**\n\n"
        "1. **Limit:** Mudrex enforces **2 requests per second** across "
        "all endpoints. Exceeding this returns HTTP 429.\n\n"
        "2. **Backoff Strategy:** Implement exponential backoff with "
        "jitter:\n"
        "   ```python\n"
        "   import time, random\n"
        "   for attempt in range(5):\n"
        "       resp = requests.post(url, headers=headers, json=payload)\n"
        "       if resp.status_code != 429:\n"
        "           break\n"
        "       wait = (2 ** attempt) + random.uniform(0, 1)\n"
        "       time.sleep(wait)\n"
        "   ```\n\n"
        "3. **Request Batching:** Avoid polling in tight loops. Use a "
        "token-bucket or leaky-bucket rate limiter to space requests "
        "at ~500 ms intervals.\n\n"
        "4. **Caching:** Cache responses for read-heavy endpoints "
        "(`GET /futures`, `GET /futures/positions`) to reduce call volume.\n\n"
        "5. **Separate Read / Write:** If you are placing orders AND "
        "polling status, stagger them so they don't compete for the "
        "same 2 req/sec budget."
    )


def troubleshoot_order_error(context: str) -> str:
    """Returns exact debugging steps for Mudrex order placement errors including -1111 precision, -1121 invalid symbol, and step size issues."""
    return (
        "**Troubleshooting Order Errors (-1111 / -1121 / Step Size)**\n\n"
        "1. **-1111 Precision Error:** The quantity or price has too many "
        "decimals. Fetch the asset's rules with "
        "`GET /fapi/v1/futures/{asset_id}` and round to the correct "
        "`stepSize` / `tickSize`.\n\n"
        "2. **-1121 Invalid Symbol:** Mudrex uses plain symbols like "
        "`BTCUSDT`, not `BTC-USDT` or `BTC/USDT`. Check available "
        "pairs with `GET /fapi/v1/futures`.\n\n"
        "3. **Step Size Rounding:** Use Python's `Decimal` for precision:\n"
        "   ```python\n"
        "   from decimal import Decimal, ROUND_DOWN\n"
        "   qty = Decimal(str(raw_qty)).quantize(\n"
        "       Decimal(step_size), rounding=ROUND_DOWN\n"
        "   )\n"
        "   ```\n\n"
        "4. **Min Notional:** The order value (`price * quantity`) must "
        "meet the minimum notional for the pair. If it's too small, "
        "increase quantity or use a higher-value asset.\n\n"
        "5. **Side & Type:** Ensure `side` is `\"BUY\"` or `\"SELL\"` "
        "(uppercase) and `type` is `\"LIMIT\"` or `\"MARKET\"`. Typos "
        "or lowercase values will fail."
    )


def troubleshoot_http_202(context: str) -> str:
    """Returns explanation that HTTP 202 Accepted from Mudrex is a SUCCESS, not an error, and how to handle it in code."""
    return (
        "**HTTP 202 is a SUCCESS — your order was accepted.**\n\n"
        "Mudrex returns **202 Accepted** when it accepts an order for "
        "processing. This is NOT an error. The response body confirms it:\n"
        '`{"success": true, "status": "CREATED", "message": "OK"}`\n\n'
        "**Why your script thinks it failed:**\n"
        "Your code likely checks `status_code == 200` only. HTTP 2xx codes "
        "(200, 201, 202) all mean success.\n\n"
        "**Fix — accept any 2xx status:**\n"
        "```python\n"
        "response = requests.post(url, headers=headers, json=payload)\n"
        "if response.status_code in (200, 201, 202):\n"
        "    print('Order placed:', response.json())\n"
        "else:\n"
        "    print(f'FAILED: {response.status_code}', response.text)\n"
        "```\n\n"
        "Or more Pythonic: `if response.ok:` (True for any 2xx).\n\n"
        "**Summary:** 202 = Mudrex accepted your order. Check the "
        "`order_id` in the response to track it."
    )


def troubleshoot_http_405(context: str) -> str:
    """Returns exact debugging steps for Mudrex HTTP 405 Method Not Allowed errors, usually caused by wrong HTTP method or missing asset_id in URL."""
    return (
        "**Troubleshooting 405 Method Not Allowed**\n\n"
        "1. **Wrong HTTP Method:** Ensure you are using `POST` (not `GET`) "
        "for order placement. The endpoint is:\n"
        "   `POST /fapi/v1/futures/{asset_id}/order`\n\n"
        "2. **Missing Asset ID in URL:** If you omit the asset ID from the "
        "path (e.g. `/fapi/v1/futures/order` instead of "
        "`/fapi/v1/futures/ETHUSDT/order`), Mudrex returns 405.\n\n"
        "3. **Symbol-based Trading:** To use a symbol like ETHUSDT directly "
        "in the URL instead of a UUID, add `?is_symbol=true`:\n"
        "   ```python\n"
        "   url = 'https://trade.mudrex.com/fapi/v1/futures/ETHUSDT/order?is_symbol=true'\n"
        "   response = requests.post(url, headers=headers, json=payload)\n"
        "   ```\n\n"
        "4. **Check the Full URL:** Print `response.url` before the call "
        "to verify the path is correct."
    )


TROUBLESHOOTING_TOOLS = [
    troubleshoot_500_error,
    troubleshoot_pnl_discrepancy,
    troubleshoot_auth_error,
    troubleshoot_rate_limit,
    troubleshoot_order_error,
    troubleshoot_http_202,
    troubleshoot_http_405,
]
