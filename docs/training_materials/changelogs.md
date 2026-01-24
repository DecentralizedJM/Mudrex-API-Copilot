# Changelogs
Source: https://docs.trade.mudrex.com/docs/changelogs
Date Scraped: 2026-01-24

---

Release Summary

Version

Release Date

Status

Summary

v1.0.3

Jan 22, 2025

RELEASED

MCP server integration guide

v1.0.2

Dec 8, 2025

RELEASED

Status code & message update for funds transfer

v1.0.1

Dec 5, 2025

RELEASED

Margin add/reduce APIs, symbol-first trading, improved errors & payloads, Change in status code and message for funds transfer endpoint

v1.0.0

Nov 5, 2025

RELEASED

Initial API trading support

Changelog — v1.0.2

Release Date:

December 8, 2025

Breaking Changes:

No

Deprecations:

No

Changed

Status code and message for funds transfer endpoint

Endpoint:

POST /fapi/v1/wallet/futures/transfer

Changed status code and message for successful fund movement

200 OK → 202 Accepted

internal_wallet_fund_transfer_request successful

→ i

nternal wallet fund transfer request accepted

Changelog — v1.0.1

Release Date:

December 5, 2025

Breaking Changes:

No

Deprecations:

No

Added

1. Add / Reduce Margin API

Endpoint:

POST /fapi/v1/futures/positions/:positionID/add-margin

Request Body:

JSON

{
  "margin": 10.2
}

margin

(float): Positive value adds margin, negative value reduces margin

Response:

Returns updated

initial_margin

and

liquidation_price

2. Estimated Liquidation Price API

Endpoint:

GET /fapi/v1/futures/positions/:positionID/liq-price?ext_margin=2.1

Query Parameters:

ext_margin

(float, optional): Hypothetical margin change

Positive value simulates adding margin

Negative value simulates reducing margin

If not provided or 0, returns current liquidation price

Response:

Returns estimated liquidation price as string

3. Symbol-First API Trading Support

The following endpoints now support trading by asset symbol instead of asset ID:

GET /fapi/v1/futures/:id

GET /fapi/v1/futures/:id/leverage

POST /fapi/v1/futures/:id/leverage

POST /fapi/v1/futures/:id/order

Usage:

Add query parameter

?is_symbol

(presence-based, value is ignored)

Note:

Asset-ID-based flows remain fully functional for backward compatibility

If the query param is passed, even if the value is false, F, f, False, 0 etc. the system will treat as a symbol-first trading. Please use the flag only when trading via symbols.

Changed

1. Get Assets (Listing) & Get Asset Info

Endpoints:

GET /fapi/v1/futures?limit=10&offset=0

GET /fapi/v1/futures/:asset_id

Removed Fields:

contract_multiplier

price_scale

Fixed Fields:

min_funding_rate

and

max_funding_rate

now return correct minimum and maximum funding rates

2. Place Order

Endpoint:

POST /fapi/v1/futures/:asset_id/order

Change:

Success status code updated from

200 OK

to

202 Accepted

3. Get Orders History

Endpoint:

GET /fapi/v1/futures/orders/history

Removed Fields:

desired_amount

liquidation_price

4. Get Open Positions

Endpoint:

GET /fapi/v1/futures/positions

Removed Field:

closed_price

5. Get Closed Positions (Position History)

Endpoint:

GET /fapi/v1/futures/positions/history

Removed Field:

unrealised_pnl

6. Place / Amend Risk Order

Endpoints:

POST /fapi/v1/futures/positions/:position_id/riskorder

PATCH /fapi/v1/futures/positions/:position_id/riskorder

Request Body Changes:

The following fields are now ignored if sent:

user_id

order_id

exchange_order_id

id

Error Handling Improvements:

404 Not Found

when

position_id

is invalid or position doesn't exist

400 Bad Request

when position is not in OPEN state

More descriptive error messages for invalid requests

7. Reverse Position

Endpoint:

POST /fapi/v1/futures/positions/:position_id/reverse

Change:

Success status code updated from

200 OK

to

202 Accepted

Fixed

General improvements to validation and error messaging for invalid requests

Migration Notes

Status Codes:

Update clients to accept

202 Accepted

for order placement and reverse position operations

Removed Fields:

Stop relying on fields that have been removed from responses

Backward Compatibility:

Existing asset-ID-based flows continue to work without changes

Changelog — v1.0.0

Wallet

GET /wallet/funds:

Fetch spot wallet balances.

POST /wallet/futures/transfer:

Transfer funds between spot and futures wallets.

Futures

GET /futures/funds:

Fetch futures wallet balances and available transfer amount.

Assets

GET /futures:

List all futures assets (supports sorting and pagination).

GET /futures/:asset_id:

Retrieve detailed information for a specific asset.

Leverage

GET /futures/:asset_id/leverage:

Get current leverage and margin type for an asset.

POST /futures/:asset_id/leverage:

Set leverage and margin type for an asset.

Orders

POST /fapi/v1/futures/:asset_id/order:

Place new orders (market or limit).

Order Management:

Endpoints to list open orders, retrieve order history, fetch individual order details, amend orders, and cancel orders.

Positions

GET /fapi/v1/futures/positions:

List open positions.

Position Management:

Endpoints to view position history, place or amend risk orders, close positions (full or partial), and reverse positions.

Fees

GET /fapi/v1/futures/fee/history:

Retrieve trading fee history with limit and offset parameters.

Updated

2 days ago

Ask AI
