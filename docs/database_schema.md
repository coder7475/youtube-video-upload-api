# Database Schema Documentation

This document describes the database schema used by the YouTube Video Upload API.

## Overview

The application uses SQLAlchemy ORM with a relational database backend. The default configuration uses SQLite, but it can be configured to use PostgreSQL or other database engines supported by SQLAlchemy.

## Base Model

All models inherit from a `BaseModel` class that provides common fields:

- `id`: UUID primary key
- `created_at`: Timestamp when the record was created
- `updated_at`: Timestamp when the record was last updated

## User Model

The `User` model stores authentication and YouTube integration data.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| `id` | UUID | Primary key | Not null |
| `email` | String(255) | User's email address | Unique, not null, indexed |
| `username` | String(50) | User's username | Unique, not null, indexed |
| `hashed_password` | String(255) | Bcrypt-hashed password | Not null |
| `is_active` | Boolean | Whether user account is active | Default: true, not null |
| `is_superuser` | Boolean | Whether user has admin privileges | Default: false, not null |
| `youtube_token` | String(2048) | OAuth access token for YouTube API | Nullable |
| `youtube_refresh_token` | String(255) | OAuth refresh token for YouTube API | Nullable |
| `youtube_token_expiry` | String(50) | Expiration timestamp for access token | Nullable |
| `created_at` | DateTime | When the user was created | Not null |
| `updated_at` | DateTime | When the user was last updated | Not null |

### Relationships

- `videos`: One-to-many relationship with `VideoSchedule` model (cascade delete)

## Video Schedule Model

The `VideoSchedule` model stores information about scheduled video uploads.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| `id` | UUID | Primary key | Not null |
| `user_id` | UUID | Foreign key to User model | Not null, references User.id with cascade delete |
| `title` | String(100) | Video title | Not null |
| `description` | Text | Video description | Nullable |
| `tags` | String(500) | Comma-separated video tags | Nullable |
| `category_id` | String(50) | YouTube category ID | Nullable |
| `file_path` | String(1024) | Path to the uploaded video file | Not null |
| `thumbnail_path` | String(1024) | Path to the uploaded thumbnail image | Nullable |
| `scheduled_time` | DateTime | When to publish the video | Not null |
| `status` | String(20) | Current status of the video upload | Default: "scheduled", not null |
| `youtube_video_id` | String(50) | ID of the uploaded YouTube video | Nullable |
| `result_message` | Text | Error or success details | Nullable |
| `privacy_status` | String(20) | YouTube privacy setting | Default: "private", not null |
| `created_at` | DateTime | When the schedule was created | Not null |
| `updated_at` | DateTime | When the schedule was last updated | Not null |

### Video Status Enum

The `status` column can have the following values:

- `scheduled`: Video is scheduled for future upload
- `pending`: Video is queued for upload
- `processing`: Video is currently being uploaded
- `uploaded`: Video was successfully uploaded
- `failed`: Video upload failed

### Relationships

- `user`: Many-to-one relationship with the `User` model

## Database Migrations

The application uses Alembic for database migrations. Migration files are stored in the `migrations` directory.

## Entity Relationship Diagram

```
+----------------+       +--------------------+
|     User       |       |   VideoSchedule    |
+----------------+       +--------------------+
| id             |       | id                 |
| email          |       | user_id          ----------> User.id
| username       |       | title              |
| hashed_password|       | description        |
| is_active      |       | tags               |
| is_superuser   |       | category_id        |
| youtube_token  |       | file_path           |
| youtube_refresh_token | | thumbnail_path      |
| youtube_token_expiry | | scheduled_time      |
| created_at     |       | status              |
| updated_at     |       | youtube_video_id    |
+----------------+       | result_message      |
                         | privacy_status      |
                         | created_at          |
                         | updated_at          |
                        +--------------------+
```

## Indexing Strategy

The following indexes are created:
- `user.email`: For fast user lookup by email
- `user.username`: For fast user lookup by username

Additional indexes may be added for performance optimization based on query patterns.

## Constraints

- Foreign key constraints ensure referential integrity
- Unique constraints prevent duplicate usernames and emails
- NOT NULL constraints ensure required fields are provided
