"""
Gmail Promotional Email to Spam Automation
This script moves all promotional emails to spam folder automatically.
"""

import os.path
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scope - needs modify permission to move emails
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def authenticate_gmail():
    """Authenticate and return Gmail API service."""
    creds = None
    
    # Token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)


def get_promotional_emails(service, max_results=100):
    """Get all promotional emails from inbox."""
    try:
        # Query for emails in CATEGORY_PROMOTIONS
        results = service.users().messages().list(
            userId='me',
            q='category:promotions',
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        return messages
    
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []


def move_to_spam(service, message_id):
    """Move a specific email to spam folder."""
    try:
        # Modify the message to add SPAM label and remove INBOX
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={
                'addLabelIds': ['SPAM'],
                'removeLabelIds': ['INBOX', 'CATEGORY_PROMOTIONS']
            }
        ).execute()
        return True
    
    except HttpError as error:
        print(f'Error moving message {message_id}: {error}')
        return False


def main():
    """Main function to move promotional emails to spam."""
    print("🚀 Starting Gmail Promotional to Spam automation...")
    
    # Authenticate with Gmail API
    print("📧 Authenticating with Gmail...")
    service = authenticate_gmail()
    print("✅ Authentication successful!")
    
    # Get promotional emails
    print("\n🔍 Searching for promotional emails...")
    promotional_emails = get_promotional_emails(service, max_results=500)
    
    if not promotional_emails:
        print("✨ No promotional emails found!")
        return
    
    print(f"📬 Found {len(promotional_emails)} promotional email(s)")
    
    # Move each promotional email to spam
    moved_count = 0
    failed_count = 0
    
    print("\n🗑️  Moving emails to spam...")
    for i, message in enumerate(promotional_emails, 1):
        message_id = message['id']
        
        if move_to_spam(service, message_id):
            moved_count += 1
            print(f"  [{i}/{len(promotional_emails)}] ✓ Moved message {message_id[:10]}...")
        else:
            failed_count += 1
            print(f"  [{i}/{len(promotional_emails)}] ✗ Failed to move {message_id[:10]}...")
    
    # Summary
    print("\n" + "="*50)
    print("📊 Summary:")
    print(f"   ✅ Successfully moved: {moved_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📧 Total processed: {len(promotional_emails)}")
    print("="*50)


if __name__ == '__main__':
    main()
