import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from typing import Optional

class DataManager:
    """
    Manages stock data retrieval and processing
    """
    
    def __init__(self):
        self.cache_duration = 300  # 5 minutes cache
        self.data_cache = {}
    
    def get_stock_data(self, symbol: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        """
        Fetch stock data from Yahoo Finance
        
        Args:
            symbol: Stock ticker symbol (can include .NS for NSE stocks)
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            interval: Data interval (1m, 5m, 15m, 1h, 4h, 1d, 1wk, 1mo)
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        cache_key = f"{symbol}_{period}_{interval}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            return self.data_cache[cache_key]['data']
        
        try:
            # Create yfinance ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch data
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                st.error(f"No data found for symbol {symbol}")
                return None
            
            # Clean and validate data
            data = self._clean_data(data)
            
            # Cache the data
            self.data_cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now()
            }
            
            return data
            
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def get_real_time_price(self, symbol: str) -> Optional[float]:
        """
        Get current/latest price for a symbol
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Current price or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if not data.empty:
                return float(data['Close'].iloc[-1])
            
            return None
            
        except Exception as e:
            st.error(f"Error fetching real-time price for {symbol}: {str(e)}")
            return None
    
    def get_stock_info(self, symbol: str) -> Optional[dict]:
        """
        Get basic stock information
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with stock info or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract relevant information
            stock_info = {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                '52_week_low': info.get('fiftyTwoWeekLow', 0)
            }
            
            return stock_info
            
        except Exception as e:
            st.error(f"Error fetching stock info for {symbol}: {str(e)}")
            return None
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a stock symbol exists
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            return not data.empty
        except:
            return False
    
    def get_multiple_stocks_data(self, symbols: list, period: str = "1d", interval: str = "1h") -> dict:
        """
        Get data for multiple stocks
        
        Args:
            symbols: List of stock ticker symbols
            period: Data period
            interval: Data interval
            
        Returns:
            Dictionary with symbol as key and DataFrame as value
        """
        results = {}
        
        for symbol in symbols:
            data = self.get_stock_data(symbol, period, interval)
            if data is not None:
                results[symbol] = data
        
        return results
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate stock data
        
        Args:
            data: Raw DataFrame from yfinance
            
        Returns:
            Cleaned DataFrame
        """
        # Remove any rows with missing OHLC data
        data = data.dropna(subset=['Open', 'High', 'Low', 'Close'])
        
        # Ensure High >= Low, Open, Close
        data['High'] = data[['High', 'Open', 'Close', 'Low']].max(axis=1)
        data['Low'] = data[['Low', 'Open', 'Close', 'High']].min(axis=1)
        
        # Remove any rows where High == Low (invalid data)
        mask = data['High'] != data['Low']
        data = data.loc[mask]
        
        # Ensure Volume is non-negative
        data['Volume'] = data['Volume'].abs()
        
        # Sort by index (datetime)
        data = data.sort_index()
        
        return data
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cached data is still valid
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            True if cache is valid, False otherwise
        """
        if cache_key not in self.data_cache:
            return False
        
        cache_time = self.data_cache[cache_key]['timestamp']
        return (datetime.now() - cache_time).total_seconds() < self.cache_duration
    
    def clear_cache(self):
        """Clear all cached data"""
        self.data_cache.clear()
    
    def get_market_hours_data(self, symbol: str) -> dict:
        """
        Get market hours information for a symbol
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with market hours info
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Basic market hours (US market default)
            market_info = {
                'market_open': '09:30',
                'market_close': '16:00',
                'timezone': 'US/Eastern',
                'is_market_open': self._is_market_open(),
                'exchange': info.get('exchange', 'Unknown')
            }
            
            return market_info
            
        except Exception as e:
            st.error(f"Error fetching market hours for {symbol}: {str(e)}")
            return {
                'market_open': '09:30',
                'market_close': '16:00',
                'timezone': 'US/Eastern',
                'is_market_open': False,
                'exchange': 'Unknown'
            }
    
    def _is_market_open(self) -> bool:
        """
        Check if US market is currently open (simplified)
        
        Returns:
            True if market is likely open, False otherwise
        """
        now = datetime.now()
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Simple time check (9:30 AM to 4:00 PM EST)
        current_hour = now.hour
        current_minute = now.minute
        
        # Convert to minutes since midnight
        current_time_minutes = current_hour * 60 + current_minute
        market_open_minutes = 9 * 60 + 30  # 9:30 AM
        market_close_minutes = 16 * 60  # 4:00 PM
        
        return market_open_minutes <= current_time_minutes <= market_close_minutes
