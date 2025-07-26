# Stock Trading Dashboard

## Overview

This is a Streamlit-based stock trading dashboard that provides real-time demand and supply zone analysis with email notifications across multiple timeframes including weekly and monthly zones. The application uses technical analysis to identify key price levels where stocks may reverse direction, with support for both US and NSE stocks. It features real-time data fetching from Yahoo Finance, interactive charts with Plotly, EMA indicators, multi-timeframe analysis, and automated alert systems.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit for web interface
- **Visualization**: Plotly for interactive charts and graphs
- **Layout**: Wide layout with expandable sidebar for configuration
- **Session Management**: Streamlit session state for maintaining alerts, monitored stocks, and notification settings

### Backend Architecture
- **Data Source**: Yahoo Finance API via yfinance library
- **Analysis Engine**: Custom zone detection algorithms using pandas and numpy
- **Notification System**: SMTP-based email alerts with HTML formatting
- **Caching**: In-memory data caching with 5-minute expiration

### Key Design Patterns
- **Modular Architecture**: Separate classes for different responsibilities (DataManager, ZoneDetector, NotificationManager)
- **Object-Oriented Design**: Each component encapsulated in its own class with clear interfaces
- **Session State Management**: Persistent data storage across user interactions

## Key Components

### 1. Main Application (app.py)
- **Purpose**: Entry point and UI orchestration
- **Responsibilities**: 
  - Page configuration and layout
  - Session state initialization
  - Multi-exchange support (US/NSE stocks)
  - User interface components with technical indicators
  - Multi-timeframe zone analysis
  - Real-time dashboard updates

### 2. Data Manager (data_manager.py)
- **Purpose**: Stock data retrieval and processing
- **Key Features**:
  - Yahoo Finance integration
  - Data caching (5-minute expiration)
  - Data cleaning and validation
  - Multiple timeframe support (1m to 1d intervals)

### 3. Zone Detector (zone_detector.py)
- **Purpose**: Technical analysis for demand/supply zones
- **Algorithm Components**:
  - Adaptive pivot point detection (local highs/lows)
  - Timeframe-aware window sizing for weekly/monthly data
  - Zone identification using support/resistance levels
  - Zone strength calculation with multi-factor scoring
  - Minimum touch validation with HTF zone support

### 4. Notification Manager (notification_manager.py)
- **Purpose**: Email alert system
- **Features**:
  - SMTP email sending via Gmail
  - HTML email formatting
  - Zone proximity alerts
  - Configurable recipient settings

## Data Flow

1. **User Input**: Stock symbol and timeframe selection via sidebar
2. **Data Retrieval**: DataManager fetches data from Yahoo Finance API
3. **Cache Check**: System checks for cached data to avoid redundant API calls
4. **Zone Analysis**: ZoneDetector processes OHLCV data to identify key levels
5. **Visualization**: Plotly renders interactive charts with detected zones
6. **Alert Processing**: System monitors price proximity to zones
7. **Notification**: Email alerts sent when price approaches significant zones

## External Dependencies

### Core Libraries
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **plotly**: Interactive visualization
- **yfinance**: Yahoo Finance API client

### Email Integration
- **smtplib**: SMTP email sending
- **email.mime**: Email formatting utilities

### Environment Variables
- `SMTP_EMAIL`: Sender email address
- `SMTP_PASSWORD`: Application password for Gmail SMTP

## Deployment Strategy

### Current Setup
- **Platform**: Designed for Replit deployment
- **Configuration**: Streamlit web app with automatic port detection
- **Dependencies**: All dependencies managed via requirements.txt (implied)

### Scalability Considerations
- **Caching**: In-memory caching reduces API calls but limits to single instance
- **Real-time Updates**: Currently uses session state; could be enhanced with WebSocket connections
- **Database**: No persistent storage currently; all data is session-based

### Security Measures
- **API Keys**: Environment variables for SMTP credentials
- **Input Validation**: Stock symbol validation and data cleaning
- **Error Handling**: Graceful degradation when external services fail

## Architecture Decisions

### Data Source Choice
- **Decision**: Yahoo Finance via yfinance library
- **Rationale**: Free, reliable, and comprehensive stock data
- **Alternatives**: Alpha Vantage, IEX Cloud (require paid API keys)
- **Trade-offs**: Limited to Yahoo Finance data quality and availability

### Visualization Framework
- **Decision**: Plotly for interactive charts
- **Rationale**: Rich interactivity, financial chart support, Streamlit integration
- **Alternatives**: Matplotlib (static), Bokeh (complex setup)
- **Benefits**: Real-time updates, zoom/pan capabilities, professional appearance

### Zone Detection Algorithm
- **Decision**: Pivot point-based support/resistance analysis
- **Rationale**: Well-established technical analysis method
- **Implementation**: Custom algorithm with configurable parameters
- **Validation**: Minimum touch requirements and strength scoring

### Notification System
- **Decision**: SMTP email alerts
- **Rationale**: Universal compatibility and reliability
- **Alternatives**: SMS, push notifications, Discord/Slack webhooks
- **Benefits**: No additional service dependencies, HTML formatting support

## Recent Changes: Latest modifications with dates

### January 26, 2025
- **Enhanced Multi-Timeframe Support**: Added weekly (1wk) and monthly (1mo) timeframe analysis
- **NSE Stock Integration**: Full support for National Stock Exchange stocks with .NS suffix handling
- **20 EMA Technical Indicator**: Added 20-period and 50-period Exponential Moving Averages with toggle controls
- **Higher Timeframe Zones**: Implemented multi-timeframe zone detection showing weekly/monthly zones on lower timeframes
- **Adaptive Zone Detection**: Zone detector now uses timeframe-appropriate window sizes for better accuracy
- **Enhanced UI**: Added exchange selection, technical indicator controls, and timeframe column in zone analysis table
- **Volume Chart Removal**: Removed volume subplot and enlarged main price chart to 800px height for better zone visibility
- **Fresh Zone Algorithm**: Completely redesigned zone detection to focus on fresh zones with strong price reactions (3%+ moves)
- **HTF Confluence System**: Added higher timeframe confluence scoring to validate zone quality
- **Quality-Based Filtering**: Zones now ranked by reaction strength, freshness, and HTF support rather than just touches
- **Enhanced Zone Table**: Added reaction percentage, fresh/tested status, quality rating, and HTF support columns
- **Smart Zone Selection**: Algorithm now prioritizes untested zones with good moves and tested zones with exceptional reactions
- **Breakout Scanner**: Added comprehensive breakout detection with 5 pattern types (resistance, support, MA, volume, ATH)
- **Index-wide Scanning**: Scan entire NSE indices (NIFTY 50, BANK, IT, AUTO, PHARMA, FMCG, METAL, ENERGY, REALTY, PSU BANK, MIDCAP 50)
- **Individual Stock Analysis**: Direct breakout analysis for any NSE stock with buy/sell signals
- **ATH Breakout Detection**: Special algorithm for all-time high breakout attempts with multiple tries and volume confirmation
- **Auto-completion**: Stock symbol selection with searchable dropdown for better user experience
- **NSE-only Focus**: Removed US exchange option to focus solely on Indian stock market
- **Buy/Sell Signals**: Clear trading signals (BUY/SELL/WATCH) with confidence scoring for each breakout pattern