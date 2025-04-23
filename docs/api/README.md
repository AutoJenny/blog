# API Documentation

## Authentication
- Clan.com API key configuration
- Local authentication
- Rate limiting

## Local API Endpoints

### Posts
```
GET /api/posts - List local drafts
POST /api/posts - Create new draft
GET /api/posts/{id} - Get draft details
PUT /api/posts/{id} - Update draft
DELETE /api/posts/{id} - Delete draft
```

### Media
```
GET /api/media - List local media
POST /api/media - Upload new media
GET /api/media/{id} - Get media details
DELETE /api/media/{id} - Delete media
```

### AI Assistance
```
POST /api/ai/generate - Generate content
POST /api/ai/enhance - Enhance content
POST /api/ai/analyze - Analyze content
```

### Clan.com Integration
```
POST /api/export/{id} - Export post to clan.com
GET /api/export/status/{id} - Check export status
POST /api/preview/sync - Sync preview theme
GET /api/preview/{id} - Get preview with clan.com styling
```

## Response Formats
- Success responses
- Error handling
- Export status codes
- Preview data structure

## Integration Examples
- Content export workflow
- Media synchronization
- Preview generation
- Error recovery procedures 