import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Optional
import streamlit as st

class NotificationManager:
    """
    Manages email notifications for zone alerts
    """
    
    def __init__(self):
        self.email_address = None
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("SMTP_EMAIL", "trading.alerts@example.com")
        self.sender_password = os.getenv("SMTP_PASSWORD", "your_app_password")
    
    def set_email(self, email: str):
        """Set the recipient email address"""
        self.email_address = email
    
    def send_alert(self, message: str, symbol: str, zone: Dict, current_price: float) -> bool:
        """
        Send email alert for zone proximity
        
        Args:
            message: Alert message text
            symbol: Stock symbol
            zone: Zone dictionary with details
            current_price: Current stock price
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.email_address:
            st.warning("No email address configured for alerts")
            return False
        
        try:
            # Create email content
            subject = f"🚨 Zone Alert: {symbol} - {zone['type'].title()} Zone"
            
            # Create HTML email body
            html_body = self._create_html_email_body(symbol, zone, current_price, message)
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.email_address
            
            # Add HTML content
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Add plain text fallback
            text_body = self._create_text_email_body(symbol, zone, current_price, message)
            text_part = MIMEText(text_body, 'plain')
            msg.attach(text_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            st.error(f"Failed to send email notification: {str(e)}")
            return False
    
    def _create_html_email_body(self, symbol: str, zone: Dict, current_price: float, message: str) -> str:
        """Create HTML email body"""
        zone_color = "#e74c3c" if zone['type'] == 'supply' else "#27ae60"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: {zone_color}; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; }}
                .zone-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .price {{ font-size: 1.2em; font-weight: bold; }}
                .alert {{ color: #e74c3c; font-weight: bold; }}
                .footer {{ margin-top: 20px; font-size: 0.9em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 Stock Trading Alert</h2>
                <p>{message}</p>
            </div>
            
            <div class="content">
                <h3>Alert Details</h3>
                
                <div class="zone-info">
                    <h4>Stock Information</h4>
                    <p><strong>Symbol:</strong> {symbol}</p>
                    <p><strong>Current Price:</strong> <span class="price">${current_price:.2f}</span></p>
                    <p><strong>Alert Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="zone-info">
                    <h4>Zone Information</h4>
                    <p><strong>Zone Type:</strong> {zone['type'].title()}</p>
                    <p><strong>Zone Level:</strong> <span class="price">${zone['level']:.2f}</span></p>
                    <p><strong>Zone Strength:</strong> {zone['strength'].title()}</p>
                    <p><strong>Number of Touches:</strong> {zone['touches']}</p>
                </div>
                
                <div class="zone-info">
                    <h4>Analysis</h4>
                    <p><strong>Distance from Zone:</strong> {abs(zone['level'] - current_price) / current_price * 100:.2f}%</p>
                    <p><strong>Price Direction:</strong> {"Above" if current_price > zone['level'] else "Below"} zone level</p>
                </div>
                
                <p class="alert">⚠️ This is an automated alert. Please conduct your own analysis before making trading decisions.</p>
            </div>
            
            <div class="footer">
                <p>This alert was generated by your Stock Trading Dashboard.</p>
                <p>If you no longer wish to receive these alerts, please update your settings in the dashboard.</p>
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def _create_text_email_body(self, symbol: str, zone: Dict, current_price: float, message: str) -> str:
        """Create plain text email body as fallback"""
        distance_pct = abs(zone['level'] - current_price) / current_price * 100
        direction = "above" if current_price > zone['level'] else "below"
        
        text_body = f"""
STOCK TRADING ALERT
{message}

STOCK INFORMATION:
Symbol: {symbol}
Current Price: ${current_price:.2f}
Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ZONE INFORMATION:
Zone Type: {zone['type'].title()}
Zone Level: ${zone['level']:.2f}
Zone Strength: {zone['strength'].title()}
Number of Touches: {zone['touches']}

ANALYSIS:
Distance from Zone: {distance_pct:.2f}%
Price Direction: {direction} zone level

⚠️ This is an automated alert. Please conduct your own analysis before making trading decisions.

---
This alert was generated by your Stock Trading Dashboard.
If you no longer wish to receive these alerts, please update your settings in the dashboard.
        """
        
        return text_body
    
    def test_email_connection(self) -> bool:
        """Test email connection and credentials"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.quit()
            return True
        except Exception as e:
            st.error(f"Email connection test failed: {str(e)}")
            return False
    
    def send_test_alert(self) -> bool:
        """Send a test alert to verify email functionality"""
        if not self.email_address:
            st.warning("No email address configured")
            return False
        
        test_zone = {
            'type': 'demand',
            'level': 150.00,
            'strength': 'strong',
            'touches': 3
        }
        
        test_message = "This is a test alert from your Stock Trading Dashboard"
        
        return self.send_alert(test_message, "TEST", test_zone, 148.50)
