import pandas as pd
import numpy as np

class BreakoutDetector:
    def __init__(self):
        self.min_volume_increase = 1.5  # Minimum volume increase for breakout confirmation
        self.min_price_move = 2.0  # Minimum price move percentage for breakout
        self.lookback_period = 20  # Period to look back for resistance/support levels
        self.ath_threshold = 0.95  # Within 5% of ATH to be considered near ATH
        
    def detect_breakouts(self, data, timeframe='1d'):
        """
        Detect breakout patterns in stock data
        Returns breakout information with type, strength, and confirmation
        """
        if data is None or len(data) < self.lookback_period:
            return None
            
        data = data.copy()
        
        # Calculate technical indicators
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['Volume_SMA'] = data['Volume'].rolling(window=20).mean()
        data['High_20'] = data['High'].rolling(window=20).max()
        data['Low_20'] = data['Low'].rolling(window=20).min()
        
        # Get current values
        current_close = data['Close'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        prev_close = data['Close'].iloc[-2] if len(data) > 1 else current_close
        avg_volume = data['Volume_SMA'].iloc[-1]
        
        # Calculate price change
        price_change = ((current_close - prev_close) / prev_close) * 100
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Detect breakout type
        breakout_info = self._analyze_breakout_pattern(data)
        
        if breakout_info:
            breakout_info.update({
                'current_price': current_close,
                'price_change_pct': price_change,
                'volume_ratio': volume_ratio,
                'confirmation_strength': self._calculate_confirmation_strength(data, breakout_info),
                'timeframe': timeframe
            })
            
        return breakout_info
    
    def _analyze_breakout_pattern(self, data):
        """Analyze different types of breakout patterns"""
        current_close = data['Close'].iloc[-1]
        current_high = data['High'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        # Resistance breakout - price breaking above recent highs
        resistance_level = data['High_20'].iloc[-2]  # Previous 20-day high
        if current_high > resistance_level:
            price_move = ((current_close - resistance_level) / resistance_level) * 100
            if price_move >= self.min_price_move:
                return {
                    'type': 'resistance_breakout',
                    'level': resistance_level,
                    'current_price': current_close,
                    'breakout_strength': price_move,
                    'pattern': 'Resistance Breakout'
                }
        
        # Support breakdown - price breaking below recent lows
        support_level = data['Low_20'].iloc[-2]  # Previous 20-day low
        if current_close < support_level:
            price_move = ((support_level - current_close) / support_level) * 100
            if price_move >= self.min_price_move:
                return {
                    'type': 'support_breakdown',
                    'level': support_level,
                    'current_price': current_close,
                    'breakout_strength': price_move,
                    'pattern': 'Support Breakdown'
                }
        
        # Moving average breakout
        if len(data) >= 50:
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]
            
            # Bullish MA breakout
            if current_close > sma_20 and sma_20 > sma_50:
                prev_close = data['Close'].iloc[-2]
                prev_sma_20 = data['SMA_20'].iloc[-2]
                
                # Check if this is a fresh breakout above 20 SMA
                if prev_close <= prev_sma_20 and current_close > sma_20:
                    price_move = ((current_close - sma_20) / sma_20) * 100
                    if price_move >= 1.0:  # Lower threshold for MA breakouts
                        return {
                            'type': 'ma_breakout_bullish',
                            'level': sma_20,
                            'current_price': current_close,
                            'breakout_strength': price_move,
                            'pattern': 'Moving Average Breakout'
                        }
        
        # Volume breakout - unusual volume with price movement
        avg_volume = data['Volume_SMA'].iloc[-1]
        if current_volume > (avg_volume * self.min_volume_increase):
            price_change = ((current_close - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
            if abs(price_change) >= 3.0:  # Significant price move with volume
                return {
                    'type': 'volume_breakout',
                    'level': data['Close'].iloc[-2],
                    'current_price': current_close,
                    'breakout_strength': abs(price_change),
                    'pattern': 'Volume Breakout',
                    'volume_increase': current_volume / avg_volume
                }
        
        # ATH breakout - near all-time high with volume
        ath_level = data['High'].max()
        ath_distance = ((ath_level - current_close) / ath_level) * 100
        
        if ath_distance <= (100 - self.ath_threshold * 100):  # Within 5% of ATH
            # Check for multiple attempts near ATH in recent days
            recent_highs = data['High'].tail(10)
            attempts_near_ath = sum(1 for high in recent_highs if ((ath_level - high) / ath_level) * 100 <= 2.0)
            
            if attempts_near_ath >= 2 and current_volume > (avg_volume * 1.3):  # Multiple attempts + volume
                if current_close > ath_level * 0.98:  # Very close to ATH
                    price_move = ((current_close - ath_level * 0.95) / (ath_level * 0.95)) * 100
                    return {
                        'type': 'ath_breakout',
                        'level': ath_level,
                        'current_price': current_close,
                        'breakout_strength': max(price_move, 2.0),
                        'pattern': 'ATH Breakout Attempt',
                        'ath_distance': ath_distance,
                        'attempts': attempts_near_ath
                    }
        
        return None
    
    def _calculate_confirmation_strength(self, data, breakout_info):
        """Calculate how strong the breakout confirmation is"""
        if not breakout_info:
            return 0
            
        score = 0
        current_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume_SMA'].iloc[-1]
        
        # Volume confirmation (0-40 points)
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        if volume_ratio >= 2.0:
            score += 40
        elif volume_ratio >= 1.5:
            score += 25
        elif volume_ratio >= 1.2:
            score += 15
        
        # Price movement strength (0-30 points)
        strength = breakout_info.get('breakout_strength', 0)
        if strength >= 5.0:
            score += 30
        elif strength >= 3.0:
            score += 20
        elif strength >= 2.0:
            score += 10
        
        # Pattern reliability (0-30 points)
        pattern_type = breakout_info.get('type', '')
        if pattern_type == 'ath_breakout':
            score += 30  # Highest score for ATH breakouts
        elif pattern_type == 'resistance_breakout':
            score += 25
        elif pattern_type == 'support_breakdown':
            score += 20
        elif pattern_type == 'ma_breakout_bullish':
            score += 15
        elif pattern_type == 'volume_breakout':
            score += 10
        
        return min(score, 100)  # Cap at 100
    
    def scan_index_breakouts(self, data_manager, index_stocks, timeframe='1d', period='3mo'):
        """
        Scan all stocks in an index for breakout patterns
        Returns list of stocks with breakout information
        """
        breakout_stocks = []
        
        for symbol in index_stocks:
            try:
                # Format symbol for NSE
                formatted_symbol = f"{symbol}.NS"
                
                # Get stock data
                stock_data = data_manager.get_stock_data(formatted_symbol, period, timeframe)
                
                if stock_data is not None and not stock_data.empty:
                    # Detect breakouts
                    breakout_info = self.detect_breakouts(stock_data, timeframe)
                    
                    if breakout_info and breakout_info.get('confirmation_strength', 0) >= 30:
                        breakout_stocks.append({
                            'symbol': symbol,
                            'formatted_symbol': formatted_symbol,
                            'breakout_info': breakout_info
                        })
                        
            except Exception as e:
                # Skip stocks that can't be processed
                continue
        
        # Sort by confirmation strength
        breakout_stocks.sort(key=lambda x: x['breakout_info']['confirmation_strength'], reverse=True)
        
        return breakout_stocks
    
    def get_breakout_summary(self, breakout_info):
        """Get a human-readable summary of the breakout"""
        if not breakout_info:
            return "No breakout detected"
            
        pattern = breakout_info.get('pattern', 'Unknown')
        strength = breakout_info.get('breakout_strength', 0)
        confirmation = breakout_info.get('confirmation_strength', 0)
        
        strength_label = "Strong" if strength >= 5 else "Moderate" if strength >= 3 else "Weak"
        confidence_label = "High" if confirmation >= 70 else "Medium" if confirmation >= 40 else "Low"
        
        return f"{pattern} - {strength_label} ({strength:.1f}%) - {confidence_label} Confidence"