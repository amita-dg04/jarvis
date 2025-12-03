"""
Tasks Manager for Personal AI Assistant
Handles SQLite-based task and reminder management
"""

import sqlite3
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TasksManager:
    def __init__(self, db_path: str = "./assistant.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize the SQLite database with tasks table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    due_date TEXT,
                    due_ts INTEGER,
                    completed INTEGER DEFAULT 0,
                    priority TEXT DEFAULT 'medium',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
            """)
            # Backfill schema if existing table lacks due_ts
            try:
                cursor.execute("ALTER TABLE tasks ADD COLUMN due_ts INTEGER")
            except Exception:
                pass
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
    
    def add_task(self, text: str, due_date: Optional[str] = None, priority: str = "medium") -> int:
        """
        Add a new task to the database
        
        Args:
            text: Task description
            due_date: Due date in ISO format (optional)
            priority: Task priority (high, medium, low)
            
        Returns:
            int: Task ID if successful, -1 if failed
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure table exists (for in-memory databases)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    due_date TEXT,
                    due_ts INTEGER,
                    completed INTEGER DEFAULT 0,
                    priority TEXT DEFAULT 'medium',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
            """)
            
            # Compute epoch seconds (UTC) for reliable comparisons
            due_ts: Optional[int] = None
            if due_date:
                try:
                    dt = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                    due_ts = int(dt.timestamp())
                except Exception:
                    due_ts = None

            cursor.execute("""
                INSERT INTO tasks (text, due_date, due_ts, priority)
                VALUES (?, ?, ?, ?)
            """, (text, due_date, due_ts, priority))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Task added: {text} (ID: {task_id})")
            return task_id
            
        except sqlite3.Error as e:
            logger.error(f"Error adding task: {e}")
            return -1
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """
        Get a specific task by ID
        
        Args:
            task_id: The task ID
            
        Returns:
            Dict with task data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, text, due_date, completed, priority, created_at, completed_at
                    FROM tasks WHERE id = ?
                """, (task_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'text': row[1],
                        'due_date': row[2],
                        'completed': bool(row[3]),
                        'priority': row[4],
                        'created_at': row[5],
                        'completed_at': row[6]
                    }
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None
    
    def get_pending_tasks(self) -> List[Dict]:
        """
        Get all pending (incomplete) tasks
        
        Returns:
            List of task dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure table exists (for in-memory databases)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    due_date TEXT,
                    completed INTEGER DEFAULT 0,
                    priority TEXT DEFAULT 'medium',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
            """)
            
            cursor.execute("""
                SELECT id, text, due_date, priority, created_at
                FROM tasks 
                WHERE completed = 0
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                    END,
                    due_date ASC,
                    created_at ASC
            """)
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    'id': row[0],
                    'text': row[1],
                    'due_date': row[2],
                    'priority': row[3],
                    'created_at': row[4]
                })
            
            conn.close()
            logger.info(f"Retrieved {len(tasks)} pending tasks")
            return tasks
            
        except sqlite3.Error as e:
            logger.error(f"Error getting pending tasks: {e}")
            return []
    
    def get_tasks_due_soon(self, minutes_ahead: int = 30) -> List[Dict]:
        """
        Get tasks that are due within the specified time window
        
        Args:
            minutes_ahead: How many minutes ahead to check
            
        Returns:
            List of tasks due soon
        """
        try:
            now_ts = int(datetime.utcnow().timestamp())
            future_time_ts = now_ts + int(minutes_ahead * 60)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, text, due_date, priority
                    FROM tasks 
                    WHERE completed = 0 
                    AND due_ts IS NOT NULL
                    AND due_ts BETWEEN ? AND ?
                    ORDER BY due_ts ASC
                """, (now_ts, future_time_ts))
                
                tasks = []
                for row in cursor.fetchall():
                    tasks.append({
                        'id': row[0],
                        'text': row[1],
                        'due_date': row[2],
                        'priority': row[3]
                    })
                
                logger.info(f"Found {len(tasks)} tasks due within {minutes_ahead} minutes")
                return tasks
                
        except sqlite3.Error as e:
            logger.error(f"Error getting tasks due soon: {e}")
            return []
    
    def complete_task(self, task_id: int) -> bool:
        """
        Mark a task as completed
        
        Args:
            task_id: The task ID to complete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure table exists (for in-memory databases)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    due_date TEXT,
                    completed INTEGER DEFAULT 0,
                    priority TEXT DEFAULT 'medium',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
            """)
            
            cursor.execute("""
                UPDATE tasks 
                SET completed = 1, completed_at = CURRENT_TIMESTAMP
                WHERE id = ? AND completed = 0
            """, (task_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                logger.info(f"Task {task_id} marked as completed")
                return True
            else:
                conn.close()
                logger.warning(f"Task {task_id} not found or already completed")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Error completing task {task_id}: {e}")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """
        Delete a task from the database
        
        Args:
            task_id: The task ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Task {task_id} deleted")
                    return True
                else:
                    logger.warning(f"Task {task_id} not found")
                    return False
                    
        except sqlite3.Error as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False
    
    def get_task_summary(self) -> str:
        """
        Get a formatted summary of pending tasks
        
        Returns:
            str: Formatted task summary
        """
        tasks = self.get_pending_tasks()
        
        if not tasks:
            return "You have no pending tasks! 🎉"
        
        summary_parts = [f"You have {len(tasks)} pending task{'s' if len(tasks) != 1 else ''}:"]
        
        for task in tasks[:5]:  # Show max 5 tasks
            task_id = task['id']
            text = task['text']
            due_date = task['due_date']
            priority = task['priority']
            
            # Format priority emoji
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "🟡")
            
            # Format due date
            if due_date:
                try:
                    due_dt = datetime.fromisoformat(due_date)
                    due_str = due_dt.strftime("%m/%d %H:%M")
                    summary_parts.append(f"{priority_emoji} {task_id}. {text} (due: {due_str})")
                except:
                    summary_parts.append(f"{priority_emoji} {task_id}. {text} (due: {due_date})")
            else:
                summary_parts.append(f"{priority_emoji} {task_id}. {text}")
        
        if len(tasks) > 5:
            summary_parts.append(f"... and {len(tasks) - 5} more")
        
        return "\n".join(summary_parts)
    
    def get_overdue_tasks(self) -> List[Dict]:
        """
        Get tasks that are overdue
        
        Returns:
            List of overdue tasks
        """
        try:
            now_ts = int(datetime.utcnow().timestamp())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, text, due_date, priority
                    FROM tasks 
                    WHERE completed = 0 
                    AND due_ts IS NOT NULL
                    AND due_ts < ?
                    ORDER BY due_ts ASC
                """, (now_ts,))
                
                tasks = []
                for row in cursor.fetchall():
                    tasks.append({
                        'id': row[0],
                        'text': row[1],
                        'due_date': row[2],
                        'priority': row[3]
                    })
                
                logger.info(f"Found {len(tasks)} overdue tasks")
                return tasks
                
        except sqlite3.Error as e:
            logger.error(f"Error getting overdue tasks: {e}")
            return []
