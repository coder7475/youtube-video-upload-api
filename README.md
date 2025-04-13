# YouTube Video Upload Scheduler API

A FastAPI-based application that allows users to schedule and automate YouTube video uploads. This API enables content creators to prepare their videos in advance and have them published at specific times without manual intervention.

## Documentation

Comprehensive documentation for this project is available:

- [API Documentation](docs/api_documentation.md) - Detailed information about API endpoints, request/response formats
- [Database Schema](docs/database_schema.md) - Complete database structure and relationship details
- [Usage Guide](docs/usage_guide.md) - Step-by-step instructions for using the API

## Features

- **User Authentication**: Secure JWT-based authentication system
- **YouTube OAuth Integration**: Secure connection to users' YouTube accounts
- **Scheduled Uploads**: Schedule videos to be uploaded at specific times
- **File Management**: Upload and store video files until their publish time
- **Automatic Publishing**: Background tasks automatically publish videos at scheduled times
- **Error Handling**: Robust error handling and retry mechanisms
- **API Documentation**: Comprehensive API documentation with Swagger UI

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Celery**: Distributed task queue for handling background operations
- **Redis**: Message broker for Celery
- **Google API Client**: For YouTube API integration
- **JWT Authentication**: For secure user authentication
- **Pydantic**: Data validation and settings management

## Setup Instructions

### Prerequisites

- Python 3.8+
- Redis server
- Google Developer Account with YouTube Data API v3 enabled
- OAuth 2.0 credentials from Google Cloud Console

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/youtube-video-upload-fastapi.git
   cd youtube-video-upload-fastapi
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**

   Copy the example environment file and update it with your credentials:

   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file and fill in your:
   - Google API credentials (client ID and secret)
   - Database connection string
   - Secret key for JWT
   - Redis URL
   
5. **Set up Google API credentials**

   a. Go to [Google Cloud Console](https://console.cloud.google.com/)
   
   b. Create a new project or select an existing one
   
   c. Enable the YouTube Data API v3
   
   d. Create OAuth 2.0 credentials (Web application type)
   
   e. Add the redirect URI: `http://localhost:8000/api/v1/youtube/callback`
   
   f. Download the credentials as JSON and save as `.client_secrets.json` in the project root

6. **Initialize the database**

   Run the database migration to create the tables:

   ```bash
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

### Running the Application

1. **Start the FastAPI server**

   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at http://localhost:8000

2. **Start the Celery worker**

   In a separate terminal:

   ```bash
   celery -A app.worker worker --loglevel=info
   ```

3. **Start the Celery beat scheduler**

   In another terminal:

   ```bash
   celery -A app.worker beat --loglevel=info
   ```

## API Documentation

Once the application is running, you can access the interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Using the API

### 1. Register a new user

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "username": "myusername", "password": "securepassword"}'
```

### 2. Login to get access token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=myusername&password=securepassword"
```

### 3. Connect to YouTube account

Visit the authorization URL to allow the application to access your YouTube account:

```bash
curl -X GET "http://localhost:8000/api/v1/youtube/authorize" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Follow the URL returned in the response to authorize the application. You'll be redirected back to the callback URL.

### 4. Schedule a video upload

```bash
curl -X POST "http://localhost:8000/api/v1/videos" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -F "title=My Video Title" \
     -F "description=Video description here" \
     -F "scheduled_time=2025-04-20T15:00:00Z" \
     -F "privacy_status=private" \
     -F "video_file=@/path/to/your/video.mp4"
```

### 5. List scheduled videos

```bash
curl -X GET "http://localhost:8000/api/v1/videos" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Deployment

For production deployment:

1. Use a production-ready database like PostgreSQL
2. Set up proper environment variables for production
3. Use a process manager like Supervisord to manage FastAPI and Celery processes
4. Consider containerizing with Docker for easier deployment
5. Set up proper logging and monitoring

## Troubleshooting

### Common Issues

- **YouTube API Quota**: The YouTube API has daily quota limits. Check the quota usage in Google Cloud Console if uploads start failing.
- **Authentication Errors**: Ensure your Google API credentials are correct and have the necessary scopes.
- **Database Connections**: If using SQLite in a multi-process environment, you might encounter database locking issues.
- **Redis Connection**: Ensure Redis is running and accessible at the URL specified in your environment.

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

