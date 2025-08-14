# Vertigo Debug Toolkit

A comprehensive Flask-based debug toolkit for monitoring and optimizing the Vertigo email inbox agent using Langfuse for prompt management, performance monitoring, and cost tracking.

## 🚀 Features

### Core Functionality
- **Prompt Management System** - Create, edit, test, and optimize AI prompts
- **User Authentication** - Secure login system with admin privileges
- **Performance Monitoring** - Track prompt performance and usage metrics
- **Cost Tracking** - Monitor AI API costs and usage patterns
- **Langfuse Integration** - Advanced prompt optimization and analytics

### Pre-loaded Prompts
1. **Detailed Extraction** - Comprehensive meeting analysis with structured JSON output
2. **Executive Summary** - High-level strategic focus for leadership
3. **Daily Summary (3:00 PM)** - Professional boss update format
4. **Technical Focus** - Technical details and architecture decisions
5. **Action Oriented** - Deliverables and next steps tracking

### Admin Features
- User management and role assignment
- Prompt version control and testing
- Performance analytics dashboard
- Cost analysis and reporting

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vertigo-debug-toolkit
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database and create admin user**
   ```bash
   python setup_admin.py
   ```

6. **Run the application**
   ```bash
   PORT=8080 python app.py
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///instance/vertigo.db

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com

# Admin User
ADMIN_EMAIL=admin@vertigo.com
ADMIN_PASSWORD=admin123

# Optional: Gmail Integration
GMAIL_CREDENTIALS_FILE=path/to/credentials.json
GMAIL_TOKEN_FILE=path/to/token.json
```

### Langfuse Setup

1. Create an account at [Langfuse](https://langfuse.com)
2. Get your API keys from the dashboard
3. Configure the data region (US, EU, or HIPAA)
4. Add the keys to your `.env` file

## 📖 Usage

### Accessing the Application

1. **Start the server**: `PORT=8080 python app.py`
2. **Open browser**: Navigate to `http://localhost:8080`
3. **Login**: Use admin credentials (default: admin@vertigo.com / admin123)

### Key Pages

- **Dashboard** (`/dashboard`) - Overview of system metrics
- **Prompts** (`/prompts`) - Manage and test AI prompts
- **Performance** (`/performance`) - Monitor system performance
- **Costs** (`/costs`) - Track API usage and costs
- **Admin** (`/admin/users`) - User management (admin only)

### Testing Prompts

1. Navigate to the Prompts section
2. Select a prompt to test
3. Click "Test" to open the testing interface
4. Enter sample data (project name and content)
5. View the formatted prompt and expected output
6. Use "Load Sample Data" for quick testing

## 🏗️ Architecture

### Project Structure
```
vertigo-debug-toolkit/
├── app/                    # Main application package
│   ├── __init__.py        # Flask app factory
│   ├── auth.py            # Authentication routes
│   ├── models.py          # Database models
│   ├── blueprints/        # Feature modules
│   │   ├── dashboard/     # Dashboard functionality
│   │   ├── prompts/       # Prompt management
│   │   ├── performance/   # Performance monitoring
│   │   └── costs/         # Cost tracking
│   └── services/          # Business logic
├── templates/             # Jinja2 templates
├── static/               # CSS, JS, and assets
├── instance/             # Database and instance files
├── app.py               # Application entry point
├── requirements.txt     # Python dependencies
└── setup_admin.py       # Initial setup script
```

### Database Models

- **User** - Authentication and user management
- **Prompt** - AI prompts with versioning and metadata
- **Trace** - Langfuse trace data for analytics
- **Cost** - API usage and cost tracking

## 🔍 API Endpoints

### Health Check
- `GET /health` - Application health status

### Authentication
- `GET /login` - Login page
- `POST /login` - Authenticate user
- `GET /logout` - Logout user
- `GET /profile` - User profile

### Prompts
- `GET /prompts/` - List all prompts
- `GET /prompts/add` - Add new prompt form
- `POST /prompts/add` - Create new prompt
- `GET /prompts/<id>/edit` - Edit prompt form
- `POST /prompts/<id>/edit` - Update prompt
- `GET /prompts/<id>/test` - Test prompt interface

### Admin
- `GET /admin/users` - User management (admin only)
- `GET /admin/users/<id>/toggle` - Toggle user status

## 🐳 Docker Deployment

### Using Docker Compose

1. **Build and run**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - Web interface: `http://localhost:8080`
   - Health check: `http://localhost:8080/health`

### Manual Docker Build

```bash
docker build -t vertigo-debug-toolkit .
docker run -p 8080:8080 vertigo-debug-toolkit
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python test_setup.py
python test_langfuse_integration.py
python test_daily_summary.py
```

### Test Coverage

The application includes tests for:
- Database setup and migrations
- Langfuse integration
- Prompt functionality
- User authentication
- API endpoints

## 🔧 Development

### Adding New Prompts

1. Navigate to `/prompts/add`
2. Fill in the prompt details:
   - **Name**: Descriptive name for the prompt
   - **Version**: Version number (e.g., "1.0")
   - **Type**: Category (meeting_analysis, daily_summary, etc.)
   - **Tags**: Comma-separated tags for organization
   - **Content**: The actual prompt with placeholders

3. Use placeholders in your prompt:
   - `{project}` - Project name
   - `{transcript}` - Content to analyze

4. Ensure the prompt returns valid JSON

### Customizing Templates

Templates are located in `templates/` and use Jinja2 syntax with Tailwind CSS for styling.

### Adding New Features

1. Create a new blueprint in `app/blueprints/`
2. Add routes and templates
3. Register the blueprint in `app/__init__.py`
4. Update navigation in `templates/base.html`

## 📊 Monitoring and Analytics

### Langfuse Integration

The application integrates with Langfuse for:
- Prompt performance tracking
- Cost analysis
- Usage patterns
- A/B testing of prompts

### Performance Metrics

- Prompt usage frequency
- Response times
- Success rates
- Cost per request
- User engagement

## 🔒 Security

### Authentication
- Flask-Login for session management
- Password hashing with Werkzeug
- Admin role-based access control

### Data Protection
- Environment variables for sensitive data
- SQLite database with proper permissions
- Input validation and sanitization

## 🚨 Troubleshooting

### Common Issues

1. **Template Not Found**
   - Ensure all template files exist in `templates/`
   - Check template inheritance in `base.html`

2. **Database Errors**
   - Run `python setup_admin.py` to initialize database
   - Check file permissions on `instance/` directory

3. **Langfuse Connection Issues**
   - Verify API keys in `.env` file
   - Check data region configuration
   - Ensure network connectivity

4. **Port Already in Use**
   - Change port in environment: `PORT=8081 python app.py`
   - Or kill existing process: `lsof -ti:8080 | xargs kill`

### Debug Mode

Enable debug mode for development:
```bash
FLASK_DEBUG=true python app.py
```

## 📝 License

This project is proprietary software. All rights reserved.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review the Langfuse documentation
- Contact the development team

---

**Version**: 1.0.0  
**Last Updated**: July 2024  
**Status**: Active Development 