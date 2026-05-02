import imaplib
import email
from email.header import decode_header
import re
import time

class PromotionalSpamFilter:
    def __init__(self, email_address, password, imap_server, imap_port=993):
        """
        Initialize the spam filter
        
        Common IMAP servers:
        - Gmail: imap.gmail.com (port 993)
        - Outlook: outlook.office365.com (port 993)
        - Yahoo: imap.mail.yahoo.com (port 993)
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.mail = None
    
    def connect(self):
        """Connect to the email server"""
        try:
            print(f"Connecting to {self.imap_server}...")
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.email_address, self.password)
            print("✓ Connected successfully!")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {str(e)}")
            return False
    
    def is_promotional(self, msg):
        """
        Check if an email is promotional based on multiple criteria
        """
        promotional_indicators = 0
        
        # Get email details
        subject = self.get_header(msg, 'Subject')
        from_addr = self.get_header(msg, 'From')
        
        # Check for unsubscribe link (strong indicator)
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" or part.get_content_type() == "text/html":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        if re.search(r'unsubscribe', body, re.IGNORECASE):
                            promotional_indicators += 2
                        if re.search(r'marketing', body, re.IGNORECASE):
                            promotional_indicators += 1
                        break
                    except:
                        pass
        
        # Check sender patterns
        promo_patterns = [
            r'noreply@',
            r'marketing@',
            r'newsletter@',
            r'info@',
            r'promo@',
            r'offers@',
            r'deals@',
            r'subscribe@'
        ]
        
        for pattern in promo_patterns:
            if re.search(pattern, from_addr, re.IGNORECASE):
                promotional_indicators += 1
                break
        
        # Check subject patterns
        subject_keywords = [
            r'sale', r'discount', r'offer', r'deal', r'promotion',
            r'limited time', r'exclusive', r'save \d+%', r'free shipping',
            r'subscribe', r'newsletter', r'don\'t miss'
        ]
        
        for keyword in subject_keywords:
            if re.search(keyword, subject, re.IGNORECASE):
                promotional_indicators += 1
                break
        
        # If score is 2 or more, likely promotional
        return promotional_indicators >= 2
    
    def get_header(self, msg, header_name):
        """Decode email header"""
        header = msg.get(header_name, '')
        decoded_parts = decode_header(header)
        decoded_header = ''
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_header += part.decode(encoding or 'utf-8')
                except:
                    decoded_header += part.decode('utf-8', errors='ignore')
            else:
                decoded_header += str(part)
        
        return decoded_header
    
    def move_to_spam(self, email_id):
        """Move email to spam/junk folder"""
        try:
            # Mark as spam and move
            # Different providers use different spam folder names
            spam_folders = ['[Gmail]/Spam', 'Junk', 'Spam', 'INBOX.Spam']
            
            for spam_folder in spam_folders:
                try:
                    # Copy to spam folder
                    result = self.mail.copy(email_id, spam_folder)
                    if result[0] == 'OK':
                        # Mark original as deleted
                        self.mail.store(email_id, '+FLAGS', '\\Deleted')
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"Error moving email: {str(e)}")
            return False
    
    def process_inbox(self, limit=50):
        """Process emails in inbox and move promotional ones to spam"""
        try:
            # Select inbox
            self.mail.select('INBOX')
            
            # Search for all emails (you can modify this to search unread only)
            status, messages = self.mail.search(None, 'ALL')
            
            if status != 'OK':
                print("No emails found")
                return
            
            email_ids = messages[0].split()
            total_emails = len(email_ids)
            
            # Process only the most recent emails (limit)
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            print(f"\nProcessing {len(email_ids)} emails (out of {total_emails} total)...")
            print("-" * 60)
            
            moved_count = 0
            
            for i, email_id in enumerate(email_ids, 1):
                try:
                    # Fetch email
                    status, msg_data = self.mail.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parse email
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    subject = self.get_header(msg, 'Subject')
                    from_addr = self.get_header(msg, 'From')
                    
                    # Check if promotional
                    if self.is_promotional(msg):
                        print(f"\n[{i}/{len(email_ids)}] PROMOTIONAL DETECTED:")
                        print(f"  From: {from_addr[:60]}...")
                        print(f"  Subject: {subject[:60]}...")
                        
                        if self.move_to_spam(email_id):
                            print("  ✓ Moved to spam")
                            moved_count += 1
                        else:
                            print("  ✗ Failed to move")
                    else:
                        print(f"[{i}/{len(email_ids)}] Skipped (not promotional)")
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error processing email {i}: {str(e)}")
                    continue
            
            # Expunge deleted emails
            self.mail.expunge()
            
            print("\n" + "=" * 60)
            print(f"Summary: {moved_count} promotional emails moved to spam")
            print("=" * 60)
            
        except Exception as e:
            print(f"Error processing inbox: {str(e)}")
    
    def disconnect(self):
        """Disconnect from email server"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
                print("\n✓ Disconnected from server")
            except:
                pass


def main():
    """Main function - Configure your email settings here"""
    
    print("=" * 60)
    print("  PROMOTIONAL EMAIL SPAM FILTER")
    print("=" * 60)
    
    # ============= CONFIGURATION =============
    # Replace these with your email credentials
    EMAIL = "your.email@gmail.com"
    PASSWORD = "your_app_password_here"  # Use app password, not regular password!
    
    # IMAP Server settings (choose based on your provider)
    IMAP_SERVER = "imap.gmail.com"  # Gmail
    # IMAP_SERVER = "outlook.office365.com"  # Outlook
    # IMAP_SERVER = "imap.mail.yahoo.com"  # Yahoo
    
    IMAP_PORT = 993
    
    # Number of recent emails to check
    EMAIL_LIMIT = 50
    # =========================================
    
    # Create filter instance
    spam_filter = PromotionalSpamFilter(EMAIL, PASSWORD, IMAP_SERVER, IMAP_PORT)
    
    # Connect and process
    if spam_filter.connect():
        spam_filter.process_inbox(limit=EMAIL_LIMIT)
        spam_filter.disconnect()
    else:
        print("Failed to connect. Please check your credentials and settings.")
        print("\nFor Gmail users:")
        print("1. Enable 2-factor authentication")
        print("2. Generate an 'App Password' at: https://myaccount.google.com/apppasswords")
        print("3. Use the app password instead of your regular password")


if __name__ == "__main__":
    main()
