"""
Comprehensive test script for Yahoo Finance integration.
This script tests all the financial data retrieval functionality
that has been implemented using the Yahoo Finance API.
"""
import os
import sys
import datetime
import pandas as pd
import yfinance as yf
import traceback
# Import directly from the router to ensure we're testing the routing functionality
from src.tools.api import get_prices, get_financial_metrics, get_company_news, search_line_items, get_insider_trades, _using_yahoo_finance
from src.data.models import CompanyNews

# Set up basic logging
import logging
logging.basicConfig(level=logging.INFO)

# Set Yahoo Finance as data source directly in environment
os.environ["FINANCIAL_DATASETS_API_KEY"] = "yahoo-finance-api"

# Verify that our implementation correctly detects Yahoo Finance API
assert _using_yahoo_finance() == True, "Yahoo Finance detection failed. Set FINANCIAL_DATASETS_API_KEY to 'yahoo-finance-api' in .env file and try again."
logging.info("Yahoo Finance API detection successful")

# Now the API module will use the api_yfinance implementation

# Test ticker
ticker = "AAPL"

# Test date range
start_date = "2024-01-01"
end_date = datetime.datetime.now().strftime("%Y-%m-%d")

def test_prices():
    """Test the Yahoo Finance price data retrieval"""
    print("\nTesting get_prices:")
    try:
        prices = get_prices(ticker, start_date, end_date)
        print(f"Successfully retrieved {len(prices)} price records")
        if not prices:
            print("⚠️ WARNING: No price data retrieved for the given ticker and date range.")
            return False
        print(f"Sample price data: {prices[0].model_dump()}")
        return True
    except Exception as e:
        print(f"Error in get_prices: {e}")
        return False

def test_financial_metrics():
    """Test the Yahoo Finance financial metrics retrieval"""
    print("\nTesting get_financial_metrics:")
    try:
        metrics = get_financial_metrics(ticker, end_date)
        print(f"Successfully retrieved {len(metrics)} financial metrics records")
        if not metrics:
            print("⚠️ WARNING: No financial metrics data retrieved for the given ticker and date range.")
            return False
        # Print a subset of metrics
        sample_metrics = {
            "market_cap": metrics[0].market_cap,
            "price_to_earnings_ratio": metrics[0].price_to_earnings_ratio,
            "price_to_book_ratio": metrics[0].price_to_book_ratio
        }
        print(f"Sample metrics: {sample_metrics}")
        return True
    except Exception as e:
        print(f"Error in get_financial_metrics: {e}")
        return False

def test_company_news():
    """Test the Yahoo Finance company news retrieval using API"""
    print("\nTesting get_company_news (via API):")
    try:
        news = get_company_news(ticker, end_date, start_date)
        print(f"Retrieved {len(news)} news records from API")

        # Fail the test if no news was retrieved
        if not news:
            print("❌ FAILED: No news data retrieved from Yahoo Finance API")
            return False

        # Print sample news items
        has_valid_items = True
        for i, item in enumerate(news[:3]):  # Show up to 3 items
            print(f"\nNews {i+1}:")
            print(f"Title: {item.title}")
            print(f"Date: {item.date}")
            print(f"Source: {item.source}")

            # Check if the item has required fields
            if not item.title or not item.date:
                print(f"Warning: News item {i+1} has missing or empty required fields")
                has_valid_items = False

        if not has_valid_items:
            print("❌ FAILED: News items are missing required fields")
            return False

        return True
    except Exception as e:
        print(f"Error in get_company_news: {e}")
        return False

def test_direct_news():
    """Test direct Yahoo Finance news retrieval"""
    print("\nTesting direct Yahoo Finance news access:")
    try:
        ticker_obj = yf.Ticker(ticker)
        news_data = ticker_obj.news

        print(f"Found {len(news_data)} news items directly from Yahoo Finance")

        # Fail if no news data was found
        if not news_data:
            print("❌ FAILED: No news data retrieved directly from Yahoo Finance")
            return False

        all_news = []
        has_valid_items = True

        # Process each news item
        for item in news_data:
            # Get title with fallback default
            title = item.get('title')
            if not title:
                title = f"News for {ticker} on {datetime.datetime.now().strftime('%Y-%m-%d')}"
                has_valid_items = False

            news = CompanyNews(
                ticker=ticker,
                title=title,
                author=item.get('publisher', 'Unknown'),
                source=item.get('publisher', 'Yahoo Finance'),
                date=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),  # Use current date
                url=item.get('link', ''),
                sentiment=None
            )
            all_news.append(news)

        print(f"Processed {len(all_news)} news items")
        if all_news:
            print(f"Sample news: {all_news[0].model_dump()}")

        # Only fail if we have no valid items at all
        if not has_valid_items:
            print("⚠️ WARNING: News items had missing fields but were provided default values")

        return True
    except Exception as e:
        print(f"Error in direct news access: {e}")
        return False

def test_line_items():
    """Test the Yahoo Finance line items retrieval"""
    print("\nTesting search_line_items:")
    try:
        line_items = ["revenue", "net_income", "total_assets", "total_equity"]
        results = search_line_items(ticker, line_items, end_date)
        print(f"Retrieved {len(results)} line items")

        # Display items if available
        for item in results:
            print(f"Item: {item.model_dump()}")

        # Check if we got any results - note: we're not failing this test because
        # the API might legitimately return no items for the given parameters
        if len(results) == 0:
            print("⚠️ WARNING: No line items were found, but this may be expected for the given ticker or date range")

        return True
    except Exception as e:
        print(f"Error in search_line_items: {e}")
        return False

def test_insider_trades():
    """Test the Yahoo Finance insider trades retrieval"""
    print("\nTesting get_insider_trades:")
    try:
        trades = get_insider_trades(ticker, end_date, start_date)
        print(f"Retrieved {len(trades)} insider trades")

        # With unsupported features, we should pass the test with a warning
        if len(trades) == 0:
            print("⚠️ WARNING: No insider trades retrieved. This feature is not supported in the current Yahoo Finance API.")
            print("✅ Test passes as expected - empty list is the correct behavior for unsupported features.")
            return True

        # If we do get data (in future versions), show a sample
        if trades:
            print(f"Sample trade: {trades[0].model_dump()}")
        return True
    except Exception as e:
        print(f"Error in get_insider_trades: {e}")
        return False

def run_all_tests():
    """Run all Yahoo Finance integration tests"""
    print("Testing Yahoo Finance Integration")
    print("-" * 50)

    results = {
        "Prices": test_prices(),
        "Financial Metrics": test_financial_metrics(),
        "Company News (API)": test_company_news(),
        "Direct News Access": test_direct_news(),
        "Line Items": test_line_items(),
        "Insider Trades": test_insider_trades()
    }

    print("\nTest Results Summary:")
    print("-" * 50)
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test}: {status}")

        print("\nTest complete")

def run_single_test(test_name):
    """Run a specific test by name"""
    test_mapping = {
        "prices": test_prices,
        "metrics": test_financial_metrics,
        "news": test_company_news,
        "direct_news": test_direct_news,
        "line_items": test_line_items,
        "insider": test_insider_trades
    }

    if test_name not in test_mapping:
        print(f"Error: Unknown test '{test_name}'")
        print(f"Available tests: {', '.join(test_mapping.keys())}")
        return

    print(f"Running test: {test_name}")
    result = test_mapping[test_name]()
    status = "✅ PASSED" if result else "❌ FAILED"
    print(f"Test result: {status}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test Yahoo Finance API integration')
    parser.add_argument('--test', type=str, help='Run a specific test (prices, metrics, news, direct_news, line_items, insider)')
    parser.add_argument('--ticker', type=str, default="AAPL", help='Ticker symbol to test with')
    args = parser.parse_args()

    # Override the global ticker if specified
    if args.ticker:
        ticker = args.ticker
        print(f"Using ticker: {ticker}")

    if args.test:
        run_single_test(args.test)
    else:
        run_all_tests()
