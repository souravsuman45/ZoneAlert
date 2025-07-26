import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import time
import threading
from zone_detector import ZoneDetector
from notification_manager import NotificationManager
from data_manager import DataManager
from breakout_detector import BreakoutDetector

# Page configuration
st.set_page_config(
    page_title="Stock Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'monitored_stocks' not in st.session_state:
    st.session_state.monitored_stocks = []
if 'notification_manager' not in st.session_state:
    st.session_state.notification_manager = NotificationManager()
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

def main():
    st.title("📈 Stock Trading Dashboard")
    st.markdown("### Demand and Supply Zone Analysis with Real-time Notifications")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Stock exchange selection - NSE only
        exchange = "NSE (Yahoo Finance)"
        st.info("📈 Trading on National Stock Exchange (NSE)")
        
        # Store exchange selection in session state
        if exchange != st.session_state.get('selected_exchange', ''):
            st.session_state.selected_exchange = exchange
        
        # Stock symbol input with auto-completion
        nse_stocks = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", "LT", "SBIN", "BHARTIARTL",
            "ITC", "ASIANPAINT", "AXISBANK", "MARUTI", "NESTLEIND", "BAJFINANCE", "HCLTECH", "WIPRO", "ULTRACEMCO", "ONGC",
            "M&M", "TATASTEEL", "JSWSTEEL", "BPCL", "GRASIM", "HINDALCO", "POWERGRID", "NTPC", "COALINDIA", "DRREDDY",
            "SUNPHARMA", "CIPLA", "DIVISLAB", "BIOCON", "LUPIN", "AUROPHARMA", "TORNTPHARM", "BRITANNIA", "MARICO",
            "GODREJCP", "DABUR", "COLPAL", "TATACONSUM", "VEDL", "SAIL", "NMDC", "IOC", "GAIL", "DLF", "GODREJPROP",
            "ADANIPORTS", "GUJGASLTD", "LICHSGFIN", "PIRAMALENT", "PEL", "MUTHOOTFIN", "PERSISTENT", "MPHASIS", "COFORGE",
            "HEROMOTOCO", "EICHERMOT", "TVSMOTORS", "ASHOKLEY", "BALKRISIND", "PNB", "BANKBARODA", "CANBK", "UNIONBANK",
            "IDFCFIRSTB", "INDIANB", "CENTRALBK", "IOB", "INDUSINDBK", "FEDERALBNK", "BANDHANBNK", "LTTS", "LTIM", "TECHM"
        ]
        
        symbol = st.selectbox("Stock Symbol", ["Choose a stock..."] + sorted(nse_stocks), index=0,
                             help="Select NSE stock symbol or type to search")
        
        # Analysis Mode Selection
        analysis_mode = st.radio(
            "Analysis Mode",
            ["Zone Analysis", "Breakout Scanner"],
            index=0,
            help="Choose between detailed zone analysis or breakout scanning"
        )
        
        # Index filtering and stock suggestions
        # Index selection for NSE stocks
        index_options = {
                "All NSE Stocks": [],
                "NIFTY 50": ["RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", "LT", "SBIN", "BHARTIARTL", 
                           "ITC", "ASIANPAINT", "AXISBANK", "MARUTI", "NESTLEIND", "BAJFINANCE", "HCLTECH", "WIPRO", "ULTRACEMCO", "ONGC",
                           "M&M", "TATASTEEL", "JSWSTEEL", "BPCL", "GRASIM", "HINDALCO", "POWERGRID", "NTPC", "COALINDIA", "DRREDDY"],
                "NIFTY 100": ["RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", "LT", "SBIN", "BHARTIARTL",
                            "ADANIPORTS", "APOLLOHOSP", "BAJAJ-AUTO", "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY", "GODREJCP",
                            "HAVELLS", "HEROMOTOCO", "INDUSINDBK", "JINDALSTEL", "MARICO", "MCDOWELL-N", "MOTHERSON", "PAGEIND", "PIDILITIND"],
                "PSU BANK": ["SBIN", "PNB", "BANKBARODA", "CANBK", "UNIONBANK", "IDFCFIRSTB", "INDIANB", "CENTRALBK", "IOB", "MAHABANK"],
                "NIFTY AUTO": ["MARUTI", "M&M", "BAJAJ-AUTO", "TATAMOTORS", "HEROMOTOCO", "EICHERMOT", "TVSMOTORS", "ASHOKLEY", "BALKRISIND"],
                "NIFTY IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTTS", "LTIM", "PERSISTENT", "MPHASIS", "COFORGE"],
                "NIFTY PHARMA": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "BIOCON", "LUPIN", "AUROPHARMA", "CADILAHC", "TORNTPHARM"],
                "NIFTY BANK": ["HDFCBANK", "ICICIBANK", "KOTAKBANK", "SBIN", "AXISBANK", "INDUSINDBK", "FEDERALBNK", "BANDHANBNK", "IDFCFIRSTB"]
        }
        
        selected_index = st.selectbox("Stock Index Filter", list(index_options.keys()), index=0)
        
        if selected_index != "All NSE Stocks":
            # Show dropdown with all stocks from selected index
            stock_list = index_options[selected_index]
            selected_stock = st.selectbox(
                f"Select {selected_index} Stock", 
                ["Choose a stock..."] + stock_list,
                index=0,
                help=f"Choose from {len(stock_list)} stocks in {selected_index}"
            )
            
            # Update symbol if a stock was selected
            if selected_stock != "Choose a stock...":
                symbol = selected_stock
                
            st.caption(f"📈 {len(stock_list)} stocks available in {selected_index}")
        else:
            st.caption("💡 Popular stocks: RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, KOTAKBANK, LT, WIPRO, MARUTI, ASIANPAINT")
        
        # Timeframe selection
        timeframes = {
            "1 Minute": "1m",
            "5 Minutes": "5m", 
            "15 Minutes": "15m",
            "1 Hour": "1h",
            "4 Hours": "4h",
            "1 Day": "1d",
            "1 Week": "1wk",
            "1 Month": "1mo"
        }
        
        selected_timeframe_display = st.selectbox("Timeframe", list(timeframes.keys()), index=5)
        selected_timeframe = timeframes[selected_timeframe_display]
        
        # Period selection based on timeframe
        if selected_timeframe in ['1m', '5m', '15m']:
            period_options = ["1d", "5d", "1mo"]
            default_period = "5d"
        elif selected_timeframe in ['1h', '4h']:
            period_options = ["1mo", "3mo", "6mo", "1y"]
            default_period = "3mo"
        elif selected_timeframe in ['1d']:
            period_options = ["6mo", "1y", "2y", "5y"]
            default_period = "1y"
        elif selected_timeframe in ['1wk']:
            period_options = ["1y", "2y", "5y", "10y"]
            default_period = "2y"
        else:  # 1mo
            period_options = ["2y", "5y", "10y", "max"]
            default_period = "5y"
            
        period = st.selectbox("Data Period", period_options, 
                            index=period_options.index(default_period))
        
        # Alert configuration
        st.subheader("Alert Settings")
        enable_alerts = st.checkbox("Enable Alerts", value=True)
        
        email = ""
        alert_distance = 1.0
        
        if enable_alerts:
            email = st.text_input("Email for Notifications", 
                                placeholder="your.email@example.com")
            alert_distance = st.slider("Alert Distance (%)", 0.1, 5.0, 1.0, 0.1,
                                     help="Alert when price is within this % of a zone")
            
            if email:
                st.session_state.notification_manager.set_email(email)
        
        # Technical indicators
        st.subheader("Technical Indicators")
        show_ema_20 = st.checkbox("Show 20 EMA", value=True)
        show_ema_50 = st.checkbox("Show 50 EMA", value=False)
        show_volume_profile = st.checkbox("Show Volume Profile", value=False)
        
        # Zone Filtering Options
        st.subheader("Zone Filters")
        
        # Zone type filter
        zone_type_filter = st.multiselect(
            "Zone Types", 
            ["Demand Zones", "Supply Zones"], 
            default=["Demand Zones", "Supply Zones"],
            help="Select which zone types to display"
        )
        
        # Zone strength filter
        strength_filter = st.multiselect(
            "Zone Strength",
            ["Strong", "Medium", "Weak"],
            default=["Strong", "Medium"],
            help="Filter zones by strength rating"
        )
        
        # Zone status filter
        status_filter = st.multiselect(
            "Zone Status",
            ["Fresh", "Tested"],
            default=["Fresh", "Tested"],
            help="Fresh = untested zones, Tested = zones with 1-2 touches"
        )
        
        # Zone quality filter
        quality_filter = st.multiselect(
            "Zone Quality",
            ["High", "Medium"],
            default=["High", "Medium"],
            help="Based on reaction strength (High = 5%+, Medium = 3-5%)"
        )
        
        # Minimum reaction strength
        min_reaction = st.slider(
            "Min Reaction %", 
            0.0, 10.0, 3.0, 0.5,
            help="Minimum price reaction from zone"
        )
        
        # HTF confluence filter
        htf_only = st.checkbox(
            "HTF Supported Only", 
            value=False,
            help="Show only zones supported by higher timeframe"
        )
        
        # Multi-timeframe analysis
        st.subheader("Multi-Timeframe Analysis")
        enable_htf_zones = st.checkbox("Show Higher Timeframe Zones", value=True,
                                      help="Show weekly/monthly zones on lower timeframes")
        
        # Auto-refresh
        auto_refresh = st.checkbox("Auto Refresh (30s)", value=False)
        
        # Manual refresh button
        if st.button("🔄 Refresh Data"):
            st.session_state.last_update = datetime.now()
            st.rerun()
    
    # Main content area
    if analysis_mode == "Breakout Scanner":
        # Breakout Scanner Mode
        st.subheader("🚀 Breakout Scanner")
        
        # Individual stock analysis option
        analyze_individual = st.checkbox("Analyze Individual Stock", value=False, help="Check breakout for a specific stock")
        
        if analyze_individual:
            individual_stock = st.selectbox("Select Stock for Breakout Analysis", 
                                          ["Choose a stock..."] + sorted(nse_stocks), 
                                          index=0, key="individual_breakout_stock")
            if st.button("🔍 Check Breakout", type="primary") and individual_stock != "Choose a stock...":
                with st.spinner(f"Analyzing {individual_stock}..."):
                    data_manager = DataManager()
                    breakout_detector = BreakoutDetector()
                    
                    formatted_symbol = f"{individual_stock}.NS"
                    stock_data = data_manager.get_stock_data(formatted_symbol, period, selected_timeframe)
                    
                    if stock_data is not None and not stock_data.empty:
                        breakout_info = breakout_detector.detect_breakouts(stock_data, selected_timeframe)
                        
                        if breakout_info:
                            st.success(f"Breakout detected in {individual_stock}!")
                            
                            # Display breakout details
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Pattern", breakout_info.get('pattern', 'Unknown'))
                            with col2:
                                st.metric("Strength", f"{breakout_info.get('breakout_strength', 0):.1f}%")
                            with col3:
                                confidence = breakout_info.get('confirmation_strength', 0)
                                st.metric("Confidence", f"{confidence:.0f}%")
                            
                            # Buy/Sell signal
                            pattern_type = breakout_info.get('type', '')
                            if pattern_type in ['resistance_breakout', 'ma_breakout_bullish', 'ath_breakout']:
                                st.success("📈 **BUY SIGNAL** - Bullish breakout pattern")
                            elif pattern_type == 'volume_breakout':
                                st.warning("📈 **WATCH SIGNAL** - Volume breakout detected")
                            elif pattern_type == 'support_breakdown':
                                st.error("📉 **SELL SIGNAL** - Bearish breakdown pattern")
                            
                            # Detailed explanation
                            st.write(f"**Analysis**: {breakout_detector.get_breakout_summary(breakout_info)}")
                        else:
                            st.info(f"No significant breakout pattern detected in {individual_stock}")
                    else:
                        st.error(f"Could not fetch data for {individual_stock}")
        
        else:
            # Get index options for scanning
            index_options = {
                "NIFTY 50": ["RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", "LT", "SBIN", "BHARTIARTL", 
                           "ITC", "ASIANPAINT", "AXISBANK", "MARUTI", "NESTLEIND", "BAJFINANCE", "HCLTECH", "WIPRO", "ULTRACEMCO", "ONGC",
                           "M&M", "TATASTEEL", "JSWSTEEL", "BPCL", "GRASIM", "HINDALCO", "POWERGRID", "NTPC", "COALINDIA", "DRREDDY"],
                "NIFTY BANK": ["HDFCBANK", "ICICIBANK", "KOTAKBANK", "SBIN", "AXISBANK", "INDUSINDBK", "FEDERALBNK", "BANDHANBNK", "IDFCFIRSTB"],
                "NIFTY IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTTS", "LTIM", "PERSISTENT", "MPHASIS", "COFORGE"],
                "NIFTY AUTO": ["MARUTI", "M&M", "BAJAJ-AUTO", "TATAMOTORS", "HEROMOTOCO", "EICHERMOT", "TVSMOTORS", "ASHOKLEY", "BALKRISIND"],
                "NIFTY PHARMA": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "BIOCON", "LUPIN", "AUROPHARMA", "TORNTPHARM"],
                "NIFTY FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "MARICO", "GODREJCP", "DABUR", "COLPAL", "TATACONSUM"],
                "NIFTY METAL": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "COALINDIA", "JINDALSTEL", "SAIL", "NMDC", "MOIL"],
                "NIFTY ENERGY": ["RELIANCE", "ONGC", "BPCL", "IOC", "GAIL", "POWERGRID", "NTPC", "COALINDIA"],
                "NIFTY REALTY": ["DLF", "GODREJPROP", "OBEROIRLTY", "PHOENIXLTD", "PRESTIGE", "SOBHA", "BRIGADIER"],
                "PSU BANK": ["SBIN", "PNB", "BANKBARODA", "CANBK", "UNIONBANK", "IDFCFIRSTB", "INDIANB", "CENTRALBK", "IOB"],
                "NIFTY MIDCAP 50": ["ADANIPORTS", "GUJGASLTD", "LICHSGFIN", "PIRAMALENT", "JINDALSTEL", "PEL", "GODREJPROP", "MUTHOOTFIN"]
            }
        
            selected_index = st.selectbox("Select Index to Scan", list(index_options.keys()), index=0, key="breakout_index")
        
        if selected_index:
            stock_list = index_options[selected_index]
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.info(f"Scanning {len(stock_list)} stocks in {selected_index} for breakout patterns...")
            with col2:
                if st.button("🔍 Scan for Breakouts", type="primary"):
                    st.session_state['run_breakout_scan'] = True
                    st.rerun()
            
            # Run breakout scan
            if st.session_state.get('run_breakout_scan', False):
                with st.spinner("Scanning for breakouts..."):
                    data_manager = DataManager()
                    breakout_detector = BreakoutDetector()
                    
                    breakout_stocks = breakout_detector.scan_index_breakouts(
                        data_manager, stock_list, selected_timeframe, period
                    )
                
                st.session_state['run_breakout_scan'] = False
                
                if breakout_stocks:
                    st.success(f"Found {len(breakout_stocks)} stocks with breakout patterns!")
                    
                    # Display breakout stocks in a table with detailed explanations
                    st.subheader("📋 Breakout Analysis Details")
                    
                    # Show breakout criteria explanation
                    with st.expander("🔍 What Qualifies as a Breakout?", expanded=True):
                        st.markdown("""
                        **Breakout Detection Criteria:**
                        
                        1. **Resistance Breakout**: Price breaks above 20-day high with 2%+ move ➡️ **BUY**
                        2. **Support Breakdown**: Price breaks below 20-day low with 2%+ move ➡️ **SELL**  
                        3. **Moving Average Breakout**: Price crosses above 20 SMA after being below ➡️ **BUY**
                        4. **Volume Breakout**: 1.5x+ volume increase with 3%+ price move ➡️ **BUY/SELL**
                        5. **ATH Breakout**: Near all-time high with multiple attempts + volume ➡️ **STRONG BUY**
                        
                        **Confidence Scoring (0-100%):**
                        - Volume confirmation: High volume = higher confidence
                        - Price strength: Larger moves = higher confidence
                        - Pattern reliability: Resistance breakouts score highest
                        """)
                    
                    breakout_data = []
                    for stock in breakout_stocks:
                        info = stock['breakout_info']
                        breakout_data.append({
                            'Stock': stock['symbol'],
                            'Pattern': info.get('pattern', 'Unknown'),
                            'Signal': get_breakout_signal(info.get('type', '')),
                            'Breakout Level': f"₹{info.get('level', 0):.2f}",
                            'Current Price': f"₹{info.get('current_price', 0):.2f}",
                            'Strength': f"{info.get('breakout_strength', 0):.1f}%",
                            'Confidence': f"{info.get('confirmation_strength', 0):.0f}%",
                            'Volume Ratio': f"{info.get('volume_ratio', 1):.1f}x",
                            'Daily Change': f"{info.get('price_change_pct', 0):+.1f}%"
                        })
                    
                    breakout_df = pd.DataFrame(breakout_data)
                    
                    st.dataframe(breakout_df, use_container_width=True)
                    
                    # Show detailed breakout explanation for each stock
                    with st.expander("📊 Individual Stock Breakout Details"):
                        for stock in breakout_stocks:
                            info = stock['breakout_info']
                            with st.container():
                                st.markdown(f"**{stock['symbol']}** - {info.get('pattern', 'Unknown')}")
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Breakout Level", f"₹{info.get('level', 0):.2f}")
                                with col2:
                                    st.metric("Current Price", f"₹{info.get('current_price', 0):.2f}")
                                with col3:
                                    st.metric("Strength", f"{info.get('breakout_strength', 0):.1f}%")
                                
                                # Explain the specific breakout logic
                                pattern_type = info.get('type', '')
                                if pattern_type == 'resistance_breakout':
                                    st.write(f"✅ **Logic**: Price broke above 20-day high of ₹{info.get('level', 0):.2f} with {info.get('breakout_strength', 0):.1f}% strength")
                                elif pattern_type == 'ma_breakout_bullish':
                                    st.write(f"✅ **Logic**: Price crossed above 20-day SMA of ₹{info.get('level', 0):.2f} after being below it")
                                elif pattern_type == 'volume_breakout':
                                    st.write(f"✅ **Logic**: Volume spike {info.get('volume_ratio', 1):.1f}x with {info.get('breakout_strength', 0):.1f}% price move")
                                elif pattern_type == 'support_breakdown':
                                    st.write(f"⚠️ **Logic**: Price broke below 20-day low of ₹{info.get('level', 0):.2f} with {info.get('breakout_strength', 0):.1f}% strength")
                                elif pattern_type == 'ath_breakout':
                                    st.write(f"🚀 **Logic**: Near ATH of ₹{info.get('level', 0):.2f} with {info.get('attempts', 0)} attempts and volume confirmation")
                                
                                st.write(f"📈 Volume: {info.get('volume_ratio', 1):.1f}x average | Confidence: {info.get('confirmation_strength', 0):.0f}%")
                                st.divider()
                    
                    # Make stock symbols clickable for detailed analysis
                    selected_breakout_stock = st.selectbox(
                        "Select stock for detailed analysis:",
                        ["Choose a stock..."] + [stock['symbol'] for stock in breakout_stocks],
                        key="breakout_stock_selector"
                    )
                    
                    # If a stock is selected, show detailed analysis
                    if selected_breakout_stock != "Choose a stock...":
                        symbol = selected_breakout_stock
                        st.session_state['detailed_analysis'] = True
                        st.rerun()
                else:
                    st.info("No strong breakout patterns found in the current timeframe. Try a different timeframe or index.")
        else:
            st.warning("Please select a specific index to scan for breakouts.")
    
    # Handle detailed analysis from breakout scanner or regular zone analysis  
    elif symbol != "Choose a stock..." and symbol and ((analysis_mode == "Zone Analysis") or st.session_state.get('detailed_analysis', False)):
        # Show back button if coming from breakout scanner
        if st.session_state.get('detailed_analysis', False):
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("← Back to Scanner"):
                    st.session_state['detailed_analysis'] = False
                    st.rerun()
            with col2:
                st.subheader(f"📊 Detailed Analysis: {symbol}")
        
        try:
                
            # Create data manager and zone detector
            data_manager = DataManager()
            zone_detector = ZoneDetector()
            
            # Format symbol for NSE stocks
            formatted_symbol = format_symbol_for_exchange(symbol, exchange)
            
            # Fetch stock data
            with st.spinner(f"Fetching data for {formatted_symbol}..."):
                stock_data = data_manager.get_stock_data(formatted_symbol, period, selected_timeframe)
            
            if stock_data is not None and not stock_data.empty:
                # Add technical indicators (use defaults if coming from breakout scanner)
                if st.session_state.get('detailed_analysis', False):
                    stock_data = add_technical_indicators(stock_data, True, False)  # Default: 20 EMA only
                else:
                    stock_data = add_technical_indicators(stock_data, show_ema_20, show_ema_50)
                
                # Get higher timeframe zones first for confluence
                htf_zones = []
                enable_htf = enable_htf_zones if not st.session_state.get('detailed_analysis', False) else True
                if enable_htf and selected_timeframe not in ['1wk', '1mo']:
                    htf_zones = get_higher_timeframe_zones(data_manager, zone_detector, 
                                                         formatted_symbol, selected_timeframe, period)
                
                # Detect zones with enhanced algorithm including HTF confluence
                zones = zone_detector.detect_zones(stock_data, selected_timeframe, htf_zones)
                
                # Add HTF zones to display list
                zones.extend(htf_zones)
                
                # Apply zone filters (use defaults if coming from breakout scanner)
                if st.session_state.get('detailed_analysis', False):
                    # Default filters for breakout analysis
                    zones = apply_zone_filters(zones, ["Demand Zones", "Supply Zones"], ["Strong", "Medium"], 
                                             ["Fresh", "Tested"], ["High", "Medium"], 3.0, False)
                else:
                    # Use user-selected filters
                    zones = apply_zone_filters(zones, zone_type_filter, strength_filter, 
                                             status_filter, quality_filter, min_reaction, htf_only)
                
                # Display current price and basic info
                current_price = stock_data['Close'].iloc[-1]
                prev_close = stock_data['Close'].iloc[-2] if len(stock_data) > 1 else current_price
                price_change = current_price - prev_close
                price_change_pct = (price_change / prev_close) * 100 if prev_close != 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Current Price", f"${current_price:.2f}", 
                             f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
                
                with col2:
                    demand_zones = [z for z in zones if z['type'] == 'demand']
                    st.metric("Demand Zones", len(demand_zones))
                
                with col3:
                    supply_zones = [z for z in zones if z['type'] == 'supply']
                    st.metric("Supply Zones", len(supply_zones))
                
                with col4:
                    strong_zones = [z for z in zones if z['strength'] == 'strong']
                    st.metric("Strong Zones", len(strong_zones))
                
                # Create interactive chart
                fig = create_chart(stock_data, zones, formatted_symbol, selected_timeframe_display, 
                                 show_ema_20, show_ema_50, htf_zones)
                st.plotly_chart(fig, use_container_width=True)
                
                # Zone analysis table
                st.subheader("📊 Zone Analysis")
                
                if zones:
                    zone_df = pd.DataFrame(zones)
                    zone_df['distance_from_price'] = abs(zone_df['level'] - current_price) / current_price * 100
                    zone_df = zone_df.sort_values('distance_from_price')
                    
                    # Calculate zone ranges for display
                    zone_df['zone_range'] = zone_df['level'] * 0.015  # 1.5% range
                    zone_df['zone_low'] = zone_df['level'] - zone_df['zone_range']
                    zone_df['zone_high'] = zone_df['level'] + zone_df['zone_range']
                    
                    # Add timeframe column for display
                    zone_df['display_timeframe'] = zone_df.apply(
                        lambda x: x.get('timeframe', selected_timeframe_display), axis=1
                    )
                    
                    # Create range string for better visualization
                    zone_df['price_range'] = zone_df.apply(
                        lambda x: f"${x['zone_low']:.2f} - ${x['zone_high']:.2f}", axis=1
                    )
                    
                    # Add enhanced zone information
                    zone_df['reaction_strength'] = zone_df.apply(
                        lambda x: f"{x.get('reaction_strength', 0):.1f}%" if 'reaction_strength' in x else "N/A", axis=1
                    )
                    zone_df['zone_quality'] = zone_df.apply(
                        lambda x: x.get('zone_quality', 'medium').title(), axis=1
                    )
                    zone_df['fresh_status'] = zone_df.apply(
                        lambda x: "Fresh" if x.get('is_fresh', False) else "Tested", axis=1
                    )
                    zone_df['htf_support'] = zone_df.apply(
                        lambda x: "✓" if x.get('has_htf_support', False) else "", axis=1
                    )
                    
                    # Display zones table with enhanced information
                    display_cols = ['type', 'level', 'price_range', 'strength', 'distance_from_price', 
                                   'reaction_strength', 'fresh_status', 'zone_quality', 'htf_support', 'display_timeframe']
                    display_df = zone_df[display_cols].copy()
                    display_df.columns = ['Type', 'Center ($)', 'Zone Range', 'Strength', 'Distance (%)', 
                                         'Reaction %', 'Status', 'Quality', 'HTF', 'Timeframe']
                    display_df['Center ($)'] = display_df['Center ($)'].round(2)
                    display_df['Distance (%)'] = display_df['Distance (%)'].round(2)
                    
                    # Style the dataframe
                    styled_df = display_df.style.apply(
                        lambda x: ['background-color: #ffeeee' if v == 'supply' else 'background-color: #eeffee' if v == 'demand' else '' for v in x], 
                        subset=['Type']
                    )
                    
                    st.dataframe(styled_df, use_container_width=True)
                    
                    # Add explanation
                    st.info("""
                    **Zone Explanation:**
                    
                    🟢 **Demand Zones (Green)**: Areas where price historically found support and bounced up. These are potential buying areas.
                    
                    🔴 **Supply Zones (Red)**: Areas where price historically found resistance and dropped down. These are potential selling areas.
                    
                    **Zone Range**: Each zone covers ±1.5% around the center level, shown as filled rectangles on the chart.
                    
                    **Strength**: Strong zones have more touches and volume, making them more reliable.
                    """)
                    
                    # Debug information with enhanced details
                    with st.expander("🔧 Zone Detection Debug Info"):
                        st.write(f"**Total zones detected:** {len(zones)}")
                        demand_zones = [z for z in zones if z['type'] == 'demand']
                        supply_zones = [z for z in zones if z['type'] == 'supply']
                        fresh_zones = [z for z in zones if z.get('is_fresh', False)]
                        htf_supported = [z for z in zones if z.get('has_htf_support', False)]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Demand zones:** {len(demand_zones)}")
                            st.write(f"**Supply zones:** {len(supply_zones)}")
                        with col2:
                            st.write(f"**Fresh zones:** {len(fresh_zones)}")
                            st.write(f"**HTF supported:** {len(htf_supported)}")
                        
                        # Show high quality zones
                        high_quality = [z for z in zones if z.get('zone_quality') == 'high']
                        st.write(f"**High quality zones:** {len(high_quality)}")
                        
                        if high_quality:
                            st.write("**Top Quality Zones:**")
                            for zone in high_quality[:3]:
                                reaction = zone.get('reaction_strength', 0)
                                fresh = "Fresh" if zone.get('is_fresh', False) else "Tested"
                                htf = "with HTF support" if zone.get('has_htf_support', False) else ""
                                st.write(f"- {zone['type'].title()} at ${zone['level']:.2f} ({reaction:.1f}% reaction, {fresh}) {htf}")
                    
                    # Check for alerts
                    if enable_alerts and email:
                        check_alerts(formatted_symbol, current_price, zones, alert_distance)
                
                else:
                    st.info("No significant demand/supply zones detected in the current timeframe.")
                
                # Recent alerts
                if st.session_state.alerts:
                    st.subheader("🔔 Recent Alerts")
                    alert_df = pd.DataFrame(st.session_state.alerts[-10:])  # Show last 10 alerts
                    st.dataframe(alert_df, use_container_width=True)
                
                # Stock monitoring
                st.subheader("📋 Stock Monitoring")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    new_stock = st.text_input("Add stock to monitor", placeholder="Enter ticker symbol")
                with col2:
                    if st.button("Add Stock") and new_stock:
                        if new_stock.upper() not in st.session_state.monitored_stocks:
                            st.session_state.monitored_stocks.append(new_stock.upper())
                            st.success(f"Added {new_stock.upper()} to monitoring list")
                            st.rerun()
                
                if st.session_state.monitored_stocks:
                    st.write("**Monitored Stocks:**")
                    for i, stock in enumerate(st.session_state.monitored_stocks):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"• {stock}")
                        with col2:
                            if st.button("Remove", key=f"remove_{i}"):
                                st.session_state.monitored_stocks.remove(stock)
                                st.rerun()
                
            else:
                st.error("Unable to fetch data for the specified symbol. Please check the ticker symbol and try again.")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please check your internet connection and the stock symbol.")
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(30)
        st.rerun()

def get_breakout_signal(breakout_type):
    """Get buy/sell signal based on breakout type"""
    if breakout_type in ['resistance_breakout', 'ma_breakout_bullish', 'ath_breakout']:
        return "🟢 BUY"
    elif breakout_type == 'support_breakdown':
        return "🔴 SELL"
    elif breakout_type == 'volume_breakout':
        return "🟡 WATCH"
    else:
        return "⚪ NEUTRAL"

def apply_zone_filters(zones, zone_type_filter, strength_filter, status_filter, 
                      quality_filter, min_reaction, htf_only):
    """Apply user-selected filters to zones"""
    filtered_zones = []
    
    for zone in zones:
        # Zone type filter
        zone_type = "Demand Zones" if zone['type'] == 'demand' else "Supply Zones"
        if zone_type not in zone_type_filter:
            continue
            
        # Strength filter
        if zone['strength'].title() not in strength_filter:
            continue
            
        # Status filter (Fresh/Tested)
        status = "Fresh" if zone.get('is_fresh', False) else "Tested"
        if status not in status_filter:
            continue
            
        # Quality filter
        quality = zone.get('zone_quality', 'medium').title()
        if quality not in quality_filter:
            continue
            
        # Minimum reaction filter
        reaction = zone.get('reaction_strength', 0)
        if reaction < min_reaction:
            continue
            
        # HTF confluence filter
        if htf_only and not zone.get('has_htf_support', False):
            continue
            
        filtered_zones.append(zone)
    
    return filtered_zones

def format_symbol_for_exchange(symbol, exchange):
    """Format symbol based on selected exchange"""
    if "NSE" in exchange:
        # Add .NS suffix for NSE stocks if not already present
        if not symbol.upper().endswith('.NS'):
            return f"{symbol.upper()}.NS"
        return symbol.upper()
    else:
        # Remove .NS suffix for US stocks if present
        if symbol.upper().endswith('.NS'):
            return symbol.upper()[:-3]
        return symbol.upper()

def add_technical_indicators(data, show_ema_20=True, show_ema_50=False):
    """Add technical indicators to stock data"""
    data = data.copy()
    
    if show_ema_20:
        data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()
    
    if show_ema_50:
        data['EMA_50'] = data['Close'].ewm(span=50, adjust=False).mean()
    
    return data

def get_higher_timeframe_zones(data_manager, zone_detector, symbol, current_timeframe, period):
    """Get zones from higher timeframes"""
    htf_zones = []
    
    # Define higher timeframes based on current timeframe
    htf_mapping = {
        '1m': ['5m', '15m', '1h'],
        '5m': ['15m', '1h', '4h'],
        '15m': ['1h', '4h', '1d'],
        '1h': ['4h', '1d', '1wk'],
        '4h': ['1d', '1wk', '1mo'],
        '1d': ['1wk', '1mo']
    }
    
    if current_timeframe not in htf_mapping:
        return htf_zones
    
    for htf in htf_mapping[current_timeframe][:2]:  # Get top 2 higher timeframes
        try:
            # Adjust period for higher timeframes
            htf_period = period
            if htf in ['1wk', '1mo']:
                if period in ['1d', '5d']:
                    htf_period = '1y'
                elif period in ['1mo', '3mo']:
                    htf_period = '2y'
            
            htf_data = data_manager.get_stock_data(symbol, htf_period, htf)
            if htf_data is not None and not htf_data.empty:
                htf_zones_raw = zone_detector.detect_zones(htf_data, htf)
                
                # Mark zones with timeframe info
                for zone in htf_zones_raw[:3]:  # Only take top 3 zones from each HTF
                    zone['timeframe'] = htf
                    zone['is_htf'] = True
                    htf_zones.append(zone)
                    
        except Exception as e:
            st.warning(f"Could not fetch {htf} data: {str(e)}")
            continue
    
    return htf_zones

def create_chart(data, zones, symbol, timeframe, show_ema_20=False, show_ema_50=False, htf_zones=None):
    """Create interactive candlestick chart with zones"""
    
    # Create single chart without volume subplot
    fig = go.Figure()
    
    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name=symbol,
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ))
    
    # Add EMAs if enabled
    if show_ema_20 and 'EMA_20' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['EMA_20'],
            name='EMA 20',
            line=dict(color='orange', width=2),
            opacity=0.8
        ))
    
    if show_ema_50 and 'EMA_50' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['EMA_50'],
            name='EMA 50',
            line=dict(color='purple', width=2),
            opacity=0.8
        ))
    
    # Add zones to the chart with enhanced visibility
    for i, zone in enumerate(zones):
        # Color coding: Red for supply zones, Green for demand zones
        color = '#ff4444' if zone['type'] == 'supply' else '#00aa44'
        fill_color = '#ffcccc' if zone['type'] == 'supply' else '#ccffcc'
        
        # Opacity based on strength and HTF
        base_opacity = 0.8 if zone['strength'] == 'strong' else 0.6
        opacity = base_opacity * 0.7 if zone.get('is_htf', False) else base_opacity
        
        # Different styling for HTF zones
        line_style = "dash" if zone.get('is_htf', False) else "solid"
        line_width = 2 if zone.get('is_htf', False) else 3
        
        # Calculate zone range - make it more visible
        zone_range = zone['level'] * 0.015  # 1.5% range around level for better visibility
        
        # Create detailed annotation text with range info
        range_info = f"${zone['level'] - zone_range:.2f} - ${zone['level'] + zone_range:.2f}"
        annotation_text = f"{zone['type'].upper()} Zone<br>{zone['strength'].title()} | Range: {range_info}"
        if zone.get('is_htf', False):
            annotation_text += f"<br>({zone.get('timeframe', 'HTF')})"
        
        # Add zone area (filled rectangle) first for better visibility
        zone_opacity = 0.15 if zone.get('is_htf', False) else 0.25
        fig.add_hrect(
            y0=zone['level'] - zone_range,
            y1=zone['level'] + zone_range,
            fillcolor=fill_color,
            opacity=zone_opacity,
            line_width=1,
            line_color=color
        )
        
        # Add center horizontal line for zone level
        fig.add_hline(
            y=zone['level'],
            line_dash=line_style,
            line_color=color,
            line_width=line_width,
            opacity=opacity,
            annotation_text=annotation_text,
            annotation_position="right"
        )
        
        # Add top and bottom boundary lines
        fig.add_hline(
            y=zone['level'] + zone_range,
            line_dash="dot",
            line_color=color,
            line_width=1,
            opacity=opacity * 0.7
        )
        
        fig.add_hline(
            y=zone['level'] - zone_range,
            line_dash="dot",
            line_color=color,
            line_width=1,
            opacity=opacity * 0.7
        )
    
    # Update layout - larger chart without volume
    fig.update_layout(
        title=f"{symbol} Stock Analysis - {timeframe}",
        yaxis_title="Price ($)",
        xaxis_title="Time",
        template="plotly_white",
        height=800,  # Increased height since no volume chart
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        xaxis_rangeslider_visible=False,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Improve axis formatting
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        side="right"
    )
    
    return fig

def check_alerts(symbol, current_price, zones, alert_distance):
    """Check if current price is near any zones and trigger alerts"""
    for zone in zones:
        distance_pct = abs(zone['level'] - current_price) / current_price * 100
        
        if distance_pct <= alert_distance:
            alert_message = f"ALERT: {symbol} is {distance_pct:.2f}% away from {zone['type']} zone at ${zone['level']:.2f}"
            
            # Check if this alert was already sent recently (avoid spam)
            recent_alerts = [a for a in st.session_state.alerts if a.get('symbol') == symbol and a.get('zone_level') == zone['level']]
            last_alert_time = max([datetime.fromisoformat(a['timestamp']) for a in recent_alerts]) if recent_alerts else datetime.min
            
            if datetime.now() - last_alert_time > timedelta(minutes=30):  # 30 minutes cooldown
                # Add to alerts list
                alert_data = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'message': alert_message,
                    'zone_type': zone['type'],
                    'zone_level': zone['level'],
                    'current_price': current_price,
                    'distance_pct': distance_pct
                }
                
                st.session_state.alerts.append(alert_data)
                
                # Send email notification
                try:
                    st.session_state.notification_manager.send_alert(alert_message, symbol, zone, current_price)
                    st.success(f"Alert sent: {alert_message}")
                except Exception as e:
                    st.warning(f"Failed to send email alert: {str(e)}")
                
                # Keep only last 50 alerts to avoid memory issues
                if len(st.session_state.alerts) > 50:
                    st.session_state.alerts = st.session_state.alerts[-50:]

if __name__ == "__main__":
    main()
