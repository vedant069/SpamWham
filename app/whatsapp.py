from flask import Blueprint, request, jsonify
import logging
from dotenv import load_dotenv
import os
from .rag import (
    generate_response,
    add_document_to_vector_db,
    clear_vector_db,
    debug_database_state,
    retrieve_relevant_chunks
)
from .get_emails import fetch_recent_emails
from .utils.whatsapp_utils import get_text_message_input, send_message, process_text_for_whatsapp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create blueprint
whatsapp_blueprint = Blueprint('whatsapp', __name__, url_prefix='/whatsapp')

# Store user conversations
user_conversations = {}



# @whatsapp_blueprint.route("/webhook", methods=['GET'])
# def verify_webhook():
#     """Verify webhook for WhatsApp API"""
#     mode = request.args.get("hub.mode")
#     token = request.args.get("hub.verify_token")
#     challenge = request.args.get("hub.challenge")
    
#     if mode and token:
#         if mode == "subscribe" and token == os.getenv("VERIFY_TOKEN"):
#             return challenge, 200
#         return "Forbidden", 403
#     return "Bad Request", 400

# Initialize email database
def init_email_database():
    try:
        logger.info("Loading initial emails into database...")
        emails = fetch_recent_emails()
        if emails:
            stored_count = add_document_to_vector_db("recent_emails", emails)
            logger.info(f"Loaded {stored_count} recent emails into database")
    except Exception as e:
        logger.error(f"Error loading initial emails: {e}")

# Initialize when blueprint is registered
init_email_database()
