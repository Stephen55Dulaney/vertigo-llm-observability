# Daily Cursor Meeting Summary Automation

This system automatically generates and emails daily meeting summaries based on your Cursor workspace activity, including git commits, file changes, and project progress.

## 🎯 What It Does

- **Analyzes workspace activity**: Git commits, file modifications, TODOs
- **Generates AI-powered summaries**: Using Gemini AI for professional meeting notes
- **Sends daily emails**: To specified recipients at 5 PM CST
- **Provides fallback options**: Works even without AI or email setup
- **Logs everything**: Complete audit trail of all activities

## 📧 Email Recipients

- **To**: verigo.agent.2025@gmail.com
- **CC**: stephen.dulaney@gmail.com

## 🚀 Quick Setup

### 1. Run the Setup Script

```bash
chmod +x setup_daily_summary_cron.sh
./setup_daily_summary_cron.sh
```

### 2. Set Up Gmail Authentication

#### Option A: Using Existing Token (if available)
If you already have a `token.json` file from the existing Gmail setup:
```bash
cp token.json /workspace/
```

#### Option B: Set Up New OAuth2 Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Gmail API
3. Create OAuth2 credentials
4. Download as `credentials.json`
5. Place in `/workspace/credentials.json`

### 3. Test the Setup

```bash
./test_summary.sh
```

### 4. (Optional) Enable AI Summaries

Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey):

```bash
# Edit setup_env.sh and uncomment:
export GEMINI_API_KEY="your-api-key-here"
```

## 📋 What Gets Included in Summaries

### Git Activity
- Recent commits (last 24 hours)
- Files changed
- Current branch
- Commit authors and messages

### Workspace Activity
- Recently modified files
- Project structure overview
- TODO/FIXME comments found in code

### AI-Generated Sections
- **Today's Accomplishments**: What was worked on
- **Key Changes Made**: Important commits and modifications
- **Current Status**: Where the project stands
- **Next Steps**: Recommended actions based on TODOs
- **Technical Notes**: Important technical details

## ⏰ Schedule

The cron job runs daily at **5:00 PM CST/CDT** (22:00 UTC).

## 📁 Files Created

- `cursor_meeting_summarizer.py` - Main summarizer script
- `setup_daily_summary_cron.sh` - Cron job setup script
- `setup_env.sh` - Environment configuration
- `test_summary.sh` - Testing script
- `cursor_summary.log` - Daily execution logs
- `meeting_summary_YYYY-MM-DD.md` - Backup files (if email fails)

## 🔧 Configuration

### Environment Variables

Edit `setup_env.sh` to configure:

```bash
# Required for email functionality
export GMAIL_CREDENTIALS_PATH="/workspace/credentials.json"

# Optional for AI summaries
export GEMINI_API_KEY="your-gemini-api-key"

# Optional for Google Cloud features
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

### Email Recipients

To change email recipients, edit `cursor_meeting_summarizer.py`:

```python
self.recipients = {
    'to': 'your-primary-email@example.com',
    'cc': 'your-cc-email@example.com'
}
```

## 🧪 Testing

### Test Individual Components

```bash
# Test git activity collection
cd /workspace
git log --since="yesterday" --oneline

# Test workspace analysis
find . -type f -mtime -1 -not -path "./.git/*"

# Test email functionality
python3 -c "from cursor_meeting_summarizer import CursorMeetingSummarizer; s = CursorMeetingSummarizer(); print('Gmail service:', 'OK' if s.gmail_service else 'Not configured')"
```

### Full System Test

```bash
./test_summary.sh
```

### Check Cron Job

```bash
# View current cron jobs
crontab -l

# Check if cron service is running
sudo systemctl status cron

# View recent logs
tail -f cursor_summary.log
```

## 🐛 Troubleshooting

### Email Not Sending

1. **Check Gmail credentials**:
   ```bash
   ls -la credentials.json token.json
   ```

2. **Re-authenticate**:
   ```bash
   rm token.json
   ./test_summary.sh  # Will prompt for re-authentication
   ```

3. **Check Gmail API quota**: Visit Google Cloud Console

### AI Summaries Not Working

1. **Verify API key**:
   ```bash
   echo $GEMINI_API_KEY
   ```

2. **Test API access**:
   ```bash
   python3 -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('API OK')"
   ```

### Cron Job Not Running

1. **Check cron service**:
   ```bash
   sudo systemctl status cron
   sudo systemctl start cron  # if not running
   ```

2. **Check cron logs**:
   ```bash
   sudo tail -f /var/log/cron.log
   ```

3. **Verify file permissions**:
   ```bash
   chmod +x cursor_meeting_summarizer.py
   ```

## 📊 Sample Output

```
# Daily Development Summary - January 29, 2025

## Today's Accomplishments
- Implemented daily meeting summarizer automation
- Set up Gmail API integration for automated emails
- Created comprehensive cron job scheduling system

## Key Changes Made
- **a1e6f2b** by developer on 2025-01-29: Add cursor meeting summarizer script
- **b2f7c3d** by developer on 2025-01-29: Configure Gmail API integration
- **c3g8d4e** by developer on 2025-01-29: Set up automated cron scheduling

## Current Status
Working on branch: cursor/daily-cursor-meeting-summary-and-email-a1e6
Total commits today: 3
Files modified: 5

## Next Steps
1. Test email delivery to both recipients
2. Verify cron job execution at scheduled time
3. Monitor logs for any issues

---
*This summary was automatically generated from workspace activity.*
```

## 🔒 Security Notes

- Gmail credentials are stored locally and encrypted
- API keys should be kept secure and not committed to git
- Log files may contain sensitive information - review regularly
- Cron jobs run with user permissions only

## 📞 Support

If you encounter issues:

1. Check the logs: `tail -f cursor_summary.log`
2. Run the test script: `./test_summary.sh`
3. Verify all dependencies are installed: `pip install -r requirements.txt`
4. Check cron job status: `crontab -l`

The system is designed to be robust and will save summaries to files even if email delivery fails.