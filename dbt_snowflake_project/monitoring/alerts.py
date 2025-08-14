#!/usr/bin/env python3
"""
Data Quality Alerting System
Monitors data quality metrics and sends alerts based on configurable thresholds.
"""

import os
import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Any
import requests
from snowflake.connector import connect
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataQualityAlerting:
    """Data quality alerting system with multiple notification channels."""
    
    def __init__(self):
        self.snowflake_config = {
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'user': os.getenv('SNOWFLAKE_USER'),
            'password': os.getenv('SNOWFLAKE_PASSWORD'),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'FINANCE_WH'),
            'database': os.getenv('SNOWFLAKE_DATABASE', 'FINANCE_DB'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA', 'TEST_FAILURES'),
        }
        
        # Alert configuration
        self.config = {
            'test_failure_threshold': int(os.getenv('TEST_FAILURE_THRESHOLD', '5')),
            'freshness_threshold_hours': int(os.getenv('FRESHNESS_THRESHOLD_HOURS', '48')),
            'pass_rate_threshold': float(os.getenv('PASS_RATE_THRESHOLD', '95.0')),
            'critical_models': os.getenv('CRITICAL_MODELS', 'fct_daily_order_revenue,dim_customers').split(','),
            'email_recipients': os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(','),
            'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL', ''),
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_username': os.getenv('SMTP_USERNAME', ''),
            'smtp_password': os.getenv('SMTP_PASSWORD', ''),
        }
    
    def get_connection(self):
        """Get Snowflake connection."""
        return connect(**self.snowflake_config)
    
    def check_test_failures(self) -> Dict[str, Any]:
        """Check for recent test failures."""
        query = """
        SELECT 
            test_name,
            model_name,
            test_status,
            executed_at,
            error_message,
            rows_affected
        FROM test_results 
        WHERE test_status = 'fail'
          AND executed_at >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
        ORDER BY executed_at DESC
        """
        
        with self.get_connection() as conn:
            failures = pd.read_sql(query, conn)
        
        critical_failures = failures[failures['model_name'].isin(self.config['critical_models'])]
        
        return {
            'total_failures': len(failures),
            'critical_failures': len(critical_failures),
            'failures_data': failures.to_dict('records'),
            'critical_failures_data': critical_failures.to_dict('records'),
            'threshold_exceeded': len(failures) > self.config['test_failure_threshold'],
            'has_critical_failures': len(critical_failures) > 0
        }
    
    def check_data_freshness(self) -> Dict[str, Any]:
        """Check data freshness for critical models."""
        query = f"""
        SELECT 
            model_name,
            last_updated,
            DATEDIFF('hour', last_updated, CURRENT_TIMESTAMP()) as hours_since_update,
            row_count,
            freshness_status
        FROM model_freshness_summary
        WHERE hours_since_update > {self.config['freshness_threshold_hours']}
           OR freshness_status = 'stale'
        ORDER BY hours_since_update DESC
        """
        
        with self.get_connection() as conn:
            stale_models = pd.read_sql(query, conn)
        
        critical_stale = stale_models[stale_models['model_name'].isin(self.config['critical_models'])]
        
        return {
            'total_stale': len(stale_models),
            'critical_stale': len(critical_stale),
            'stale_models': stale_models.to_dict('records'),
            'critical_stale_models': critical_stale.to_dict('records'),
            'has_stale_critical': len(critical_stale) > 0
        }
    
    def check_pass_rate(self) -> Dict[str, Any]:
        """Check overall test pass rate."""
        query = """
        SELECT 
            COUNT(*) as total_tests,
            SUM(CASE WHEN test_status = 'pass' THEN 1 ELSE 0 END) as passed_tests,
            ROUND(passed_tests::FLOAT / total_tests::FLOAT * 100, 2) as pass_rate
        FROM test_results 
        WHERE executed_at >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
        """
        
        with self.get_connection() as conn:
            result = pd.read_sql(query, conn).iloc[0]
        
        return {
            'total_tests': int(result['total_tests']),
            'passed_tests': int(result['passed_tests']),
            'pass_rate': float(result['pass_rate']),
            'threshold_exceeded': result['pass_rate'] < self.config['pass_rate_threshold']
        }
    
    def send_email_alert(self, subject: str, body: str, is_critical: bool = False):
        """Send email alert."""
        if not self.config['email_recipients'] or not self.config['smtp_username']:
            logger.warning("Email configuration missing, skipping email alert")
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.config['smtp_username']
            msg['To'] = ', '.join(self.config['email_recipients'])
            msg['Subject'] = f"{'🚨 CRITICAL' if is_critical else '⚠️ WARNING'} - {subject}"
            
            msg.attach(MimeText(body, 'html'))
            
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['smtp_username'], self.config['smtp_password'])
            
            text = msg.as_string()
            server.sendmail(self.config['smtp_username'], self.config['email_recipients'], text)
            server.quit()
            
            logger.info(f"Email alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
    
    def send_slack_alert(self, message: str, is_critical: bool = False):
        """Send Slack alert."""
        if not self.config['slack_webhook_url']:
            logger.warning("Slack webhook URL not configured, skipping Slack alert")
            return
        
        try:
            color = "#ff0000" if is_critical else "#ffaa00"
            icon = "🚨" if is_critical else "⚠️"
            
            payload = {
                "text": f"{icon} Data Quality Alert",
                "attachments": [
                    {
                        "color": color,
                        "text": message,
                        "footer": "Finance Data Platform",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(self.config['slack_webhook_url'], json=payload)
            response.raise_for_status()
            
            logger.info("Slack alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {str(e)}")
    
    def format_email_body(self, alerts: Dict[str, Any]) -> str:
        """Format email body with alert details."""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .critical { color: #d32f2f; font-weight: bold; }
                .warning { color: #f57c00; font-weight: bold; }
                .success { color: #388e3c; font-weight: bold; }
                table { border-collapse: collapse; width: 100%; margin: 10px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h2>Data Quality Alert Summary</h2>
            <p><strong>Generated:</strong> {timestamp}</p>
        """.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
        
        # Test failures section
        if alerts['test_failures']['threshold_exceeded'] or alerts['test_failures']['has_critical_failures']:
            html += f"""
            <h3 class="{'critical' if alerts['test_failures']['has_critical_failures'] else 'warning'}">
                Test Failures Alert
            </h3>
            <p>Total failures in last 24h: <strong>{alerts['test_failures']['total_failures']}</strong></p>
            <p>Critical model failures: <strong>{alerts['test_failures']['critical_failures']}</strong></p>
            """
            
            if alerts['test_failures']['failures_data']:
                html += "<h4>Recent Test Failures:</h4><table><tr><th>Model</th><th>Test</th><th>Error</th><th>Time</th></tr>"
                for failure in alerts['test_failures']['failures_data'][:10]:  # Limit to 10 recent
                    html += f"""
                    <tr>
                        <td>{failure['model_name']}</td>
                        <td>{failure['test_name']}</td>
                        <td>{failure['error_message'][:100]}...</td>
                        <td>{failure['executed_at']}</td>
                    </tr>
                    """
                html += "</table>"
        
        # Freshness section
        if alerts['freshness']['has_stale_critical']:
            html += f"""
            <h3 class="critical">Data Freshness Alert</h3>
            <p>Critical models with stale data: <strong>{alerts['freshness']['critical_stale']}</strong></p>
            """
            
            if alerts['freshness']['critical_stale_models']:
                html += "<h4>Stale Critical Models:</h4><table><tr><th>Model</th><th>Hours Stale</th><th>Last Updated</th></tr>"
                for model in alerts['freshness']['critical_stale_models']:
                    html += f"""
                    <tr>
                        <td>{model['model_name']}</td>
                        <td>{model['hours_since_update']}</td>
                        <td>{model['last_updated']}</td>
                    </tr>
                    """
                html += "</table>"
        
        # Pass rate section
        if alerts['pass_rate']['threshold_exceeded']:
            html += f"""
            <h3 class="warning">Pass Rate Alert</h3>
            <p>Current pass rate: <strong>{alerts['pass_rate']['pass_rate']:.1f}%</strong></p>
            <p>Threshold: <strong>{self.config['pass_rate_threshold']}%</strong></p>
            <p>Tests run: {alerts['pass_rate']['passed_tests']}/{alerts['pass_rate']['total_tests']}</p>
            """
        
        html += """
            <hr>
            <p><em>This is an automated alert from the Finance Data Platform monitoring system.</em></p>
        </body>
        </html>
        """
        
        return html
    
    def format_slack_message(self, alerts: Dict[str, Any]) -> str:
        """Format Slack message with alert details."""
        message = "*Data Quality Alert Summary*\n"
        message += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        
        # Test failures
        if alerts['test_failures']['threshold_exceeded'] or alerts['test_failures']['has_critical_failures']:
            severity = "🚨 CRITICAL" if alerts['test_failures']['has_critical_failures'] else "⚠️ WARNING"
            message += f"{severity} *Test Failures*\n"
            message += f"• Total failures (24h): {alerts['test_failures']['total_failures']}\n"
            message += f"• Critical model failures: {alerts['test_failures']['critical_failures']}\n\n"
        
        # Freshness
        if alerts['freshness']['has_stale_critical']:
            message += "🚨 CRITICAL *Data Freshness*\n"
            message += f"• Critical models with stale data: {alerts['freshness']['critical_stale']}\n\n"
        
        # Pass rate
        if alerts['pass_rate']['threshold_exceeded']:
            message += "⚠️ WARNING *Pass Rate*\n"
            message += f"• Current rate: {alerts['pass_rate']['pass_rate']:.1f}%\n"
            message += f"• Threshold: {self.config['pass_rate_threshold']}%\n\n"
        
        message += "_Automated alert from Finance Data Platform_"
        
        return message
    
    def run_monitoring_cycle(self):
        """Run complete monitoring cycle and send alerts if needed."""
        logger.info("Starting data quality monitoring cycle")
        
        try:
            # Collect all alert data
            alerts = {
                'test_failures': self.check_test_failures(),
                'freshness': self.check_data_freshness(),
                'pass_rate': self.check_pass_rate()
            }
            
            # Determine if alerts should be sent
            should_alert = (
                alerts['test_failures']['threshold_exceeded'] or
                alerts['test_failures']['has_critical_failures'] or
                alerts['freshness']['has_stale_critical'] or
                alerts['pass_rate']['threshold_exceeded']
            )
            
            is_critical = (
                alerts['test_failures']['has_critical_failures'] or
                alerts['freshness']['has_stale_critical']
            )
            
            if should_alert:
                logger.warning(f"Data quality issues detected. Critical: {is_critical}")
                
                # Send alerts
                email_subject = "Data Quality Issues Detected"
                email_body = self.format_email_body(alerts)
                slack_message = self.format_slack_message(alerts)
                
                self.send_email_alert(email_subject, email_body, is_critical)
                self.send_slack_alert(slack_message, is_critical)
                
                # Log alert summary
                logger.info(f"Alerts sent - Test failures: {alerts['test_failures']['total_failures']}, "
                           f"Stale critical models: {alerts['freshness']['critical_stale']}, "
                           f"Pass rate: {alerts['pass_rate']['pass_rate']:.1f}%")
            else:
                logger.info("No data quality issues detected")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {str(e)}")
            # Send error alert
            error_message = f"Data quality monitoring system encountered an error: {str(e)}"
            self.send_slack_alert(error_message, is_critical=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Quality Alerting System")
    parser.add_argument("--dry-run", action="store_true", help="Run without sending alerts")
    args = parser.parse_args()
    
    alerting = DataQualityAlerting()
    
    if args.dry_run:
        logger.info("Running in dry-run mode - no alerts will be sent")
        # Override send methods for dry run
        alerting.send_email_alert = lambda *args, **kwargs: logger.info("DRY RUN: Would send email alert")
        alerting.send_slack_alert = lambda *args, **kwargs: logger.info("DRY RUN: Would send Slack alert")
    
    alerting.run_monitoring_cycle()
