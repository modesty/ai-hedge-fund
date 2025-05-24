"""
Yahoo Finance API integration for the AI Hedge Fund project.
This module provides functions to retrieve financial data from Yahoo Finance.
"""
import datetime
import os
import pandas as pd
import yfinance as yf
from typing import Union, Literal

from src.data.cache import get_cache
from src.data.models import (
    CompanyNews,
    FinancialMetrics,
    Price,
    LineItem,
    InsiderTrade,
)

# Global cache instance
_cache = get_cache()

def get_prices(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch price data from Yahoo Finance API."""
    try:
        # Convert dates to datetime objects for yfinance
        start_date_dt = pd.to_datetime(start_date)
        end_date_dt = pd.to_datetime(end_date)

        # Add one day to end_date to include it in the results
        end_date_dt = end_date_dt + pd.Timedelta(days=1)

        # Get data from Yahoo Finance
        data = yf.download(ticker, start=start_date_dt, end=end_date_dt)

        if data.empty:
            return []

        # Format the data to match the Price model
        prices = []
        for date, row in data.iterrows():
            price = Price(
                open=float(row['Open'].iloc[0]) if hasattr(row['Open'], 'iloc') else float(row['Open']),
                close=float(row['Close'].iloc[0]) if hasattr(row['Close'], 'iloc') else float(row['Close']),
                high=float(row['High'].iloc[0]) if hasattr(row['High'], 'iloc') else float(row['High']),
                low=float(row['Low'].iloc[0]) if hasattr(row['Low'], 'iloc') else float(row['Low']),
                volume=int(row['Volume'].iloc[0]) if hasattr(row['Volume'], 'iloc') else int(row['Volume']),
                time=date.strftime('%Y-%m-%d')
            )
            prices.append(price)

        # Cache the results
        _cache.set_prices(ticker, [p.model_dump() for p in prices])
        return prices
    except Exception as e:
        raise Exception(f"Error fetching data from Yahoo Finance for {ticker}: {str(e)}")


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[FinancialMetrics]:
    """Fetch financial metrics from Yahoo Finance API."""
    try:
        # Get ticker info
        ticker_obj = yf.Ticker(ticker)

        # Get financial data
        info = ticker_obj.info
        financials = ticker_obj.financials
        balance_sheet = ticker_obj.balance_sheet
        cash_flow = ticker_obj.cashflow

        # Get current date for report period
        current_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")

        # Calculate financial metrics
        market_cap = info.get('marketCap')
        enterprise_value = info.get('enterpriseValue')

        # Extract common financial metrics
        metrics = []

        # Create basic FinancialMetrics object with all required fields
        financial_metric = FinancialMetrics(
            ticker=ticker,
            report_period=current_date,
            period=period,
            currency="USD",  # Yahoo Finance typically reports in USD
            market_cap=market_cap,
            enterprise_value=enterprise_value,
            price_to_earnings_ratio=info.get('trailingPE'),
            price_to_book_ratio=info.get('priceToBook'),
            price_to_sales_ratio=info.get('priceToSalesTrailing12Months'),
            enterprise_value_to_ebitda_ratio=info.get('enterpriseToEbitda'),
            enterprise_value_to_revenue_ratio=None,  # Not directly provided by Yahoo
            free_cash_flow_yield=None,  # Need to calculate
            peg_ratio=info.get('pegRatio'),
            gross_margin=info.get('grossMargins'),
            operating_margin=info.get('operatingMargins'),
            net_margin=info.get('profitMargins'),
            return_on_equity=info.get('returnOnEquity'),
            return_on_assets=info.get('returnOnAssets'),
            return_on_invested_capital=None,  # Not directly provided
            asset_turnover=None,  # Not directly provided
            inventory_turnover=None,  # Not directly provided
            receivables_turnover=None,  # Not directly provided
            days_sales_outstanding=None,  # Not directly provided
            operating_cycle=None,  # Not directly provided
            working_capital_turnover=None,  # Not directly provided
            current_ratio=info.get('currentRatio'),
            quick_ratio=info.get('quickRatio'),
            cash_ratio=None,  # Not directly provided
            operating_cash_flow_ratio=None,  # Not directly provided
            debt_to_equity=info.get('debtToEquity'),
            debt_to_assets=None,  # Not directly provided
            interest_coverage=None,  # Not directly provided
            revenue_growth=info.get('revenueGrowth'),
            earnings_growth=None,  # Not directly provided
            book_value_growth=None,  # Not directly provided
            earnings_per_share_growth=info.get('earningsQuarterlyGrowth'),
            free_cash_flow_growth=None,  # Not directly provided
            operating_income_growth=None,  # Not directly provided
            ebitda_growth=None,  # Not directly provided
            payout_ratio=info.get('payoutRatio'),
            earnings_per_share=info.get('trailingEps'),
            book_value_per_share=info.get('bookValue'),
            free_cash_flow_per_share=None  # Not directly provided
        )

        metrics.append(financial_metric)

        # Cache the results
        _cache.set_financial_metrics(ticker, [m.model_dump() for m in metrics])
        return metrics[:limit]
    except Exception as e:
        raise Exception(f"Error fetching financial metrics from Yahoo Finance for {ticker}: {str(e)}")


def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str,
    limit: int = 10,
) -> list[CompanyNews]:
    """Fetch company news from Yahoo Finance API."""
    try:
        # Get ticker info and news
        ticker_obj = yf.Ticker(ticker)
        news_data = ticker_obj.news

        # Check if we have any news
        if not news_data:
            print(f"Warning: No news data available for {ticker}")
            return []

        # Process the news data
        news_items = []
        for item in news_data[:limit]:  # Limit the number of news items
            # Convert timestamp to ISO format date
            timestamp = item.get('providerPublishTime')
            if timestamp:
                date = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S")
            else:
                date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")  # Use current date as fallback

            # Get title and ensure it's not empty
            title = item.get('title')
            if not title:
                title = f"News for {ticker} on {date}"  # Provide a default title

            # Create CompanyNews object
            news = CompanyNews(
                ticker=ticker,
                title=title,
                author=item.get('publisher', 'Unknown'),
                source=item.get('publisher', 'Yahoo Finance'),
                date=date,
                url=item.get('link', ''),
                sentiment=None  # Yahoo doesn't provide sentiment
            )
            news_items.append(news)

        return news_items
    except Exception as e:
        raise Exception(f"Error fetching news from Yahoo Finance for {ticker}: {str(e)}")


def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",  # Added parameter for consistency with API
    limit: int = 10,      # Added parameter for consistency with API
) -> list[LineItem]:
    """Search for financial line items in Yahoo Finance data."""
    try:
        # Get ticker info
        ticker_obj = yf.Ticker(ticker)

        # Get financial statements
        try:
            income_stmt = ticker_obj.income_stmt
            balance_sheet = ticker_obj.balance_sheet
            cash_flow = ticker_obj.cashflow
        except Exception as e:
            print(f"Warning: Could not retrieve financial statements for {ticker}: {str(e)}")
            return []

        # Check if any financial data is available
        if income_stmt.empty and balance_sheet.empty and cash_flow.empty:
            print(f"Warning: No financial data available for {ticker}")
            return []

        # Map common line items to Yahoo Finance data
        line_item_mapping = {
            "revenue": ("totalRevenue", income_stmt),
            "net_income": ("netIncome", income_stmt),
            "ebitda": ("ebit", income_stmt),  # Using EBIT as a proxy
            "total_assets": ("totalAssets", balance_sheet),
            "total_liabilities": ("totalLiab", balance_sheet),
            "total_equity": ("totalStockholderEquity", balance_sheet),
            "cash": ("cash", balance_sheet),
            "debt": ("totalDebt", balance_sheet),
            "free_cash_flow": ("freeCashFlow", cash_flow),
            "operating_cash_flow": ("operatingCashflow", cash_flow),
        }

        results = []
        current_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")

        # Get values for requested line items
        for item_name in line_items:
            if item_name in line_item_mapping:
                yf_name, statement = line_item_mapping[item_name]

                # Try to get the value
                try:
                    if hasattr(statement, 'index') and yf_name in statement.index:
                        # Get the most recent value (first column)
                        value = statement.loc[yf_name].iloc[0]

                        # Create LineItem object
                        line_item = LineItem(
                            ticker=ticker,
                            report_period=current_date,
                            period=period,  # Use provided period
                            currency="USD",  # Yahoo Finance typically reports in USD
                            **{item_name: float(value) if not pd.isna(value) else None}
                        )
                        results.append(line_item)
                except Exception as e:
                    # Skip this item if we can't get it
                    continue

        return results[:limit]  # Apply limit parameter for consistency
    except Exception as e:
        raise Exception(f"Error fetching line items from Yahoo Finance for {ticker}: {str(e)}")


def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str,
    limit: int = 10,
) -> list[InsiderTrade]:
    """
    Fetch insider trades from Yahoo Finance API.

    Note: This feature is currently not supported by the yfinance library.
    It's included for API compatibility but will return an empty list with a warning.
    Consider using an alternative API for insider trade data.
    """
    try:
        # Get ticker info
        ticker_obj = yf.Ticker(ticker)

        # Note: yfinance library does not currently support insider trades data retrieval
        # This is a known limitation as of now

        # Try to access the attribute that might be added in future versions
        if hasattr(ticker_obj, "insiders"):
            # If the attribute exists in a future version, try to use it
            insider_data = getattr(ticker_obj, "insiders")
            if insider_data and len(insider_data) > 0:
                # Process the data if available
                trades = []
                # Implement processing logic here when the API supports it
                return trades[:limit]

        # If we reach here, the feature is not available
        print(f"WARNING: Insider trades data is not supported in the current Yahoo Finance API version for {ticker}")
        # Return empty list - this is expected behavior, not an error
        return []
    except Exception as e:
        print(f"WARNING: Error fetching insider trades from Yahoo Finance for {ticker}: {str(e)}")
        return []


def get_market_cap(ticker: str, end_date: str) -> float:
    """Get market capitalization from Yahoo Finance."""
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        market_cap = info.get("marketCap")
        return float(market_cap) if market_cap else None
    except Exception as e:
        raise Exception(f"Error fetching market cap from Yahoo Finance for {ticker}: {str(e)}")
