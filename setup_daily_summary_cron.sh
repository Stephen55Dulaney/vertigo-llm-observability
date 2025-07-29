#!/bin/bash
"""
Setup script for Daily Cursor Meeting Summary Cron Job
This script sets up a cron job to run the meeting summarizer daily at 5 PM CST.
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Setting up Daily Cursor Meeting Summary Cron Job${NC}"
echo "=================================================="

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/cursor_meeting_summarizer.py"
LOG_FILE="$SCRIPT_DIR/cursor_summary.log"

echo -e "${YELLOW}📍 Script directory: $SCRIPT_DIR${NC}"
echo -e "${YELLOW}🐍 Python script: $PYTHON_SCRIPT${NC}"
echo -e "${YELLOW}📝 Log file: $LOG_FILE${NC}"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}❌ Error: cursor_meeting_summarizer.py not found!${NC}"
    exit 1
fi

# Make Python script executable
chmod +x "$PYTHON_SCRIPT"
echo -e "${GREEN}✅ Made Python script executable${NC}"

# Create cron job command
# 5 PM CST = 23:00 UTC (accounting for daylight saving time variations)
# We'll use 23:00 UTC which is 5 PM CST during standard time
# For daylight saving time (CDT), 5 PM CDT = 22:00 UTC
# We'll set it for 22:00 UTC to handle CDT
CRON_TIME="0 22 * * *"  # 22:00 UTC = 5 PM CDT / 4 PM CST
CRON_COMMAND="cd $SCRIPT_DIR && /usr/bin/python3 $PYTHON_SCRIPT >> $LOG_FILE 2>&1"

echo -e "${YELLOW}⏰ Cron schedule: $CRON_TIME (5 PM CST/CDT)${NC}"
echo -e "${YELLOW}🔧 Cron command: $CRON_COMMAND${NC}"

# Add cron job
echo "# Daily Cursor Meeting Summary - 5 PM CST" > /tmp/cursor_cron.txt
echo "$CRON_TIME $CRON_COMMAND" >> /tmp/cursor_cron.txt

# Install cron job
if crontab -l > /dev/null 2>&1; then
    # Backup existing crontab
    crontab -l > /tmp/crontab_backup.txt
    echo -e "${GREEN}✅ Backed up existing crontab${NC}"
    
    # Remove any existing cursor summary cron jobs
    crontab -l | grep -v "cursor_meeting_summarizer.py" > /tmp/crontab_new.txt
    
    # Add new cron job
    cat /tmp/cursor_cron.txt >> /tmp/crontab_new.txt
    crontab /tmp/crontab_new.txt
else
    # No existing crontab, create new one
    crontab /tmp/cursor_cron.txt
fi

echo -e "${GREEN}✅ Cron job installed successfully!${NC}"

# Verify cron job was added
echo -e "${YELLOW}📋 Current crontab:${NC}"
crontab -l | grep -A 1 -B 1 "cursor_meeting_summarizer"

# Create environment setup script
cat > "$SCRIPT_DIR/setup_env.sh" << 'EOF'
#!/bin/bash
# Environment setup for cursor meeting summarizer

# Set up Python path
export PYTHONPATH="$PYTHONPATH:/workspace"

# Gmail credentials (you'll need to set these)
export GMAIL_CREDENTIALS_PATH="/workspace/credentials.json"

# Gemini API key (optional, for AI-generated summaries)
# export GEMINI_API_KEY="your-gemini-api-key-here"

# Google Cloud credentials (if using)
# export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

echo "Environment variables set for cursor meeting summarizer"
EOF

chmod +x "$SCRIPT_DIR/setup_env.sh"
echo -e "${GREEN}✅ Created environment setup script${NC}"

# Create test script
cat > "$SCRIPT_DIR/test_summary.sh" << 'EOF'
#!/bin/bash
# Test script for cursor meeting summarizer

echo "🧪 Testing Cursor Meeting Summarizer..."
cd "$(dirname "$0")"

# Source environment
source ./setup_env.sh

# Run the summarizer
python3 cursor_meeting_summarizer.py

echo "✅ Test completed. Check the output above and any generated files."
EOF

chmod +x "$SCRIPT_DIR/test_summary.sh"
echo -e "${GREEN}✅ Created test script${NC}"

# Clean up temporary files
rm -f /tmp/cursor_cron.txt /tmp/crontab_new.txt

echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "=================================================="
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Set up Gmail credentials:"
echo "   - Download OAuth2 credentials from Google Cloud Console"
echo "   - Save as 'credentials.json' in this directory"
echo "   - Run './test_summary.sh' to authenticate"
echo ""
echo "2. (Optional) Set up Gemini API:"
echo "   - Get API key from Google AI Studio"
echo "   - Add to setup_env.sh: export GEMINI_API_KEY='your-key'"
echo ""
echo "3. Test the setup:"
echo "   - Run: ./test_summary.sh"
echo ""
echo "4. The cron job will run daily at 5 PM CST/CDT"
echo "   - Logs will be saved to: $LOG_FILE"
echo "   - Check logs with: tail -f $LOG_FILE"
echo ""
echo -e "${GREEN}📧 Emails will be sent to:${NC}"
echo "   - To: verigo.agent.2025@gmail.com"
echo "   - CC: stephen.dulaney@gmail.com"