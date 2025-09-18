# Social Media Command Center - UI Layout Diagram

## Overall Structure

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           HEADER SECTION                                        │
│  🚀 Social Media Command Center                                                │
│  Centralized dashboard for managing all social media content across platforms  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                            KPI PANEL                                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ Scheduled   │ │ Published   │ │ Platforms   │ │ Queue       │              │
│  │ Posts: 0    │ │ Today: 0    │ │ Active: 0   │ │ Health: 0   │              │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘              │
│                                                                                 │
│  [Daily Product Posts] [Create New Post] [Schedule Posts] [View Analytics]     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MAIN CONTENT                                       │
│  ┌─────────────────────────────────────────────────────┐ ┌─────────────────┐   │
│  │                TIMELINE SECTION                     │ │    SIDEBAR      │   │
│  │                                                     │ │                 │   │
│  │  Real-Time Posting Timeline                         │ │  Queue Status   │   │
│  │                                                     │ │                 │   │
│  │  [All] [Facebook] [Instagram] [Twitter] [LinkedIn]  │ │  Quick Schedule │   │
│  │                                                     │ │                 │   │
│  │  ┌─────────────────────────────────────────────────┐ │ │  Platform Status│   │
│  │  │ Date/Time │ Platform │ Type │ Content │ Status │ │ │                 │   │
│  │  │ 01/28 17:00│ Facebook │Product│ Preview │ Ready │ │ │  Recent Activity│   │
│  │  │ 01/29 09:00│ Instagram│ Blog  │ Preview │ Pending│ │ │                 │   │
│  │  │ 01/29 14:00│ Twitter  │Tartan │ Preview │ Ready │ │ │                 │   │
│  │  └─────────────────────────────────────────────────┘ │ │                 │   │
│  └─────────────────────────────────────────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Header Section
- **Title**: "🚀 Social Media Command Center"
- **Subtitle**: "Centralized dashboard for managing all social media content across platforms"
- **Purpose**: Clear identification and context

### 2. KPI Panel (Full Width)
- **Layout**: 4-column grid of KPI cards
- **KPIs**:
  - Scheduled Posts (count)
  - Published Today (count)
  - Platforms Active (count)
  - Queue Health (status)
- **Quick Actions**: 4 main action buttons
  - Daily Product Posts (link to existing system)
  - Create New Post (future)
  - Schedule Posts (future)
  - View Analytics (future)

### 3. Main Content (2-Column Layout)

#### Left Column: Timeline Section
- **Title**: "Real-Time Posting Timeline"
- **Platform Filter**: Tab-based platform selector
  - All Platforms (default)
  - Facebook
  - Instagram
  - Twitter
  - LinkedIn
- **Timeline Table**: 
  - Date/Time column
  - Platform column (with badges)
  - Type column (with badges)
  - Content Preview column
  - Status column (with badges)
  - Actions column (buttons)

#### Right Column: Sidebar
- **Queue Status Card**: Current queue information
- **Quick Schedule Card**: Quick scheduling tools
- **Platform Status Card**: Platform connectivity status
- **Recent Activity Card**: Recent posting activity

## Color Coding System

### Platform Badges
- **Facebook**: Blue (#1877F2)
- **Instagram**: Gradient (pink to purple)
- **Twitter**: Light Blue (#1DA1F2)
- **LinkedIn**: Dark Blue (#0077B5)

### Content Type Badges
- **Product**: Green (#10B981)
- **Blog**: Purple (#8B5CF6)
- **Tartan**: Orange (#F59E0B)
- **Event**: Red (#EF4444)

### Status Badges
- **Pending**: Gray (#6B7280)
- **Ready**: Yellow (#F59E0B)
- **Published**: Green (#10B981)
- **Failed**: Red (#EF4444)

## Responsive Design

### Desktop (1400px+)
- Full 2-column layout
- 4-column KPI grid
- Full timeline table

### Tablet (768px - 1024px)
- Single column layout
- 2-column KPI grid
- Condensed timeline

### Mobile (< 768px)
- Single column layout
- 2-column KPI grid
- Card-based timeline

## Interactive Elements

### Platform Filtering
- Click platform tabs to filter timeline
- Visual feedback for active tab
- Real-time filtering without page reload

### Timeline Actions
- Edit button for each post
- Reschedule button
- Cancel/Delete button
- Status indicators

### KPI Panel
- Hover effects on cards
- Click-through to detailed views
- Real-time updates

## Future Enhancements

### Phase 2: Enhanced Timeline
- Drag-and-drop reordering
- Bulk selection and actions
- Advanced filtering options
- Calendar view toggle

### Phase 3: Analytics Integration
- KPI charts and graphs
- Performance metrics
- Engagement tracking
- Trend analysis

### Phase 4: Advanced Features
- Real-time notifications
- Team collaboration tools
- Content approval workflow
- A/B testing interface
