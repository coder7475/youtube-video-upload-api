# YouTube Video Upload API Documentation

This document provides a comprehensive overview of the YouTube Video Upload API endpoints, request/response formats, and usage examples.

## Base URL

All API endpoints are prefixed with `/api/v1/`.

## Authentication

Most endpoints require authentication using JWT tokens. Include the token in the Authorization header of your requests:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## API Endpoints

### Authentication

#### Register a new user

- **URL**: `/auth/register`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "username": "myusername",
    "password": "securepassword"
  }
  ```
- **Response**:
  ```json
  {
    "id": "uuid-string",
    "email": "user@example.com",
    "username": "myusername",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-04-13T12:00:00Z",
    "updated_at": "2025-04-13T12:00:00Z"
  }
  ```
- **Status Codes**:
  - `201 Created`: User registered successfully
  - `400 Bad Request`: Invalid input or username/email already exists

#### Login to get access token

- **URL**: `/auth/login`
- **Method**: `POST`
- **Request Body**:
  ```
  username=myusername&password=securepassword
  ```
  *(Content-Type: application/x-www-form-urlencoded)*
- **Response**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "uuid-string",
      "email": "user@example.com",
      "username": "myusername",
      "is_active": true,
      "is_superuser": false
    }
  }
  ```
- **Status Codes**:
  - `200 OK`: Login successful
  - `401 Unauthorized`: Invalid credentials

### YouTube Integration

#### Authorize YouTube Account

- **URL**: `/youtube/authorize`
- **Method**: `GET`
- **Auth Required**: Yes
- **Response**:
  ```json
  {
    "authorization_url": "https://accounts.google.com/o/oauth2/auth?..."
  }
  ```
- **Status Codes**:
  - `200 OK`: Authorization URL generated successfully

#### YouTube OAuth Callback

- **URL**: `/youtube/callback`
- **Method**: `GET`
- **Query Parameters**:
  - `code`: OAuth authorization code from Google
  - `state`: State parameter for security validation
- **Response**: Redirect to frontend with success/error message
- **Status Codes**:
  - `302 Found`: Redirect to frontend

### Video Management

#### List Videos

- **URL**: `/videos`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `skip`: Number of records to skip (default: 0)
  - `limit`: Maximum number of records to return (default: 100, max: 1000)
  - `status`: Filter by status (optional)
- **Response**:
  ```json
  [
    {
      "id": "uuid-string",
      "title": "My Video Title",
      "description": "Video description",
      "tags": "tag1,tag2,tag3",
      "category_id": "22",
      "file_path": "/path/to/video.mp4",
      "thumbnail_path": "/path/to/thumbnail.jpg",
      "scheduled_time": "2025-04-20T15:00:00Z",
      "status": "scheduled",
      "youtube_video_id": null,
      "result_message": null,
      "privacy_status": "private",
      "created_at": "2025-04-13T12:00:00Z",
      "updated_at": "2025-04-13T12:00:00Z"
    }
  ]
  ```
- **Status Codes**:
  - `200 OK`: Videos retrieved successfully

#### Get Video by ID

- **URL**: `/videos/{video_id}`
- **Method**: `GET`
- **Auth Required**: Yes
- **Path Parameters**:
  - `video_id`: ID of the video to retrieve
- **Response**: Same as a single item in the list response
- **Status Codes**:
  - `200 OK`: Video retrieved successfully
  - `404 Not Found`: Video not found

#### Create Video Schedule

- **URL**: `/videos`
- **Method**: `POST`
- **Auth Required**: Yes
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `video_file`: The video file to upload (required)
  - `title`: Video title (required, max 100 chars)
  - `description`: Video description (optional)
  - `tags`: Comma-separated tags (optional)
  - `category_id`: YouTube category ID (optional)
  - `privacy_status`: Privacy setting (private, public, unlisted, default: private)
  - `scheduled_time`: When to publish the video (ISO 8601 format, required)
- **Response**: Same as a single video item
- **Status Codes**:
  - `201 Created`: Video scheduled successfully
  - `400 Bad Request`: Invalid input
  - `401 Unauthorized`: Not authenticated
  - `403 Forbidden`: YouTube account not connected

#### Update Video Schedule

- **URL**: `/videos/{video_id}`
- **Method**: `PUT`
- **Auth Required**: Yes
- **Path Parameters**:
  - `video_id`: ID of the video to update
- **Request Body**:
  ```json
  {
    "title": "Updated Video Title",
    "description": "Updated description",
    "tags": "updated,tags",
    "category_id": "22",
    "privacy_status": "unlisted",
    "scheduled_time": "2025-04-25T15:00:00Z"
  }
  ```
- **Response**: Updated video object
- **Status Codes**:
  - `200 OK`: Video updated successfully
  - `400 Bad Request`: Invalid input or video already being processed
  - `404 Not Found`: Video not found

#### Delete Video Schedule

- **URL**: `/videos/{video_id}`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **Path Parameters**:
  - `video_id`: ID of the video to delete
- **Response**:
  ```json
  {
    "success": true,
    "message": "Video schedule deleted successfully"
  }
  ```
- **Status Codes**:
  - `200 OK`: Video deleted successfully
  - `400 Bad Request`: Cannot delete a video being processed
  - `404 Not Found`: Video not found

#### Cancel Video Schedule

- **URL**: `/videos/{video_id}/cancel`
- **Method**: `POST`
- **Auth Required**: Yes
- **Path Parameters**:
  - `video_id`: ID of the video to cancel
- **Response**: Updated video object with status set to "failed"
- **Status Codes**:
  - `200 OK`: Video canceled successfully
  - `400 Bad Request`: Cannot cancel a video with non-scheduled status
  - `404 Not Found`: Video not found

#### Upload Thumbnail

- **URL**: `/videos/{video_id}/thumbnail`
- **Method**: `POST`
- **Auth Required**: Yes
- **Content-Type**: `multipart/form-data`
- **Path Parameters**:
  - `video_id`: ID of the video
- **Form Fields**:
  - `thumbnail_file`: Image file (JPG, JPEG, or PNG)
- **Response**: Updated video object with thumbnail_path
- **Status Codes**:
  - `200 OK`: Thumbnail uploaded successfully
  - `400 Bad Request`: Invalid file format
  - `404 Not Found`: Video not found

## Error Handling

All API errors return JSON responses with the following structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Limits are:
- 60 requests per minute for authenticated endpoints
- 10 requests per minute for authentication endpoints

Exceeding these limits will result in a `429 Too Many Requests` response.

## Authentication Flow

1. Register a new user account
2. Log in to obtain an access token
3. Include the access token in subsequent requests in the Authorization header
4. For YouTube operations, first authorize your YouTube account
5. Access tokens expire after a certain time period; when this happens, you'll need to log in again

## Request Examples

### Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
           "email": "user@example.com",
           "username": "myusername",
           "password": "securepassword"
         }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=myusername&password=securepassword"
```

### Upload a Video

```bash
curl -X POST "http://localhost:8000/api/v1/videos" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -F "title=My Video Title" \
     -F "description=Video description here" \
     -F "tags=tag1,tag2,tag3" \
     -F "category_id=22" \
     -F "privacy_status=private" \
     -F "scheduled_time=2025-04-20T15:00:00Z" \
     -F "video_file=@/path/to/your/video.mp4"
```

## YouTube Category IDs

When specifying a `category_id`, use one of the following standard YouTube category IDs:

| ID | Category Name |
|----|--------------|
| 1 | Film & Animation |
| 2 | Autos & Vehicles |
| 10 | Music |
| 15 | Pets & Animals |
| 17 | Sports |
| 18 | Short Movies |
| 19 | Travel & Events |
| 20 | Gaming |
| 21 | Videoblogging |
| 22 | People & Blogs |
| 23 | Comedy |
| 24 | Entertainment |
| 25 | News & Politics |
| 26 | Howto & Style |
| 27 | Education |
| 28 | Science & Technology |
| 29 | Nonprofits & Activism |
| 30 | Movies |
| 31 | Anime/Animation |
| 32 | Action/Adventure |
| 33 | Classics |
| 34 | Comedy |
| 35 | Documentary |
| 36 | Drama |
| 37 | Family |
| 38 | Foreign |
| 39 | Horror |
| 40 | Sci-Fi/Fantasy |
| 41 | Thriller |
| 42 | Shorts |
| 43 | Shows |
| 44 | Trailers |

