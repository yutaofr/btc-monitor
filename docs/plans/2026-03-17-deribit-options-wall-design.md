# Deribit Options-Wall Design

## Goal
Replace the Yahoo options chain dependency for `Options_Wall` with a free, public source that is reliable for end-of-day signals. The signal should remain stable, low-noise, and avoid total failure when a provider rate-limits or blocks by providing a secondary fallback.

## Data Sources
Use Deribit public endpoints only for the primary signal. Fetch the full BTC option instrument list and the book summary by currency. This avoids per-instrument requests and keeps calls lightweight. The option list supplies expiry, strike, and option type. The book summary supplies open interest and underlying price for each instrument.

For fallback, use Tradier (free token) ETF option chains for BITO. Fetch expirations and the chain for the chosen expiry, then compute the put wall from open interest. ETF price is sourced via the existing CNBC/MarketWatch flow.

## Expiry Selection
Select the next monthly expiry (the last Friday of the month) based on UTC dates. If no monthly expiry is available, fall back to the nearest expiry at least 7 days away. If that is also missing, use the next upcoming expiry. This prioritizes stability while still guaranteeing a result when the chain is sparse. The same rule is applied to Tradier expiry dates.

## Put Wall Calculation
Filter to put options for the selected expiry. Pick the strike with the maximum open interest as the put wall. Use Deribit `underlying_price` when available and fall back to Binance spot if missing. For ETF fallback, use CNBC/MarketWatch for the ETF price. Compute distance: `(price - strike) / strike` and score with the existing buckets (near wall, below wall, neutral).

## Error Handling
All network calls use timeouts and return empty lists on failure. If the primary BTC options signal fails, attempt the ETF fallback. If both fail, return an invalid `IndicatorResult` with a clear description. This preserves overall score normalization by dropping invalid inputs.

## Testing
Update unit tests to mock Deribit instrument and summary responses and Tradier fallback responses. Validate score selection, strike choice, and description. Keep tests offline and deterministic.
