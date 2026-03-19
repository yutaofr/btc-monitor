import datetime as dt
import re

import pandas as pd
import requests
from src.config import Config
from src.indicators.base import IndicatorResult
from src.fetchers.binance_fetcher import BinanceFetcher

class OptionsETFIndicator:
    def __init__(self, binance_fetcher=None):
        self.binance_fetcher = binance_fetcher or BinanceFetcher()
        self.deribit_base_url = "https://www.deribit.com/api/v2/public"
        self.tradier_base_url = "https://api.tradier.com/v1/markets"
        self.tradier_token = Config.TRADIER_API_TOKEN
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def _fetch_etf_data_cnbc(self, symbol):
        """Fetch ETF Volume and Price from CNBC public API."""
        url = f"https://quote.cnbc.com/quote-html-webservice/quote.htm?symbols={symbol}&output=json"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            data = resp.json()
            quote_data = data['QuickQuoteResult']['QuickQuote']
            
            # Handle if quote_data is a list instead of a dict
            if isinstance(quote_data, list):
                quote = quote_data[0]
            else:
                quote = quote_data
            
            price = float(quote.get('last', 0))
            volume = float(quote.get('volume', 0))
            return price, volume
        except Exception as e:
            print(f"[DEBUG] CNBC API failed for {symbol}: {e}")
            return None, None

    def _fetch_etf_history_fallback(self, symbol):
        """Fallback to MarketWatch scraping."""
        url = f"https://www.marketwatch.com/investing/fund/{symbol.lower()}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            html = resp.text
            
            # Price regex - look for data-last-price or similar
            price_match = re.search(r'data-last-price="([\d\.,]+)"', html)
            if not price_match:
                price_match = re.search(r'>\$([\d\.,]+)<', html)
            
            # Volume regex
            vol_match = re.search(r'Volume</span>\s*<span class="data">([\d\.M,K]+)</span>', html)
            
            price, vol = None, None
            if price_match:
                price = float(price_match.group(1).replace(',', ''))
            
            if vol_match:
                vol_str = vol_match.group(1).replace(',', '')
                if 'M' in vol_str:
                    vol = float(vol_str.replace('M', '')) * 1_000_000
                elif 'K' in vol_str:
                    vol = float(vol_str.replace('K', '')) * 1_000
                else:
                    vol = float(vol_str)
            
            return price, vol
        except Exception as e:
            print(f"[DEBUG] MarketWatch fallback failed: {e}")
        return None, None

    def _fetch_deribit_instruments(self, currency="BTC"):
        url = f"{self.deribit_base_url}/get_instruments"
        params = {"currency": currency, "kind": "option", "expired": "false"}
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            data = resp.json()
            return data.get("result", [])
        except Exception as e:
            print(f"[DEBUG] Deribit instruments failed: {e}")
            return []

    def _fetch_deribit_book_summary(self, currency="BTC"):
        url = f"{self.deribit_base_url}/get_book_summary_by_currency"
        params = {"currency": currency, "kind": "option"}
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            data = resp.json()
            return data.get("result", [])
        except Exception as e:
            print(f"[DEBUG] Deribit book summary failed: {e}")
            return []

    def _fetch_tradier_expirations(self, symbol):
        if not self.tradier_token:
            return []
        url = f"{self.tradier_base_url}/options/expirations"
        headers = {
            "Authorization": f"Bearer {self.tradier_token}",
            "Accept": "application/json"
        }
        try:
            resp = requests.get(url, headers=headers, params={"symbol": symbol}, timeout=10)
            data = resp.json()
            expirations = data.get("expirations", {}).get("date", [])
            if isinstance(expirations, str):
                return [expirations]
            return expirations
        except Exception as e:
            print(f"[DEBUG] Tradier expirations failed for {symbol}: {e}")
            return []

    def _fetch_tradier_chain(self, symbol, expiration):
        if not self.tradier_token:
            return []
        url = f"{self.tradier_base_url}/options/chains"
        headers = {
            "Authorization": f"Bearer {self.tradier_token}",
            "Accept": "application/json"
        }
        params = {"symbol": symbol, "expiration": expiration, "greeks": "false"}
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            data = resp.json()
            options = data.get("options", {}).get("option", [])
            if isinstance(options, dict):
                return [options]
            return options
        except Exception as e:
            print(f"[DEBUG] Tradier chain failed for {symbol}: {e}")
            return []

    def _is_last_friday(self, date_value):
        return date_value.weekday() == 4 and (date_value + dt.timedelta(days=7)).month != date_value.month

    def _as_research_only(self, result):
        description = result.description or ""
        if not description.lower().startswith("research-only"):
            description = f"Research-only: {description}" if description else "Research-only"
        details = dict(result.details)
        details["research_only"] = True
        return IndicatorResult(
            name=result.name,
            score=result.score,
            weight=result.weight,
            details=details,
            description=description,
            is_valid=False,
        )

    def _select_target_expiry(self, instruments, min_days_ahead=7):
        now = dt.datetime.utcnow()
        now_ts = int(now.timestamp() * 1000)
        expiries = sorted({inst.get("expiration_timestamp") for inst in instruments if inst.get("expiration_timestamp")})

        monthly = []
        for expiry_ts in expiries:
            if expiry_ts < now_ts:
                continue
            expiry_date = dt.datetime.fromtimestamp(expiry_ts / 1000, dt.timezone.utc).date()
            if self._is_last_friday(expiry_date):
                monthly.append(expiry_ts)

        if monthly:
            return monthly[0]

        min_future_ts = now_ts + int(min_days_ahead * 24 * 60 * 60 * 1000)
        future = [expiry_ts for expiry_ts in expiries if expiry_ts >= min_future_ts]
        if future:
            return future[0]

        upcoming = [expiry_ts for expiry_ts in expiries if expiry_ts >= now_ts]
        return upcoming[0] if upcoming else None

    def _select_target_expiry_date(self, expiry_dates, min_days_ahead=7):
        today = dt.date.today()
        monthly = [d for d in expiry_dates if d >= today and self._is_last_friday(d)]
        if monthly:
            return min(monthly)

        min_future = today + dt.timedelta(days=min_days_ahead)
        future = [d for d in expiry_dates if d >= min_future]
        if future:
            return min(future)

        upcoming = [d for d in expiry_dates if d >= today]
        return min(upcoming) if upcoming else None

    def _get_btc_options_wall_score(self, currency="BTC"):
        instruments = self._fetch_deribit_instruments(currency)
        if not instruments:
            return IndicatorResult("Options_Wall", 0, description="BTC options data unavailable", is_valid=False)

        target_expiry = self._select_target_expiry(instruments)
        if not target_expiry:
            return IndicatorResult("Options_Wall", 0, description="No BTC options expiry found", is_valid=False)

        instrument_map = {
            inst.get("instrument_name"): inst
            for inst in instruments
            if inst.get("option_type") == "put" and inst.get("expiration_timestamp") == target_expiry
        }
        if not instrument_map:
            return IndicatorResult("Options_Wall", 0, description="No BTC put options found", is_valid=False)

        summaries = self._fetch_deribit_book_summary(currency)
        candidates = []
        for summary in summaries:
            name = summary.get("instrument_name")
            inst = instrument_map.get(name)
            if not inst:
                continue
            open_interest = summary.get("open_interest")
            if open_interest is None:
                continue
            candidates.append((open_interest, summary, inst))

        if not candidates:
            return IndicatorResult("Options_Wall", 0, description="No BTC OI data for puts", is_valid=False)

        open_interest, summary, inst = max(candidates, key=lambda item: item[0])
        put_wall_strike = inst.get("strike")
        curr_price = summary.get("underlying_price") or self.binance_fetcher.get_current_price() or 0

        if not put_wall_strike or curr_price == 0:
            return IndicatorResult("Options_Wall", 0, description="Invalid BTC price/strike data", is_valid=False)

        distance = (curr_price - put_wall_strike) / put_wall_strike
        expiry_date = dt.datetime.fromtimestamp(target_expiry / 1000, dt.timezone.utc).date().isoformat()

        if 0 <= distance <= 0.05:
            score = 5.0
            desc = f"BTC price near Put Wall support at {put_wall_strike} ({expiry_date})"
        elif distance < 0:
            score = 8.0
            desc = f"BTC price below Put Wall (Oversold) at {put_wall_strike} ({expiry_date})"
        else:
            score = 2.0
            desc = f"BTC neutral distance from Put Wall at {put_wall_strike} ({expiry_date})"

        return IndicatorResult(
            name="Options_Wall",
            score=score,
            details={
                "source": "deribit",
                "strike": put_wall_strike,
                "expiry": expiry_date,
                "open_interest": open_interest
            },
            description=desc
        )

    def _get_etf_options_wall_score(self, symbol="BITO"):
        if not self.tradier_token:
            return IndicatorResult("Options_Wall", 0, description="Tradier token missing", is_valid=False)

        expiry_strings = self._fetch_tradier_expirations(symbol)
        expiry_dates = []
        for date_str in expiry_strings:
            try:
                expiry_dates.append(dt.date.fromisoformat(date_str))
            except ValueError:
                continue

        target_expiry = self._select_target_expiry_date(expiry_dates)
        if not target_expiry:
            return IndicatorResult("Options_Wall", 0, description="No ETF options expiry found", is_valid=False)

        chain = self._fetch_tradier_chain(symbol, target_expiry.isoformat())
        puts = []
        for opt in chain:
            if opt.get("option_type") != "put":
                continue
            try:
                strike = float(opt.get("strike"))
                open_interest = float(opt.get("open_interest", 0))
            except (TypeError, ValueError):
                continue
            puts.append((open_interest, strike))

        if not puts:
            return IndicatorResult("Options_Wall", 0, description="No ETF put OI data", is_valid=False)

        open_interest, put_wall_strike = max(puts, key=lambda item: item[0])
        price_etf, _ = self._fetch_etf_data_cnbc(symbol)
        if price_etf is None or price_etf == 0:
            price_etf, _ = self._fetch_etf_history_fallback(symbol)

        if not put_wall_strike or not price_etf:
            return IndicatorResult("Options_Wall", 0, description="Invalid ETF price/strike data", is_valid=False)

        distance = (price_etf - put_wall_strike) / put_wall_strike
        expiry_date = target_expiry.isoformat()

        if 0 <= distance <= 0.05:
            score = 5.0
            desc = f"ETF price near Put Wall at {put_wall_strike} ({expiry_date})"
        elif distance < 0:
            score = 8.0
            desc = f"ETF price below Put Wall (Oversold) at {put_wall_strike} ({expiry_date})"
        else:
            score = 2.0
            desc = f"ETF neutral distance from Put Wall at {put_wall_strike} ({expiry_date})"

        return IndicatorResult(
            name="Options_Wall",
            score=score,
            details={
                "source": "tradier",
                "symbol": symbol,
                "strike": put_wall_strike,
                "expiry": expiry_date,
                "open_interest": open_interest
            },
            description=desc
        )

    def get_options_wall_score(self):
        """
        Primary: BTC options wall (Deribit).
        Fallback: ETF options wall (BITO via Tradier).
        """
        try:
            primary = self._get_btc_options_wall_score()
            if primary.is_valid:
                return self._as_research_only(primary)
            fallback = self._get_etf_options_wall_score()
            chosen = fallback if fallback.is_valid else primary
            return self._as_research_only(chosen)
        except Exception:
            return self._as_research_only(
                IndicatorResult("Options_Wall", 0, description="Options source blocked", is_valid=False)
            )

    def get_etf_flow_divergence_score(self, etf_symbol="IBIT"):
        """Detect divergence using multiple fallbacks."""
        try:
            df_btc = self.binance_fetcher.fetch_ohlcv(timeframe="1d", limit=10)
            # Try CNBC first
            price_etf, vol_etf = self._fetch_etf_data_cnbc(etf_symbol)
            
            # If CNBC fails, try MarketWatch
            if price_etf is None or price_etf == 0:
                price_etf, vol_etf = self._fetch_etf_history_fallback(etf_symbol)

            if price_etf is None or price_etf == 0 or df_btc is None:
                return self._as_research_only(
                    IndicatorResult("ETF_Flow", 0, description="ETF data unavailable", is_valid=False)
                )

            price_trend = df_btc['close'].iloc[-1] / df_btc['close'].iloc[-4]
            
            score = 0
            if price_trend < 0.97:
                score = 5.0 
                desc = f"ETF Active - Price: {price_etf}, Vol: {vol_etf:,.0f}"
            else:
                score = 0
                desc = f"ETF Price: {price_etf}, Vol: {vol_etf:,.0f}"
                
            return self._as_research_only(IndicatorResult(
                name="ETF_Flow",
                score=score,
                details={"etf_price": price_etf, "vol": vol_etf},
                description=desc
            ))
        except Exception as e:
            return self._as_research_only(
                IndicatorResult("ETF_Flow", 0, description="ETF parsing error", is_valid=False)
            )

if __name__ == "__main__":
    indicator = OptionsETFIndicator()
    print(indicator.get_etf_flow_divergence_score())
