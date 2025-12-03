"""
Memory Manager for Personal AI Assistant
Handles integration with Supermemory API for persistent long-term recall
"""

import os
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        self.api_key = os.getenv('SUPERMEMORY_API_KEY')
        self.base_url = "https://api.supermemory.com/v1"  # Update with actual Supermemory API URL
        
        if not self.api_key or self.api_key.lower() == "disabled":
            logger.warning("SUPERMEMORY_API_KEY not found or disabled. Memory features will be limited.")
            self.api_key = None
            self.headers = {"Content-Type": "application/json"}
        else:
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
    
    def add_memory(self, entry: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add a new memory entry to Supermemory
        
        Args:
            entry: The text content to store
            metadata: Optional metadata (timestamp, type, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.api_key:
            logger.warning("Cannot add memory: Supermemory API key not configured")
            return False
            
        try:
            payload = {
                "content": entry,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            response = requests.post(
                f"{self.base_url}/memories",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201:
                logger.info(f"Successfully added memory: {entry[:50]}...")
                return True
            else:
                logger.error(f"Failed to add memory: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error adding memory: {e}")
            return False
    
    def query_memories(self, prompt: str, limit: int = 5) -> List[Dict]:
        """
        Query Supermemory for relevant memories based on a prompt
        
        Args:
            prompt: The search query
            limit: Maximum number of memories to return
            
        Returns:
            List of relevant memory dictionaries
        """
        if not self.api_key:
            logger.warning("Cannot query memories: Supermemory API key not configured")
            return []
            
        try:
            payload = {
                "query": prompt,
                "limit": limit
            }
            
            response = requests.post(
                f"{self.base_url}/memories/search",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                memories = data.get('memories', [])
                logger.info(f"Found {len(memories)} relevant memories for query: {prompt[:50]}...")
                return memories
            else:
                logger.error(f"Failed to query memories: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying memories: {e}")
            return []
    
    def forget_last(self) -> bool:
        """
        Delete the most recent memory entry
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.api_key:
            logger.warning("Cannot forget memory: Supermemory API key not configured")
            return False
            
        try:
            # First, get the most recent memory
            response = requests.get(
                f"{self.base_url}/memories/recent",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                memory = response.json()
                memory_id = memory.get('id')
                
                if memory_id:
                    # Delete the memory
                    delete_response = requests.delete(
                        f"{self.base_url}/memories/{memory_id}",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if delete_response.status_code == 204:
                        logger.info("Successfully deleted most recent memory")
                        return True
                    else:
                        logger.error(f"Failed to delete memory: {delete_response.status_code}")
                        return False
                else:
                    logger.warning("No recent memory found to delete")
                    return False
            else:
                logger.error(f"Failed to get recent memory: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error forgetting memory: {e}")
            return False
    
    def add_conversation(self, user_message: str, assistant_response: str) -> bool:
        """
        Add a conversation pair to memory
        
        Args:
            user_message: The user's message
            assistant_response: The assistant's response
            
        Returns:
            bool: True if successful, False otherwise
        """
        conversation_entry = f"User: {user_message}\nAssistant: {assistant_response}"
        metadata = {
            "type": "conversation",
            "user_message": user_message,
            "assistant_response": assistant_response
        }
        
        return self.add_memory(conversation_entry, metadata)
    
    def get_context_for_prompt(self, current_prompt: str) -> str:
        """
        Get relevant context from memory for a given prompt
        
        Args:
            current_prompt: The current user prompt
            
        Returns:
            str: Formatted context string
        """
        memories = self.query_memories(current_prompt, limit=3)
        
        if not memories:
            return ""
        
        context_parts = []
        for memory in memories:
            content = memory.get('content', '')
            timestamp = memory.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M')
                    context_parts.append(f"[{formatted_time}] {content}")
                except:
                    context_parts.append(content)
            else:
                context_parts.append(content)
        
        if context_parts:
            return "Relevant context:\n" + "\n".join(context_parts) + "\n\n"
        
        return ""

