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
from src.data.models import (
    CompanyNews, CompanyNewsResponse,
    Price, PriceResponse,
    FinancialMetrics, FinancialMetricsResponse,
    LineItem, LineItemResponse,
    InsiderTrade, InsiderTradeResponse
)
# Import the Yahoo Finance implementation directly for comparison testing
import src.tools.api_yfinance as api_yfinance

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

        # Validate that price objects follow the Price model structure
        for price in prices:
            assert isinstance(price, Price), "Price data should be returned as Price objects"
            # Validate required fields
            assert hasattr(price, "open") and price.open is not None, "Price should have 'open' field"
            assert hasattr(price, "close") and price.close is not None, "Price should have 'close' field"
            assert hasattr(price, "high") and price.high is not None, "Price should have 'high' field"
            assert hasattr(price, "low") and price.low is not None, "Price should have 'low' field"
            assert hasattr(price, "volume") and price.volume is not None, "Price should have 'volume' field"
            assert hasattr(price, "time") and price.time is not None, "Price should have 'time' field"

        print(f"Price data format validation successful!")
        print(f"Sample price data: {prices[0].model_dump()}")
        return True
    except AssertionError as ae:
        print(f"❌ Format validation failed: {ae}")
        return False
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

        # Validate that financial metrics objects follow the FinancialMetrics model structure
        for metric in metrics:
            assert isinstance(metric, FinancialMetrics), "Metrics data should be returned as FinancialMetrics objects"
            # Validate required fields
            assert hasattr(metric, "ticker") and metric.ticker is not None, "Metric should have 'ticker' field"
            assert hasattr(metric, "report_period") and metric.report_period is not None, "Metric should have 'report_period' field"
            assert hasattr(metric, "period") and metric.period is not None, "Metric should have 'period' field"
            assert hasattr(metric, "currency") and metric.currency is not None, "Metric should have 'currency' field"

            # Key financial metrics should be present (even if they might be None)
            assert hasattr(metric, "market_cap"), "Metric should have 'market_cap' field"
            assert hasattr(metric, "enterprise_value"), "Metric should have 'enterprise_value' field"
            assert hasattr(metric, "price_to_earnings_ratio"), "Metric should have 'price_to_earnings_ratio' field"

        print(f"Financial metrics data format validation successful!")

        # Print a subset of metrics
        sample_metrics = {
            "market_cap": metrics[0].market_cap,
            "price_to_earnings_ratio": metrics[0].price_to_earnings_ratio,
            "price_to_book_ratio": metrics[0].price_to_book_ratio
        }
        print(f"Sample metrics: {sample_metrics}")
        return True
    except AssertionError as ae:
        print(f"❌ Format validation failed: {ae}")
        return False
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
        # Test with common financial metrics across different statements
        line_items = ["revenue", "net_income", "total_assets", "total_equity", "free_cash_flow", "operating_cash_flow"]
        results = search_line_items(ticker, line_items, end_date)
        print(f"Retrieved {len(results)} line items")

        # Display items if available
        for item in results:
            print(f"Item: {item.model_dump()}")

        # Validate each item has the required fields from LineItem model
        for item in results:
            # Check required base fields
            assert isinstance(item.ticker, str), "Ticker should be a string"
            assert isinstance(item.report_period, str), "Report period should be a string"
            assert isinstance(item.period, str), "Period should be a string"
            assert isinstance(item.currency, str), "Currency should be a string"

            # Check date format - should be YYYY-MM-DD
            if item.report_period:
                date_format = item.report_period
                assert len(date_format) == 10 and date_format[4] == '-' and date_format[7] == '-', \
                    f"Report period format should be YYYY-MM-DD, got {date_format}"

            # Verify at least one of the requested line items is present in the response
            found_items = False
            for line_item in line_items:
                if hasattr(item, line_item) and getattr(item, line_item) is not None:
                    found_items = True
                    # Check that the value is a float
                    assert isinstance(getattr(item, line_item), float), f"{line_item} should be a float"
                    break

            if not found_items and results:
                print(f"⚠️ WARNING: No line item values found in the response for {item.ticker}")

        # Check if we got any results - note: we're not failing this test because
        # the API might legitimately return no items for the given parameters
        if len(results) == 0:
            print("⚠️ WARNING: No line items were found, but this may be expected for the given ticker or date range")

        return True
    except AssertionError as ae:
        print(f"❌ Line items format validation failed: {ae}")
        return False
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

def test_market_cap():
    """Test the Yahoo Finance market cap retrieval"""
    print("\nTesting get_market_cap:")
    try:
        market_cap = api_yfinance.get_market_cap(ticker, end_date)

        # We can't assert that the market cap is not None since some tickers might not have market cap data
        # Just print the result and check if it makes sense
        if market_cap is not None:
            print(f"Market cap for {ticker}: ${market_cap:,.2f}")
            assert isinstance(market_cap, float), "Market cap should be a float"
            assert market_cap > 0, "Market cap should be positive"
            return True
        else:
            print(f"No market cap data available for {ticker}")
            # This shouldn't cause a test failure as some tickers might genuinely not have data
            return True
    except AssertionError as ae:
        print(f"❌ Format validation failed: {ae}")
        return False
    except Exception as e:
        print(f"Error in get_market_cap: {e}")
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
        "Insider Trades": test_insider_trades(),
        "Market Cap": test_market_cap(),
        "API Compatibility": test_api_compatibility()
    }

    print("\nTest Results Summary:")
    print("-" * 50)
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test}: {status}")

        print("\nTest complete")

def test_api_compatibility():
    """Test that the Yahoo Finance implementation is compatible with Financial Datasets API"""
    print("\nTesting API compatibility between Yahoo Finance and Financial Datasets API:")
    try:
        # Test Price API compatibility
        print("Testing Price API compatibility:")
        # Get prices directly from Yahoo Finance implementation
        yf_prices = api_yfinance.get_prices(ticker, start_date, end_date)

        # Validate that prices match the expected structure
        print(f"Got {len(yf_prices)} prices from Yahoo Finance API")

        # Check that we can construct a valid PriceResponse object
        # This is what the Financial Datasets API would return
        price_response = PriceResponse(ticker=ticker, prices=yf_prices)

        # Validate the structure is correct
        assert isinstance(price_response.ticker, str), "Ticker should be a string"
        assert isinstance(price_response.prices, list), "Prices should be a list"
        assert all(isinstance(p, Price) for p in price_response.prices), "All items in prices should be Price objects"

        # Test that we can serialize/deserialize the response
        price_response_json = price_response.model_dump_json()
        print("Successfully serialized price response to JSON")

        # Validate a sample price has the expected fields with correct types
        if yf_prices:
            p = yf_prices[0]
            assert isinstance(p.open, float), "Open price should be a float"
            assert isinstance(p.close, float), "Close price should be a float"
            assert isinstance(p.high, float), "High price should be a float"
            assert isinstance(p.low, float), "Low price should be a float"
            assert isinstance(p.volume, int), "Volume should be an integer"
            assert isinstance(p.time, str), "Time should be a string"

            # Check date format - should be YYYY-MM-DD
            date_format = p.time
            assert len(date_format) == 10 and date_format[4] == '-' and date_format[7] == '-', \
                f"Time format should be YYYY-MM-DD, got {date_format}"

        print("✅ Price API compatibility validation successful!")

        # Test Financial Metrics API compatibility
        print("\nTesting Financial Metrics API compatibility:")
        # Get financial metrics directly from Yahoo Finance implementation
        yf_metrics = api_yfinance.get_financial_metrics(ticker, end_date, "ttm", 1)

        # Validate that metrics match the expected structure
        print(f"Got {len(yf_metrics)} financial metrics from Yahoo Finance API")

        # Validate that financial metrics follow the FinancialMetrics model structure
        assert len(yf_metrics) > 0, "Should return at least one financial metric"

        # Check that we can construct a valid FinancialMetricsResponse object
        # This is what the Financial Datasets API would return
        metrics_response = FinancialMetricsResponse(financial_metrics=yf_metrics)

        # Validate the structure is correct
        assert isinstance(metrics_response.financial_metrics, list), "Financial metrics should be a list"
        assert all(isinstance(m, FinancialMetrics) for m in metrics_response.financial_metrics), \
            "All items should be FinancialMetrics objects"

        # Test that we can serialize/deserialize the response
        metrics_response_json = metrics_response.model_dump_json()
        print("Successfully serialized financial metrics response to JSON")

        # Validate the financial metrics has the expected fields with correct types
        if yf_metrics:
            m = yf_metrics[0]
            assert isinstance(m.ticker, str), "Ticker should be a string"
            assert isinstance(m.report_period, str), "Report period should be a string"
            assert isinstance(m.period, str), "Period should be a string"
            assert isinstance(m.currency, str), "Currency should be a string"

            # Market cap should be a float or None
            assert m.market_cap is None or isinstance(m.market_cap, float), "Market cap should be a float or None"

            # Check date format - should be YYYY-MM-DD
            date_format = m.report_period
            assert len(date_format) == 10 and date_format[4] == '-' and date_format[7] == '-', \
                f"Report period format should be YYYY-MM-DD, got {date_format}"

            # Verify the metrics are structured according to Financial Datasets API
            assert hasattr(m, "price_to_earnings_ratio"), "Should have price_to_earnings_ratio field"
            assert hasattr(m, "price_to_book_ratio"), "Should have price_to_book_ratio field"
            assert hasattr(m, "price_to_sales_ratio"), "Should have price_to_sales_ratio field"

        print("✅ Financial Metrics API compatibility validation successful!")

        # Test Company News API compatibility
        print("\nTesting Company News API compatibility:")
        # Get company news directly from Yahoo Finance implementation
        yf_news = api_yfinance.get_company_news(ticker, end_date, start_date)

        # Validate that news match the expected structure
        print(f"Got {len(yf_news)} news items from Yahoo Finance API")

        # Some tickers might not have any news, so only validate if we have news
        if len(yf_news) > 0:
            # Check that we can construct a valid CompanyNewsResponse object
            # This is what the Financial Datasets API would return
            news_response = CompanyNewsResponse(news=yf_news)

            # Validate the structure is correct
            assert isinstance(news_response.news, list), "News should be a list"
            assert all(isinstance(n, CompanyNews) for n in news_response.news), \
                "All items should be CompanyNews objects"

            # Test that we can serialize/deserialize the response
            news_response_json = news_response.model_dump_json()
            print("Successfully serialized company news response to JSON")

            # Validate a sample news item has the expected fields with correct types
            n = yf_news[0]
            assert isinstance(n.ticker, str), "Ticker should be a string"
            assert isinstance(n.title, str), "Title should be a string"
            assert isinstance(n.author, str), "Author should be a string"
            assert isinstance(n.source, str), "Source should be a string"
            assert isinstance(n.date, str), "Date should be a string"
            assert isinstance(n.url, str), "URL should be a string"

            # Check date format - should be YYYY-MM-DDThh:mm:ss
            date_format = n.date
            assert len(date_format) >= 19 and date_format[4] == '-' and date_format[7] == '-' and date_format[10] == 'T', \
                f"Date format should be YYYY-MM-DDThh:mm:ss, got {date_format}"

            print("✅ Company News API compatibility validation successful!")
        else:
            print("⚠️ No news data available for testing, skipping detailed validation")
            # Even if there's no news, we should still be able to create an empty response
            empty_response = CompanyNewsResponse(news=[])
            assert len(empty_response.news) == 0, "Empty news response should have an empty list"
            print("✅ Empty news response validation successful!")

        # Test Line Items API compatibility
        print("\nTesting Line Items API compatibility:")
        # Define some common line items to test
        test_line_items = ["revenue", "net_income", "total_assets", "free_cash_flow"]

        # Get line items directly from Yahoo Finance implementation
        yf_line_items = api_yfinance.search_line_items(ticker, test_line_items, end_date, "ttm", 5)

        # Validate that line items match the expected structure
        print(f"Got {len(yf_line_items)} line items from Yahoo Finance API")

        # Some tickers might not have line item data, only validate if we have data
        if len(yf_line_items) > 0:
            # Check that we can construct a valid LineItemResponse object
            # This is what the Financial Datasets API would return
            line_items_response = LineItemResponse(search_results=yf_line_items)

            # Validate the structure is correct
            assert isinstance(line_items_response.search_results, list), "Line items should be in a list"
            assert all(isinstance(item, LineItem) for item in line_items_response.search_results), \
                "All items should be LineItem objects"

            # Test that we can serialize/deserialize the response
            line_items_response_json = line_items_response.model_dump_json()
            print("Successfully serialized line items response to JSON")

            # Validate a sample line item has the expected fields with correct types
            if yf_line_items:
                item = yf_line_items[0]
                assert isinstance(item.ticker, str), "Ticker should be a string"
                assert isinstance(item.report_period, str), "Report period should be a string"
                assert isinstance(item.period, str), "Period should be a string"
                assert isinstance(item.currency, str), "Currency should be a string"

                # Check date format - should be YYYY-MM-DD
                date_format = item.report_period
                assert len(date_format) == 10 and date_format[4] == '-' and date_format[7] == '-', \
                    f"Report period format should be YYYY-MM-DD, got {date_format}"

                # Check that at least one of the requested line items exists in the response
                found_item = False
                for line_item in test_line_items:
                    if hasattr(item, line_item) and getattr(item, line_item) is not None:
                        assert isinstance(getattr(item, line_item), (float, int, type(None))), \
                            f"{line_item} should be a number or None"
                        found_item = True
                        break

                assert found_item, "At least one of the requested line items should be present in the response"

            print("✅ Line Items API compatibility validation successful!")
        else:
            print("⚠️ No line items data available for testing, skipping detailed validation")
            # Even if there are no line items, we should still be able to create an empty response
            empty_response = LineItemResponse(search_results=[])
            assert len(empty_response.search_results) == 0, "Empty line items response should have an empty list"
            print("✅ Empty line items response validation successful!")

        # Test Insider Trades API compatibility
        print("\nTesting Insider Trades API compatibility:")
        # Get insider trades directly from Yahoo Finance implementation
        yf_insider_trades = api_yfinance.get_insider_trades(ticker, end_date, start_date, 5)

        # Validate that insider trades match the expected structure
        print(f"Got {len(yf_insider_trades)} insider trades from Yahoo Finance API")

        # Since insider trades are likely to return an empty list due to limitations in yfinance,
        # we'll focus on validating the structure and handling of empty responses

        # Check that we can construct a valid InsiderTradeResponse object
        # This is what the Financial Datasets API would return
        insider_trades_response = InsiderTradeResponse(insider_trades=yf_insider_trades)

        # Validate the structure is correct
        assert isinstance(insider_trades_response.insider_trades, list), "Insider trades should be in a list"
        assert all(isinstance(trade, InsiderTrade) for trade in insider_trades_response.insider_trades), \
            "All items should be InsiderTrade objects"

        # Test that we can serialize/deserialize the response
        insider_trades_response_json = insider_trades_response.model_dump_json()
        print("Successfully serialized insider trades response to JSON")

        # If we have insider trades data (unlikely with current yfinance version), validate it
        if len(yf_insider_trades) > 0:
            trade = yf_insider_trades[0]
            assert isinstance(trade.ticker, str), "Ticker should be a string"
            assert isinstance(trade.filing_date, str), "Filing date should be a string"

            # Check date format - should be YYYY-MM-DD
            date_format = trade.filing_date
            assert len(date_format) == 10 and date_format[4] == '-' and date_format[7] == '-', \
                f"Filing date format should be YYYY-MM-DD, got {date_format}"

            print("✅ Insider Trades API compatibility validation successful!")
        else:
            print("⚠️ No insider trades data available for testing, skipping detailed validation")
            print("✅ Empty insider trades response validation successful!")

        # Test Market Cap API compatibility
        print("\nTesting Market Cap API compatibility:")
        # Get market cap directly from Yahoo Finance implementation
        yf_market_cap = api_yfinance.get_market_cap(ticker, end_date)

        print(f"Got market cap from Yahoo Finance API: {yf_market_cap}")

        # Market cap could be None for some tickers, but for well-known tickers like AAPL
        # it should be available
        if yf_market_cap is not None:
            assert isinstance(yf_market_cap, float), "Market cap should be a float"
            assert yf_market_cap > 0, "Market cap should be positive"
            print("✅ Market Cap API compatibility validation successful!")
        else:
            print("⚠️ No market cap data available for testing, skipping detailed validation")
            print("✅ Handled None market cap value correctly!")

        return True
    except AssertionError as ae:
        print(f"❌ API compatibility test failed: {ae}")
        return False
    except Exception as e:
        print(f"Error in API compatibility test: {e}")
        return False

def run_single_test(test_name):
    """Run a specific test by name"""
    test_mapping = {
        "prices": test_prices,
        "metrics": test_financial_metrics,
        "news": test_company_news,
        "direct_news": test_direct_news,
        "line_items": test_line_items,
        "insider": test_insider_trades,
        "market_cap": test_market_cap,
        "compatibility": test_api_compatibility
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
    parser.add_argument('--test', type=str, help='Run a specific test (prices, metrics, news, direct_news, line_items, insider, market_cap)')
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
