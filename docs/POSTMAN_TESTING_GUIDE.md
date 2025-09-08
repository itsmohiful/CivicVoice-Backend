# Testing File Attachment API with Postman

This guide shows you how to test the CivicVoice file attachment API using Postman.

## Prerequisites

1. **Django server running**: Make sure your Django development server is running on `http://localhost:8000`
2. **Authentication token**: You'll need a valid JWT token
3. **Test files**: Prepare some test files (images, PDFs, etc.) for uploading

## Step 1: Get Authentication Token

### 1.1 Create User Account (if needed)

**Request:**
```
POST http://localhost:8000/api/auth/register/
Content-Type: application/json

{
    "email": "testuser@example.com",
    "password": "testpassword123",
    "name": "Test User"
}
```

### 1.2 Login to Get Token

**Request:**
```
POST http://localhost:8000/api/auth/login/
Content-Type: application/json

{
    "email": "testuser@example.com",
    "password": "testpassword123"
}
```

**Response:**
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "email": "testuser@example.com",
        "name": "Test User"
    }
}
```

**Save the token** - you'll need it for authenticated requests.

## Step 2: Get Available Categories

Before creating a complaint, get the available categories:

**Request:**
```
GET http://localhost:8000/api/categories/
```

**Response:**
```json
[
    {
        "id": 1,
        "name": "Municipal Services",
        "description": "Street lights, roads, parks, etc.",
        "is_active": true
    },
    {
        "id": 2,
        "name": "Police Services", 
        "description": "Crime, safety, traffic issues",
        "is_active": true
    }
]
```

## Step 3: Create Complaint with File Attachments

### 3.1 Set up Postman Request

1. **Method**: `POST`
2. **URL**: `http://localhost:8000/api/complaints/`
3. **Headers**:
   - `Authorization`: `Bearer YOUR_JWT_TOKEN_HERE`
   - `X-Request-ID`: `postman-test-123` (optional)

### 3.2 Configure Request Body

1. Go to **Body** tab in Postman
2. Select **form-data** (NOT raw JSON)
3. Add the following fields:

#### Required Fields:
| Key | Type | Value |
|-----|------|-------|
| `title` | Text | `Test Complaint from Postman` |
| `description` | Text | `This is a test complaint created from Postman to test file attachment functionality. The issue involves testing the API endpoints.` |
| `category` | Text | `1` |

#### Optional Fields:
| Key | Type | Value |
|-----|------|-------|
| `priority` | Text | `medium` |
| `privacy` | Text | `public` |
| `allow_comments` | Text | `true` |
| `allow_sharing` | Text | `true` |

#### File Attachments:
| Key | Type | Value |
|-----|------|-------|
| `attachment_files` | File | Select your first file |
| `attachment_files` | File | Select your second file |
| `attachment_files` | File | Select your third file (optional) |

**Note**: Use the same key `attachment_files` for multiple files.

### 3.3 Visual Guide for Postman Setup

```
POST http://localhost:8000/api/complaints/

Headers:
├── Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
└── X-Request-ID: postman-test-123

Body (form-data):
├── title: "Test Complaint from Postman"
├── description: "This is a test complaint created from Postman..."
├── category: "1"
├── priority: "medium"
├── privacy: "public"
├── allow_comments: "true"
├── allow_sharing: "true"
├── attachment_files: [FILE] test-image-1.jpg
├── attachment_files: [FILE] document.pdf
└── attachment_files: [FILE] test-image-2.png
```

### 3.4 Expected Success Response (201 Created)

```json
{
    "id": 123,
    "title": "Test Complaint from Postman",
    "description": "This is a test complaint created from Postman to test file attachment functionality...",
    "complaint_number": "CMP202409000001",
    "status": "draft",
    "priority": "medium",
    "privacy": "public",
    "category": 1,
    "category_name": "Municipal Services",
    "subcategory": null,
    "subcategory_name": null,
    "allow_comments": true,
    "allow_sharing": true,
    "created_by": 1,
    "created_by_name": "Test User",
    "attachments": [
        {
            "id": 1,
            "file_url": "http://localhost:8000/media/complaints/attachments/2024/09/test-image-1.jpg",
            "original_name": "test-image-1.jpg",
            "file_size": 245760,
            "file_type": "image/jpeg",
            "description": null,
            "created_at": "2024-09-08T15:30:00Z"
        },
        {
            "id": 2,
            "file_url": "http://localhost:8000/media/complaints/attachments/2024/09/document.pdf", 
            "original_name": "document.pdf",
            "file_size": 1048576,
            "file_type": "application/pdf",
            "description": null,
            "created_at": "2024-09-08T15:30:01Z"
        },
        {
            "id": 3,
            "file_url": "http://localhost:8000/media/complaints/attachments/2024/09/test-image-2.png",
            "original_name": "test-image-2.png", 
            "file_size": 512000,
            "file_type": "image/png",
            "description": null,
            "created_at": "2024-09-08T15:30:02Z"
        }
    ],
    "created_at": "2024-09-08T15:30:00Z",
    "updated_at": "2024-09-08T15:30:00Z"
}
```

## Step 4: Test File Download

Copy any `file_url` from the response and test downloading:

**Request:**
```
GET http://localhost:8000/media/complaints/attachments/2024/09/test-image-1.jpg
```

This should download or display the uploaded file.

## Step 5: Get Complaint Details

Verify the complaint was created with attachments:

**Request:**
```
GET http://localhost:8000/api/complaints/{complaint_id}/
Authorization: Bearer YOUR_JWT_TOKEN_HERE
```

## Step 6: Test Error Scenarios

### 6.1 Test File Size Limit (>10MB)

Try uploading a file larger than 10MB to test validation:

**Expected Response (400 Bad Request):**
```json
{
    "attachment_files": [
        "File 'large-file.mp4' exceeds 10MB limit"
    ]
}
```

### 6.2 Test Too Many Files (>10 files)

Try uploading more than 10 files:

**Expected Response (400 Bad Request):**
```json
{
    "attachment_files": [
        "Maximum 10 files allowed per complaint"
    ]
}
```

### 6.3 Test Missing Required Fields

Try creating complaint without title or description:

**Expected Response (400 Bad Request):**
```json
{
    "title": ["This field is required."],
    "description": ["This field is required."]
}
```

### 6.4 Test Invalid Authentication

Try without Authorization header:

**Expected Response (401 Unauthorized):**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

## Step 7: Advanced Testing

### 7.1 Add Additional Attachments to Existing Complaint

**Request:**
```
POST http://localhost:8000/api/attachments/
Authorization: Bearer YOUR_JWT_TOKEN_HERE
Content-Type: multipart/form-data

Body (form-data):
├── complaint: "123"
├── file: [FILE] additional-document.pdf
└── description: "Additional evidence" (optional)
```

### 7.2 List All Complaints

**Request:**
```
GET http://localhost:8000/api/complaints/
Authorization: Bearer YOUR_JWT_TOKEN_HERE
```

### 7.3 Get User's Own Complaints

**Request:**
```
GET http://localhost:8000/api/complaints/my_complaints/
Authorization: Bearer YOUR_JWT_TOKEN_HERE
```

## Common Issues & Solutions

### Issue 1: "Authentication credentials were not provided"
**Solution**: Make sure you have the Authorization header with "Bearer " prefix:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Issue 2: "CORS policy" error
**Solution**: This shouldn't happen in Postman, but if it does, make sure Django server is running and CORS is configured properly.

### Issue 3: Files not uploading
**Solution**: 
- Make sure you're using **form-data** not **raw** in Postman body
- Select **File** type for attachment_files fields
- Use the same key name `attachment_files` for multiple files

### Issue 4: "Category not found" error
**Solution**: 
- First get available categories with `GET /api/categories/`
- Use a valid category ID in your request

### Issue 5: File size validation error
**Solution**: 
- Check file sizes are under 10MB each
- Check total size is under 50MB
- Use smaller test files if needed

## Postman Collection Export

You can create a Postman collection with these requests:

1. **Auth** folder:
   - Register User
   - Login User

2. **Categories** folder:
   - Get Categories
   - Get Subcategories

3. **Complaints** folder:
   - Create Complaint (no files)
   - Create Complaint (with files)
   - Get Complaint Details
   - List Complaints
   - My Complaints

4. **Attachments** folder:
   - Add Additional Attachment
   - List Attachments

5. **Error Testing** folder:
   - File Too Large
   - Too Many Files
   - Missing Auth
   - Invalid Data

## Environment Variables

Set up Postman environment variables:

- `baseUrl`: `http://localhost:8000`
- `authToken`: `{{token}}` (set after login)
- `complaintId`: `{{complaint_id}}` (set after creating complaint)

This allows you to use `{{baseUrl}}/api/complaints/` instead of full URLs.
