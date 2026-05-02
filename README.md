# Gmail Promotional Emails to Spam Automation

Automatically move all promotional emails to spam folder using Gmail API.

## Setup Instructions

### 1. Enable Gmail API and Get Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as application type
   - Download the credentials JSON file
   - Rename it to `credentials.json` and place it in this folder

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Script

```bash
python promotional_to_spam.py
```

**First run:**
- Browser will open asking you to authorize the app
- Sign in with your Gmail account
- Grant the requested permissions
- Script will save a `token.pickle` file for future runs

**Subsequent runs:**
- Script will automatically use saved credentials
- No browser authentication needed

## Features

✅ Finds all emails in "Promotions" category  
✅ Moves them to Spam folder  
✅ Processes up to 500 emails per run  
✅ Shows progress and summary  
✅ Saves credentials for future use  

## Automation (Optional)

### Windows Task Scheduler
Run the script automatically every day:
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 9 AM)
4. Action: Start a program
5. Program: `python`
6. Arguments: `"d:\Bitflow_softwares\timepass\promotional_to_spam.py"`
7. Start in: `d:\Bitflow_softwares\timepass`

### Manual Scheduling
Or simply run the script whenever you want to clean up promotional emails!

## Notes

- The script only processes promotional emails (category:promotions)
- Maximum 500 emails per run (can be adjusted in code)
- Requires internet connection
- Safe to run multiple times
