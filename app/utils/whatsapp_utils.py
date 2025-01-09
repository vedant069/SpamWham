import logging
from flask import current_app, jsonify
import json
import requests
import re
from ..rag import generate_response, add_document_to_vector_db, clear_vector_db, model, debug_database_state
from ..compose import EmailComposer, handle_compose_request
from ..get_emails import fetch_recent_emails

email_composer = EmailComposer(model)
active_drafts = {}

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        # Log request details for debugging
        logging.info(f"Sending message to URL: {url}")
        logging.info(f"Headers: {headers}")
        logging.info(f"Data: {data}")

        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )
        
        # Log response for debugging
        logging.info(f"Response status code: {response.status_code}")
        logging.info(f"Response content: {response.text}")
        
        if response.status_code == 401:
            logging.error("Authentication failed. Please check your ACCESS_TOKEN")
            logging.error(f"Response: {response.text}")
            return jsonify({"status": "error", "message": "Authentication failed"}), 401
            
        response.raise_for_status()
        return jsonify({"status": "success"}), 200
        
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"Error sending message: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


def handle_command(message_body):
    """Handle special commands like refresh and clear"""
    try:
        if message_body == "refresh":
            logging.info("Refreshing email database...")
            clear_vector_db()
            emails = fetch_recent_emails()
            if emails:
                stored_count = add_document_to_vector_db("recent_emails", emails)
                return f"✨ Database refreshed! Loaded {stored_count} recent emails."
            return "❌ No recent emails found to refresh."
            
        elif message_body == "clear":
            logging.info("Clearing email database...")
            clear_vector_db()
            return "🧹 Database cleared!"
            
        elif message_body == "status":
            debug_info = debug_database_state()
            return f"📊 Email Database Status:\n{debug_info}"
            
        return None
    except Exception as e:
        logging.error(f"Error handling command: {e}")
        return f"❌ Error executing command: {str(e)}"


def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"].strip()

    logging.info(f"Processing message from {name} ({wa_id}): {message_body}")

    # First check if this is a command
    command_response = handle_command(message_body.lower())
    if command_response:
        response = process_text_for_whatsapp(command_response)
        data = get_text_message_input(wa_id, response)
        send_message(data)
        return

    # Then check if this is a compose-related message
    current_draft = active_drafts.get(wa_id)
    response, draft_id = handle_compose_request(message_body, email_composer, current_draft)
    
    if response is not None:
        # This was a compose-related message
        if draft_id:
            active_drafts[wa_id] = draft_id
        else:
            active_drafts.pop(wa_id, None)  # Remove draft if composition is complete/cancelled
            
        response = process_text_for_whatsapp(response)
        data = get_text_message_input(wa_id, response)
        send_message(data)
        return
    
    # If not a command or compose message, use RAG pipeline
    response = generate_response("", message_body)  # Empty conversation history for now
    response = process_text_for_whatsapp(response)

    logging.info(f"Generated response: {response}")

    data = get_text_message_input(wa_id, response)
    send_message(data)


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
