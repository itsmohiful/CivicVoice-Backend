# Complaint System Documentation

## Overview

The CivicVoice Complaint System is a comprehensive e-complaint platform that allows citizens to submit complaints to government departments and track their progress. The system is designed with privacy controls, engagement features, and administrative capabilities.

## Key Features

### 🎯 Core Functionality
- **Multi-category Complaints**: Support for various complaint categories (Police, Municipal, Healthcare, Education, etc.)
- **Privacy Controls**: Public, Private, and Anonymous complaint options
- **Status Tracking**: Real-time complaint status updates
- **Priority Levels**: 5 priority levels from Low to Critical
- **Location-based**: Geo-located complaints for better management

### 👥 User Features
- **Authenticated Access**: Only registered users can submit complaints
- **Personal Dashboard**: Users can view and manage their own complaints
- **Social Features**: Like, comment, share, and follow complaints
- **Notifications**: Follow complaints for updates
- **Analytics**: Personal complaint analytics for users

### 🔒 Privacy & Security
- **Privacy Levels**:
  - **Public**: Visible to everyone
  - **Private**: Only visible to owner and staff
  - **Anonymous**: Public but author identity hidden
- **Comment Controls**: Users can allow/disable comments
- **Sharing Controls**: Users can allow/disable sharing
- **Report System**: Report inappropriate content

### 📊 Administrative Features
- **Status Management**: Admins can update complaint status
- **Assignment System**: Assign complaints to specific officers
- **Escalation System**: Auto-escalation based on time limits
- **Bulk Actions**: Manage multiple complaints at once
- **Analytics Dashboard**: Comprehensive statistics and charts

## Database Schema

### Core Models

#### ComplaintCategory
- **Purpose**: Main complaint categories (Police, Municipal, etc.)
- **Key Fields**: name, description, icon, color, department_email, escalation_days
- **Features**: Hierarchical structure with subcategories

#### Complaint (Main Model)
- **Purpose**: Central complaint entity
- **Key Fields**: 
  - Basic: title, description, category, subcategory
  - Status: status, priority, assigned_to
  - Privacy: privacy, allow_comments, allow_sharing
  - Tracking: complaint_number, created_at, due_date, resolved_at
  - Analytics: view_count, reaction_count, comment_count
- **Relationships**: Many-to-One with Category, Location, User

#### ComplaintComment
- **Purpose**: User comments on complaints
- **Features**: Threaded comments, anonymous comments, official responses
- **Moderation**: Can be marked as official responses

#### ComplaintReaction
- **Purpose**: User reactions (like, support, concern, etc.)
- **Constraint**: One reaction per user per complaint
- **Types**: Like, Support, Concern, Angry, Sad

### Supporting Models

#### Location
- **Purpose**: Geographic information for complaints
- **Fields**: country, state, city, area, address, lat/lng coordinates

#### ComplaintTag
- **Purpose**: Flexible tagging system
- **Features**: Color-coded tags for better organization

#### ComplaintAttachment
- **Purpose**: File uploads (images, documents)
- **Validation**: File type and size restrictions (10MB limit)

### Engagement Models

#### ComplaintShare
- **Purpose**: Track complaint sharing
- **Analytics**: Monitor viral complaints

#### ComplaintFollower
- **Purpose**: Users following complaints for updates
- **Notifications**: Configurable notification preferences

#### ComplaintReport
- **Purpose**: Report inappropriate complaints
- **Workflow**: Admin review and resolution tracking

### Administrative Models

#### ComplaintStatusHistory
- **Purpose**: Audit trail of status changes
- **Features**: Track who changed what and when

## Status Workflow

```
DRAFT → SUBMITTED → UNDER_REVIEW → IN_PROGRESS → RESOLVED/CLOSED
                               ↓
                          PENDING_INFO
                               ↓
                          ESCALATED/REJECTED
```

### Status Descriptions

1. **DRAFT**: User is still editing
2. **SUBMITTED**: Complaint submitted and waiting for review
3. **UNDER_REVIEW**: Authority is reviewing the complaint
4. **IN_PROGRESS**: Work has started on resolving the issue
5. **PENDING_INFO**: More information needed from complainant
6. **RESOLVED**: Issue has been resolved
7. **CLOSED**: Complaint closed (with or without resolution)
8. **REJECTED**: Complaint rejected (invalid/spam)
9. **ESCALATED**: Escalated to higher authority

## Privacy System

### Public Complaints
- Visible to all users
- Appear in public listings
- Can be commented on (if enabled)
- Can be shared (if enabled)

### Private Complaints
- Only visible to:
  - Complaint owner
  - Assigned officer
  - Administrative staff
- Do not appear in public listings

### Anonymous Complaints
- Publicly visible but author identity hidden
- Shown as "Anonymous User"
- Useful for sensitive issues

## API Endpoints

### Main Views
```
GET  /complaints/                    # List all public complaints
GET  /complaints/create/             # Create new complaint form
POST /complaints/create/             # Submit new complaint
GET  /complaints/<number>/           # Complaint detail view
GET  /complaints/<number>/edit/      # Edit complaint (owner only)
POST /complaints/<number>/edit/      # Update complaint
GET  /complaints/my-complaints/      # User's own complaints
GET  /complaints/stats/              # Public statistics
```

### AJAX Endpoints
```
POST /complaints/<number>/comment/   # Add comment
POST /complaints/<number>/react/     # Toggle reaction
POST /complaints/<number>/follow/    # Follow/unfollow
POST /complaints/<number>/share/     # Track sharing
POST /complaints/<number>/report/    # Report complaint
```

### Category & Search
```
GET  /complaints/category/<id>/      # Category-specific complaints
GET  /complaints/api/search/         # Search API (AJAX)
```

## Forms

### ComplaintCreateForm
- **Purpose**: Create new complaints
- **Features**: Dynamic subcategory loading, location fields
- **Validation**: Title (10+ chars), Description (50+ chars)

### ComplaintUpdateForm
- **Purpose**: Edit existing complaints
- **Restrictions**: Only editable in DRAFT/SUBMITTED status

### ComplaintCommentForm
- **Purpose**: Add comments
- **Features**: Anonymous comment option

### ComplaintSearchForm
- **Purpose**: Search and filter complaints
- **Filters**: Category, status, priority, location, sort options

## Management Commands

### populate_complaints
```bash
python manage.py populate_complaints --users 20 --complaints 100
```
- Creates sample categories, subcategories, tags
- Generates sample users and complaints
- Adds realistic comments and reactions

## Installation & Setup

### 1. Add to INSTALLED_APPS
```python
INSTALLED_APPS = [
    # ... other apps
    'civicvoice_backend.complaints',
]
```

### 2. Include URLs
```python
# config/urls.py
urlpatterns = [
    # ... other patterns
    path("complaints/", include("civicvoice_backend.complaints.urls", namespace="complaints")),
]
```

### 3. Run Migrations
```bash
python manage.py makemigrations complaints
python manage.py migrate
```

### 4. Populate Sample Data
```bash
python manage.py populate_complaints
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

## Admin Interface

### ComplaintAdmin
- **List View**: Shows key complaint info with filters
- **Detail View**: Comprehensive complaint management
- **Actions**: Bulk status updates, escalation
- **Inlines**: Attachments, status history

### CategoryAdmin
- **Features**: Manage categories and subcategories
- **Inlines**: Subcategory management
- **Statistics**: Complaint counts per category

## Security Considerations

### Access Control
- All complaint actions require authentication
- Privacy settings are strictly enforced
- Admin-only actions are protected

### Data Validation
- File upload restrictions (type, size)
- Content length validations
- XSS protection through Django's built-in security

### Rate Limiting
- Consider implementing rate limiting for:
  - Complaint submission
  - Comment posting
  - Reaction toggling

## Performance Optimizations

### Database
- Indexes on frequently queried fields
- Select/prefetch related for list views
- Atomic operations for counters

### Caching
- Consider caching for:
  - Category lists
  - Public statistics
  - Popular complaints

### Search
- Basic search implemented
- Consider Elasticsearch for advanced search

## Customization Options

### Categories
- Easily add new complaint categories
- Configure department email/phone
- Set auto-escalation timeframes

### Status Workflow
- Modify status choices in models
- Customize workflow logic

### Privacy Levels
- Extend privacy options if needed
- Add role-based permissions

### Engagement Features
- Add new reaction types
- Extend notification system
- Add sharing platforms

## Future Enhancements

### Planned Features
1. **Real-time Notifications**: WebSocket-based updates
2. **Mobile App**: React Native mobile application
3. **Advanced Analytics**: Data visualization dashboard
4. **Integration**: Government system APIs
5. **Multilingual**: Multiple language support
6. **Geolocation**: Map-based complaint viewing
7. **AI Moderation**: Automatic content moderation
8. **Chatbot**: AI-powered complaint assistance

### Scalability
- Implement caching layer (Redis)
- Database optimization
- CDN for file uploads
- Load balancing for high traffic

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Django is installed and virtual environment is active
2. **Migration Issues**: Check model relationships and run migrations in order
3. **Permission Denied**: Verify user authentication and privacy settings
4. **File Upload Issues**: Check MEDIA_URL and file permissions

### Debug Tips
- Enable Django debug toolbar for development
- Check server logs for errors
- Use Django admin for data inspection
- Test with sample data using management commands

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to classes and methods
- Write unit tests for new features

### Development Workflow
1. Create feature branch
2. Implement changes with tests
3. Update documentation
4. Submit pull request

This complaint system provides a solid foundation for an e-governance platform with room for customization and expansion based on specific requirements.
