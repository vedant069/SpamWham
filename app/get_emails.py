import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gmail IMAP configuration
IMAP_SERVER = "imap.gmail.com"
EMAIL_USER = "vedantnadhe069@gmail.com"  # Get from environment variable
EMAIL_PASS = "jkns dsef asfp imhr"  # Get from environment variable

# Step 1: Connect to Gmail IMAP server
def connect_to_gmail():
    if not EMAIL_USER or not EMAIL_PASS:
        print("Error: Email credentials not found in environment variables")
        return None
        
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)  # Secure connection to IMAP server
        mail.login(EMAIL_USER, EMAIL_PASS)    # Log in with email and app password
        return mail
    except Exception as e:
        print(f"Error connecting to Gmail: {e}")
        return None

# Step 2: Fetch recent emails
def fetch_recent_emails(max_emails=50):
    """
    Fetch only emails from today and yesterday, up to max_emails
    """
    mail = connect_to_gmail()
    if not mail:
        return []

    try:
        mail.select("inbox")
        
        # Calculate dates
        now = datetime.now()
        today = now.date()
        yesterday = today - timedelta(days=1)
        two_days_ago = (today - timedelta(days=2)).strftime("%d-%b-%Y")
        
        # Search for emails from the last 2 days
        status, messages = mail.search(None, f'SINCE {two_days_ago}')
        email_ids = messages[0].split()
        
        if not email_ids:
            return []
        
        # Get only the most recent emails if we have more than max_emails
        recent_email_ids = email_ids[-max_emails:] if len(email_ids) > max_emails else email_ids
        
        email_data = []
        
        for email_id in recent_email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Parse date to timestamp
                    date_str = msg.get("Date")
                    try:
                        parsed_date = email.utils.parsedate_to_datetime(date_str)
                        email_date = parsed_date.date()
                        timestamp = parsed_date.timestamp()
                        
                        # Only include emails from today and yesterday
                        if email_date not in [today, yesterday]:
                            continue
                            
                    except Exception as e:
                        print(f"Error parsing date: {e}")
                        continue

                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    
                    # Extract body
                    body = extract_email_body(msg)
                    if not body.strip():
                        body = "No content available"
                    
                    email_data.append({
                        "subject": subject,
                        "sender": msg.get("From"),
                        "date": date_str,
                        "timestamp": timestamp,
                        "body": body,
                        "day": "today" if email_date == today else "yesterday"
                    })
        
        # Sort emails by timestamp (most recent first)
        email_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Log summary
        today_count = sum(1 for email in email_data if email['day'] == 'today')
        yesterday_count = sum(1 for email in email_data if email['day'] == 'yesterday')
        print(f"Found {today_count} emails from today and {yesterday_count} from yesterday")
        
        return email_data

    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []
    finally:
        mail.logout()

def extract_email_body(msg):
    """Extract email body with better formatting"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    part_body = part.get_payload(decode=True).decode()
                    body += clean_email_body(part_body)
                except:
                    continue
    else:
        try:
            body = msg.get_payload(decode=True).decode()
            body = clean_email_body(body)
        except:
            body = "Could not decode email body"
    return body

def clean_email_body(body):
    """Clean and format email body"""
    # Remove extra whitespace and newlines
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    cleaned_body = "\n".join(lines)
    return cleaned_body

# Step 3: Display emails
if __name__ == "__main__":
    emails = fetch_recent_emails()
    for i, email in enumerate(emails, start=1):
        print(f"\nEmail {i}:")
        print("=" * 70)
        print(f"Subject: {email['subject']}")
        print(f"From: {email['sender']}")
        print(f"Date: {email['date']}")
        print("-" * 70)
        print("Body:")
        print(email['body'])
        print("=" * 70)
