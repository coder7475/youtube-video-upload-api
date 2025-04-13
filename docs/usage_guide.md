# YouTube Video Upload API - Detailed Usage Guide

This guide provides step-by-step instructions for using the YouTube Video Upload API to automate and schedule your YouTube video uploads.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Setting Up YouTube Integration](#setting-up-youtube-integration)
3. [Managing Video Uploads](#managing-video-uploads)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)

## Getting Started

### Creating an Account

Before you can use the API, you need to create an account:

1. Send a POST request to the registration endpoint:

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

The response will include the details of your scheduled video:

```json
{
  "id": "video-uuid",
  "title": "My Video Title",
  "description": "Video description here",
  "tags": "tag1,tag2,tag3",
  "category_id": "22",
  "file_path": "/path/to/stored/video.mp4",
  "scheduled_time": "2025-04-20T15:00:00Z",
  "status": "scheduled",
  "privacy_status": "private",
  "created_at": "2025-04-13T12:00:00Z",
  "updated_at": "2025-04-13T12:00:00Z"
}
```

### Listing Your Videos

To see all your scheduled videos:

```bash
curl -X GET "http://localhost:8000/api/v1/videos" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

You can filter by status:

```bash
curl -X GET "http://localhost:8000/api/v1/videos?status=scheduled" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Updating a Video

To modify a scheduled video:

```bash
curl -X PUT "http://localhost:8000/api/v1/videos/VIDEO_ID" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Updated Title",
       "description": "Updated description",
       "scheduled_time": "2025-04-25T18:00:00Z",
       "privacy_status": "unlisted"
     }'
```

### Adding a Thumbnail

To add a custom thumbnail:

```bash
curl -X POST "http://localhost:8000/api/v1/videos/VIDEO_ID/thumbnail" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -F "thumbnail_file=@/path/to/thumbnail.jpg"
```

### Canceling a Scheduled Upload

If you need to cancel a scheduled upload:

```bash
curl -X POST "http://localhost:8000/api/v1/videos/VIDEO_ID/cancel" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Deleting a Video Schedule

To completely remove a video schedule:

```bash
curl -X DELETE "http://localhost:8000/api/v1/videos/VIDEO_ID" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Best Practices

1. **Plan Your Uploads**: Schedule videos well in advance to ensure they're processed before their publication time.

2. **Optimize Video Files**: Compress videos before uploading to improve upload speed and reduce storage usage.

3. **Use Meaningful Titles**: Give your videos descriptive titles for better organization.

4. **Monitor Upload Status**: Regularly check the status of your scheduled uploads.

5. **Handle Errors Appropriately**: If an upload fails, check the result_message for details on what went wrong.

6. **Limit Concurrent Uploads**: Avoid scheduling too many videos to upload at the exact same time.

7. **Respect YouTube Quotas**: Be aware of YouTube API quotas and limits to avoid restrictions.

## Troubleshooting

### Common Issues

#### Authentication Problems

- **Issue**: Getting 401 Unauthorized errors
- **Solution**: Your token may have expired. Try logging in again to get a fresh token.

#### YouTube Connection Issues

- **Issue**: Unable to connect to YouTube account
- **Solution**: Check that your Google account has the necessary permissions and that the YouTube API is enabled.

#### Failed Uploads

- **Issue**: Videos stay in "failed" status
- **Solution**: Check the result_message field for specific error details. Common issues include:
  - Video file format not supported
  - Title too long or contains invalid characters
  - Insufficient YouTube API quota

#### Video Processing Stuck

- **Issue**: Video stays in "processing" status
- **Solution**: This could indicate an issue with the background worker. Check Celery logs and ensure the Celery worker and Redis are running properly.

### Getting Help

If you encounter issues not covered in this guide, you can:

1. Check the application logs for detailed error messages
2. Review the [YouTube API documentation](https://developers.google.com/youtube/v3/docs)
3. Contact the API administrator for assistance
     -H "Content-Type: application/json" \
     -d '{"email": "your-email@example.com", "username": "yourusername", "password": "your-secure-password"}'
```

2. Note the response, which includes your user ID and other details.

### Logging In

To authenticate with the API, you need to obtain an access token:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=yourusername&password=your-secure-password"
```

The response will include an `access_token` that you'll use for all subsequent requests:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user-uuid",
    "email": "your-email@example.com",
    "username": "yourusername",
    "is_active": true,
    "is_superuser": false
  }
}
```

### Using the Access Token

Include the access token in the Authorization header of all your API requests:

```bash
curl -X GET "http://localhost:8000/api/v1/videos" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Setting Up YouTube Integration

Before you can schedule video uploads, you need to connect your YouTube account:

### 1. Authorize with YouTube

Request an authorization URL:

```bash
curl -X GET "http://localhost:8000/api/v1/youtube/authorize" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

The response will include an authorization URL:

```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

### 2. Complete OAuth Flow

1. Open the authorization URL in your browser
2. Sign in to your Google account
3. Grant the requested permissions to the application
4. You'll be redirected to the callback URL with a success message

Once this process is complete, your YouTube account is connected to the API and you can start scheduling video uploads.

## Managing Video Uploads

### Scheduling a Video Upload

To schedule a video upload, use the following request:

```bash
curl -X POST "http://localhost:8000/api/v1/videos

