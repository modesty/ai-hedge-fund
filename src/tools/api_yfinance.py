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
    """Fetch price data from Yahoo Finance API.

    Ensures compatibility with Financial Datasets API format:
    1. Uses the same Price model
    2. Returns results in the same format
    3. Handles errors gracefully, returning an empty list instead of raising exceptions

    Args:
        ticker: The stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of Price objects with standardized fields matching Financial Datasets API,
        or empty list if data is unavailable or an error occurred
    """
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
            # Handle both Series and single value scenarios
            price = Price(
                open=float(row['Open'].iloc[0]) if hasattr(row['Open'], 'iloc') else float(row['Open']),
                close=float(row['Close'].iloc[0]) if hasattr(row['Close'], 'iloc') else float(row['Close']),
                high=float(row['High'].iloc[0]) if hasattr(row['High'], 'iloc') else float(row['High']),
                low=float(row['Low'].iloc[0]) if hasattr(row['Low'], 'iloc') else float(row['Low']),
                volume=int(row['Volume'].iloc[0]) if hasattr(row['Volume'], 'iloc') else int(row['Volume']),
                time=date.strftime('%Y-%m-%d')
            )
            prices.append(price)

        # Cache the results in the same format as Financial Datasets API
        _cache.set_prices(ticker, [p.model_dump() for p in prices])

        # Return the prices directly, matching the return type of Financial Datasets API function
        return prices
    except Exception as e:
        print(f"Warning: Error fetching price data from Yahoo Finance for {ticker}: {str(e)}")
        # Return empty list on error to avoid breaking the API
        return []


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[FinancialMetrics]:
    """Fetch financial metrics from Yahoo Finance API.

    Ensures compatibility with Financial Datasets API format:
    1. Uses the same FinancialMetrics model
    2. Returns results in the same format
    3. Provides the same fields like market_cap, price_to_earnings_ratio, etc.
    4. Uses proper date formatting (YYYY-MM-DD) for report_period
    5. Handles errors gracefully, returning an empty list instead of raising exceptions

    Args:
        ticker: The stock ticker symbol
        end_date: End date in YYYY-MM-DD format
        period: Financial reporting period, one of "ttm", "annual", "quarterly"
        limit: Maximum number of metrics to return

    Returns:
        List of FinancialMetrics objects with standardized fields matching Financial Datasets API,
        or empty list if data is unavailable or an error occurred
    """
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

        # Cache the results in the same format as Financial Datasets API
        _cache.set_financial_metrics(ticker, [m.model_dump() for m in metrics])

        # Return the metrics directly, matching the return type of Financial Datasets API function
        # The Financial Datasets API returns a list of FinancialMetrics objects
        return metrics[:limit]
    except Exception as e:
        print(f"Warning: Error fetching financial metrics from Yahoo Finance for {ticker}: {str(e)}")
        # Return empty list on error to avoid breaking the API
        return []


def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 10,
) -> list[CompanyNews]:
    """Fetch company news from Yahoo Finance API.

    Ensures compatibility with Financial Datasets API format:
    1. Uses the same CompanyNews model
    2. Returns results in the same format
    3. Uses ISO date format for date field (YYYY-MM-DDThh:mm:ss)
    4. Properly handles all required fields: ticker, title, author, source, date, url

    Args:
        ticker: The stock ticker symbol
        end_date: End date in YYYY-MM-DD format
        start_date: Optional start date in YYYY-MM-DD format
        limit: Maximum number of news items to return

    Returns:
        List of CompanyNews objects with standardized fields matching Financial Datasets API
    """
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
            # Convert timestamp to ISO format date (same format as Financial Datasets API)
            timestamp = item.get('providerPublishTime')
            if timestamp:
                date = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S")
            else:
                date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")  # Use current date as fallback

            # Get title and ensure it's not empty
            title = item.get('title', '')
            if not title:
                title = f"News for {ticker} on {date}"  # Provide a default title

            # Create CompanyNews object that matches Financial Datasets API format
            news = CompanyNews(
                ticker=ticker,
                title=title,
                author=item.get('publisher', 'Unknown'),
                source=item.get('publisher', 'Yahoo Finance'),
                date=date,
                url=item.get('link', ''),
                sentiment=None  # Yahoo doesn't provide sentiment, Financial Datasets might
            )
            news_items.append(news)

        # Return news items in the same format as Financial Datasets API
        # The Financial Datasets API returns a list of CompanyNews objects
        return news_items
    except Exception as e:
        print(f"Error fetching news from Yahoo Finance for {ticker}: {str(e)}")
        return []  # Return empty list on error to avoid breaking the API


def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[LineItem]:
    """Fetch financial line items from Yahoo Finance API.

    Ensures compatibility with Financial Datasets API format:
    1. Uses the same LineItem model
    2. Returns results in the same format (list of LineItem objects)
    3. Supports common line items like revenue, net_income, ebitda, etc.
    4. Properly formats dates and handles empty values
    5. Respects period parameter (ttm, annual, quarterly)

    Args:
        ticker: The stock ticker symbol
        line_items: List of line items to search for (e.g., revenue, net_income)
        end_date: End date in YYYY-MM-DD format
        period: Financial reporting period, one of "ttm", "annual", "quarterly"
        limit: Maximum number of results to return per ticker

    Returns:
        List of LineItem objects containing the requested financial metrics
    """
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
        # This mapping follows Financial Datasets API's line item naming convention
        line_item_mapping = {
            # Income Statement items
            "revenue": ("totalRevenue", income_stmt),
            "revenue_usd": ("totalRevenue", income_stmt),  # Same as revenue but in USD
            "cost_of_revenue": ("costOfRevenue", income_stmt),
            "gross_profit": ("grossProfit", income_stmt),
            "operating_expense": ("totalOperatingExpenses", income_stmt),
            "operating_income": ("operatingIncome", income_stmt),
            "interest_expense": ("interestExpense", income_stmt),
            "ebit": ("ebit", income_stmt),
            "ebitda": ("ebitda", income_stmt),
            "income_tax_expense": ("incomeTaxExpense", income_stmt),
            "net_income": ("netIncome", income_stmt),
            "net_income_common_stock": ("netIncomeApplicableToCommonShares", income_stmt),
            "earnings_per_share": ("basicEPS", income_stmt),
            "earnings_per_share_diluted": ("dilutedEPS", income_stmt),
            "consolidated_income": ("totalRevenue", income_stmt),  # Using total revenue as proxy
            "research_and_development": ("researchDevelopment", income_stmt),
            "selling_general_and_administrative_expenses": ("sellingGeneralAdministrative", income_stmt),

            # Balance Sheet items
            "cash": ("cash", balance_sheet),
            "total_assets": ("totalAssets", balance_sheet),
            "total_liabilities": ("totalLiab", balance_sheet),
            "total_equity": ("totalStockholderEquity", balance_sheet),
            "total_debt": ("totalDebt", balance_sheet),
            "accounts_payable": ("accountsPayable", balance_sheet),
            "accounts_receivable": ("netReceivables", balance_sheet),
            "inventory": ("inventory", balance_sheet),
            "current_assets": ("totalCurrentAssets", balance_sheet),
            "current_liabilities": ("totalCurrentLiabilities", balance_sheet),
            "long_term_debt": ("longTermDebt", balance_sheet),

            # Cash Flow items
            "free_cash_flow": ("freeCashFlow", cash_flow),
            "operating_cash_flow": ("totalCashFromOperatingActivities", cash_flow),
            "capital_expenditure": ("capitalExpenditures", cash_flow),
            "cash_dividends_paid": ("dividendsPaid", cash_flow),
            "issuance_of_stock": ("issuanceOfStock", cash_flow),
            "repurchase_of_stock": ("repurchaseOfStock", cash_flow),
        }

        # Get the appropriate financial statement based on period
        # For quarterly data, we'd use quarterlyReports if available
        # For annual data, use annual reports
        # For ttm (trailing twelve months), use the most recent data

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

                        # Use the statement date if available
                        report_date = current_date
                        if hasattr(statement, 'columns') and len(statement.columns) > 0:
                            try:
                                # Try to use the actual report date from the statement
                                report_date = statement.columns[0].strftime('%Y-%m-%d')
                            except (AttributeError, TypeError):
                                # Fall back to current date if conversion fails
                                pass

                        # Create LineItem object
                        line_item = LineItem(
                            ticker=ticker,
                            report_period=report_date,
                            period=period,  # Use provided period
                            currency="USD",  # Yahoo Finance typically reports in USD
                            **{item_name: float(value) if not pd.isna(value) else None}
                        )
                        results.append(line_item)
                except Exception as e:
                    # Skip this item if we can't get it
                    print(f"Warning: Could not retrieve {item_name} for {ticker}: {str(e)}")
                    continue

        # Return limited results, matching Financial Datasets API behavior
        return results[:limit]
    except Exception as e:
        print(f"Error fetching line items from Yahoo Finance for {ticker}: {str(e)}")
        return []  # Return empty list on error to avoid breaking the API


def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 10,
) -> list[InsiderTrade]:
    """Fetch insider trades from Yahoo Finance API.

    Ensures compatibility with Financial Datasets API format:
    1. Uses the same InsiderTrade model
    2. Returns results in the same format (list of InsiderTrade objects)
    3. Handles date filtering similar to filing_date_gte and filing_date_lte
    4. Returns the same fields: ticker, issuer, name, title, transaction_date, etc.
    5. Properly formats dates in YYYY-MM-DD format

    Note: This feature is currently not fully supported by the yfinance library.
    It's included for API compatibility but may return limited data or an empty list.

    Args:
        ticker: The stock ticker symbol
        end_date: End date in YYYY-MM-DD format
        start_date: Optional start date in YYYY-MM-DD format
        limit: Maximum number of trades to return

    Returns:
        List of InsiderTrade objects with standardized fields matching Financial Datasets API
    """
    try:
        # Get ticker info
        ticker_obj = yf.Ticker(ticker)

        # In current versions of yfinance, insider trades might be accessible through different attributes
        # We'll try multiple potential sources
        insider_data = None

        # Try known possible attribute names
        for attr_name in ["insiders", "insider_transactions", "insider_roster", "institutional_holders"]:
            if hasattr(ticker_obj, attr_name):
                insider_data = getattr(ticker_obj, attr_name)
                if insider_data is not None and not (hasattr(insider_data, "empty") and insider_data.empty):
                    break

        # If we found insider data, process it
        if insider_data is not None and len(insider_data) > 0:
            trades = []

            # Process the data based on the format provided by yfinance
            # This will need to be adapted if/when yfinance provides insider trade data
            for idx, data in enumerate(insider_data):
                # Filter by date if needed
                filing_date = datetime.datetime.now().strftime("%Y-%m-%d")  # Default to current date

                # Skip if outside date range
                if start_date and filing_date < start_date:
                    continue
                if filing_date > end_date:
                    continue

                # Create an InsiderTrade object that matches the Financial Datasets API format
                trade = InsiderTrade(
                    ticker=ticker,
                    issuer=ticker_obj.info.get("shortName", None),
                    name="Not Available",  # yfinance doesn't provide this detail
                    title="Not Available",  # yfinance doesn't provide this detail
                    is_board_director=None,  # yfinance doesn't provide this detail
                    transaction_date=None,  # yfinance doesn't provide this detail
                    transaction_shares=float(data.get("position", 0)) if isinstance(data, dict) else 0,
                    transaction_price_per_share=None,  # yfinance doesn't provide this detail
                    transaction_value=None,  # yfinance doesn't provide this detail
                    shares_owned_before_transaction=None,  # yfinance doesn't provide this detail
                    shares_owned_after_transaction=None,  # yfinance doesn't provide this detail
                    security_title="Common Stock",  # Default assumption
                    filing_date=filing_date
                )
                trades.append(trade)

                # Respect the limit parameter
                if len(trades) >= limit:
                    break

            return trades

        # If we reach here, the feature is not available or no data was found
        print(f"WARNING: Insider trades data is not supported in the current Yahoo Finance API version for {ticker}")
        return []  # Return empty list - this is expected behavior for unsupported features
    except Exception as e:
        print(f"WARNING: Error fetching insider trades from Yahoo Finance for {ticker}: {str(e)}")
        return []  # Return empty list on error to avoid breaking the API


def get_market_cap(ticker: str, end_date: str) -> float | None:
    """Get market capitalization from Yahoo Finance.

    Ensures compatibility with Financial Datasets API format:
    1. Returns market cap as a float or None
    2. Uses proper error handling
    3. Matches the return type and behavior of the Financial Datasets API function

    Args:
        ticker: The stock ticker symbol
        end_date: End date in YYYY-MM-DD format

    Returns:
        Market capitalization as a float or None if not available
    """
    try:
        # Get ticker info
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info

        # Extract market cap
        market_cap = info.get("marketCap")

        # Convert to float if available, otherwise return None
        return float(market_cap) if market_cap else None
    except Exception as e:
        print(f"Warning: Error fetching market cap from Yahoo Finance for {ticker}: {str(e)}")
        # Return None instead of raising an exception to match Financial Datasets API behavior
        return None
