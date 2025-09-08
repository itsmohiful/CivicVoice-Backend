# File Attachment API Documentation

## Creating a Complaint with Attachments

The CivicVoice API now supports uploading multiple files when creating a complaint. Here's how to use it:

### API Endpoint
```
POST /api/complaints/
```

### Authentication
Include JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Content Type
Use `multipart/form-data` for file uploads:
```
Content-Type: multipart/form-data
```

### Request Parameters

#### Required Fields
- `title` (string): Complaint title (min 10 characters)
- `description` (string): Detailed description (min 50 characters) 
- `category` (integer): Category ID from `/api/categories/`

#### Optional Fields
- `subcategory` (integer): Subcategory ID
- `priority` (string): One of: `low`, `medium`, `high`, `urgent`, `critical`
- `privacy` (string): One of: `public`, `private`, `anonymous`
- `allow_comments` (boolean): Allow comments on complaint
- `allow_sharing` (boolean): Allow sharing of complaint
- `incident_date` (datetime): When the incident occurred
- `location` (integer): Location ID from `/api/locations/`
- `tags` (array): Array of tag IDs
- `reference_number` (string): External reference number

#### File Attachment Fields
- `attachment_files` (array of files): List of files to upload (max 10 files, optional)

### File Constraints
- **Maximum files per complaint**: 10
- **Maximum file size**: 10MB per file
- **Maximum total size**: 50MB per complaint
- **Supported formats**: All file types (images, PDFs, documents, etc.)
- **Descriptions**: Not required - files will use their original filenames

### Example Usage

#### JavaScript (Fetch API)
```javascript
const formData = new FormData();

// Required fields
formData.append('title', 'Broken streetlight on Main Street');
formData.append('description', 'The streetlight has been broken for 3 days causing safety concerns for pedestrians');
formData.append('category', '1'); // Municipal Services category

// Optional fields
formData.append('priority', 'high');
formData.append('privacy', 'public');
formData.append('allow_comments', 'true');

// File attachments - just add the files
const fileInput = document.getElementById('fileInput');
const files = fileInput.files;

for (let i = 0; i < files.length; i++) {
    formData.append('attachment_files', files[i]);
}

// Make the request
fetch('/api/complaints/', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + token,
        'X-Request-ID': 'complaint-create-' + Date.now()
    },
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Complaint created:', data);
    // data.attachments will contain the uploaded files
})
.catch(error => {
    console.error('Error:', error);
});
```

#### Python (requests)
```python
import requests

url = 'http://localhost:8000/api/complaints/'
headers = {
    'Authorization': 'Bearer ' + token,
    'X-Request-ID': 'complaint-create-123'
}

# Prepare the data
data = {
    'title': 'Pothole on Highway 101',
    'description': 'Large pothole causing damage to vehicles. Located near mile marker 15.',
    'category': 2,  # Road Maintenance category
    'priority': 'urgent',
    'privacy': 'public'
}

# Prepare files - simple approach
files = [
    ('attachment_files', open('pothole_photo1.jpg', 'rb')),
    ('attachment_files', open('pothole_photo2.jpg', 'rb'))
]

response = requests.post(url, headers=headers, data=data, files=files)

# Close the files
for _, file_obj in files:
    file_obj.close()

if response.status_code == 201:
    complaint = response.json()
    print(f"Complaint created: {complaint['complaint_number']}")
    print(f"Attachments uploaded: {len(complaint['attachments'])}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

#### cURL Example
```bash
curl -X POST http://localhost:8000/api/complaints/ \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "X-Request-ID: complaint-create-$(date +%s)" \\
  -F "title=Noise complaint from construction" \\
  -F "description=Excessive noise from construction site starting at 5 AM daily" \\
  -F "category=3" \\
  -F "priority=medium" \\
  -F "privacy=public" \\
  -F "attachment_files=@noise_recording.mp3" \\
  -F "attachment_files=@construction_photo.jpg"
```

### Response Format

#### Success Response (201 Created)
```json
{
    "id": 123,
    "title": "Broken streetlight on Main Street",
    "description": "The streetlight has been broken for 3 days...",
    "complaint_number": "CMP202409000001",
    "status": "draft",
    "priority": "high",
    "privacy": "public",
    "category": 1,
    "category_name": "Municipal Services",
    "created_by": 456,
    "created_by_name": "John Doe",
    "attachments": [
        {
            "id": 789,
            "file_url": "http://localhost:8000/media/complaints/attachments/2024/09/photo1.jpg",
            "original_name": "streetlight_photo1.jpg",
            "file_size": 2048576,
            "file_type": "image/jpeg",
            "description": null,
            "created_at": "2024-09-08T10:30:00Z"
        },
        {
            "id": 790,
            "file_url": "http://localhost:8000/media/complaints/attachments/2024/09/photo2.jpg",
            "original_name": "streetlight_photo2.jpg", 
            "file_size": 1876543,
            "file_type": "image/jpeg",
            "description": null,
            "created_at": "2024-09-08T10:30:01Z"
        }
    ],
    "created_at": "2024-09-08T10:30:00Z",
    "updated_at": "2024-09-08T10:30:00Z"
}
```

#### Error Response (400 Bad Request)
```json
{
    "attachment_files": [
        "File 'large_video.mp4' exceeds 10MB limit"
    ],
    "title": [
        "This field is required."
    ]
}
```

### Managing Attachments After Creation

#### Add More Attachments
You can add more attachments to an existing complaint using the attachment endpoint:

```
POST /api/attachments/
```

```json
{
    "complaint": 123,
    "file": "<file_upload>",
    "description": "Additional evidence photo"  // Optional
}
```

#### List Complaint Attachments
```
GET /api/complaints/{id}/
```
The response includes all attachments in the `attachments` field.

#### Download Attachment
Use the `file_url` from the attachment object:
```
GET {attachment.file_url}
```

### Error Handling

Common error scenarios:

1. **File too large**: Individual files > 10MB
2. **Too many files**: More than 10 files per complaint
3. **Total size exceeded**: Combined files > 50MB
4. **Invalid file**: Corrupted or unreadable files
5. **Missing required fields**: Title, description, or category not provided
6. **Authentication required**: Missing or invalid JWT token

### Best Practices

1. **Compress images** before uploading to stay under size limits
2. **Use descriptive filenames** and descriptions for better organization
3. **Check file sizes** client-side before uploading
4. **Handle upload progress** for better user experience
5. **Validate file types** based on your requirements
6. **Show upload status** and error messages to users

### Security Considerations

- Files are stored securely on the server
- File content is validated on upload
- Only authenticated users can upload attachments
- File URLs include domain for absolute access
- Consider implementing virus scanning for production use
