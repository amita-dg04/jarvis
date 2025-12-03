"""
Message Sender for Personal AI Assistant
Handles proactive messaging via Twilio (SMS/WhatsApp)
"""

import os
import logging
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

logger = logging.getLogger(__name__)

class MessageSender:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.use_whatsapp = (os.getenv("USE_WHATSAPP", "false").lower() == "true")
        
        # Phone numbers
        self.user_number = self._format_destination(
            os.getenv("USER_PHONE_NUMBER"), 
            self.use_whatsapp
        )
        self.from_number = self._format_destination(
            os.getenv("WHATSAPP_FROM") if self.use_whatsapp else os.getenv("TWILIO_PHONE_NUMBER"),
            self.use_whatsapp
        )
        
        # Initialize Twilio client
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info(f"MessageSender initialized - Channel: {'WhatsApp' if self.use_whatsapp else 'SMS'}")
        else:
            self.client = None
            logger.error("MessageSender: Missing Twilio credentials")
    
    def _format_destination(self, number: str, use_whatsapp: bool) -> str:
        """Format phone number for WhatsApp or SMS"""
        if not number:
            return number
        if use_whatsapp and not number.startswith("whatsapp:"):
            return f"whatsapp:{number}"
        return number
    
    def is_configured(self) -> bool:
        """Check if all required configuration is present"""
        return bool(
            self.client and 
            self.user_number and 
            self.from_number and
            self.account_sid and 
            self.auth_token
        )
    
    def send_reminder(self, task_text: str, due_date: str, task_id: int) -> bool:
        """
        Send a reminder message for a specific task
        
        Args:
            task_text: The task description
            due_date: The due date/time
            task_id: The task ID
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self.is_configured():
            logger.error("Cannot send reminder: MessageSender not properly configured")
            return False
        
        # Create reminder message
        message_body = f"⏰ Reminder: {task_text}\n\nReply 'done {task_id}' when completed!"
        
        try:
            logger.info(f"Sending reminder to {self.user_number}: {task_text[:50]}...")
            
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=self.user_number
            )
            
            logger.info(f"Reminder sent successfully - SID: {message.sid}")
            return True
            
        except TwilioException as e:
            logger.error(f"Twilio error sending reminder: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending reminder: {e}")
            return False
    
    def send_test_message(self) -> bool:
        """
        Send a test message to verify configuration
        
        Returns:
            bool: True if test message was sent successfully
        """
        if not self.is_configured():
            logger.error("Cannot send test message: MessageSender not properly configured")
            return False
        
        test_message = "🧪 Test message from your AI Assistant - configuration is working!"
        
        try:
            logger.info(f"Sending test message to {self.user_number}")
            
            message = self.client.messages.create(
                body=test_message,
                from_=self.from_number,
                to=self.user_number
            )
            
            logger.info(f"Test message sent successfully - SID: {message.sid}")
            return True
            
        except TwilioException as e:
            logger.error(f"Twilio error sending test message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending test message: {e}")
            return False
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """
        Get current configuration status for debugging
        
        Returns:
            Dict with configuration details
        """
        return {
            "configured": self.is_configured(),
            "use_whatsapp": self.use_whatsapp,
            "user_number": self.user_number,
            "from_number": self.from_number,
            "has_account_sid": bool(self.account_sid),
            "has_auth_token": bool(self.auth_token),
            "has_client": bool(self.client)
        }

