#!/usr/bin/env python3
"""
FastAPI entrypoint and Twilio SMS webhook
"""

import os
from typing import Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import uvicorn

from sms_handler import SMSHandler
from scheduler import start_scheduler, stop_scheduler, run_reminder_scan_now
from message_sender import MessageSender

load_dotenv("config.env", override=True)

app = FastAPI(title="Personal AI Assistant v1")
handler = SMSHandler()


@app.on_event("startup")
async def on_startup() -> None:
    start_scheduler()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    stop_scheduler()


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/debug/sms")
async def debug_sms(text: str = "hello", from_number: str = "+10000000000") -> Response:
    reply_text = handler.process_message(text, from_number)
    resp = MessagingResponse()
    resp.message(reply_text)
    return Response(content=str(resp), media_type="application/xml")


@app.post("/debug/run-reminders")
async def debug_run_reminders() -> Dict[str, int]:
    """Trigger a one-off reminder scan immediately."""
    sent = run_reminder_scan_now()
    return {"attempted": sent}


@app.post("/debug/send-test-message")
async def debug_send_test_message() -> Dict[str, Any]:
    """Send a test message to verify messaging configuration."""
    message_sender = MessageSender()
    success = message_sender.send_test_message()
    config_status = message_sender.get_configuration_status()
    
    return {
        "success": success,
        "configuration": config_status
    }


@app.get("/debug/messaging-status")
async def debug_messaging_status() -> Dict[str, Any]:
    """Get messaging configuration status."""
    message_sender = MessageSender()
    return message_sender.get_configuration_status()


@app.get("/debug/test-date-parsing")
async def debug_test_date_parsing(text: str = "remind me to test in 1 minute") -> Dict[str, Any]:
    """Test date parsing directly."""
    parsed_date = handler._parse_date_nlp(text)
    return {
        "input": text,
        "parsed_date": parsed_date,
        "success": parsed_date is not None
    }


@app.post("/sms")
async def sms_webhook(request: Request, background_tasks: BackgroundTasks) -> Response:
    form = await request.form()
    incoming_msg = (form.get("Body") or "").strip()
    from_number = (form.get("From") or "").strip()

    # Process message
    reply_text = handler.process_message(incoming_msg, from_number)

    # Build Twilio XML response (TwiML)
    resp = MessagingResponse()
    resp.message(reply_text)
    return Response(content=str(resp), media_type="application/xml")


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=False)
