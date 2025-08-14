"""
Yahoo Finance data extractor.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import yfinance as yf
from google.cloud import storage


class YahooFinanceExtractor:
    """Extractor for Yahoo Finance stock data."""
    
    def __init__(self, bucket_name: str) -> None:
        """
        Initialize the Yahoo Finance extractor.
        
        Args:
            bucket_name: GCS bucket name for data storage
        """
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        self.logger = logging.getLogger(__name__)
    
    def extract_stock_data(
        self, 
        symbols: List[str], 
        target_date: datetime
    ) -> Dict[str, bool]:
        """
        Extract stock data for given symbols and date.
        
        Args:
            symbols: List of stock symbols to extract
            target_date: Date to extract data for
            
        Returns:
            Dictionary mapping symbols to success status
        """
        results = {}
        target_date_str = target_date.strftime("%Y-%m-%d")
        
        for symbol in symbols:
            try:
                results[symbol] = self._extract_single_stock(symbol, target_date, target_date_str)
            except Exception as e:
                self.logger.error(f"Error processing symbol {symbol}: {e}")
                results[symbol] = False
        
        return results
    
    def _extract_single_stock(
        self, 
        symbol: str, 
        target_date: datetime, 
        target_date_str: str
    ) -> bool:
        """
        Extract data for a single stock symbol.
        
        Args:
            symbol: Stock symbol
            target_date: Target date for extraction
            target_date_str: Target date as string
            
        Returns:
            True if successful, False otherwise
        """
        # Create Yahoo Finance ticker object
        ticker = yf.Ticker(symbol)
        
        # Fetch historical data for target date
        data = ticker.history(
            start=target_date,
            end=target_date + timedelta(days=1),
            interval="1d"
        )
        
        if data.empty:
            self.logger.warning(f"No data available for {symbol} on {target_date_str}")
            return False
        
        # Prepare data in JSON format
        stock_data = {
            "ticker": symbol,
            "date": target_date_str,
            "open": float(data['Open'].iloc[0]),
            "high": float(data['High'].iloc[0]),
            "low": float(data['Low'].iloc[0]),
            "close": float(data['Close'].iloc[0]),
            "volume": int(data['Volume'].iloc[0]),
            "timestamp": int(target_date.timestamp() * 1000)  # For compatibility
        }
        
        # Upload to GCS
        blob_name = f"raw/yahoo/yahoo_{symbol}_{target_date_str}.json"
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(stock_data),
            content_type="application/json"
        )
        
        self.logger.info(f"Successfully uploaded data for {symbol}")
        return True
