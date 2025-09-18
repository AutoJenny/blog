# Blog Launchpad - Social Media Database Reference

## Overview
This document provides a comprehensive reference for all database tables relevant to the Blog Launchpad social media component. It serves as a ready-reference for developers and includes field definitions, relationships, and update procedures.

**Document Version**: 1.0  
**Created**: 2025-01-27  
**Status**: **ACTIVE REFERENCE**  
**Database**: PostgreSQL (production) / SQLite (development)

---

## 🎯 **CORE SOCIAL MEDIA TABLES**

### **1. posting_queue** - Main Queue Management
**Purpose**: Stores all scheduled social media posts across platforms  
**Owner**: postgres  
**Status**: ✅ **ACTIVE** - Core table for queue management

#### **Table Structure**
```sql
CREATE TABLE posting_queue (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES clan_products(id),
    scheduled_date DATE,
    scheduled_time TIME,
    schedule_name VARCHAR(100),
    timezone VARCHAR(50),
    generated_content TEXT,
    queue_order INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ready',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Key Fields**
- **`id`**: Primary key (auto-increment)
- **`product_id`**: Foreign key to `clan_products.id`
- **`scheduled_date`**: Date for posting (NULL if unscheduled)
- **`scheduled_time`**: Time of day for posting (NULL if unscheduled)
- **`schedule_name`**: Name of schedule that generated this item
- **`timezone`**: Timezone for scheduled post
- **`generated_content`**: AI-generated post content
- **`queue_order`**: Display order in queue (0 = default)
- **`status`**: Current status ('ready', 'pending', 'published', 'failed')
- **`created_at`**: Creation timestamp
- **`updated_at`**: Last update timestamp

#### **Indexes**
- `idx_posting_queue_order` - Queue display order
- `idx_posting_queue_product_id` - Product lookups
- `idx_posting_queue_scheduled_datetime` - Scheduling queries
- `idx_posting_queue_status` - Status filtering

#### **Common Queries**
```sql
-- Get all pending posts in order
SELECT * FROM posting_queue 
WHERE status = 'pending' 
ORDER BY queue_order ASC, created_at ASC;

-- Get posts for specific date
SELECT * FROM posting_queue 
WHERE scheduled_date = '2025-01-27' 
ORDER BY scheduled_time ASC;

-- Update queue order
UPDATE posting_queue 
SET queue_order = 1, updated_at = NOW() 
WHERE id = 123;
```

---

### **2. platforms** - Social Media Platforms
**Purpose**: Registry of all supported social media platforms  
**Owner**: nickfiddes  
**Status**: ✅ **ACTIVE** - Platform management

#### **Table Structure**
```sql
CREATE TABLE platforms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    priority INTEGER DEFAULT 0,
    website_url VARCHAR(255),
    api_documentation_url VARCHAR(255),
    logo_url VARCHAR(255),
    development_status VARCHAR(20) DEFAULT 'not_started',
    is_featured BOOLEAN DEFAULT false,
    menu_priority INTEGER DEFAULT 0,
    is_visible_in_ui BOOLEAN DEFAULT true,
    last_activity_at TIMESTAMP,
    last_post_at TIMESTAMP,
    last_api_call_at TIMESTAMP,
    total_posts_count INTEGER DEFAULT 0,
    success_rate_percentage DECIMAL(5,2),
    average_response_time_ms INTEGER,
    estimated_completion_date DATE,
    actual_completion_date DATE,
    development_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Key Fields**
- **`name`**: Platform identifier ('facebook', 'instagram', 'twitter')
- **`display_name`**: Human-readable name ('Facebook', 'Instagram', 'Twitter')
- **`status`**: Platform status ('active', 'inactive', 'deprecated')
- **`development_status`**: Development progress ('not_started', 'in_progress', 'developed', 'active')
- **`is_visible_in_ui`**: Whether to show in user interface
- **`total_posts_count`**: Total posts made to this platform
- **`success_rate_percentage`**: Success rate of posts
- **`last_post_at`**: Last time content was posted

#### **Current Data**
```sql
-- Currently configured platforms
SELECT name, display_name, status, development_status 
FROM platforms 
ORDER BY priority ASC;
```

---

### **3. channel_types** - Content Channel Types
**Purpose**: Defines different types of content channels across platforms  
**Owner**: postgres  
**Status**: ✅ **ACTIVE** - Channel type management

#### **Table Structure**
```sql
CREATE TABLE channel_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    content_type VARCHAR(50) NOT NULL,
    media_support TEXT[],
    default_priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Key Fields**
- **`name`**: Channel identifier ('feed_post', 'story_post', 'reels_post')
- **`display_name`**: Human-readable name ('Feed Post', 'Story Post', 'Reels Post')
- **`content_type`**: Type of content ('text', 'image', 'video', 'mixed')
- **`media_support`**: Array of supported media types
- **`is_active`**: Whether channel is currently active
- **`display_order`**: Order for UI display

#### **Current Data**
```sql
-- Currently configured channel types
SELECT name, display_name, content_type, media_support 
FROM channel_types 
WHERE is_active = true 
ORDER BY display_order ASC;
```

---

### **4. channel_requirements** - Platform-Specific Requirements
**Purpose**: Stores specific requirements for each platform-channel combination  
**Owner**: postgres  
**Status**: ✅ **ACTIVE** - Requirements management

#### **Table Structure**
```sql
CREATE TABLE channel_requirements (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    channel_type_id INTEGER NOT NULL REFERENCES channel_types(id) ON DELETE CASCADE,
    requirement_category VARCHAR(50) NOT NULL,
    requirement_key VARCHAR(100) NOT NULL,
    requirement_value TEXT NOT NULL,
    description TEXT,
    is_required BOOLEAN DEFAULT true,
    validation_rules JSONB,
    unit VARCHAR(50),
    min_value TEXT,
    max_value TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, channel_type_id, requirement_category, requirement_key)
);
```

#### **Key Fields**
- **`platform_id`**: Foreign key to platforms table
- **`channel_type_id`**: Foreign key to channel_types table
- **`requirement_category`**: Category ('dimensions', 'content', 'engagement', 'technical')
- **`requirement_key`**: Specific requirement ('image_width', 'max_hashtags', 'tone')
- **`requirement_value`**: Actual requirement value
- **`is_required`**: Whether this is mandatory
- **`validation_rules`**: JSON validation rules
- **`unit`**: Unit of measurement ('pixels', 'characters', 'seconds')

#### **Common Queries**
```sql
-- Get requirements for Facebook Feed Post
SELECT cr.requirement_category, cr.requirement_key, cr.requirement_value, cr.description
FROM channel_requirements cr
JOIN platforms p ON cr.platform_id = p.id
JOIN channel_types ct ON cr.channel_type_id = ct.id
WHERE p.name = 'facebook' AND ct.name = 'feed_post'
ORDER BY cr.requirement_category, cr.requirement_key;

-- Get all active requirements
SELECT p.name as platform, ct.name as channel, cr.requirement_category, cr.requirement_key
FROM channel_requirements cr
JOIN platforms p ON cr.platform_id = p.id
JOIN channel_types ct ON cr.channel_type_id = ct.id
WHERE cr.is_active = true
ORDER BY p.name, ct.name, cr.requirement_category;
```

---

## 🔗 **SUPPORTING TABLES**

### **5. platform_channel_support** - Platform-Channel Compatibility
**Purpose**: Defines which platforms support which channels  
**Owner**: postgres  
**Status**: ✅ **ACTIVE** - Compatibility matrix

#### **Table Structure**
```sql
CREATE TABLE platform_channel_support (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    channel_type_id INTEGER NOT NULL REFERENCES channel_types(id) ON DELETE CASCADE,
    is_supported BOOLEAN DEFAULT true,
    status VARCHAR(20) DEFAULT 'active',
    development_status VARCHAR(20) DEFAULT 'not_started',
    priority INTEGER DEFAULT 0,
    notes TEXT,
    estimated_completion_date DATE,
    actual_completion_date DATE,
    development_notes TEXT,
    last_activity_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, channel_type_id)
);
```

### **6. platform_capabilities** - Platform Capabilities
**Purpose**: Stores platform-wide capabilities and specifications  
**Owner**: postgres  
**Status**: ✅ **ACTIVE** - Capability management

#### **Table Structure**
```sql
CREATE TABLE platform_capabilities (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    capability_type VARCHAR(50) NOT NULL,
    capability_name VARCHAR(100) NOT NULL,
    capability_value TEXT NOT NULL,
    description TEXT,
    unit VARCHAR(50),
    min_value TEXT,
    max_value TEXT,
    validation_rules JSONB,
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, capability_type, capability_name)
);
```

### **7. platform_credentials** - API Credentials
**Purpose**: Stores API keys and authentication details  
**Owner**: postgres  
**Status**: ✅ **ACTIVE** - Credential management

#### **Table Structure**
```sql
CREATE TABLE platform_credentials (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    credential_type VARCHAR(50) NOT NULL,
    credential_key VARCHAR(100) NOT NULL,
    credential_value TEXT NOT NULL,
    is_encrypted BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, credential_type, credential_key)
);
```

---

## 📊 **RELATED BLOG-CORE TABLES**

### **8. clan_products** - Product Data
**Purpose**: Clan.com product information (referenced by posting_queue)  
**Owner**: nickfiddes  
**Status**: ✅ **ACTIVE** - Product data source

#### **Key Fields**
- **`id`**: Primary key (referenced by posting_queue.product_id)
- **`name`**: Product name
- **`sku`**: Product SKU
- **`price`**: Product price
- **`image_url`**: Product image URL
- **`description`**: Product description

### **9. llm_interaction** - AI Content Generation
**Purpose**: Stores AI-generated content and metadata  
**Owner**: nickfiddes  
**Status**: ✅ **ACTIVE** - AI content storage

#### **Key Fields**
- **`id`**: Primary key
- **`input_text`**: Original content
- **`output_text`**: Generated content
- **`interaction_metadata`**: JSON metadata
- **`parameters_used`**: JSON parameters
- **`created_at`**: Generation timestamp

---

## 🔄 **TABLE RELATIONSHIPS**

### **Primary Relationships**
```
posting_queue (1) → (1) clan_products
posting_queue (1) → (1) platforms [via platform field - TO BE ADDED]
posting_queue (1) → (1) channel_types [via channel_type field - TO BE ADDED]

platforms (1) → (many) channel_requirements
platforms (1) → (many) platform_capabilities
platforms (1) → (many) platform_credentials
platforms (1) → (many) platform_channel_support

channel_types (1) → (many) channel_requirements
channel_types (1) → (many) platform_channel_support
```

### **Missing Relationships (TO BE IMPLEMENTED)**
```
posting_queue (many) → (1) platforms [NEEDS: platform field]
posting_queue (many) → (1) channel_types [NEEDS: channel_type field]
posting_queue (many) → (1) content_processes [NEEDS: process_id field]
```

---

## 🛠️ **UPDATE PROCEDURES**

### **Adding New Platform**
1. **Insert into platforms table**:
   ```sql
   INSERT INTO platforms (name, display_name, description, status, development_status)
   VALUES ('instagram', 'Instagram', 'Photo and video sharing platform', 'active', 'not_started');
   ```

2. **Add platform capabilities**:
   ```sql
   INSERT INTO platform_capabilities (platform_id, capability_type, capability_name, capability_value)
   VALUES (2, 'content', 'max_character_limit', '2200');
   ```

3. **Add platform credentials**:
   ```sql
   INSERT INTO platform_credentials (platform_id, credential_type, credential_key, credential_value)
   VALUES (2, 'api_key', 'access_token', 'your_token_here');
   ```

### **Adding New Channel Type**
1. **Insert into channel_types table**:
   ```sql
   INSERT INTO channel_types (name, display_name, content_type, media_support)
   VALUES ('story_post', 'Story Post', 'mixed', ARRAY['image', 'video']);
   ```

2. **Add platform support**:
   ```sql
   INSERT INTO platform_channel_support (platform_id, channel_type_id, is_supported)
   VALUES (1, 2, true);
   ```

3. **Add channel requirements**:
   ```sql
   INSERT INTO channel_requirements (platform_id, channel_type_id, requirement_category, requirement_key, requirement_value)
   VALUES (1, 2, 'dimensions', 'aspect_ratio', '9:16');
   ```

### **Updating Posting Queue**
1. **Add new queue item**:
   ```sql
   INSERT INTO posting_queue (product_id, scheduled_date, scheduled_time, generated_content, status)
   VALUES (123, '2025-01-28', '17:00:00', 'Generated content here', 'pending');
   ```

2. **Update queue order**:
   ```sql
   UPDATE posting_queue 
   SET queue_order = 1, updated_at = NOW() 
   WHERE id = 456;
   ```

3. **Update status**:
   ```sql
   UPDATE posting_queue 
   SET status = 'published', updated_at = NOW() 
   WHERE id = 456;
   ```

---

## 🚨 **CRITICAL MISSING FIELDS**

### **posting_queue Table Extensions Needed**
The current `posting_queue` table is missing critical fields for the Social Media Command Center:

```sql
-- MISSING FIELDS TO ADD:
ALTER TABLE posting_queue ADD COLUMN platform VARCHAR(50) DEFAULT 'facebook';
ALTER TABLE posting_queue ADD COLUMN channel_type VARCHAR(50) DEFAULT 'feed_post';
ALTER TABLE posting_queue ADD COLUMN content_type VARCHAR(50) DEFAULT 'product';
ALTER TABLE posting_queue ADD COLUMN scheduled_timestamp TIMESTAMP;
ALTER TABLE posting_queue ADD COLUMN platform_post_id VARCHAR(100);
ALTER TABLE posting_queue ADD COLUMN error_message TEXT;
```

### **Migration Script**
```sql
-- Add platform fields to posting_queue
ALTER TABLE posting_queue ADD COLUMN platform VARCHAR(50) DEFAULT 'facebook';
ALTER TABLE posting_queue ADD COLUMN channel_type VARCHAR(50) DEFAULT 'feed_post';
ALTER TABLE posting_queue ADD COLUMN content_type VARCHAR(50) DEFAULT 'product';
ALTER TABLE posting_queue ADD COLUMN scheduled_timestamp TIMESTAMP;
ALTER TABLE posting_queue ADD COLUMN platform_post_id VARCHAR(100);
ALTER TABLE posting_queue ADD COLUMN error_message TEXT;

-- Create indexes for new fields
CREATE INDEX idx_posting_queue_platform ON posting_queue(platform);
CREATE INDEX idx_posting_queue_channel_type ON posting_queue(channel_type);
CREATE INDEX idx_posting_queue_content_type ON posting_queue(content_type);
CREATE INDEX idx_posting_queue_scheduled_timestamp ON posting_queue(scheduled_timestamp);

-- Update existing records
UPDATE posting_queue 
SET platform = 'facebook', 
    channel_type = 'feed_post', 
    content_type = 'product',
    scheduled_timestamp = CASE 
        WHEN scheduled_date IS NOT NULL AND scheduled_time IS NOT NULL 
        THEN (scheduled_date + scheduled_time)::timestamp
        ELSE created_at
    END
WHERE platform IS NULL;
```

---

## 📈 **PERFORMANCE OPTIMIZATION**

### **Current Indexes**
- `idx_posting_queue_order` - Queue ordering
- `idx_posting_queue_product_id` - Product lookups
- `idx_posting_queue_scheduled_datetime` - Date/time queries
- `idx_posting_queue_status` - Status filtering

### **Recommended Additional Indexes**
```sql
-- For Social Media Command Center timeline
CREATE INDEX idx_posting_queue_platform_status ON posting_queue(platform, status);
CREATE INDEX idx_posting_queue_timestamp_status ON posting_queue(scheduled_timestamp, status);
CREATE INDEX idx_posting_queue_content_type ON posting_queue(content_type);
```

---

## 🔍 **COMMON QUERIES**

### **Timeline Queries**
```sql
-- Get unified timeline for all platforms
SELECT pq.*, p.name as platform_name, ct.name as channel_name, cp.name as product_name
FROM posting_queue pq
LEFT JOIN platforms p ON pq.platform = p.name
LEFT JOIN channel_types ct ON pq.channel_type = ct.name
LEFT JOIN clan_products cp ON pq.product_id = cp.id
WHERE pq.status IN ('pending', 'ready', 'published', 'failed')
ORDER BY pq.scheduled_timestamp ASC, pq.created_at ASC;

-- Get platform-specific timeline
SELECT pq.*, cp.name as product_name
FROM posting_queue pq
LEFT JOIN clan_products cp ON pq.product_id = cp.id
WHERE pq.platform = 'facebook' AND pq.status = 'pending'
ORDER BY pq.scheduled_timestamp ASC;
```

### **Analytics Queries**
```sql
-- Count posts by platform
SELECT platform, COUNT(*) as post_count
FROM posting_queue
GROUP BY platform
ORDER BY post_count DESC;

-- Count posts by status
SELECT status, COUNT(*) as count
FROM posting_queue
GROUP BY status
ORDER BY count DESC;

-- Get posting frequency by day
SELECT DATE(scheduled_timestamp) as post_date, COUNT(*) as posts
FROM posting_queue
WHERE scheduled_timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(scheduled_timestamp)
ORDER BY post_date DESC;
```

---

## 🚀 **FUTURE ENHANCEMENTS**

### **Phase 1: Basic Timeline (Immediate)**
- Add missing fields to `posting_queue`
- Create unified timeline API
- Implement platform filtering
- Add status tracking

### **Phase 2: Multi-Platform Support (Short-term)**
- Add Instagram, Twitter, LinkedIn platforms
- Implement platform-specific posting
- Add cross-platform scheduling
- Create platform analytics

### **Phase 3: Advanced Features (Long-term)**
- Add content adaptation system
- Implement A/B testing
- Add performance analytics
- Create team collaboration features

---

## 📝 **MAINTENANCE CHECKLIST**

### **Daily Tasks**
- [ ] Check posting_queue for failed posts
- [ ] Monitor platform API status
- [ ] Review error logs
- [ ] Verify scheduled posts

### **Weekly Tasks**
- [ ] Clean up old queue items
- [ ] Update platform statistics
- [ ] Review performance metrics
- [ ] Backup database

### **Monthly Tasks**
- [ ] Analyze posting patterns
- [ ] Update platform capabilities
- [ ] Review and update requirements
- [ ] Performance optimization

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-27  
**Status**: **ACTIVE REFERENCE**  
**Next Review**: After posting_queue table extensions are implemented
