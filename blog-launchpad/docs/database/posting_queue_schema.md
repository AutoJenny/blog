# Posting Queue Database Schema

## Overview

The `posting_queue` table is the central storage for all social media posting content across all platforms, channels, and content types. This unified approach replaces the previous fragmented system with separate tables for each content type.

**Table Name**: `posting_queue`  
**Database**: PostgreSQL  
**Last Updated**: 2025-01-27

---

## Table Structure

```sql
CREATE TABLE posting_queue (
    id SERIAL PRIMARY KEY,
    product_id INTEGER,                    -- References clan_products(id) for products
    section_id INTEGER,                    -- References post_section(id) for blog posts
    platform VARCHAR(50) DEFAULT 'facebook',
    channel_type VARCHAR(50) DEFAULT 'feed_post',
    content_type VARCHAR(50) DEFAULT 'product',
    scheduled_date DATE,
    scheduled_time TIME,
    scheduled_timestamp TIMESTAMP,
    schedule_name VARCHAR(100),
    timezone VARCHAR(50),
    generated_content TEXT,
    queue_order INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ready',
    platform_post_id VARCHAR(100),        -- ID from social platform after posting
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Column Descriptions

### Primary Key
- **`id`** (SERIAL PRIMARY KEY): Unique identifier for each queue item

### Content References
- **`product_id`** (INTEGER): Foreign key to `clan_products(id)` for product content
- **`section_id`** (INTEGER): Foreign key to `post_section(id)` for blog post content

### Platform/Channel Classification
- **`platform`** (VARCHAR(50)): Social media platform (facebook, instagram, twitter, linkedin)
- **`channel_type`** (VARCHAR(50)): Type of channel (feed_post, story, reel, carousel)
- **`content_type`** (VARCHAR(50)): Type of content (product, blog_post, event, announcement)

### Scheduling Information
- **`scheduled_date`** (DATE): Date when the post should be published
- **`scheduled_time`** (TIME): Time when the post should be published
- **`scheduled_timestamp`** (TIMESTAMP): Combined date and time for efficient querying
- **`schedule_name`** (VARCHAR(100)): Name of the schedule that generated this item
- **`timezone`** (VARCHAR(50)): Timezone for the scheduled post

### Content and Status
- **`generated_content`** (TEXT): The actual content to be posted
- **`queue_order`** (INTEGER): Display order in the queue (default: 0)
- **`status`** (VARCHAR(20)): Current status of the item

### Posting Results
- **`platform_post_id`** (VARCHAR(100)): ID returned by the social platform after posting
- **`error_message`** (TEXT): Error message if posting failed

### Timestamps
- **`created_at`** (TIMESTAMP): When the item was created
- **`updated_at`** (TIMESTAMP): When the item was last updated

---

## Indexes

### Primary Index
```sql
CREATE INDEX idx_posting_queue_pkey ON posting_queue (id);
```

### Filtering Indexes
```sql
-- Platform filtering
CREATE INDEX idx_posting_queue_platform ON posting_queue (platform);

-- Channel type filtering
CREATE INDEX idx_posting_queue_channel_type ON posting_queue (channel_type);

-- Content type filtering
CREATE INDEX idx_posting_queue_content_type ON posting_queue (content_type);

-- Status filtering
CREATE INDEX idx_posting_queue_status ON posting_queue (status);
```

### Scheduling Indexes
```sql
-- Date filtering
CREATE INDEX idx_posting_queue_scheduled_date ON posting_queue (scheduled_date);

-- Timestamp filtering (most efficient for date ranges)
CREATE INDEX idx_posting_queue_scheduled_timestamp ON posting_queue (scheduled_timestamp);

-- Combined date/time filtering
CREATE INDEX idx_posting_queue_scheduled_datetime ON posting_queue (scheduled_date, scheduled_time);
```

### Ordering Indexes
```sql
-- Queue order
CREATE INDEX idx_posting_queue_order ON posting_queue (queue_order);

-- Creation time ordering
CREATE INDEX idx_posting_queue_created_at ON posting_queue (created_at);
```

### Foreign Key Indexes
```sql
-- Product reference
CREATE INDEX idx_posting_queue_product_id ON posting_queue (product_id);

-- Platform post ID (for status updates)
CREATE INDEX idx_posting_queue_platform_post_id ON posting_queue (platform_post_id);
```

---

## Data Types and Constraints

### Platform Values
```sql
-- Valid platform values
CHECK (platform IN ('facebook', 'instagram', 'twitter', 'linkedin'))
```

### Channel Type Values
```sql
-- Valid channel type values
CHECK (channel_type IN ('feed_post', 'story', 'reel', 'carousel'))
```

### Content Type Values
```sql
-- Valid content type values
CHECK (content_type IN ('product', 'blog_post', 'event', 'announcement'))
```

### Status Values
```sql
-- Valid status values
CHECK (status IN ('pending', 'ready', 'published', 'failed', 'cancelled'))
```

---

## Sample Data

### Product Content Item
```sql
INSERT INTO posting_queue (
    platform, channel_type, content_type, product_id,
    generated_content, scheduled_timestamp, status,
    schedule_name, timezone, queue_order
) VALUES (
    'facebook', 'feed_post', 'product', 123,
    'Check out this amazing Tartan Scarf! Perfect for any occasion. #Tartan #Fashion',
    '2025-01-28 17:00:00', 'ready',
    'Daily Product Posts', 'GMT', 1
);
```

### Blog Post Content Item
```sql
INSERT INTO posting_queue (
    platform, channel_type, content_type, section_id,
    generated_content, scheduled_timestamp, status,
    schedule_name, timezone, queue_order
) VALUES (
    'facebook', 'feed_post', 'blog_post', 456,
    'Discover the rich tradition of Scottish storytelling in our latest blog post. From ancient myths to modern literature, explore how these stories continue to inspire today. #Storytelling #Scotland #Culture',
    '2025-01-28 18:00:00', 'ready',
    'Blog Post Schedule', 'GMT', 2
);
```

### Published Item
```sql
INSERT INTO posting_queue (
    platform, channel_type, content_type, product_id,
    generated_content, scheduled_timestamp, status,
    platform_post_id, schedule_name, timezone
) VALUES (
    'facebook', 'feed_post', 'product', 789,
    'Amazing Highland Whisky Glasses now available! Perfect for your next gathering. #Whisky #Highland #Gift',
    '2025-01-27 16:00:00', 'published',
    'fb_post_123456789', 'Daily Product Posts', 'GMT'
);
```

---

## Common Queries

### Get All Ready Items
```sql
SELECT * FROM posting_queue 
WHERE status = 'ready' 
ORDER BY scheduled_timestamp ASC;
```

### Get Product Items for Facebook
```sql
SELECT pq.*, cp.name as product_name, cp.image_url
FROM posting_queue pq
LEFT JOIN clan_products cp ON pq.product_id = cp.id
WHERE pq.platform = 'facebook' 
  AND pq.channel_type = 'feed_post' 
  AND pq.content_type = 'product'
ORDER BY pq.scheduled_timestamp ASC;
```

### Get Blog Post Items
```sql
SELECT pq.*, p.title as post_title, ps.section_heading as section_title
FROM posting_queue pq
LEFT JOIN post p ON pq.section_id = ps.id AND ps.post_id = p.id
LEFT JOIN post_section ps ON pq.section_id = ps.id
WHERE pq.content_type = 'blog_post'
ORDER BY pq.scheduled_timestamp ASC;
```

### Get Items by Date Range
```sql
SELECT * FROM posting_queue 
WHERE scheduled_timestamp BETWEEN '2025-01-27 00:00:00' AND '2025-01-28 23:59:59'
ORDER BY scheduled_timestamp ASC;
```

### Get Failed Items
```sql
SELECT * FROM posting_queue 
WHERE status = 'failed' 
ORDER BY updated_at DESC;
```

### Count Items by Status
```sql
SELECT status, COUNT(*) as count
FROM posting_queue 
GROUP BY status
ORDER BY count DESC;
```

### Count Items by Content Type
```sql
SELECT content_type, COUNT(*) as count
FROM posting_queue 
GROUP BY content_type
ORDER BY count DESC;
```

---

## Performance Considerations

### Query Optimization
1. **Use Indexed Columns**: Always filter by indexed columns when possible
2. **Limit Results**: Use LIMIT clause for large datasets
3. **Avoid SELECT \***: Only select needed columns
4. **Use Timestamp Filtering**: Use `scheduled_timestamp` for date ranges

### Maintenance
1. **Regular Cleanup**: Remove old published items periodically
2. **Index Maintenance**: Monitor index usage and rebuild if needed
3. **Statistics Updates**: Keep table statistics current
4. **Archival Strategy**: Archive old data to separate tables

### Monitoring
1. **Query Performance**: Monitor slow queries
2. **Index Usage**: Check which indexes are being used
3. **Table Size**: Monitor table growth
4. **Lock Contention**: Watch for blocking queries

---

## Migration from Old System

### From Separate Tables
If migrating from separate tables for each content type:

```sql
-- Migrate product posts
INSERT INTO posting_queue (
    platform, channel_type, content_type, product_id,
    generated_content, scheduled_timestamp, status,
    schedule_name, timezone, queue_order, created_at
)
SELECT 
    'facebook', 'feed_post', 'product', product_id,
    generated_content, scheduled_timestamp, status,
    schedule_name, timezone, queue_order, created_at
FROM old_product_queue;

-- Migrate blog post items
INSERT INTO posting_queue (
    platform, channel_type, content_type, section_id,
    generated_content, scheduled_timestamp, status,
    schedule_name, timezone, queue_order, created_at
)
SELECT 
    'facebook', 'feed_post', 'blog_post', section_id,
    generated_content, scheduled_timestamp, status,
    schedule_name, timezone, queue_order, created_at
FROM old_blog_queue;
```

---

## Backup and Recovery

### Backup Strategy
```sql
-- Full table backup
pg_dump -t posting_queue blog > posting_queue_backup.sql

-- Data-only backup
pg_dump -t posting_queue --data-only blog > posting_queue_data.sql
```

### Recovery
```sql
-- Restore from backup
psql blog < posting_queue_backup.sql
```

---

## Security Considerations

### Access Control
1. **Read Access**: Allow read access to queue items
2. **Write Access**: Restrict write access to authorized users
3. **Delete Access**: Limit delete access to administrators
4. **Audit Trail**: Log all modifications

### Data Protection
1. **Content Encryption**: Consider encrypting sensitive content
2. **Access Logging**: Log all database access
3. **Regular Backups**: Maintain current backups
4. **Disaster Recovery**: Test recovery procedures

---

## Troubleshooting

### Common Issues

#### Slow Queries
- Check if proper indexes are being used
- Analyze query execution plans
- Consider adding composite indexes

#### Lock Contention
- Monitor for long-running transactions
- Use appropriate isolation levels
- Consider connection pooling

#### Data Inconsistency
- Check foreign key constraints
- Validate data integrity
- Monitor for orphaned records

### Diagnostic Queries

#### Check Index Usage
```sql
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename = 'posting_queue'
ORDER BY idx_scan DESC;
```

#### Check Table Size
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE tablename = 'posting_queue';
```

#### Check Recent Activity
```sql
SELECT status, COUNT(*) as count, MAX(updated_at) as last_update
FROM posting_queue 
GROUP BY status
ORDER BY last_update DESC;
```

---

*This schema documentation is maintained by the Blog Launchpad development team. Last updated: 2025-01-27*
