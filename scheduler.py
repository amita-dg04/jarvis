#!/usr/bin/env python3
"""
Background scheduler for proactive reminders via SMS or WhatsApp (Twilio)
"""

import os
import threading
import logging
from typing import Optional

import schedule
from dotenv import load_dotenv

from tasks_manager import TasksManager
from message_sender import MessageSender

load_dotenv("config.env", override=True)
logger = logging.getLogger(__name__)

_scheduler_thread: Optional[threading.Thread] = None
_scheduler_stop = threading.Event()
_message_sender: Optional[MessageSender] = None


def _get_message_sender() -> MessageSender:
    """Get or create the message sender instance"""
    global _message_sender
    if _message_sender is None:
        _message_sender = MessageSender()
    return _message_sender


def _check_and_send_reminders() -> None:
    """Check for due tasks and send reminders"""
    database_path = os.getenv("DATABASE_PATH", "./assistant.db")
    
    # Get message sender
    message_sender = _get_message_sender()
    if not message_sender.is_configured():
        logger.debug("Scheduler skip: MessageSender not configured")
        return
    
    # Get due tasks (only overdue tasks, not "due soon")
    tm = TasksManager(database_path)
    due_tasks = tm.get_overdue_tasks()
    
    if not due_tasks:
        logger.debug("No due reminders to send right now")
        return
    
    logger.info(f"Found {len(due_tasks)} due reminders to send")
    
    # Send reminders
    sent_count = 0
    seen = set()
    
    for task in due_tasks:
        if task['id'] in seen:
            continue
        seen.add(task['id'])
        
        try:
            success = message_sender.send_reminder(
                task['text'], 
                task['due_date'], 
                task['id']
            )
            
            if success:
                sent_count += 1
                # Mark as completed after sending to avoid duplicate sends
                try:
                    tm.complete_task(task['id'])
                    logger.info(f"Task {task['id']} marked as completed after reminder sent")
                except Exception as e:
                    logger.error(f"Failed to mark task {task['id']} as completed: {e}")
            else:
                logger.error(f"Failed to send reminder for task {task['id']}")
                
        except Exception as e:
            logger.error(f"Unexpected error processing task {task['id']}: {e}")
            continue
    
    if sent_count > 0:
        logger.info(f"Successfully sent {sent_count} reminders")


def run_reminder_scan_now() -> int:
    """Run a one-off reminder scan immediately. Returns number of messages attempted."""
    database_path = os.getenv("DATABASE_PATH", "./assistant.db")
    
    # Get message sender
    message_sender = _get_message_sender()
    if not message_sender.is_configured():
        logger.warning("Cannot run reminder scan: MessageSender not configured")
        return 0
    
    # Get due tasks (only overdue tasks, not "due soon")
    tm = TasksManager(database_path)
    due_tasks = tm.get_overdue_tasks()
    
    if not due_tasks:
        logger.info("Manual scan: no due reminders")
        return 0
    
    logger.info(f"Manual scan: found {len(due_tasks)} due reminders")
    
    # Send reminders
    sent_count = 0
    seen = set()
    
    for task in due_tasks:
        if task['id'] in seen:
            continue
        seen.add(task['id'])
        
        try:
            success = message_sender.send_reminder(
                task['text'], 
                task['due_date'], 
                task['id']
            )
            
            if success:
                sent_count += 1
                # Mark as completed after sending
                try:
                    tm.complete_task(task['id'])
                except Exception as e:
                    logger.error(f"Failed to mark task {task['id']} as completed: {e}")
            else:
                logger.error(f"Manual scan: failed to send reminder for task {task['id']}")
                
        except Exception as e:
            logger.error(f"Manual scan: unexpected error processing task {task['id']}: {e}")
            continue
    
    logger.info(f"Manual scan: successfully sent {sent_count} reminders")
    return sent_count


def _run_loop() -> None:
    logger.info("Reminder scheduler loop starting")
    # Check every 10 seconds for near-real-time reminders
    schedule.every(10).seconds.do(_check_and_send_reminders)
    while not _scheduler_stop.is_set():
        schedule.run_pending()
        _scheduler_stop.wait(1.0)
    logger.info("Reminder scheduler loop stopping")


def start_scheduler() -> None:
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        logger.debug("Scheduler already running; start skipped")
        return
    _scheduler_stop.clear()
    _scheduler_thread = threading.Thread(target=_run_loop, name="reminder-scheduler", daemon=True)
    _scheduler_thread.start()
    logger.info("Reminder scheduler started")


def stop_scheduler() -> None:
    _scheduler_stop.set()
    logger.info("Reminder scheduler stop requested")
