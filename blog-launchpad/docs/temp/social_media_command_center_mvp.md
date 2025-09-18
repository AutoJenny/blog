# Social Media Command Center - MVP Framework

## Project Overview
**Name**: Social Media Command Center  
**URL**: `/social-media-command-center`  
**Purpose**: Centralized dashboard for managing and monitoring all scheduled social media posts across platforms

## MVP Scope (Phase 1)
**Focus**: Facebook Product Posts Only  
**Goal**: Display and manage existing Facebook daily product post queue with real-time timeline view

## Core MVP Features

### 1. Real-Time Posting Timeline
**Primary View**: Table showing next 30 scheduled Facebook product posts

#### Data Source
- Existing `posting_queue` table from daily-product-posts
- Queue items with `status = 'pending'`
- Sorted by `scheduled_time` (next first)

#### Table Columns
| Column | Description | Data Source |
|--------|-------------|-------------|
| **Date/Time** | Scheduled posting time | `scheduled_time` |
| **Platform** | Always "Facebook" for MVP | Static |
| **Content Type** | Always "Product Post" for MVP | Static |
| **Product** | Product name and SKU | `product_name`, `sku` |
| **Title** | Generated post title | `generated_content` (first line) |
| **Status** | Pending/Ready/Published/Failed | `status` |
| **Actions** | Edit/Reschedule/Cancel | Buttons |

#### Color Coding
- **Platform**: Facebook blue (#1877F2)
- **Content Type**: Product green (#10B981)
- **Status Colors**:
  - Pending: Gray (#6B7280)
  - Ready: Yellow (#F59E0B)
  - Published: Green (#10B981)
  - Failed: Red (#EF4444)

### 2. Quick Actions Panel
**Location**: Top of timeline table

#### Actions
- **Refresh Queue**: Reload data from database
- **Add 10 Items**: Generate 10 new queue items
- **Clear Queue**: Remove all pending items
- **Bulk Actions**: Select multiple items for batch operations

### 3. Queue Management
**Integration**: Use existing daily-product-posts functionality

#### Features
- Display current queue count
- Show queue health (empty/low/normal/full)
- Quick access to generate new content
- Clear all functionality

## Technical Implementation

### Database Schema
**Existing Tables** (No changes needed):
- `posting_queue` - Main queue data
- `product_content_templates` - Content generation templates
- `posting_schedules` - Schedule patterns

### API Endpoints
**Existing Endpoints** (Reuse):
- `GET /api/daily-product-posts/queue` - Get queue data
- `POST /api/daily-product-posts/generate-batch` - Generate new items
- `DELETE /api/daily-product-posts/queue/clear` - Clear queue
- `PUT /api/daily-product-posts/queue/{id}` - Update queue item

**New Endpoints** (MVP):
- `GET /api/social-media/timeline` - Get timeline data (wrapper around existing queue)
- `PUT /api/social-media/timeline/{id}/reschedule` - Reschedule specific item
- `DELETE /api/social-media/timeline/{id}` - Cancel specific item

### Frontend Structure
```
/social-media-command-center
├── templates/
│   ├── social_media_command_center.html (main template)
│   └── includes/
│       ├── timeline_table.html
│       ├── quick_actions.html
│       └── queue_status.html
├── static/css/
│   └── social_media_command_center.css
└── static/js/
    └── social_media_command_center.js
```

## UI/UX Design Principles

### Layout
- **Header**: Page title + quick stats
- **Main Content**: Timeline table (primary focus)
- **Sidebar**: Queue status + quick actions
- **Footer**: Platform status indicators

### Responsive Design
- **Desktop**: Full table with all columns
- **Tablet**: Condensed table with key columns
- **Mobile**: Card-based layout

### Real-Time Updates
- **Auto-refresh**: Every 30 seconds
- **Manual refresh**: Button in quick actions
- **Live indicators**: Show when data is updating

## Future Phases (Not in MVP)

### Phase 2: Multi-Platform Support
- Add Instagram, Twitter, LinkedIn
- Platform-specific scheduling
- Cross-platform content adaptation

### Phase 3: Content Calendar
- Monthly/weekly calendar view
- Drag-and-drop rescheduling
- Bulk scheduling tools

### Phase 4: Event Management
- Annual events calendar
- Theme-based content suggestions
- Campaign planning tools

### Phase 5: Analytics Integration
- Performance metrics
- Engagement tracking
- Optimization suggestions

## Development Approach

### Phase 1A: Basic Structure
1. Create main template with basic layout
2. Implement timeline table with static data
3. Add basic styling and responsive design

### Phase 1B: Data Integration
1. Connect to existing queue API
2. Implement real-time updates
3. Add quick actions functionality

### Phase 1C: Queue Management
1. Integrate with existing queue management
2. Add reschedule/cancel functionality
3. Implement bulk actions

### Phase 1D: Polish & Testing
1. Add loading states and error handling
2. Implement user feedback
3. Performance optimization

## Success Metrics
- **Functionality**: All existing queue features accessible
- **Performance**: Page loads in <2 seconds
- **Usability**: Intuitive navigation and actions
- **Reliability**: 99% uptime for queue operations

## Risk Mitigation
- **Data Loss**: All operations use existing, tested APIs
- **Performance**: Start with 30 items, optimize as needed
- **Complexity**: Keep MVP simple, avoid over-engineering
- **Integration**: Reuse existing components where possible

## Notes
- This MVP focuses on Facebook product posts only
- All existing functionality must remain accessible
- New features should enhance, not replace, existing tools
- Consider this a "view" layer on top of existing functionality
- Future phases can expand to other platforms and content types

## Next Steps
1. Create basic template structure
2. Implement timeline table component
3. Connect to existing queue data
4. Add basic styling and interactions
5. Test with real data
6. Iterate based on feedback
