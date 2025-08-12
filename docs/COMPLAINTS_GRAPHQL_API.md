# CivicVoice Complaints System - GraphQL API Documentation

## Overview

The CivicVoice Complaints System provides a comprehensive GraphQL API for managing citizen complaints, government responses, and community engagement. This system allows authenticated users to submit complaints, track their progress, and interact with other community members.

## Key Features

### 🏛️ **Complaint Management**
- Create, update, and submit complaints
- Categorize complaints by department/service
- Track complaint status and resolution
- Support for attachments and location data
- Privacy controls (Public, Private, Anonymous)

### 👥 **User Interactions**
- Comment on complaints
- React to complaints (like, support, concern, etc.)
- Follow complaints for updates
- Share complaints with community
- Report inappropriate content

### 📊 **Analytics & Tracking**
- View counts and engagement metrics
- Status history tracking
- Resolution time analytics
- Category-wise statistics

### 🔐 **Privacy & Security**
- Role-based access control
- Anonymous complaint submission
- Content moderation and reporting
- Secure file uploads

## GraphQL Schema Structure

### Main Object Types

#### ComplaintObjectType
```graphql
type Complaint {
  id: ID!
  title: String!
  description: String!
  complaintNumber: String!
  status: String!
  priority: String!
  privacy: String!
  category: ComplaintCategory!
  subcategory: ComplaintSubCategory
  location: Location
  tags: [ComplaintTag!]
  allowComments: Boolean!
  allowSharing: Boolean!
  incidentDate: DateTime
  submittedAt: DateTime
  dueDate: DateTime
  resolvedAt: DateTime
  viewCount: Int!
  reactionCount: Int!
  commentCount: Int!
  shareCount: Int!
  createdBy: User!
  assignedTo: User
  referenceNumber: String
  escalatedFrom: Complaint
  escalationReason: String
  createdAt: DateTime!
  updatedAt: DateTime!
  
  # Computed fields
  canEdit: Boolean!
  canView: Boolean!
  isFollowing: Boolean!
  userReaction: ComplaintReaction
  reactionCounts: JSONString!
  isOverdue: Boolean!
  
  # Related data
  comments(first: Int, after: String): ComplaintCommentConnection!
  attachments(first: Int, after: String): ComplaintAttachmentConnection!
  reactions(first: Int, after: String): ComplaintReactionConnection!
  statusHistory(first: Int, after: String): ComplaintStatusHistoryConnection!
}
```

#### ComplaintCategoryObjectType
```graphql
type ComplaintCategory {
  id: ID!
  name: String!
  description: String!
  icon: String!
  color: String!
  isActive: Boolean!
  sortOrder: Int!
  departmentEmail: String
  departmentPhone: String
  escalationDays: Int!
  complaintCount: Int!
  subcategories: [ComplaintSubCategory!]!
}
```

#### ComplaintCommentObjectType
```graphql
type ComplaintComment {
  id: ID!
  content: String!
  isOfficial: Boolean!
  isAnonymous: Boolean!
  createdBy: User
  parent: ComplaintComment
  createdAt: DateTime!
  updatedAt: DateTime!
  authorName: String!
  repliesCount: Int!
  replies: [ComplaintComment!]!
  reactions: [ComplaintCommentReaction!]!
}
```

## Main Queries

### Public Queries (No Authentication Required)

```graphql
# Get all public complaints with filtering
query GetComplaints($first: Int, $after: String, $search: String, $category: ID) {
  complaints(first: $first, after: $after, search: $search, category: $category) {
    edges {
      node {
        id
        title
        complaintNumber
        status
        priority
        category {
          name
          color
        }
        location {
          city
          state
        }
        createdAt
        viewCount
        reactionCount
        commentCount
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}

# Get complaint details
query GetComplaint($complaintNumber: String!) {
  complaint(complaintNumber: $complaintNumber) {
    id
    title
    description
    status
    priority
    privacy
    category {
      name
      color
    }
    location {
      city
      state
      country
    }
    tags {
      name
      color
    }
    createdBy {
      name
    }
    createdAt
    viewCount
    reactionCount
    commentCount
    reactionCounts
    comments(first: 10) {
      edges {
        node {
          id
          content
          authorName
          isOfficial
          createdAt
        }
      }
    }
  }
}

# Get complaint categories
query GetCategories {
  complaintCategories {
    edges {
      node {
        id
        name
        description
        icon
        color
        complaintCount
        subcategories {
          id
          name
        }
      }
    }
  }
}

# Search complaints
query SearchComplaints($query: String!, $limit: Int) {
  searchComplaints(query: $query, limit: $limit) {
    id
    title
    complaintNumber
    status
    category {
      name
    }
  }
}
```

### Authenticated User Queries

```graphql
# Get user's own complaints
query GetMyComplaints($first: Int, $after: String) {
  myComplaints(first: $first, after: $after) {
    edges {
      node {
        id
        title
        complaintNumber
        status
        priority
        privacy
        canEdit
        createdAt
        viewCount
        reactionCount
        commentCount
      }
    }
  }
}

# Get followed complaints
query GetFollowedComplaints($first: Int, $after: String) {
  myFollowedComplaints(first: $first, after: $after) {
    edges {
      node {
        id
        title
        complaintNumber
        status
        category {
          name
        }
        createdAt
      }
    }
  }
}
```

### Admin Queries

```graphql
# Get reported complaints
query GetReportedComplaints($first: Int, $after: String) {
  reportedComplaints(first: $first, after: $after) {
    edges {
      node {
        id
        reason
        description
        complaint {
          complaintNumber
          title
        }
        reportedBy {
          name
          email
        }
        createdAt
      }
    }
  }
}

# Get overdue complaints
query GetOverdueComplaints($first: Int, $after: String) {
  overdueComplaints(first: $first, after: $after) {
    edges {
      node {
        id
        complaintNumber
        title
        status
        dueDate
        category {
          name
        }
        assignedTo {
          name
        }
      }
    }
  }
}
```

## Main Mutations

### Complaint Management

```graphql
# Create a new complaint
mutation CreateComplaint($input: CreateComplaintInput!) {
  createComplaint(input: $input) {
    success
    message
    complaint {
      id
      complaintNumber
      title
      status
    }
  }
}

# Update complaint
mutation UpdateComplaint($complaintNumber: String!, $input: UpdateComplaintInput!) {
  updateComplaint(complaintNumber: $complaintNumber, input: $input) {
    success
    message
    complaint {
      id
      title
      description
      updatedAt
    }
  }
}

# Submit complaint (change from draft to submitted)
mutation SubmitComplaint($complaintNumber: String!) {
  submitComplaint(complaintNumber: $complaintNumber) {
    success
    message
    complaint {
      id
      status
      submittedAt
    }
  }
}

# Admin update complaint status
mutation AdminUpdateComplaint($complaintNumber: String!, $input: AdminUpdateComplaintInput!) {
  adminUpdateComplaint(complaintNumber: $complaintNumber, input: $input) {
    success
    message
    complaint {
      id
      status
      assignedTo {
        name
      }
      referenceNumber
    }
  }
}
```

### User Interactions

```graphql
# Add comment
mutation CreateComment($complaintNumber: String!, $input: CreateCommentInput!) {
  createComment(complaintNumber: $complaintNumber, input: $input) {
    success
    message
    comment {
      id
      content
      authorName
      createdAt
    }
  }
}

# React to complaint
mutation ReactToComplaint($complaintNumber: String!, $input: ReactToComplaintInput!) {
  reactToComplaint(complaintNumber: $complaintNumber, input: $input) {
    success
    message
    action
    reaction {
      id
      reactionType
    }
  }
}

# Follow/unfollow complaint
mutation FollowComplaint($complaintNumber: String!, $input: FollowComplaintInput) {
  followComplaint(complaintNumber: $complaintNumber, input: $input) {
    success
    message
    following
    follower {
      id
      notifyStatusChange
      notifyNewComment
      notifyResolution
    }
  }
}

# Share complaint
mutation ShareComplaint($complaintNumber: String!, $input: ShareComplaintInput) {
  shareComplaint(complaintNumber: $complaintNumber, input: $input) {
    success
    message
    shareCount
  }
}

# Report complaint
mutation ReportComplaint($complaintNumber: String!, $input: ReportComplaintInput!) {
  reportComplaint(complaintNumber: $complaintNumber, input: $input) {
    success
    message
    report {
      id
      reason
    }
  }
}
```

## Input Types

### CreateComplaintInput
```graphql
input CreateComplaintInput {
  title: String!
  description: String!
  categoryId: ID!
  subcategoryId: ID
  priority: String!
  privacy: String!
  allowComments: Boolean = true
  allowSharing: Boolean = true
  incidentDate: DateTime
  location: LocationInput
  tagIds: [ID!]
}

input LocationInput {
  country: String!
  state: String!
  city: String!
  area: String
  postalCode: String
  address: String
  latitude: Float
  longitude: Float
}
```

### CreateCommentInput
```graphql
input CreateCommentInput {
  content: String!
  parentId: ID
  isAnonymous: Boolean = false
  isOfficial: Boolean = false
}
```

### ReactToComplaintInput
```graphql
input ReactToComplaintInput {
  reactionType: String! # "like", "support", "concern", "angry", "sad"
}
```

## Filtering and Search

The API supports comprehensive filtering through GraphQL connection fields:

```graphql
query FilteredComplaints {
  complaints(
    search: "road"
    status: "submitted"
    priority: "high"
    category: "1"
    locationCity: "Dhaka"
    createdAfter: "2024-01-01T00:00:00Z"
    hasAttachments: true
    isOverdue: false
    first: 20
  ) {
    edges {
      node {
        title
        status
        priority
        category {
          name
        }
      }
    }
  }
}
```

## Error Handling

The API uses GraphQL's built-in error handling system. Common errors include:

- **Authentication Required**: User must be logged in
- **Permission Denied**: User doesn't have required permissions
- **Validation Error**: Input data is invalid
- **Not Found**: Requested resource doesn't exist

Example error response:
```json
{
  "errors": [
    {
      "message": "Authentication required",
      "locations": [{"line": 2, "column": 3}],
      "path": ["createComplaint"]
    }
  ],
  "data": {
    "createComplaint": null
  }
}
```

## Best Practices

### 1. **Use Connections for Lists**
Always use GraphQL connections with pagination for list queries:
```graphql
complaints(first: 10, after: "cursor") {
  edges {
    node { ... }
  }
  pageInfo {
    hasNextPage
    endCursor
  }
}
```

### 2. **Request Only Needed Fields**
GraphQL allows you to request only the fields you need:
```graphql
query MinimalComplaints {
  complaints(first: 10) {
    edges {
      node {
        id
        title
        status
        createdAt
      }
    }
  }
}
```

### 3. **Use Fragments for Reusability**
```graphql
fragment ComplaintSummary on Complaint {
  id
  title
  complaintNumber
  status
  priority
  category {
    name
    color
  }
  createdAt
}

query GetComplaints {
  complaints(first: 10) {
    edges {
      node {
        ...ComplaintSummary
      }
    }
  }
}
```

### 4. **Handle Errors Gracefully**
Always check for errors in your GraphQL responses and handle them appropriately in your frontend application.

### 5. **Use Variables for Dynamic Queries**
```graphql
query GetUserComplaints($userId: ID!, $status: String) {
  complaints(createdBy: $userId, status: $status) {
    edges {
      node {
        title
        status
      }
    }
  }
}
```

## Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: JWT <your-token-here>
```

## Rate Limiting

To prevent abuse, the API implements rate limiting:
- **Authenticated users**: 1000 requests per hour
- **Anonymous users**: 100 requests per hour
- **Comment creation**: 10 per minute per user
- **Reaction toggles**: 30 per minute per user

## Subscriptions (Future Enhancement)

The system is designed to support GraphQL subscriptions for real-time updates:

```graphql
subscription ComplaintUpdates($complaintNumber: String!) {
  complaintUpdated(complaintNumber: $complaintNumber) {
    id
    status
    commentCount
    reactionCount
  }
}

subscription NewComments($complaintNumber: String!) {
  commentAdded(complaintNumber: $complaintNumber) {
    id
    content
    authorName
    createdAt
  }
}
```

This comprehensive GraphQL API provides a modern, flexible, and efficient way to interact with the CivicVoice complaints system, supporting everything from basic complaint submission to advanced analytics and community engagement features.
