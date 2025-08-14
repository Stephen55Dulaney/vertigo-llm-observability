# Vertigo Debug Toolkit - Deployment Guide

## Directory and Environment Setup

### Working Directory
**MUST run from**: `/Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit/`

```bash
cd /Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit/
```

### Virtual Environment
**MUST activate virtual environment first**:

```bash
# Activate the virtual environment
source venv/bin/activate

# Verify you're in the correct venv (should show vertigo-debug-toolkit path)
which python
```

### Starting the Application
**Exact command that works**:

```bash
python app.py --port 8080 --debug
```

## Complete Startup Sequence

```bash
# 1. Navigate to correct directory
cd /Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit/

# 2. Activate virtual environment  
source venv/bin/activate

# 3. Start the application
python app.py --port 8080 --debug
```

## Access Information

- **URL**: http://127.0.0.1:8080
- **Login**: admin@vertigo.com
- **Password**: SecureTest123!

## Environment Requirements

- Python virtual environment located at: `venv/`
- Dependencies installed via: `pip install -r requirements.txt`
- Database: SQLite (auto-created in `instance/`)
- Configuration: `.env` file with secure settings

## Troubleshooting

### If app won't start:
1. Verify you're in `/Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit/`
2. Ensure virtual environment is activated: `source venv/bin/activate`
3. Check dependencies are installed: `pip install -r requirements.txt`
4. Kill any existing processes: `pkill -f "python app.py"`

### If port 8080 is busy:
- Try a different port: `python app.py --port 8081 --debug`
- Or kill existing processes and retry

## Notes from Cursor Setup
- This configuration was confirmed working with Cursor IDE
- The virtual environment and directory location are critical
- Must use `--port 8080 --debug` flags for proper operation
- Database and admin user are pre-configured and ready

## Security Features Active
- ✅ CSRF Protection
- ✅ Strong Password Policy  
- ✅ Input Validation & XSS Prevention
- ✅ Secure Session Configuration
- ✅ All vulnerabilities patched by agent team

## Agent Framework Available
- Thomas debugging agent ready for systematic testing
- Specialist agents (Spec, Custodia, Forge, Hue, Probe) available
- Bug triage and resolution system operational