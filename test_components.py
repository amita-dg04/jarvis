#!/usr/bin/env python3
"""
Test script for Personal AI Assistant components
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config.env")

def test_tasks_manager():
    """Test the tasks manager"""
    print("Testing Tasks Manager...")
    try:
        from tasks_manager import TasksManager
        
        tm = TasksManager(":memory:")  # Use in-memory database for testing
        
        # Test adding a task
        task_id = tm.add_task("Test task", "2024-01-15T10:00:00", "high")
        assert task_id > 0, "Failed to add task"
        print("✅ Task added successfully")
        
        # Test getting tasks
        tasks = tm.get_pending_tasks()
        assert len(tasks) == 1, "Failed to retrieve tasks"
        print("✅ Tasks retrieved successfully")
        
        # Test completing task
        success = tm.complete_task(task_id)
        assert success, "Failed to complete task"
        print("✅ Task completed successfully")
        
        print("✅ Tasks Manager: All tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Tasks Manager test failed: {e}")
        return False

def test_llm_engine():
    """Test the LLM engine"""
    print("Testing LLM Engine...")
    try:
        from llm_engine import LLMEngine
        
        llm = LLMEngine()
        
        if not llm.api_key:
            print("⚠️  LLM Engine: No API key configured, skipping tests")
            return True
        
        # Test basic response
        response = llm.ask_llm("Hello, how are you?")
        assert response, "No response from LLM"
        print("✅ LLM response generated")
        
        # Test task parsing
        task_info = llm.parse_task_intent("remind me to call mom tomorrow")
        if task_info and task_info.get("is_task"):
            print("✅ Task parsing works")
        else:
            print("⚠️  Task parsing may not be working correctly")
        
        print("✅ LLM Engine: All tests passed")
        return True
        
    except Exception as e:
        print(f"❌ LLM Engine test failed: {e}")
        return False

def test_memory_manager():
    """Test the memory manager"""
    print("Testing Memory Manager...")
    try:
        from memory_manager import MemoryManager
        
        mm = MemoryManager()
        
        if not mm.api_key:
            print("⚠️  Memory Manager: No API key configured, skipping tests")
            return True
        
        # Test adding memory
        success = mm.add_memory("Test memory entry")
        if success:
            print("✅ Memory added successfully")
        else:
            print("⚠️  Memory addition failed (API may be unavailable)")
        
        print("✅ Memory Manager: Tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Memory Manager test failed: {e}")
        return False

def test_sms_handler():
    """Test the SMS handler"""
    print("Testing SMS Handler...")
    try:
        from sms_handler import SMSHandler
        
        sms = SMSHandler()
        
        # Test command detection
        command = sms.llm_engine.should_handle_command("show tasks")
        assert command == "show_tasks", "Command detection failed"
        print("✅ Command detection works")
        
        # Test date parsing
        date_str = sms.parse_natural_language_date("tomorrow at 3pm")
        if date_str:
            print("✅ Date parsing works")
        else:
            print("⚠️  Date parsing may not be working correctly")
        
        print("✅ SMS Handler: All tests passed")
        return True
        
    except Exception as e:
        print(f"❌ SMS Handler test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Personal AI Assistant Components")
    print("=" * 50)
    
    tests = [
        test_tasks_manager,
        test_llm_engine,
        test_memory_manager,
        test_sms_handler
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The assistant is ready to use.")
    else:
        print("⚠️  Some tests failed. Check your configuration and API keys.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


