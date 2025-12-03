"""
LLM Engine for Personal AI Assistant
Handles OpenAI GPT-3.5-turbo integration with context-aware responses
"""

import os
import openai
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class LLMEngine:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 150
        self.temperature = 0.7
        
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            logger.warning("OPENAI_API_KEY not found. LLM features will be limited.")
            self.client = None
    
    def set_model(self, model_name: str) -> None:
        """
        Change the LLM model
        
        Args:
            model_name: The model to use (e.g., 'gpt-3.5-turbo', 'gpt-4')
        """
        self.model = model_name
        logger.info(f"LLM model changed to: {model_name}")
    
    def ask_llm(self, prompt: str, context: str = "", system_prompt: Optional[str] = None) -> str:
        """
        Send a prompt to the LLM and get a response
        
        Args:
            prompt: The user's prompt
            context: Relevant context from memory
            system_prompt: Optional custom system prompt
            
        Returns:
            str: The LLM's response
        """
        if not self.api_key:
            return "I'm sorry, but I'm not properly configured to respond right now. Please check my API keys."
        
        try:
            if not self.client:
                return "I'm sorry, but I'm not properly configured to respond right now. Please check my API keys."
            
            # Default system prompt for personal assistant
            if not system_prompt:
                system_prompt = """You are a helpful personal AI assistant that communicates via SMS. 
                You should be concise, friendly, and helpful. Keep responses short (under 160 characters when possible) 
                since this is SMS communication. You help with reminders, tasks, and general questions."""
            
            # Combine context and prompt
            full_prompt = context + prompt if context else prompt
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            assistant_response = response.choices[0].message.content.strip()
            logger.info(f"LLM response generated: {assistant_response[:50]}...")
            
            return assistant_response
            
        except Exception as e:
            if "openai" in str(type(e)).lower():
                logger.error(f"OpenAI API error: {e}")
                return "I'm having trouble connecting to my AI service right now. Please try again later."
            else:
                logger.error(f"Unexpected error in LLM engine: {e}")
                return "I encountered an unexpected error. Please try again."
    
    def parse_task_intent(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Use LLM to parse task/reminder intent from natural language
        
        Args:
            message: The user's message
            
        Returns:
            Dict with task information or None if no task detected
        """
        if not self.api_key:
            return None
            
        try:
            system_prompt = """You are a task parsing assistant. Analyze the user's message and determine if they want to create a task or reminder.
            
            If they do, respond with a JSON object containing:
            - "is_task": true
            - "task_text": the task description
            - "due_date": the due date/time (if specified, in ISO format, otherwise null)
            - "priority": "high", "medium", or "low" (default: "medium")
            
            If no task is detected, respond with:
            - "is_task": false
            
            Examples:
            "remind me to call mom tomorrow" -> {"is_task": true, "task_text": "call mom", "due_date": "2024-01-15T09:00:00", "priority": "medium"}
            "hello there" -> {"is_task": false}
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            import json
            try:
                parsed = json.loads(result)
                if parsed.get("is_task"):
                    logger.info(f"Task detected: {parsed.get('task_text')}")
                    return parsed
            except json.JSONDecodeError:
                logger.warning(f"Could not parse task intent JSON: {result}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing task intent: {e}")
            return None
    
    def generate_reminder_message(self, task_text: str, due_date: str) -> str:
        """
        Generate a friendly reminder message for a task
        
        Args:
            task_text: The task description
            due_date: The due date/time
            
        Returns:
            str: A friendly reminder message
        """
        if not self.api_key:
            return f"⏰ Reminder: {task_text}"
        
        try:
            system_prompt = """Generate a friendly, concise reminder message for SMS. 
            Include a clock emoji and keep it under 160 characters. Be encouraging and helpful."""
            
            prompt = f"Generate a reminder message for: {task_text} (due: {due_date})"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=100,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating reminder message: {e}")
            return f"⏰ Reminder: {task_text}"
    
    def should_handle_command(self, message: str) -> Optional[str]:
        """
        Check if the message contains a special command
        
        Args:
            message: The user's message
            
        Returns:
            str: The command type if detected, None otherwise
        """
        message_lower = message.lower().strip()
        
        if message_lower == "forget this":
            return "forget"
        elif message_lower == "show tasks":
            return "show_tasks"
        elif message_lower.startswith("done "):
            return "complete_task"
        elif message_lower.startswith("delete task "):
            return "delete_task"
        
        return None
