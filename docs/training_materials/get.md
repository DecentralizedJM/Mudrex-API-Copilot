# Asset by id/symbol
Source: https://docs.trade.mudrex.com/docs/get
Date Scraped: 2026-01-24

---

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
