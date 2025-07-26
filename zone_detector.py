import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

class ZoneDetector:
    """
    Detects demand and supply zones in stock price data using support/resistance analysis
    """
    
    def __init__(self, min_touches: int = 1, zone_strength_period: int = 20):
        self.min_touches = min_touches  # Reduced to catch fresh zones
        self.zone_strength_period = zone_strength_period
    
    def detect_zones(self, data: pd.DataFrame, timeframe: str = "1d", htf_zones: List[Dict] = None) -> List[Dict]:
        """
        Main method to detect fresh, high-quality demand and supply zones
        
        Args:
            data: DataFrame with OHLCV data
            timeframe: Timeframe string (e.g., "1d", "1wk", "1mo")
            htf_zones: Higher timeframe zones for confluence
            
        Returns:
            List of zone dictionaries with type, level, strength, and other properties
        """
        zones = []
        
        # Adjust window size based on timeframe
        window_size = self._get_window_size_for_timeframe(timeframe, len(data))
        
        # Find pivot points (local highs and lows)
        pivot_highs = self._find_pivot_highs(data, window_size)
        pivot_lows = self._find_pivot_lows(data, window_size)
        
        # Identify fresh zones with strong price reactions
        fresh_supply_zones = self._identify_fresh_supply_zones(data, pivot_highs)
        zones.extend(fresh_supply_zones)
        
        fresh_demand_zones = self._identify_fresh_demand_zones(data, pivot_lows)
        zones.extend(fresh_demand_zones)
        
        # Add tested zones that showed strong reactions
        tested_zones = self._identify_tested_zones_with_reactions(data)
        zones.extend(tested_zones)
        
        # Filter for quality and recency
        zones = self._filter_fresh_zones(zones, data)
        zones = self._calculate_enhanced_zone_strength(zones, data, htf_zones)
        
        # Add HTF confluence scoring
        if htf_zones:
            zones = self._add_htf_confluence(zones, htf_zones)
        
        return zones
    
    def _get_window_size_for_timeframe(self, timeframe: str, data_length: int) -> int:
        """
        Get appropriate window size based on timeframe and data length
        
        Args:
            timeframe: Timeframe string
            data_length: Length of the data
            
        Returns:
            Window size for pivot detection
        """
        # Smaller window sizes to catch more zones
        timeframe_windows = {
            '1m': 2,
            '5m': 2, 
            '15m': 3,
            '1h': 3,
            '4h': 4,
            '1d': 5,
            '1wk': 3,  # Weekly data needs smaller window due to less data points
            '1mo': 2   # Monthly data needs even smaller window
        }
        
        base_window = timeframe_windows.get(timeframe, 3)
        
        # Scale window based on data length - more aggressive
        if data_length < 30:
            return max(1, base_window - 1)
        elif data_length < 100:
            return base_window
        else:
            return min(base_window + 1, 6)  # Cap at 6 to avoid missing zones
    
    def _find_pivot_highs(self, data: pd.DataFrame, window: int = 5) -> List[Tuple[int, float]]:
        """Find pivot high points in the data"""
        pivot_highs = []
        highs = data['High'].values
        
        for i in range(window, len(highs) - window):
            is_pivot = True
            current_high = highs[i]
            
            # Check if current point is higher than surrounding points
            for j in range(i - window, i + window + 1):
                if j != i and highs[j] >= current_high:
                    is_pivot = False
                    break
            
            if is_pivot:
                pivot_highs.append((i, current_high))
        
        return pivot_highs
    
    def _find_pivot_lows(self, data: pd.DataFrame, window: int = 5) -> List[Tuple[int, float]]:
        """Find pivot low points in the data"""
        pivot_lows = []
        lows = data['Low'].values
        
        for i in range(window, len(lows) - window):
            is_pivot = True
            current_low = lows[i]
            
            # Check if current point is lower than surrounding points
            for j in range(i - window, i + window + 1):
                if j != i and lows[j] <= current_low:
                    is_pivot = False
                    break
            
            if is_pivot:
                pivot_lows.append((i, current_low))
        
        return pivot_lows
    
    def _identify_fresh_supply_zones(self, data: pd.DataFrame, pivot_highs: List[Tuple[int, float]]) -> List[Dict]:
        """Identify fresh supply zones with strong bearish reactions"""
        zones = []
        
        for idx, high_price in pivot_highs:
            # Check if this is a fresh zone (price hasn't returned to this level)
            if self._is_fresh_zone(data, idx, high_price, 'supply'):
                # Measure the bearish reaction strength
                reaction_strength = self._measure_reaction_strength(data, idx, 'supply')
                
                if reaction_strength >= 3.0:  # Minimum 3% move required
                    zone = {
                        'type': 'supply',
                        'level': high_price,
                        'touches': 1,
                        'latest_touch_index': idx,
                        'pivot_indices': [idx],
                        'strength': 'medium',
                        'reaction_strength': reaction_strength,
                        'is_fresh': True,
                        'zone_quality': 'high' if reaction_strength >= 5.0 else 'medium'
                    }
                    zones.append(zone)
        
        return zones
    
    def _identify_fresh_demand_zones(self, data: pd.DataFrame, pivot_lows: List[Tuple[int, float]]) -> List[Dict]:
        """Identify fresh demand zones with strong bullish reactions"""
        zones = []
        
        for idx, low_price in pivot_lows:
            # Check if this is a fresh zone (price hasn't returned to this level)
            if self._is_fresh_zone(data, idx, low_price, 'demand'):
                # Measure the bullish reaction strength
                reaction_strength = self._measure_reaction_strength(data, idx, 'demand')
                
                if reaction_strength >= 3.0:  # Minimum 3% move required
                    zone = {
                        'type': 'demand',
                        'level': low_price,
                        'touches': 1,
                        'latest_touch_index': idx,
                        'pivot_indices': [idx],
                        'strength': 'medium',
                        'reaction_strength': reaction_strength,
                        'is_fresh': True,
                        'zone_quality': 'high' if reaction_strength >= 5.0 else 'medium'
                    }
                    zones.append(zone)
        
        return zones
    
    def _identify_tested_zones_with_reactions(self, data: pd.DataFrame) -> List[Dict]:
        """Identify zones that have been tested once but showed strong reactions"""
        zones = []
        highs = data['High'].values
        lows = data['Low'].values
        
        # Look for levels that were tested 2-3 times with strong reactions
        for i in range(10, len(data) - 10):  # Skip recent and very old data
            # Check for demand zone (low that was tested)
            current_low = lows[i]
            
            # Count how many times this level was tested
            touches = 0
            for j in range(i + 1, min(i + 20, len(data))):
                if abs(lows[j] - current_low) / current_low <= 0.02:  # Within 2%
                    touches += 1
            
            # If tested 1-2 times, check reaction strength
            if 1 <= touches <= 2:
                reaction_strength = self._measure_reaction_strength(data, i, 'demand')
                if reaction_strength >= 4.0:  # Strong reaction required for tested zones
                    zone = {
                        'type': 'demand',
                        'level': current_low,
                        'touches': touches + 1,
                        'latest_touch_index': i,
                        'pivot_indices': [i],
                        'strength': 'medium',
                        'reaction_strength': reaction_strength,
                        'is_fresh': False,
                        'zone_quality': 'high' if reaction_strength >= 6.0 else 'medium'
                    }
                    zones.append(zone)
            
            # Check for supply zone (high that was tested)
            current_high = highs[i]
            touches = 0
            for j in range(i + 1, min(i + 20, len(data))):
                if abs(highs[j] - current_high) / current_high <= 0.02:  # Within 2%
                    touches += 1
            
            if 1 <= touches <= 2:
                reaction_strength = self._measure_reaction_strength(data, i, 'supply')
                if reaction_strength >= 4.0:
                    zone = {
                        'type': 'supply',
                        'level': current_high,
                        'touches': touches + 1,
                        'latest_touch_index': i,
                        'pivot_indices': [i],
                        'strength': 'medium',
                        'reaction_strength': reaction_strength,
                        'is_fresh': False,
                        'zone_quality': 'high' if reaction_strength >= 6.0 else 'medium'
                    }
                    zones.append(zone)
        
        return zones
    
    def _is_fresh_zone(self, data: pd.DataFrame, pivot_idx: int, pivot_price: float, zone_type: str) -> bool:
        """Check if a zone is fresh (price hasn't returned to this level)"""
        # Look at data after the pivot point
        future_data = data.iloc[pivot_idx + 1:]
        
        if zone_type == 'demand':
            # For demand zones, check if price came back to this low level
            return not any(future_data['Low'] <= pivot_price * 1.01)  # 1% tolerance
        else:  # supply
            # For supply zones, check if price came back to this high level
            return not any(future_data['High'] >= pivot_price * 0.99)  # 1% tolerance
    
    def _measure_reaction_strength(self, data: pd.DataFrame, pivot_idx: int, zone_type: str) -> float:
        """Measure the strength of price reaction from a zone"""
        if pivot_idx >= len(data) - 5:
            return 0.0
        
        pivot_price = data.iloc[pivot_idx]['High'] if zone_type == 'supply' else data.iloc[pivot_idx]['Low']
        
        # Look at next 5-10 candles for reaction
        reaction_candles = min(10, len(data) - pivot_idx - 1)
        future_data = data.iloc[pivot_idx + 1:pivot_idx + 1 + reaction_candles]
        
        if zone_type == 'demand':
            # For demand zones, measure upward movement
            max_high = future_data['High'].max()
            reaction_pct = ((max_high - pivot_price) / pivot_price) * 100
        else:  # supply
            # For supply zones, measure downward movement
            min_low = future_data['Low'].min()
            reaction_pct = ((pivot_price - min_low) / pivot_price) * 100
        
        return max(0.0, reaction_pct)
    
    def _filter_fresh_zones(self, zones: List[Dict], data: pd.DataFrame) -> List[Dict]:
        """Filter zones to prioritize fresh zones with strong reactions"""
        if not zones:
            return zones
        
        # Sort by quality and reaction strength
        zones.sort(key=lambda z: (
            z.get('zone_quality', 'low') == 'high',
            z.get('reaction_strength', 0),
            z.get('is_fresh', False),
            -z['latest_touch_index']  # Negative for most recent first
        ), reverse=True)
        
        # Keep top quality zones
        return zones[:12]
    
    def _calculate_enhanced_zone_strength(self, zones: List[Dict], data: pd.DataFrame, htf_zones: List[Dict] = None) -> List[Dict]:
        """Enhanced strength calculation focusing on reaction quality"""
        for zone in zones:
            strength_score = 0
            
            # Factor 1: Reaction strength (most important)
            reaction_score = min(zone.get('reaction_strength', 0) * 5, 40)  # Max 40 points
            strength_score += reaction_score
            
            # Factor 2: Fresh zones get bonus
            if zone.get('is_fresh', False):
                strength_score += 20
            
            # Factor 3: Zone quality
            if zone.get('zone_quality', 'medium') == 'high':
                strength_score += 15
            
            # Factor 4: HTF confluence
            if htf_zones:
                htf_confluence = self._check_htf_confluence(zone, htf_zones)
                strength_score += htf_confluence * 10  # Max 10 points
            
            # Factor 5: Volume confirmation
            volume_score = self._calculate_volume_score(zone, data)
            strength_score += min(volume_score, 15)  # Max 15 points
            
            # Classify strength
            if strength_score >= 70:
                zone['strength'] = 'strong'
            elif strength_score >= 45:
                zone['strength'] = 'medium'
            else:
                zone['strength'] = 'weak'
            
            zone['strength_score'] = strength_score
        
        return zones
    
    def _add_htf_confluence(self, zones: List[Dict], htf_zones: List[Dict]) -> List[Dict]:
        """Add higher timeframe confluence scoring"""
        for zone in zones:
            confluence_score = self._check_htf_confluence(zone, htf_zones)
            zone['htf_confluence'] = confluence_score
            zone['has_htf_support'] = confluence_score > 0
        
        return zones
    
    def _check_htf_confluence(self, zone: Dict, htf_zones: List[Dict]) -> float:
        """Check if zone aligns with higher timeframe zones"""
        if not htf_zones:
            return 0.0
        
        zone_level = zone['level']
        confluence_score = 0.0
        
        for htf_zone in htf_zones:
            htf_level = htf_zone['level']
            # Check if zone is within 2% of HTF zone
            if abs(zone_level - htf_level) / zone_level <= 0.02:
                # Same type zones get higher score
                if zone['type'] == htf_zone['type']:
                    confluence_score += 1.0
                else:
                    confluence_score += 0.3  # Opposite type still provides some confluence
        
        return min(confluence_score, 1.0)  # Cap at 1.0
    
    def _cluster_pivots(self, pivots: List[Tuple[int, float]], threshold_pct: float = 2.5) -> List[List[Tuple[int, float]]]:
        """Group nearby pivot points into clusters with more flexible clustering"""
        if not pivots:
            return []
        
        # Sort pivots by price level
        sorted_pivots = sorted(pivots, key=lambda x: x[1])
        clusters = []
        
        # Create individual zones for fresh pivots and cluster similar ones
        for pivot in sorted_pivots:
            added_to_cluster = False
            
            # Try to add to existing cluster
            for cluster in clusters:
                cluster_avg = np.mean([p[1] for p in cluster])
                price_diff_pct = abs(pivot[1] - cluster_avg) / cluster_avg * 100
                
                if price_diff_pct <= threshold_pct:
                    cluster.append(pivot)
                    added_to_cluster = True
                    break
            
            # If not added to any cluster, create new one
            if not added_to_cluster:
                clusters.append([pivot])
        
        # Return all clusters (including single pivot clusters for fresh zones)
        valid_clusters = []
        for cluster in clusters:
            if len(cluster) >= self.min_touches:
                valid_clusters.append(cluster)
        
        return valid_clusters
    
    def _detect_support_resistance_zones(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect additional support/resistance zones by analyzing price bounces
        This catches zones that pivot detection might miss
        """
        zones = []
        highs = data['High'].values
        lows = data['Low'].values
        closes = data['Close'].values
        
        # Create price levels array (combine highs and lows)
        all_prices = np.concatenate([highs, lows])
        
        # Find significant levels where price has bounced multiple times
        price_range = np.max(all_prices) - np.min(all_prices)
        level_threshold = price_range * 0.01  # 1% of price range
        
        # Divide price range into potential levels
        min_price = np.min(all_prices)
        max_price = np.max(all_prices)
        num_levels = 50  # Check 50 potential levels
        
        for i in range(num_levels):
            level = min_price + (max_price - min_price) * i / num_levels
            
            # Count touches at this level (within threshold)
            touches = 0
            touch_indices = []
            
            # Check low touches (demand zone)
            for j, low in enumerate(lows):
                if abs(low - level) <= level_threshold:
                    touches += 1
                    touch_indices.append(j)
            
            # Check high touches (supply zone) 
            for j, high in enumerate(highs):
                if abs(high - level) <= level_threshold:
                    touches += 1
                    touch_indices.append(j)
            
            # If we found significant touches, create zone
            if touches >= 2 and len(touch_indices) >= 2:
                # Determine if it's support or resistance
                zone_type = 'demand'  # Default to demand
                
                # Check if price has moved up from this level more often (demand)
                # or down from this level more often (supply)
                up_moves = 0
                down_moves = 0
                
                for idx in touch_indices:
                    if idx < len(closes) - 5:  # Look ahead 5 periods
                        future_price = closes[idx + 5]
                        if future_price > level:
                            up_moves += 1
                        elif future_price < level:
                            down_moves += 1
                
                if down_moves > up_moves:
                    zone_type = 'supply'
                
                zone = {
                    'type': zone_type,
                    'level': level,
                    'touches': touches,
                    'latest_touch_index': max(touch_indices) if touch_indices else 0,
                    'pivot_indices': touch_indices,
                    'strength': 'medium',
                    'detection_method': 'support_resistance'
                }
                zones.append(zone)
        
        return zones
    
    def _filter_zones(self, zones: List[Dict], data: pd.DataFrame) -> List[Dict]:
        """Filter zones based on relevance and recency - more lenient"""
        if not zones:
            return zones
        
        # Remove zones that are very old (more than 80% of data length ago)
        data_length = len(data)
        cutoff_index = data_length * 0.2  # Keep zones from last 80% of data
        
        filtered_zones = []
        for zone in zones:
            if zone['latest_touch_index'] >= cutoff_index:
                filtered_zones.append(zone)
        
        # Sort by recency and relevance
        filtered_zones.sort(key=lambda z: z['latest_touch_index'], reverse=True)
        
        # Keep top 15 zones to show more potential levels
        return filtered_zones[:15]
    
    def _calculate_zone_strength(self, zones: List[Dict], data: pd.DataFrame) -> List[Dict]:
        """Calculate strength of each zone based on various factors"""
        for zone in zones:
            strength_score = 0
            
            # Factor 1: Number of touches (more touches = stronger)
            touch_score = min(zone['touches'] * 10, 50)  # Max 50 points
            strength_score += touch_score
            
            # Factor 2: Volume at zone (higher volume = stronger)
            volume_score = self._calculate_volume_score(zone, data)
            strength_score += volume_score
            
            # Factor 3: Time since last touch (recent = stronger)
            recency_score = self._calculate_recency_score(zone, data)
            strength_score += recency_score
            
            # Factor 4: Price reaction strength
            reaction_score = self._calculate_reaction_score(zone, data)
            strength_score += reaction_score
            
            # Classify strength based on total score
            if strength_score >= 70:
                zone['strength'] = 'strong'
            elif strength_score >= 40:
                zone['strength'] = 'medium'
            else:
                zone['strength'] = 'weak'
            
            zone['strength_score'] = strength_score
        
        return zones
    
    def _calculate_volume_score(self, zone: Dict, data: pd.DataFrame) -> float:
        """Calculate volume-based strength score"""
        try:
            # Get volume at pivot points
            pivot_volumes = []
            for idx in zone['pivot_indices']:
                if idx < len(data):
                    pivot_volumes.append(data['Volume'].iloc[idx])
            
            if not pivot_volumes:
                return 0
            
            avg_pivot_volume = np.mean(pivot_volumes)
            avg_total_volume = data['Volume'].mean()
            
            # Volume ratio (max 25 points)
            if avg_total_volume > 0:
                volume_ratio = avg_pivot_volume / avg_total_volume
                return min(float(volume_ratio * 25), 25.0)
            
            return 0
        except:
            return 0
    
    def _calculate_recency_score(self, zone: Dict, data: pd.DataFrame) -> float:
        """Calculate recency-based strength score"""
        data_length = len(data)
        latest_touch = zone['latest_touch_index']
        
        # More recent touches get higher scores (max 15 points)
        recency_ratio = latest_touch / data_length
        return recency_ratio * 15
    
    def _calculate_reaction_score(self, zone: Dict, data: pd.DataFrame) -> float:
        """Calculate price reaction strength score"""
        try:
            total_reaction = 0
            
            for idx in zone['pivot_indices']:
                if idx < len(data) - 5:  # Ensure we have data after the pivot
                    # Look at price movement in next 5 periods after touch
                    if zone['type'] == 'demand':
                        # For demand zones, look for upward movement
                        price_before = data['Low'].iloc[idx]
                        price_after = data['High'].iloc[idx:idx+5].max()
                        reaction = (price_after - price_before) / price_before * 100
                    else:
                        # For supply zones, look for downward movement
                        price_before = data['High'].iloc[idx]
                        price_after = data['Low'].iloc[idx:idx+5].min()
                        reaction = (price_before - price_after) / price_before * 100
                    
                    total_reaction += max(reaction, 0)
            
            # Average reaction strength (max 10 points)
            if zone['touches'] > 0:
                avg_reaction = total_reaction / zone['touches']
                return min(avg_reaction, 10)
            
            return 0
        except:
            return 0
