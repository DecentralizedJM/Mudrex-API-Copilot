# Assets
Source: https://docs.trade.mudrex.com/docs/get-asset-listing
Date Scraped: 2026-01-24

---

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
