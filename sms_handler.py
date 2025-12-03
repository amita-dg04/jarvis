"""
SMS Handler for Personal AI Assistant
Handles SMS processing, natural language task parsing, and response generation
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import os

import dateparser
import pytz

from memory_manager import MemoryManager
from llm_engine import LLMEngine
from tasks_manager import TasksManager

logger = logging.getLogger(__name__)

class SMSHandler:
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.llm_engine = LLMEngine()
        self.tasks_manager = TasksManager()
        self.user_timezone = os.getenv("USER_TIMEZONE", "America/Chicago")
        try:
            self.tzinfo = pytz.timezone(self.user_timezone)
        except Exception:
            self.tzinfo = pytz.UTC
    
    def process_message(self, user_message: str, user_phone: str) -> str:
        """
        Process an incoming SMS message and generate a response
        """
        try:
            logger.info(f"Processing message from {user_phone}: {user_message}")
            command = self.llm_engine.should_handle_command(user_message)
            if command:
                return self._handle_command(command, user_message)
            context = self.memory_manager.get_context_for_prompt(user_message)
            task_info = self.llm_engine.parse_task_intent(user_message)
            if task_info and task_info.get("is_task"):
                return self._handle_task_creation(task_info, user_message, context)
            response = self.llm_engine.ask_llm(user_message, context)
            self.memory_manager.add_conversation(user_message, response)
            return response
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I'm sorry, I encountered an error processing your message. Please try again."
    
    def _handle_command(self, command: str, message: str) -> str:
        try:
            if command == "forget":
                success = self.memory_manager.forget_last()
                return "I've forgotten our last conversation. What can I help you with?" if success else "I couldn't forget the last message. Please try again."
            elif command == "show_tasks":
                return self.tasks_manager.get_task_summary()
            elif command == "complete_task":
                task_id_match = re.search(r'done\s+(\d+)', message.lower())
                if task_id_match:
                    task_id = int(task_id_match.group(1))
                    success = self.tasks_manager.complete_task(task_id)
                    return f"✅ Task {task_id} marked as completed!" if success else f"❌ Could not find or complete task {task_id}."
                return "Please specify a task ID: 'done 123'"
            elif command == "delete_task":
                task_id_match = re.search(r'delete\s+task\s+(\d+)', message.lower())
                if task_id_match:
                    task_id = int(task_id_match.group(1))
                    success = self.tasks_manager.delete_task(task_id)
                    return f"🗑️ Task {task_id} deleted!" if success else f"❌ Could not find or delete task {task_id}."
                return "Please specify a task ID: 'delete task 123'"
            return "I didn't understand that command. Try 'show tasks', 'done X', or 'forget this'."
        except Exception as e:
            logger.error(f"Error handling command {command}: {e}")
            return "I encountered an error processing that command. Please try again."
    
    def _parse_date_nlp(self, text: str) -> Optional[str]:
        """Parse natural language date in user's timezone and return UTC ISO string."""
        try:
            logger.info(f"[DATE PARSE] Attempting to parse: '{text}'")
            settings = {
                "PREFER_DATES_FROM": "future",
                "RETURN_AS_TIMEZONE_AWARE": True,
                "RELATIVE_BASE": datetime.now(self.tzinfo),
            }
            
            # Try parsing the full text first
            parsed = dateparser.parse(text, settings=settings)
            logger.info(f"[DATE PARSE] Initial parse result: {parsed}")
            
            # If that fails, try to extract time-related phrases
            if not parsed:
                time_patterns = [
                    r'in (\d+) minute[s]?',
                    r'in (\d+) hour[s]?',
                    r'in (\d+) day[s]?',
                    r'in (\d+) second[s]?',
                    r'(\d+) minute[s]? from now',
                    r'(\d+) hour[s]? from now',
                    r'(\d+) day[s]? from now',
                    r'(\d+) second[s]? from now',
                    r'tomorrow',
                    r'today',
                    r'next week',
                    r'next month'
                ]
                
                for pattern in time_patterns:
                    match = re.search(pattern, text.lower())
                    if match:
                        if 'tomorrow' in pattern:
                            parsed = dateparser.parse('tomorrow', settings=settings)
                        elif 'today' in pattern:
                            parsed = dateparser.parse('today', settings=settings)
                        elif 'next week' in pattern:
                            parsed = dateparser.parse('next week', settings=settings)
                        elif 'next month' in pattern:
                            parsed = dateparser.parse('next month', settings=settings)
                        else:
                            # Extract the time phrase
                            time_phrase = match.group(0)
                            parsed = dateparser.parse(time_phrase, settings=settings)
                        break
            
            if not parsed:
                logger.warning(f"[DATE PARSE] Failed to parse date from: '{text}'")
                return None
                
            if parsed.tzinfo is None:
                parsed = self.tzinfo.localize(parsed)
            parsed_utc = parsed.astimezone(pytz.UTC)
            result = parsed_utc.replace(microsecond=0).isoformat()
            logger.info(f"[DATE PARSE] Final result: {result}")
            return result
        except Exception as e:
            logger.error(f"NLP date parsing failed for '{text}': {e}")
            return None
    
    def _handle_task_creation(self, task_info: Dict[str, Any], user_message: str, context: str) -> str:
        try:
            task_text = task_info.get("task_text", "")
            priority = task_info.get("priority", "medium")

            # Always parse the user's original message for timing (ignore LLM-provided due dates to avoid bias)
            logger.info(f"[TASK CREATE] User message: '{user_message}'")
            logger.info(f"[TASK CREATE] Task text: '{task_text}'")
            parsed_utc_iso = self._parse_date_nlp(user_message)
            logger.info(f"[TASK CREATE] Parsed date: {parsed_utc_iso}")

            task_id = self.tasks_manager.add_task(task_text, parsed_utc_iso, priority)
            if task_id > 0:
                if parsed_utc_iso:
                    try:
                        dt_utc = datetime.fromisoformat(parsed_utc_iso.replace("Z", "+00:00"))
                        dt_local = dt_utc.astimezone(self.tzinfo)
                        due_str = dt_local.strftime("%b %d at %I:%M %p %Z")
                        response = f"✅ Got it! I'll remind you to {task_text} on {due_str}. (Task #{task_id})"
                    except Exception:
                        response = f"✅ Got it! I'll remind you to {task_text}. (Task #{task_id})"
                else:
                    response = f"✅ Got it! I've added '{task_text}' to your tasks. (Task #{task_id})"
                self.memory_manager.add_conversation(user_message, response)
                return response
            return "❌ I couldn't save that task. Please try again."
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return "❌ I encountered an error creating that task. Please try again."
    
    def parse_natural_language_date(self, date_text: str) -> Optional[str]:
        """Deprecated: Use _parse_date_nlp. Kept for compatibility."""
        return self._parse_date_nlp(date_text)
    
    def get_reminder_message(self, task: Dict[str, Any]) -> str:
        try:
            task_text = task['text']
            due_date = task['due_date']
            reminder = self.llm_engine.generate_reminder_message(task_text, due_date)
            task_id = task['id']
            return f"{reminder}\n\nReply 'done {task_id}' when completed!"
        except Exception as e:
            logger.error(f"Error generating reminder message: {e}")
            return f"⏰ Reminder: {task['text']}\n\nReply 'done {task['id']}' when completed!"

