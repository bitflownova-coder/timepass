# API Documentation

## Overview

Complete REST API documentation for SmartDoc AI. All endpoints require authentication via JWT token except for authentication endpoints.

## Base URL

```
http://localhost:5000/api
```

## Authentication

All authenticated endpoints require the Authorization header:

```
Authorization: Bearer <jwt_token>
```

---

## Authentication Endpoints

### 1. User Registration

**POST** `/auth/register`

Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password_123",
  "full_name": "John Doe"
}
```

**Response:** (201 Created)
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "user"
  }
}
```

**Error Response:** (400 Bad Request)
```json
{
  "success": false,
  "error": "Email already exists"
}
```

---

### 2. User Login

**POST** `/auth/login`

Authenticate user and get JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

**Response:** (200 OK)
```json
{
  "success": true,
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "user"
  }
}
```

**Error Response:** (401 Unauthorized)
```json
{
  "success": false,
  "error": "Invalid email or password"
}
```

---

### 3. User Logout

**POST** `/auth/logout`

Invalidate current JWT token.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** (200 OK)
```json
{
  "success": true,
  "message": "Logout successful"
}
```

---

## Document Upload Endpoints

### 4. Upload Document

**POST** `/upload`

Upload and classify a document.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request:**
```
Form Data:
- file: <binary file> (PDF, DOCX, JPG)
- tags: "invoice, bills" (optional)
```

**Response:** (200 OK)
```json
{
  "success": true,
  "document": {
    "id": 123,
    "filename": "electricity_bill_2024.pdf",
    "file_size": 245632,
    "predicted_label": "Invoice",
    "confidence_score": 0.92,
    "suggested_folder": "Bills",
    "suggested_tags": ["invoice", "bills", "2024"],
    "text_preview": "Invoice Number: INV-2024-001...",
    "uploaded_at": "2024-04-20T10:30:00Z"
  },
  "classification": {
    "top_3_predictions": [
      {"label": "Invoice", "confidence": 0.92},
      {"label": "Bills", "confidence": 0.05},
      {"label": "Legal", "confidence": 0.03}
    ]
  }
}
```

**Error Response:** (400 Bad Request)
```json
{
  "success": false,
  "error": "File type not allowed. Only PDF, DOCX, and JPG supported"
}
```

**Error Response:** (413 Payload Too Large)
```json
{
  "success": false,
  "error": "File size exceeds 50MB limit"
}
```

---

### 5. Confirm Document Classification

**POST** `/documents/{doc_id}/confirm`

User confirms folder placement for document.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "folder": "Bills",
  "tags": ["invoice", "bills", "electricity"],
  "user_feedback": "Correct classification!"
}
```

**Response:** (200 OK)
```json
{
  "success": true,
  "message": "Document stored in Bills folder",
  "document": {
    "id": 123,
    "user_folder": "Bills",
    "tags": ["invoice", "bills", "electricity"],
    "status": "stored"
  }
}
```

---

## Document Management Endpoints

### 6. Get All Documents

**GET** `/documents`

Retrieve all documents for current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
```
?limit=20&offset=0&folder=Bills&sort=newest
```

**Response:** (200 OK)
```json
{
  "success": true,
  "documents": [
    {
      "id": 123,
      "filename": "electricity_bill.pdf",
      "user_folder": "Bills",
      "predicted_label": "Invoice",
      "confidence_score": 0.92,
      "tags": ["invoice", "bills"],
      "uploaded_at": "2024-04-20T10:30:00Z",
      "file_size": 245632
    },
    {
      "id": 124,
      "filename": "contract.pdf",
      "user_folder": "Legal",
      "predicted_label": "Legal",
      "confidence_score": 0.88,
      "tags": ["legal", "contract"],
      "uploaded_at": "2024-04-19T14:20:00Z",
      "file_size": 512340
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

---

### 7. Get Document Details

**GET** `/documents/{doc_id}`

Get detailed information about a specific document.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** (200 OK)
```json
{
  "success": true,
  "document": {
    "id": 123,
    "filename": "electricity_bill.pdf",
    "original_filename": "bill_april_2024.pdf",
    "file_size": 245632,
    "mime_type": "application/pdf",
    "user_folder": "Bills",
    "predicted_label": "Invoice",
    "confidence_score": 0.92,
    "tags": ["invoice", "bills", "electricity"],
    "text_preview": "Invoice Number: INV-2024-001\nDate: April 15, 2024...",
    "is_encrypted": true,
    "uploaded_at": "2024-04-20T10:30:00Z",
    "accessed_at": "2024-04-20T15:45:00Z"
  },
  "metadata": {
    "num_pages": 2,
    "word_count": 342,
    "language": "en",
    "ocr_used": false
  }
}
```

---

### 8. Download Document

**GET** `/documents/{doc_id}/download`

Download decrypted document file.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** (200 OK)
- Content-Type: application/pdf (or appropriate MIME type)
- Binary file data

---

### 9. Delete Document

**DELETE** `/documents/{doc_id}`

Soft delete a document (mark as deleted).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** (200 OK)
```json
{
  "success": true,
  "message": "Document deleted successfully"
}
```

---

### 10. Update Document Tags

**PATCH** `/documents/{doc_id}`

Update tags for a document.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "tags": ["invoice", "bills", "electricity", "2024-q2"]
}
```

**Response:** (200 OK)
```json
{
  "success": true,
  "document": {
    "id": 123,
    "tags": ["invoice", "bills", "electricity", "2024-q2"]
  }
}
```

---

## Classification & Prediction Endpoints

### 11. Classify Document (Without Upload)

**POST** `/classify`

Classify a document from URL or base64 encoded text.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "text": "Invoice #2024-001\nAmount: $500\nDue Date: 2024-05-01",
  "filename": "sample.txt"
}
```

**Response:** (200 OK)
```json
{
  "success": true,
  "classification": {
    "predicted_label": "Invoice",
    "confidence_score": 0.87,
    "top_3_predictions": [
      {"label": "Invoice", "confidence": 0.87},
      {"label": "Bills", "confidence": 0.10},
      {"label": "Email", "confidence": 0.03}
    ],
    "suggested_folder": "Bills",
    "feature_importance": {
      "invoice": 0.45,
      "amount": 0.25,
      "due date": 0.15,
      "payment": 0.15
    }
  }
}
```

---

## Search Endpoints

### 12. Search Documents

**GET** `/search`

Search documents by keyword with filters.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
```
?q=invoice&folder=Bills&start_date=2024-01-01&end_date=2024-12-31&limit=20
```

**Response:** (200 OK)
```json
{
  "success": true,
  "results": [
    {
      "id": 123,
      "filename": "electricity_bill.pdf",
      "user_folder": "Bills",
      "relevance_score": 0.95,
      "preview": "...Invoice #2024-001 Amount: $500...",
      "uploaded_at": "2024-04-20T10:30:00Z"
    }
  ],
  "total": 42,
  "query_time_ms": 125
}
```

---

## Dashboard Endpoints

### 13. Get Dashboard Statistics

**GET** `/dashboard/stats`

Get document statistics for dashboard.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** (200 OK)
```json
{
  "success": true,
  "stats": {
    "total_documents": 145,
    "total_storage_used": 2147483648,
    "documents_by_category": {
      "Bills": 45,
      "Resume": 22,
      "Legal": 18,
      "Research": 35,
      "Notes": 25
    },
    "recent_uploads": 12,
    "average_confidence": 0.87,
    "storage_limit": 5368709120
  }
}
```

---

### 14. Get Dashboard Charts Data

**GET** `/dashboard/charts`

Get data for dashboard charts and graphs.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
```
?period=month&year=2024
```

**Response:** (200 OK)
```json
{
  "success": true,
  "charts": {
    "uploads_over_time": [
      {"date": "2024-04-01", "count": 5},
      {"date": "2024-04-02", "count": 8},
      {"date": "2024-04-03", "count": 3}
    ],
    "category_distribution": [
      {"category": "Bills", "count": 45, "percentage": 31},
      {"category": "Resume", "count": 22, "percentage": 15},
      {"category": "Legal", "count": 18, "percentage": 12}
    ],
    "confidence_distribution": [
      {"range": "90-100%", "count": 95},
      {"range": "80-90%", "count": 35},
      {"range": "70-80%", "count": 12},
      {"range": "<70%", "count": 3}
    ]
  }
}
```

---

## Audit Log Endpoints

### 15. Get Audit Logs

**GET** `/audit-logs`

Retrieve audit logs (admin only).

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
```
?user_id=1&action=upload&limit=50&offset=0
```

**Response:** (200 OK)
```json
{
  "success": true,
  "logs": [
    {
      "id": 1001,
      "user_id": 1,
      "action": "upload",
      "resource_type": "document",
      "resource_name": "electricity_bill.pdf",
      "ip_address": "192.168.1.100",
      "status": "success",
      "created_at": "2024-04-20T10:30:00Z"
    }
  ],
  "total": 500
}
```

---

## User Profile Endpoints

### 16. Get User Profile

**GET** `/user/profile`

Get current user's profile information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** (200 OK)
```json
{
  "success": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "user",
    "storage_used": 2147483648,
    "storage_limit": 5368709120,
    "document_count": 145,
    "created_at": "2024-01-15T10:00:00Z",
    "last_login": "2024-04-20T15:45:00Z"
  }
}
```

---

### 17. Update User Profile

**PATCH** `/user/profile`

Update user profile information.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "full_name": "Jane Doe"
}
```

**Response:** (200 OK)
```json
{
  "success": true,
  "user": {
    "id": 1,
    "full_name": "Jane Doe"
  }
}
```

---

## Error Handling

### Common Error Responses

**401 Unauthorized**
```json
{
  "success": false,
  "error": "Invalid or expired token"
}
```

**403 Forbidden**
```json
{
  "success": false,
  "error": "You do not have permission to access this resource"
}
```

**404 Not Found**
```json
{
  "success": false,
  "error": "Document not found"
}
```

**429 Too Many Requests**
```json
{
  "success": false,
  "error": "Rate limit exceeded. Please try again later."
}
```

**500 Internal Server Error**
```json
{
  "success": false,
  "error": "An internal server error occurred"
}
```

---

## Rate Limiting

- **Free tier**: 100 requests/hour per user
- **Premium tier**: 1000 requests/hour per user
- **Admin tier**: Unlimited

---

## Pagination

Use `limit` and `offset` for pagination:

```
GET /documents?limit=20&offset=0  # First 20
GET /documents?limit=20&offset=20 # Next 20
```

---

## Sorting

Common sort options:
- `newest` - Most recent first (default)
- `oldest` - Oldest first
- `name` - Alphabetical by filename
- `size` - Largest first

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - New resource created |
| 204 | No Content - Successful deletion |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 413 | Payload Too Large - File too large |
| 429 | Too Many Requests - Rate limited |
| 500 | Server Error - Internal error |

---

## Example cURL Commands

### Upload Document
```bash
curl -X POST http://localhost:5000/api/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "tags=invoice,bills"
```

### Search Documents
```bash
curl -X GET "http://localhost:5000/api/search?q=invoice&folder=Bills" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Dashboard Stats
```bash
curl -X GET http://localhost:5000/api/dashboard/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

Last Updated: April 20, 2026
Version: 1.0.0
