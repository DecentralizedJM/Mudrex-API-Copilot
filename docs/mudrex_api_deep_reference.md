# Mudrex API Deep Reference

Collated from individual doc pages.

## Authentication Rate Limits
**Source**: https://docs.trade.mudrex.com/docs/authentication-rate-limits

Authentication & Rate Limits
Learn how to authenticate with Mudrex API using API keys and understand the rate limits enforced for secure trading operations.
Authentication
Mudrex enforces strong security measures. To call any private endpoint, you must:
Verify your identity
: Complete KYC verification (PAN & Aadhaar) and enable two-factor authentication for your Mudrex account.
Generate an API key
: In your dashboard, create an API key. Copy the secret and store it securely, as it will not be displayed again.
All endpoints under /fapi/v1 require: X-Authentication (your API secret). Mudrex uses ONLY this — no HMAC, no SHA256, no X-MUDREX-API-KEY, no X-MUDREX-SIGNATURE, no X-MUDREX-TIMESTAMP. Content-Type: application/json only for POST/PATCH/DELETE. Base URL: https://trade.mudrex.com/fapi/v1

Header: X-Authentication, Value: your_api_secret, Required: Yes.
Content-Type: application/json — only for POST/PATCH/DELETE.

Example Request (POST order)
Shell
curl -X POST https://trade.mudrex.com/fapi/v1/futures/<asset_id>/order \
  -H "Content-Type: application/json" \
  -H "X-Authentication: <secret-key>" \
  -d '{
    "leverage": "5",
    "quantity": "0.001",
    "order_price": "107526",
    "order_type": "LONG",
    "trigger_type": "MARKET",
    "is_takeprofit": true,
    "is_stoploss": true,
    "stoploss_price": "106900",
    "takeprofit_price": "110000",
    "reduce_only": false
  }'
Rate Limits
The following rate limits are enforced per API key:
Duration
Limit
Second
2
Minute
50
Hour
1000
Day
10000
Updated
2 days ago
What’s Next
Quickstart
Ask AI

---

## Error Handling
**Source**: https://docs.trade.mudrex.com/docs/error-handling

Errors
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
What’s Next
Wallet
Ask AI

---

## Wallet
**Source**: https://docs.trade.mudrex.com/docs/wallet

Wallet
Endpoints to view your SPOT wallet balance and transfer funds between your SPOT and FUTURES wallets.
The Wallet section provides endpoints to interact with your spot wallet.  You can retrieve your current spot balance and move funds between your spot and futures wallets.  Use these APIs to check how much you have available to invest, withdraw, or transfer, and to manage your capital allocation between spot and futures trading.  See the sub‑pages for fetching balances and initiating transfers.
Updated
2 days ago
Ask AI

---

## Get Spot Funds
**Source**: https://docs.trade.mudrex.com/docs/get-spot-funds

Funds (spot)
Retrieve your current Spot wallet balances across all supported assets.
Request
API
curl -X GET "https://trade.mudrex.com/fapi/v1/wallet/funds" \
  -H "X-Authentication: your-secret-key"
Response
JSON
{
    "success": true,
    "data": {
        "total": 4.13,
        "rewards": 0,
        "invested": 3.5,
        "withdrawable": 0.63,
        "coin_investable": 0.63,
        "coinset_investable": 0.63,
        "vault_investable": 0.63
    }
}
Parameters
Parameter
Description
total
Total value in your spot wallet across all products.
rewards
Bonus funds earned from promotions, not withdrawable.
invested
Funds currently locked in other Mudrex products.
withdrawable
Amount available to withdraw or transfer to futures.
coin_investable
Amount available for investment in individual coins.
coinset_investable
Amount available for investment in coin sets.
vault_investable
Amount available for investment in vaults.
Updated
2 days ago
Ask AI

---

## Post Transfer Funds
**Source**: https://docs.trade.mudrex.com/docs/post-transfer-funds

Transfer funds
Move funds instantly between your spot wallet (USDT Wallet)  and futures wallet to manage trading positions and margin requirements.
Request
API
curl -X POST "https://trade.mudrex.com/fapi/v1/wallet/futures/transfer" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "from_wallet_type": "SPOT",
    "to_wallet_type": "FUTURES", 
    "amount": "10.5"
  }'
Parameters
Field
Type
Required
Description
from_wallet_type
string
Yes
Source wallet:
"SPOT"
or
"FUTURES"
to_wallet_type
string
Yes
Destination wallet: must be opposite of source
amount
string
Yes
Decimal amount to transfer (must be positive)
Response
Status:
202 Accepted
JSON
{
    "success": true,
    "data": {
        "msg": "internal_wallet_fund_transfer_request accepted"
    }
}   d
Examples
Request
JSON
{
    "from_wallet_type": "SPOT",
    "to_wallet_type": "FUTURES",
    "amount": "1"
}
Response
JSON
{
    "success": true,
    "data": {
        "msg": "internal_wallet_fund_transfer_request accepted"
    }
}
Common errors
Same wallet type selected
JSON
{
    "success": false,
    "errors": [
        {
            "code": null,
            "text": "From and To wallet types must be different"
        }
    ]
}
Status:
400 Bad Request
Insufficient funds
JSON
{
    "success": false,
    "errors": [
        {
            "code": null,
            "text": "insufficient balance"
        }
    ]
}
Status:
400 Bad Request
Notes
Transfers are
instant
and
free of fees
You must have sufficient balance in the source wallet
The wallets must be different (
SPOT
↔
FUTURES
only)
Authentication is required for all transfer requests
Updated
2 days ago
Ask AI

---

## Futures Wallet
**Source**: https://docs.trade.mudrex.com/docs/futures-wallet

Futures Wallet
Endpoints to view your Futures wallet balance and available transfer amount.
The Futures Wallet section lets you see how much margin you have available for futures trading.  It exposes a single endpoint to fetch your current futures wallet balance, the amount locked in open positions or orders, and a flag indicating whether you are a first‑time futures user.  If you need to move money into or out of your futures wallet, use the transfer endpoint under the Wallet section.
Updated
2 days ago
Ask AI

---

## Get Available Funds Futures
**Source**: https://docs.trade.mudrex.com/docs/get-available-funds-futures

Funds (futures)
Fetch your available balance and margin usage from the Futures wallet.
Request
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/funds" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key"
Response
JSON
{
    "success": true,
    "data": {
        "balance": "12.6787",
        "locked_amount": "1.6979",
        "first_time_user": false
    }
}
Parameters
balance
: investable balance in futures wallet
locked_amount
: locked balance in futures wallet
first_time_user
: first time user
Updated
2 days ago
Ask AI

---

## Get Asset Listing
**Source**: https://docs.trade.mudrex.com/docs/get-asset-listing

Assets
Get a paginated list of all tradable futures asset.
Request
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures?sort=price&order=desc&offset=0&limit=3" \
  -H "X-Authentication: your-secret-key"
Parameters
Parameter
Type
Required
Description
sort
string
No
Sort by:
price
,
volume
,
change_perc
, or
popularity
(default)
order
string
No
Sort order:
asc
or
desc
offset
number
No
Number of records to skip (default: 0)
limit
number
No
Maximum number of records to return (default: 20)
Response
JSON
{
    "success": true,
    "data": [
        {
            "id": "01903a7b-bf65-707d-a7dc-d7b84c3c756c",
            "name": "Bitcoin",
            "symbol": "BTCUSDT",
            "min_contract": "0.001",
            "max_contract": "1190",
            "quantity_step": "0.001",
            "min_price": "0.1",
            "max_price": "1999999.8",
            "price_step": "0.1",
            "max_market_contract": "119",
            "min_notional_value": "5",
            "funding_fee_perc": "0.0001",
            "max_funding_rate": null,
            "min_funding_rate": null,
            "trading_fee_perc": "0.1",
            "leverage_step": "0.01",
            "min_leverage": "1",
            "max_leverage": "100",
            "funding_interval": 1759305600,
            "price": "114550",
            "last_day_price": "114060.7",
            "change_perc": "0.42898211215607",
            "volume": "66940.704",
            "popularity": "1"
        }
    ]
}
Parameters
Parameter
Description
id
Asset ID used to create positions in a particular asset. Example:
"01903a7b-bf65-707d-a7dc-d7b84c3c756c"
is for BTC
name
Asset name (e.g., "Bitcoin")
symbol
Trading symbol (e.g., "BTCUSDT")
min_contract
Minimum quantity for which a position can be opened in an asset
max_contract
Maximum quantity for which a position can be opened in an asset
quantity_step
Multiple of min contract value. Contracts must be in multiples of this value (e.g., 0.001, 0.002, 0.003)
min_price
Minimum price for SL/TP or Limit orders
max_price
Maximum price for SL/TP or Limit orders
price_step
Price increment step
max_market_contract
Maximum contract size for market orders
min_notional_value
Minimum notional value for orders
funding_fee_perc
Funding fee percentage
max_funding_rate
Maximum funding rate (correct values, can be null)
min_funding_rate
Minimum funding rate (correct values, can be null)
trading_fee_perc
Trading fee percentage
leverage_step
Leverage increment step. Valid leverage must be between min_leverage and max_leverage in multiples of this step
min_leverage
Minimum allowed leverage
max_leverage
Maximum allowed leverage
funding_interval
Funding interval in
EPOCH time
. Regular period at which funding fees are exchanged
price
Current market price
last_day_price
Price from the previous day
change_perc
Percentage change in price
volume
Trading volume
popularity
Popularity ranking of the asset
Pagination
Pagination is controlled by the
limit
and
offset
query parameters. Use
limit
to specify how many assets to return (default 10) and
offset
to skip a number of assets (default 0). When combined, these allow you to paginate through the full list of futures assets.
The response returns an array of asset objects. Each object contains fields like
id
(asset identifier),
symbol
(trading pair),
price
(current price),
volume24h
(24-hour trading volume), and
changePerc
(24-hour price change percentage). Use these fields to display basic market information about each asset.
Updated
2 days ago
Ask AI

---

## Get
**Source**: https://docs.trade.mudrex.com/docs/get

Asset by id/symbol
Pull detailed metadata about a specific asset using its ID.
Request
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/{asset_id}" \
  -H "X-Authentication: your-secret-key"
Parameters
Parameter
Type
Required
Description
asset_id
string
Yes
The unique identifier of the asset (path parameter) or trading symbol (e.g., "BTCUSDT") if
is_symbol
query parameter is present
is_symbol
string
No
Query parameter. If present (even with value false/0), the
asset_id
path parameter is treated as a trading symbol instead of asset ID. If not passed, backward compatibility is maintained and asset ID is used
Symbol-First Trading
You can use trading symbols (e.g., "BTCUSDT", "ETHUSDT") instead of asset IDs by including the
is_symbol
query parameter:
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/BTCUSDT?is_symbol" \
  -H "X-Authentication: your-secret-key"
Note
: The
is_symbol
query parameter need not have a value—its mere presence is enough. If the query parameter is passed (even with values like
false
,
f
,
False
,
0
), the system will treat the path parameter as a symbol. For backward compatibility, if the query parameter is not passed, the existing Asset ID support is used.
Response
JSON
{
    "success": true,
    "data": {
        "id": "01903bc9-973a-7106-99e2-08287b632806",
        "name": "Ethereum",
        "symbol": "ETHUSDT",
        "min_contract": "0.01",
        "max_contract": "7240",
        "quantity_step": "0.01",
        "min_price": "0.01",
        "max_price": "199999.98",
        "price_step": "0.01",
        "max_market_contract": "724",
        "min_notional_value": "5",
        "funding_fee_perc": "0.0001",
        "max_funding_rate": null,
        "min_funding_rate": null,
        "trading_fee_perc": "0.1",
        "leverage_step": "0.01",
        "min_leverage": "1",
        "max_leverage": "100",
        "funding_interval": 1759305600,
        "price": "4147.18",
        "last_day_price": "4178.99",
        "change_perc": "-0.7611887082764",
        "volume": "1429617.28",
        "popularity": "2",
        "1d_high": 4205.82,
        "1d_low": 4089.48,
        "1d_volume": 1429617.2799999975
    }
}
Parameters
Parameter
Description
id
Asset ID used to create positions in a particular asset
name
Asset name (e.g., "Ethereum")
symbol
Trading symbol (e.g., "ETHUSDT")
min_contract
Minimum quantity for which a position can be opened in an asset
max_contract
Maximum quantity for which a position can be opened in an asset
quantity_step
Multiple of min contract value. Contracts must be in multiples of this value
min_price
Minimum price for SL/TP or Limit orders
max_price
Maximum price for SL/TP or Limit orders
price_step
Price increment step
max_market_contract
Maximum contract size for market orders
min_notional_value
Minimum notional value for orders
funding_fee_perc
Funding fee percentage
max_funding_rate
Maximum funding rate (correct values, can be null)
min_funding_rate
Minimum funding rate (correct values, can be null)
trading_fee_perc
Trading fee percentage
leverage_step
Leverage increment step. Valid leverage must be between min_leverage and max_leverage in multiples of this step
min_leverage
Minimum allowed leverage
max_leverage
Maximum allowed leverage
funding_interval
Funding interval in
EPOCH time
. Regular period at which funding fees are exchanged
price
Current market price
last_day_price
Price from the previous day
change_perc
Percentage change in price
volume
Trading volume
popularity
Popularity ranking of the asset
1d_high
24-hour high price
1d_low
24-hour low price
1d_volume
24-hour trading volume
Common errors
Asset not found
JSON
{
    "success": false,
    "errors": [
        {
            "code": 404,
            "text": "Asset not found"
        }
    ]
}
Status:
404 Not Found
Updated
2 days ago
Ask AI

---

## Leverage
**Source**: https://docs.trade.mudrex.com/docs/leverage

Leverage
Endpoints to get and set leverage for a futures asset.
The Leverage section deals with how much borrowing power you apply to your trades.  Endpoints here allow you to query the current leverage and margin type (isolated) for a given asset, and to set a new leverage value.  Setting leverage affects the buying power of future orders on that asset; positions already opened remain unchanged.  Explore the sub‑pages to get and set leverage settings.
Updated
2 days ago
Ask AI

---

## Get Leverage By Asset Id
**Source**: https://docs.trade.mudrex.com/docs/get-leverage-by-asset-id

Leverage by asset id/symbol
Check the leverage level and margin type set for a given asset.
Request
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/{asset_id}/leverage" \
  -H "X-Authentication: your-secret-key"
Parameters
Parameter
Type
Required
Description
asset_id
string
Yes
The unique identifier of the asset (path parameter) or trading symbol (e.g., "BTCUSDT") if
is_symbol
query parameter is present
is_symbol
string
No
Query parameter. If present (even with value false/0), the
asset_id
path parameter is treated as a trading symbol instead of asset ID. If not passed, backward compatibility is maintained and asset ID is used
Symbol-First Trading
You can use trading symbols (e.g., "BTCUSDT", "ETHUSDT") instead of asset IDs by including the
is_symbol
query parameter:
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/BTCUSDT/leverage?is_symbol" \
  -H "X-Authentication: your-secret-key"
Note
: The
is_symbol
query parameter need not have a value—its mere presence is enough. If the query parameter is passed (even with values like
false
,
f
,
False
,
0
), the system will treat the path parameter as a symbol. For backward compatibility, if the query parameter is not passed, the existing Asset ID support is used.
Response
JSON
{
    "success": true,
    "data": {
        "Leverage": "50",
        "MarginType": "ISOLATED"
    }
}
Parameters
Parameter
Description
Leverage
Current leverage level set for the asset
MarginType
Margin type for the asset. Currently only
ISOLATED
is supported
Updated
2 days ago
Ask AI

---

## Set
**Source**: https://docs.trade.mudrex.com/docs/set

Set leverage by asset id/symbol
Set or update the leverage and margin type for a specific asset.
Request
API
curl -X POST "https://trade.mudrex.com/fapi/v1/futures/{asset_id}/leverage" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "margin_type": "ISOLATED",
    "leverage": 50
  }'
Parameters
Parameter
Type
Required
Description
asset_id
string
Yes
The unique identifier of the asset (path parameter) or trading symbol (e.g., "BTCUSDT") if
is_symbol
query parameter is present
is_symbol
string
No
Query parameter. If present (even with value false/0), the
asset_id
path parameter is treated as a trading symbol instead of asset ID. If not passed, backward compatibility is maintained and asset ID is used
margin_type
string
No
Margin type. Currently only
ISOLATED
is supported (defaults to ISOLATED)
leverage
number
Yes
Leverage value to set for the asset (must be within permissible range)
Symbol-First Trading
You can use trading symbols (e.g., "BTCUSDT", "ETHUSDT") instead of asset IDs by including the
is_symbol
query parameter:
API
curl -X POST "https://trade.mudrex.com/fapi/v1/futures/BTCUSDT/leverage?is_symbol" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "margin_type": "ISOLATED",
    "leverage": 50
  }'
Note
: The
is_symbol
query parameter need not have a value—its mere presence is enough. If the query parameter is passed (even with values like
false
,
f
,
False
,
0
), the system will treat the path parameter as a symbol. For backward compatibility, if the query parameter is not passed, the existing Asset ID support is used.
Response
JSON
{
    "success": true,
    "data": {
        "Leverage": "50",
        "MarginType": "ISOLATED"
    }
}
Parameters
Parameter
Description
Leverage
Leverage level set for the asset
MarginType
Margin type for the asset. Currently only
ISOLATED
is supported
Common errors
Leverage out of permissible range
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "leverage out of permissible range"
        }
    ]
}
Status:
400 Bad Request
This error occurs when:
Leverage value is too high (e.g.,
5999836
)
Leverage value is invalid (e.g.,
0
or negative)
Invalid asset ID
Status:
400 Bad Request
Occurs when the provided asset ID is invalid or not found.
Notes
Currently, only
margin_type = ISOLATED
is supported, so
margin_type
is not a mandatory field in the request body
Leverage must be within the permissible range for the specific asset (check asset details for min/max leverage values)
Updated
2 days ago
Ask AI

---

## Orders
**Source**: https://docs.trade.mudrex.com/docs/orders

Orders
Endpoints to query open and closed orders, retrieve details of a specific order, amend or cancel orders.
The Orders section covers the entire lifecycle of futures orders.  Use these endpoints to place new market or limit orders, view your open orders, retrieve individual order details, view historical orders, and cancel existing orders.  You can also specify reduce‑only orders to ensure they only close or reduce positions.  Refer to the sub‑pages for specifics on each operation.
Updated
2 days ago
Ask AI

---

## Post Market Order
**Source**: https://docs.trade.mudrex.com/docs/post-market-order

Create new order
Place a new market or limit order on a chosen trading pair.
Request
API
curl -X POST "https://trade.mudrex.com/fapi/v1/futures/{asset_id}/order" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "leverage": 50,
    "quantity": 0.01,
    "order_price": 12445627,
    "order_type": "LONG",
    "trigger_type": "MARKET",
    "is_takeprofit": true,
    "is_stoploss": true,
    "stoploss_price": 3800,
    "takeprofit_price": 5000,
    "reduce_only": false
  }'
Parameters
Parameter
Type
Required
Description
asset_id
string
Yes
The unique identifier of the asset (path parameter) or trading symbol (e.g., "BTCUSDT") if
is_symbol
query parameter is present
is_symbol
string
No
Query parameter. If present (even with value false/0), the
asset_id
path parameter is treated as a trading symbol instead of asset ID. If not passed, backward compatibility is maintained and asset ID is used
leverage
number
Yes
Leverage value (must be within permissible range for the asset)
quantity
number
Yes
Order quantity (must be a multiple of the quantity step for the asset)
order_price
number
Yes
Order price (must be between min & max price for the asset based on
LONG
/
SHORT
orders)
order_type
string
Yes
Order type:
LONG
or
SHORT
. If
reduce_only
is true, must be opposite of existing position
trigger_type
string
Yes
Trigger type:
MARKET
or
LIMIT
is_takeprofit
boolean
No
Whether to set a take profit order (default: false)
is_stoploss
boolean
No
Whether to set a stop loss order (default: false)
stoploss_price
number
Conditional
Required if
is_stoploss
is true. Stop loss price
takeprofit_price
number
Conditional
Required if
is_takeprofit
is true. Take profit price
reduce_only
boolean
No
If true, order can only decrease or close an existing position (default: false)
Response
Status:
202 Accepted
JSON
{
    "success": true,
    "data": {
        "leverage": "80.9",
        "amount": "222.8",
        "quantity": "0.05",
        "price": "4456",
        "order_id": "0199c39f-e866-7d6b-947e-ed2f09c90b8e",
        "status": "CREATED",
        "message": "OK"
    }
}
Parameters
Parameter
Description
order_id
UUID of the created order. This ID is used for CRUD operations on the order/position (setting SL/TP, square off, cancel, delete)
leverage
Leverage used for the order
amount
Amount used for the order
quantity
Order quantity
price
Order price
status
Order status (e.g.,
CREATED
)
message
Status message
Common errors
Params error
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "Params error"
        }
    ]
}
Status:
400 Bad Request
Invalid trigger type
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "invalid trigger type"
        }
    ]
}
Status:
400 Bad Request
Invalid order type
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "invalid order type"
        }
    ]
}
Status:
400 Bad Request
Order price out of permissible range
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "order price out of permissible range"
        }
    ]
}
Status:
400 Bad Request
Quantity not a multiple of the quantity step
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "quantity not a multiple of the quantity step"
        }
    ]
}
Status:
400 Bad Request
Leverage out of permissible range
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "leverage out of permissible range"
        }
    ]
}
Status:
400 Bad Request
Symbol-First Trading
You can use trading symbols (e.g., "BTCUSDT", "ETHUSDT") instead of asset IDs by including the
is_symbol
query parameter:
API
curl -X POST "https://trade.mudrex.com/fapi/v1/futures/BTCUSDT/order?is_symbol" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "leverage": 50,
    "quantity": 0.01,
    "order_price": 12445627,
    "order_type": "LONG",
    "trigger_type": "MARKET",
    "is_takeprofit": true,
    "is_stoploss": true,
    "stoploss_price": 3800,
    "takeprofit_price": 5000,
    "reduce_only": false
  }'
Note
: The
is_symbol
query parameter need not have a value—its mere presence is enough. If the query parameter is passed (even with values like
false
,
f
,
False
,
0
), the system will treat the path parameter as a symbol. For backward compatibility, if the query parameter is not passed, the existing Asset ID support is used.
Notes
Order Price
: Must be between min & max price for the asset based on
LONG
/
SHORT
orders
Order Type
: Can be
LONG
or
SHORT
. If there is no existing position in an asset, you can open a new position or average/reduce position sizing
Reduce-Only Orders
: If
reduce_only
is
true
and there is an existing open position in a particular asset, the order type must be opposite to the existing position (e.g., if open position is
LONG
, request body must have order type
SHORT
and vice versa). A reduce-only order ensures it can only decrease or close an existing position
Trigger Type
: Can be
MARKET
or
LIMIT
Stop Loss/Take Profit
: If
is_takeprofit
is
true
or
is_stoploss
is
true
, you must define the corresponding price. If both are
false
, stop loss and take profit prices are not required
Updated
2 days ago
Ask AI

---

## Get Order By Id
**Source**: https://docs.trade.mudrex.com/docs/get-order-by-id

Order by id
Retrieve detailed information about a particular order.
Request
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/orders/{order_id}" \
  -H "X-Authentication: your-secret-key"
Parameters
Parameter
Type
Required
Description
order_id
string
Yes
The unique identifier of the order (path parameter)
Response
JSON
{
    "success": true,
    "data": {
        "created_at": "2025-10-08T11:41:01Z",
        "updated_at": "2025-10-08T11:41:01Z",
        "reason": {
            "message": "OK"
        },
        "actual_amount": 222.8,
        "desired_amount": 0,
        "quantity": 0.05,
        "filled_quantity": 0,
        "price": 4456,
        "filled_price": 0,
        "leverage": 80.9,
        "liquidation_price": 0,
        "order_type": "LONG",
        "trigger_type": "LIMIT",
        "status": "CREATED",
        "id": "0199c39f-e866-7d6b-947e-ed2f09c90b8e",
        "asset_uuid": "018f7643-129c-7ca6-bb89-3be0e5ee94ae",
        "symbol": "ETHUSDT"
    }
}
Parameters
Parameter
Description
id
Order ID (UUID)
created_at
Timestamp when the order was created
updated_at
Timestamp when the order was last updated
reason
Reason object containing message (can be null)
actual_amount
Actual amount used for the order
desired_amount
Desired amount for the order
quantity
Order quantity
filled_quantity
Quantity that has been filled
price
Order price
filled_price
Average price at which the order has been filled
leverage
Leverage used for the order
liquidation_price
Liquidation price for the position
order_type
Type of order:
LONG
,
SHORT
, or
TAKEPROFIT
trigger_type
Trigger type:
MARKET
or
LIMIT
status
Order status (e.g.,
CREATED
,
FILLED
)
asset_uuid
UUID of the asset
symbol
Trading symbol (e.g., "ETHUSDT")
Common errors
Order not found
JSON
{
    "success": false,
    "errors": [
        {
            "code": 404,
            "text": "order not found"
        }
    ]
}
Status:
404 Not Found
Updated
2 days ago
Ask AI

---

## Get Open Orders
**Source**: https://docs.trade.mudrex.com/docs/get-open-orders

Open orders
View all active (open) orders in your account.
Request
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/orders?limit=2" \
  -H "X-Authentication: your-secret-key"
Parameters
Parameter
Type
Required
Description
limit
number
No
Maximum number of records to return (default: 20)
Response
JSON
{
    "success": true,
    "data": [
        {
            "created_at": "2025-10-08T11:41:01Z",
            "updated_at": "2025-10-08T11:41:01Z",
            "reason": {
                "message": "OK"
            },
            "actual_amount": 222.8,
            "desired_amount": 0,
            "quantity": 0.05,
            "filled_quantity": 0,
            "price": 4456,
            "filled_price": 0,
            "leverage": 80.9,
            "liquidation_price": 0,
            "order_type": "LONG",
            "trigger_type": "LIMIT",
            "status": "CREATED",
            "id": "0199c39f-e866-7d6b-947e-ed2f09c90b8e",
            "asset_uuid": "018f7643-129c-7ca6-bb89-3be0e5ee94ae",
            "symbol": "ETHUSDT"
        },
        {
            "created_at": "2025-10-08T11:41:01Z",
            "updated_at": "2025-10-08T11:41:01Z",
            "reason": null,
            "actual_amount": 0,
            "desired_amount": 0,
            "quantity": 0,
            "filled_quantity": 0,
            "price": 30000,
            "filled_price": 0,
            "leverage": 0,
            "liquidation_price": 0,
            "order_type": "TAKEPROFIT",
            "trigger_type": "MARKET",
            "status": "CREATED",
            "id": "0199c39f-e866-7d6e-b5d9-850852495106",
            "asset_uuid": "018f7643-129c-7ca6-bb89-3be0e5ee94ae",
            "symbol": "ETHUSDT"
        }
    ]
}
Parameters
Parameter
Description
id
Order ID (UUID). This ID is used for updating or deleting open orders/positions
created_at
Timestamp when the order was created
updated_at
Timestamp when the order was last updated
reason
Reason object containing message (can be null)
actual_amount
Actual amount used for the order
desired_amount
Desired amount for the order
quantity
Order quantity
filled_quantity
Quantity that has been filled
price
Order price
filled_price
Average price at which the order has been filled
leverage
Leverage used for the order
liquidation_price
Liquidation price for the position
order_type
Type of order:
LONG
,
SHORT
, or
TAKEPROFIT
trigger_type
Trigger type:
MARKET
or
LIMIT
status
Order status (e.g.,
CREATED
)
asset_uuid
UUID of the asset
symbol
Trading symbol (e.g., "ETHUSDT")
Examples
No open orders
JSON
{
    "success": true,
    "data": []
}
Updated
2 days ago
Ask AI

---

## Get Order History
**Source**: https://docs.trade.mudrex.com/docs/get-order-history

Order history
Access historical order data with filters for asset, side, and time.
Request
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/orders/history?limit=2" \
  -H "X-Authentication: your-secret-key"
Parameters
Parameter
Type
Required
Description
limit
number
No
Maximum number of records to return (default: 20)
Response
JSON
{
    "success": true,
    "data": [
        {
            "created_at": "2025-10-01T10:37:12Z",
            "updated_at": "2025-10-01T10:37:12Z",
            "reason": null,
            "actual_amount": 398.8752,
            "quantity": 1840,
            "filled_quantity": 1840,
            "price": 0.22118,
            "filled_price": 0.21678,
            "leverage": 25,
            "order_type": "SHORT",
            "trigger_type": "MARKET",
            "status": "FILLED",
            "id": "01999f58-f8cd-73e0-ad02-96b0e3451882",
            "asset_uuid": "01920a1c-88a3-7c9c-a71e-9d2d89dc1999",
            "symbol": "SQDUSDT"
        },
        {
            "created_at": "2025-10-01T10:25:41Z",
            "updated_at": "2025-10-01T10:25:41Z",
            "reason": {
                "message": "OK"
            },
            "actual_amount": 415.4904,
            "quantity": 1840,
            "filled_quantity": 1840,
            "price": 0.22568,
            "filled_price": 0.22581,
            "leverage": 25,
            "order_type": "LONG",
            "trigger_type": "MARKET",
            "status": "FILLED",
            "id": "01999f4e-6da3-7eaa-8339-096300e9b9f5",
            "asset_uuid": "01920a1c-88a3-7c9c-a71e-9d2d89dc1999",
            "symbol": "SQDUSDT"
        }
    ]
}
Parameters
Parameter
Description
id
Order ID (UUID)
created_at
Timestamp when the order was created
updated_at
Timestamp when the order was last updated
reason
Reason object containing message (can be null)
actual_amount
Actual amount used for the order
quantity
Order quantity
filled_quantity
Quantity that has been filled
price
Order price
filled_price
Average price at which the order has been filled
leverage
Leverage used for the order
order_type
Type of order:
LONG
,
SHORT
, or
TAKEPROFIT
trigger_type
Trigger type:
MARKET
or
LIMIT
status
Order status (e.g.,
FILLED
)
asset_uuid
UUID of the asset
symbol
Trading symbol (e.g., "SQDUSDT")
Updated
2 days ago
Ask AI

---

## Delete Order
**Source**: https://docs.trade.mudrex.com/docs/delete-order

Cancel order by id
Cancel a specific order using its unique ID.
Request
API
curl -X DELETE "https://trade.mudrex.com/fapi/v1/futures/orders/{order_id}" \
  -H "X-Authentication: your-secret-key"
Parameters
Parameter
Type
Required
Description
order_id
string
Yes
The unique identifier of the order (path parameter)
Response
JSON
{
    "success": true,
    "data": {
        "message": "Order cancelled successfully",
        "order_id": "0199c7e7-628f-75e0-8212-d02f6e3b1c7a",
        "status": "CANCELLED"
    }
}
Parameters
Parameter
Description
message
Status message
order_id
ID of the cancelled order
status
Status of the order (e.g.,
CANCELLED
)
Common errors
Order already deleted
Status:
400 Bad Request
Occurs when attempting to delete an order that has already been cancelled or deleted.
Invalid order ID
Status:
500 Internal Server Error
Occurs when the provided order ID is invalid or malformed.
Updated
2 days ago
Ask AI

---

## Positions
**Source**: https://docs.trade.mudrex.com/docs/positions

Positions
Endpoints to query and manage your futures positions, including retrieving open and closed positions, placing and amending risk orders, and closing or reversing positions.
The Positions section lets you monitor and manage your open and past trades.  You can fetch all current open positions along with their entry price, quantity, leverage and unrealised P&L; set or update stop‑loss and take‑profit orders; reverse a position; close part of a position; and retrieve your closed position history.  Each sub‑page addresses a different aspect of position management.
Updated
2 days ago
Ask AI

---

## Get Open Positions
**Source**: https://docs.trade.mudrex.com/docs/get-open-positions

Open Positions
Get detailed info about your currently open positions.
Request
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/positions" \
  -H "X-Authentication: your-secret-key"
Response
JSON
{
    "success": true,
    "data": [
        {
            "created_at": "2025-10-01T06:27:17Z",
            "updated_at": "2025-10-01T06:31:15Z",
            "stoploss": {
                "price": "4100",
                "order_id": "01999e77-8eab-79aa-8db3-8cc0624c7d0e",
                "order_type": "SHORT"
            },
            "takeprofit": {
                "price": "5000",
                "order_id": "01999e77-8eab-79ad-b3f0-22ee1e8e81d6",
                "order_type": "SHORT"
            },
            "entry_price": "4133.41",
            "quantity": "0.02",
            "leverage": "50",
            "liquidation_price": "4071.1",
            "pnl": "-0.0362",
            "order_type": "LONG",
            "status": "OPEN",
            "id": "01999e74-27a6-76d5-880b-4cab5eac78f1",
            "asset_uuid": "01903bc9-973a-7106-99e2-08287b632806",
            "symbol": "ETHUSDT"
        }
    ]
}
Parameters
Parameter
Description
id
Position ID (UUID)
created_at
Timestamp when the position was created
updated_at
Timestamp when the position was last updated
stoploss
Stop loss object containing
price
,
order_id
, and
order_type
(can be null if not set)
takeprofit
Take profit object containing
price
,
order_id
, and
order_type
(can be null if not set)
entry_price
Price at which the position was opened
quantity
Position quantity
leverage
Leverage used for the position
liquidation_price
Liquidation price for the position
pnl
Unrealised profit and loss for the position
order_type
Position type:
LONG
or
SHORT
status
Position status (e.g.,
OPEN
)
asset_uuid
UUID of the asset
symbol
Trading symbol (e.g., "ETHUSDT")
Examples
No open positions
JSON
{
    "success": true,
    "data": null
}
Updated
2 days ago
Ask AI

---

## Get Liquidation Price
**Source**: https://docs.trade.mudrex.com/docs/get-liquidation-price

Get Liquidation Price
Get estimated liquidation price for a position, optionally with additional margin adjustment.
Request
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/liq-price?ext_margin=2.1" \
  -H "X-Authentication: your-secret-key"
Parameters
Parameter
Type
Required
Description
position_id
string
Yes
The unique identifier of the position (path parameter)
ext_margin
float
No
Additional margin amount (positive for adding margin, negative for reducing margin). If not passed or zero, returns current liquidation price
Response
JSON
{
    "success": true,
    "data": "2.5847"
}
Parameters
Parameter
Description
data
Estimated liquidation price (string)
Examples
Get current liquidation price (no query parameter)
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/liq-price" \
  -H "X-Authentication: your-secret-key"
Get estimated liquidation price after adding margin
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/liq-price?ext_margin=10.5" \
  -H "X-Authentication: your-secret-key"
Get estimated liquidation price after reducing margin
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/liq-price?ext_margin=-5.2" \
  -H "X-Authentication: your-secret-key"
Common errors
Position not found
JSON
{
    "success": false,
    "errors": [
        {
            "code": 404,
            "text": "Position not found"
        }
    ]
}
Status:
404 Not Found
This error occurs when the position ID is incorrect or the position does not exist.
Updated
2 days ago
Ask AI

---

## Add Margin
**Source**: https://docs.trade.mudrex.com/docs/add-margin

Add/Reduce Margin
Add or reduce margin for an existing position to adjust liquidation price.
Request
API
curl -X POST "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/add-margin" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "margin": 10.2
  }'
Parameters
Parameter
Type
Required
Description
position_id
string
Yes
The unique identifier of the position (path parameter)
margin
float
Yes
Margin amount to add (positive value) or reduce (negative value)
Response
JSON
{
    "success": true,
    "data": {
        "message": "OK",
        "initial_margin": "3.01011155",
        "liquidation_price": "2.5847"
    }
}
Parameters
Parameter
Description
message
Status message
initial_margin
Updated initial margin of the position
liquidation_price
Updated liquidation price of the position
Common errors
Position not found
JSON
{
    "success": false,
    "errors": [
        {
            "code": 404,
            "text": "Position not found"
        }
    ]
}
Status:
404 Not Found
This error occurs when the position ID is incorrect or the position does not exist.
Insufficient funds
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "Insufficient funds"
        }
    ]
}
Status:
400 Bad Request
This error occurs when attempting to add margin but there are insufficient funds available.
Updated
2 days ago
Ask AI

---

## Set Sl Tp
**Source**: https://docs.trade.mudrex.com/docs/set-sl-tp

Set SL/TP
Define stop-loss and take-profit levels for an existing position.
Request
API
curl -X POST "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/riskorder" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "stoploss_price": "5289.5",
    "takeprofit_price": "50713.00",
    "order_source": "API",
    "is_stoploss": true,
    "is_takeprofit": true
  }'
Parameters
Parameter
Type
Required
Description
position_id
string
Yes
The unique identifier of the position (path parameter)
stoploss_price
string
Conditional
Required if
is_stoploss
is true. Stop loss price (must be above liquidation price for LONG positions)
takeprofit_price
string
Conditional
Required if
is_takeprofit
is true. Take profit price
order_source
string
No
Source of the order (e.g., "API")
is_stoploss
boolean
No
Whether to set a stop loss order (default: false)
is_takeprofit
boolean
No
Whether to set a take profit order (default: false)
Response
JSON
{
    "success": true,
    "data": {
        "position_id": "0199c39f-e864-7dbc-8b83-6954c1df7832",
        "status": "CREATED",
        "message": "Risk order placed successfully"
    }
}
Parameters
Parameter
Description
position_id
ID of the position for which the risk order was set
status
Status of the risk order (e.g.,
CREATED
)
message
Status message
Examples
Get position details after setting SL/TP
JSON
{
    "success": true,
    "data": [
        {
            "created_at": "2025-10-08T11:41:01Z",
            "updated_at": "2025-10-08T12:13:10Z",
            "stoploss": {
                "price": "0",
                "order_id": "",
                "order_type": ""
            },
            "takeprofit": {
                "price": "30000",
                "order_id": "0199c3bd-53ba-7491-ae5c-15bb95c1977a",
                "order_type": "SHORT"
            },
            "entry_price": "5304.392",
            "quantity": "0.05",
            "leverage": "80.9",
            "liquidation_price": "5265.16",
            "initial_margin": "3.42243351",
            "maintenance_margin": "1.47012993",
            "pnl": "-0.0076",
            "closed_price": "0",
            "order_type": "LONG",
            "status": "OPEN",
            "id": "0199c39f-e864-7dbc-8b83-6954c1df7832",
            "asset_uuid": "018f7643-129c-7ca6-bb89-3be0e5ee94ae",
            "symbol": "ETHUSDT"
        }
    ]
}
Common errors
Position not found
JSON
{
    "success": false,
    "errors": [
        {
            "code": 404,
            "text": "Position not found"
        }
    ]
}
Status:
404 Not Found
This error occurs when the position ID is incorrect or the position does not exist.
Position not in OPEN state
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "Position is not in OPEN state"
        }
    ]
}
Status:
400 Bad Request
This error occurs when attempting to set risk orders on a position that is not currently open.
Risk order creation failed (SL below liquidation)
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "Risk order creation failed"
        }
    ]
}
Status:
400 Bad Request
This error occurs when the stop loss price is set below the liquidation price for a LONG position (or above for a SHORT position).
Updated
2 days ago
Ask AI

---

## Edit Sl Tp
**Source**: https://docs.trade.mudrex.com/docs/edit-sl-tp

Edit SL/TP
Modify previously set stop-loss or take-profit values on an open position.
Request
API
curl -X PATCH "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/riskorder" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "order_price": 107526,
    "stoploss_price": 106900,
    "takeprofit_price": 110000,
    "stoploss_order_id": "<order_id>",
    "takeprofit_order_id": "<order_id>",
    "trigger_type": "MARKET",
    "is_takeprofit": true,
    "is_stoploss": true
  }'
Parameters
Parameter
Type
Required
Description
position_id
string
Yes
The unique identifier of the position (path parameter)
order_price
number
No
Order price
stoploss_price
number
Conditional
Required if
is_stoploss
is true. New stop loss price
takeprofit_price
number
Conditional
Required if
is_takeprofit
is true. New take profit price
stoploss_order_id
string
No
ID of the existing stop loss order to modify
takeprofit_order_id
string
No
ID of the existing take profit order to modify
trigger_type
string
No
Trigger type:
MARKET
or
LIMIT
is_stoploss
boolean
No
Whether to update the stop loss order (default: false)
is_takeprofit
boolean
No
Whether to update the take profit order (default: false)
Response
JSON
{
    "success": true,
    "data": {
        "position_id": "01999e74-27a6-76d5-880b-4cab5eac78f1",
        "status": "CREATED",
        "message": "Risk order updated successfully"
    }
}
Parameters
Parameter
Description
position_id
ID of the position for which the risk order was updated
status
Status of the risk order (e.g.,
CREATED
)
message
Status message
Common errors
Position not found
JSON
{
    "success": false,
    "errors": [
        {
            "code": 404,
            "text": "Position not found"
        }
    ]
}
Status:
404 Not Found
This error occurs when the position ID is incorrect or the position does not exist.
Position not in OPEN state
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "Position is not in OPEN state"
        }
    ]
}
Status:
400 Bad Request
This error occurs when attempting to amend risk orders on a position that is not currently open.
Invalid request
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "Invalid request"
        }
    ]
}
Status:
400 Bad Request
This error occurs when the request parameters are invalid or missing required fields.
Updated
2 days ago
Ask AI

---

## Reverse
**Source**: https://docs.trade.mudrex.com/docs/reverse

Reverse position
Switch an existing position from long to short or vice versa.
Request
API
curl -X POST "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/reverse" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key"
Parameters
Parameter
Type
Required
Description
position_id
string
Yes
The unique identifier of the position (path parameter)
Response
Status:
202 Accepted
JSON
{
    "success": true,
    "data": {
        "position_id": "01999e74-27a6-76d5-880b-4cab5eac78f1",
        "status": "CREATED",
        "message": "Position reversed successfully"
    }
}
Parameters
Parameter
Description
position_id
ID of the reversed position
status
Status of the reversal operation (e.g.,
CREATED
)
message
Status message
Common errors
Position not in sync with exchange
JSON
{
    "success": false,
    "errors": [
        {
            "code": null,
            "text": "position not in sync with exchange"
        }
    ]
}
Status:
400 Bad Request
This error occurs when the position state on the exchange differs from the local state, preventing the reversal operation.
Updated
2 days ago
Ask AI

---

## Partial Close
**Source**: https://docs.trade.mudrex.com/docs/partial-close

Partial Close
Close a portion of an open position without exiting entirely.
Request
API
curl -X POST "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/close/partial" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key" \
  -d '{
    "order_type": "LIMIT",
    "quantity": "0.01",
    "limit_price": "102.75"
  }'
Parameters
Parameter
Type
Required
Description
position_id
string
Yes
The unique identifier of the position (path parameter)
order_type
string
Yes
Order type:
LIMIT
or
MARKET
quantity
string
Yes
Quantity to close (must be less than the total position quantity)
limit_price
string
Conditional
Required if
order_type
is
LIMIT
. Price at which to close the partial position
Response
JSON
{
    "success": true,
    "data": true
}
Common errors
Position is not open
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "position is not open"
        }
    ]
}
Status:
400 Bad Request
Occurs when attempting to partially close a position that is not currently open.
Updated
2 days ago
Ask AI

---

## Square Off
**Source**: https://docs.trade.mudrex.com/docs/square-off

Square off
Close an entire open position immediately.
Request
API
curl -X POST "https://trade.mudrex.com/fapi/v1/futures/positions/{position_id}/close" \
  -H "Content-Type: application/json" \
  -H "X-Authentication: your-secret-key"
Parameters
Parameter
Type
Required
Description
position_id
string
Yes
The unique identifier of the position (path parameter)
Response
JSON
{
    "success": true,
    "data": {
        "position_id": "0199be9e-21f3-74c3-9439-dc826109223e",
        "status": "CREATED",
        "message": "OK"
    }
}
Parameters
Parameter
Description
position_id
ID of the position being closed
status
Status of the close operation (e.g.,
CREATED
)
message
Status message
Common errors
Position is not open
JSON
{
    "success": false,
    "errors": [
        {
            "code": 400,
            "text": "position is not open"
        }
    ]
}
Status:
400 Bad Request
Occurs when attempting to close a position that is not currently open.
Updated
2 days ago
Ask AI

---

## Get Position History
**Source**: https://docs.trade.mudrex.com/docs/get-position-history

Position history
Review your past closed positions for performance tracking.
Request
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/positions/history?limit=2" \
  -H "X-Authentication: your-secret-key"
Parameters
Parameter
Type
Required
Description
limit
number
No
Maximum number of records to return (default: 20)
Response
JSON
{
    "success": true,
    "data": [
        {
            "position_type": "LONG",
            "status": "LIQUIDATED",
            "leverage": "80.9",
            "entry_price": "6139.17",
            "closed_price": "6063.29",
            "quantity": "0.05",
            "pnl": "-3.794",
            "created_at": "2025-10-07T11:04:40Z",
            "updated_at": "2025-10-07T11:10:48Z",
            "asset_uuid": "018f7643-129c-7ca6-bb89-3be0e5ee94ae",
            "symbol": "ETHUSDT"
        },
        {
            "position_type": "LONG",
            "status": "LIQUIDATED",
            "leverage": "58",
            "entry_price": "4435.8747619047619048",
            "closed_price": "4359.4",
            "quantity": "0.21",
            "pnl": "-16.05970001",
            "created_at": "2025-09-24T07:37:22Z",
            "updated_at": "2025-09-24T07:48:21Z",
            "asset_uuid": "018f7643-129c-7ca6-bb89-3be0e5ee94ae",
            "symbol": "ETHUSDT"
        }
    ]
}
Parameters
Parameter
Description
position_type
Position type:
LONG
or
SHORT
status
Position status (e.g.,
LIQUIDATED
,
CLOSED
)
leverage
Leverage used for the position
entry_price
Price at which the position was opened
closed_price
Price at which the position was closed
quantity
Position quantity
pnl
Realised profit and loss for the closed position
created_at
Timestamp when the position was created
updated_at
Timestamp when the position was closed
asset_uuid
UUID of the asset
symbol
Trading symbol (e.g., "ETHUSDT")
Updated
2 days ago
Ask AI

---

## Fees
**Source**: https://docs.trade.mudrex.com/docs/fees

Fees
Endpoints to retrieve your futures trading and funcding fee history with pagination support using limit and offset parameters.
Request
API
curl -X GET "https://trade.mudrex.com/fapi/v1/futures/fee/history?limit=2" \
  -H "X-Authentication: your-secret-key"
Parameters
Parameter
Type
Required
Description
limit
number
No
Maximum number of records to return (default: 20)
offset
number
No
Number of records to skip (default: 0)
Response
JSON
{
    "success": true,
    "data": [
        {
            "symbol": "ETHUSDT",
            "fee_amount": "0.0206648",
            "fee_perc": "0.05",
            "fee_type": "TRANSACTION",
            "created_at": "2025-10-01T06:31:00Z",
            "transaction_amount": "41.3296"
        },
        {
            "symbol": "ETHUSDT",
            "fee_amount": "0.0206693",
            "fee_perc": "0.05",
            "fee_type": "TRANSACTION",
            "created_at": "2025-10-01T06:27:17Z",
            "transaction_amount": "41.3386"
        }
    ]
}
Parameters
Parameter
Description
symbol
Trading symbol (e.g., "ETHUSDT")
fee_amount
Fee amount charged
fee_perc
Fee percentage
fee_type
Type of fee:
TRANSACTION
or
FUNDING
created_at
Timestamp when the fee was charged
transaction_amount
Transaction amount on which the fee was calculated
Updated
2 days ago
Ask AI

---

## Faq
**Source**: https://docs.trade.mudrex.com/docs/faq

FAQ
This FAQ compiles answers to common questions about using the Mudrex Futures API, such as how to interpret decimals, how rate limits work, which leverage setting takes precedence, and what isolated versus cross margin means.  Refer here for clarifications and best practices that are not covered in the endpoint reference.
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

---

## Changelogs
**Source**: https://docs.trade.mudrex.com/docs/changelogs

Changelogs
The Changelogs section documents changes across API versions.  Each release note summarises newly added endpoints, modifications to existing endpoints, and any deprecations.  Use this to track what has changed since the last version and to plan updates to your integration.  See the sub‑pages for individual release notes.
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

---

