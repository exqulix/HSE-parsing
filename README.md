# Business Problem Justification

## Problem
Brokerage firms lose money when macroeconomic news is released due to sharp price fluctuations and their inability to execute client orders in a timely manner.

## Solution
Our project analyzes historical data from APIs (prices) and web scraping (news) to identify the types of events that have the greatest impact. This will enable automation of risk management: detecting important news events and adjusting spreads/limits in advance.

## This enables
- Risk management around high-impact news
- Data-driven signals (Actual vs Forecast)
- Ranking of event types by real effect

## Justification
When big news comes out like a report on jobs or a decision by a bank the market can change very quickly. The people who make the markets called market makers stop trading for a moment. The difference between the prices they are willing to buy and sell at gets much bigger. This means that the brokerage firms are stuck with the obligation to buy or sell at the prices, which can be very unpleasant for them. They also have trades that're already open and these can be affected very quickly by the news before anyone can even react. All of this happens fast and it can cause big losses for the firms.
Some types of news like reports on the economy or decisions by central banks are more likely to cause big changes than others. We can also see that different currencies are affected differently by types of news. This means that the firms need to have a way to react to each type of news differently than just having a blanket policy.
We can use data from the past to predict which news releases are likely to cause changes in the market. We do this by looking at how the market has reacted to news in the past. Then we use this information to adjust the prices and limits before the news is released. This way the firms can avoid the losses that happen when they are not prepared.
This solution can help the firms in three ways. First, it can be helpful to avoid losing money when the market changes quickly. Second, it can help them use their capital efficiently by only taking defensive measures when they are really needed. Third, it can help firms be more resilient by removing the need for individual traders to make decisions in reaction to news. This makes the whole process more consistent and reliable.
Brokerage firms that deal with exchange and cryptocurrency markets need to change the way they do things. They need to use data and automation to react to news releases. This is the way they can avoid big losses and stay competitive. The old way of doing things is not efficient enough anymore.
The use of automation to react to news releases is the key to avoiding losses and being successful, in currency markets. Firms need to use technology to stay ahead of the game. 


## Data Sources
- Forex Factory — scraped event data - https://www.forexfactory.com/
- Alpha Vantage — price API - fficial financial data provider for daily price history


---

# Database Structure

## events

| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| datetime | datetime | Release time |
| currency | str | ISO code |
| impact | str | Impact label |
| title | str | Indicator name |
| actual | str | Actual raw |
| forecast | str | Forecast raw |
| previous | str | Previous raw |

## Derived Features

| Column | Type | Description |
|--------|------|-------------|
| event_date | date | Extracted date |
| impact_level | int | Encoded impact |
| actual_num | float | Parsed actual |
| forecast_num | float | Parsed forecast |
| previous_num | float | Parsed previous |
| has_actual | bool | Has actual |
| has_forecast | bool | Has forecast |
| has_previous | bool | Has previous |
| is_quantitative | bool | Numeric exists |
| is_speech_like | bool | Speech-type |
| event_type | str | Classified type |
| signal | float | Directional signal |

---

## event_specs

| Column | Type | Description |
|--------|------|-------------|
| event_id | int | FK |
| label | str | Attribute |
| value | str | Value |

---

## event_history

| Column | Type | Description |
|--------|------|-------------|
| event_id | int | FK |
| date | date | Date |
| actual | str | Raw |
| forecast | str | Raw |
| previous | str | Raw |
| actual_num | float | Parsed |
| forecast_num | float | Parsed |
| previous_num | float | Parsed |

---

## currency_ohlc

| Column | Type | Description |
|--------|------|-------------|
| bar_date | date | Trading day |
| from_currency | str | Base |
| open | float | Open |
| high | float | High |
| low | float | Low |
| close | float | Close |

---

# Final Dataset (df_final)

| Column | Type | Description |
|--------|------|-------------|
| event_date | date | Date |
| currency | str | Currency |
| event_count | int | Number of events |
| impact_sum | float | Sum impact |
| impact_mean | float | Mean impact |
| inflation | int | Inflation events |
| labor | int | Labor events |
| rates | int | Rate events |
| macro | int | Macro events |
| consumption | int | Consumption |
| business | int | Business |
| sentiment | int | Sentiment |
| other | int | Other |
| signal_mean | float | Mean signal |
| open | float | Open |
| high | float | High |
| low | float | Low |
| close | float | Close |
| return | float | Return |
| volatility | float | Volatility |

---

# Missing Values

| Column | Issue | Handling |
|--------|------|----------|
| actual | Not released | NaN + backfill |
| forecast | Missing | NaN |
| previous | Rare missing | NaN |
| signal | Not computable | Fill 0 |

---

# Dependencies

- pandas
- numpy
- sqlalchemy
- psycopg2
- matplotlib
- seaborn
- scipy
