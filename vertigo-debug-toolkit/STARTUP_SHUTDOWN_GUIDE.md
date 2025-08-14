# Vertigo Debug Toolkit - Startup & Shutdown Guide

## Directory Structure
```
/Users/stephendulaney/Documents/Vertigo/
├── .venv/                          # Virtual environment
├── vertigo-debug-toolkit/          # Flask application
│   ├── app.py                      # Main Flask app
│   ├── requirements.txt            # Python dependencies
│   └── ...
└── vertigo/                        # Google Cloud Functions
    └── functions/
        └── email-processor/
            ├── main.py
            └── generate_oauth_token.py
```

## Proper Startup Process

### 1. Navigate to the Correct Directory
```bash
cd /Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit
```

### 2. Activate Virtual Environment
**For Fish Shell:**
```bash
source /Users/stephendulaney/Documents/Vertigo/.venv/bin/activate.fish
```

**For Bash/Zsh:**
```bash
source /Users/stephendulaney/Documents/Vertigo/.venv/bin/activate
```

### 3. Verify You're in the Right Place
```bash
pwd
# Should show: /Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit

ls app.py
# Should show: app.py
```

### 4. Start the Flask Application
```bash
python app.py --port 8080 --debug
```

### 5. Verify It's Running
- Open browser to: http://localhost:8080
- Check terminal for any error messages
- Look for: "Running on http://0.0.0.0:8080"

## Proper Shutdown Process

### 1. Stop the Flask Application
**Option A: Ctrl+C in the terminal running Flask**
```bash
# In the terminal where Flask is running
Ctrl+C
```

**Option B: Kill the process**
```bash
# Find the process
lsof -i :8080

# Kill it (replace PID with actual process ID)
kill -9 <PID>
```

### 2. Deactivate Virtual Environment
```bash
deactivate
```

### 3. Verify Clean Shutdown
```bash
lsof -i :8080
# Should show no processes using port 8080
```

## Troubleshooting Common Issues

### Issue: "No such file or directory"
**Problem:** You're in the wrong directory
**Solution:**
```bash
cd /Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit
pwd  # Verify you're in the right place
ls app.py  # Verify the file exists
```

### Issue: "Port already in use"
**Problem:** Another process is using port 8080
**Solution:**
```bash
# Find what's using the port
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or use a different port
python app.py --port 8081 --debug
```

### Issue: "Module not found"
**Problem:** Virtual environment not activated or packages not installed
**Solution:**
```bash
# Activate virtual environment
source /Users/stephendulaney/Documents/Vertigo/.venv/bin/activate.fish

# Install packages if needed
pip install -r requirements.txt
```

### Issue: "activate.fish not found"
**Problem:** Using wrong shell or wrong path
**Solution:**
```bash
# Check your shell
echo $SHELL

# For Fish shell:
source /Users/stephendulaney/Documents/Vertigo/.venv/bin/activate.fish

# For Bash/Zsh:
source /Users/stephendulaney/Documents/Vertigo/.venv/bin/activate
```

## Quick Commands Reference

### Start Vertigo Debug Toolkit
```bash
cd /Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit
source /Users/stephendulaney/Documents/Vertigo/.venv/bin/activate.fish
python app.py --port 8080 --debug
```

### Stop Vertigo Debug Toolkit
```bash
# In the Flask terminal: Ctrl+C
# Or kill the process:
lsof -i :8080
kill -9 <PID>
deactivate
```

### Check Status
```bash
# Check if Flask is running
lsof -i :8080

# Check current directory
pwd

# Check if virtual environment is active
echo $VIRTUAL_ENV
```

## Environment Variables
The virtual environment activation sets:
- `VIRTUAL_ENV`: Path to the virtual environment
- `PATH`: Includes the virtual environment's bin directory
- `PYTHONPATH`: Includes the virtual environment's site-packages

## Access URLs
- **Main Dashboard**: http://localhost:8080
- **Prompts**: http://localhost:8080/prompts
- **Performance**: http://localhost:8080/performance
- **Costs**: http://localhost:8080/costs 