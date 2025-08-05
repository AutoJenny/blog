# Unified Image Processing Interface Implementation Plan

**Date Created**: August 5, 2025  
**Status**: Planning Phase  
**Last Updated**: August 5, 2025  

---

## 🎯 **Project Overview**

### **Objective**
Transform the current blog-images service (port 5005) from a basic upload interface to a comprehensive unified image processing system that handles headers, sections, and featured images through a single streamlined interface.

### **Current State Analysis**
- **Service**: `blog-images` running on port 5005
- **Current Interface**: Basic upload functionality with tabs (Generate/Upload)
- **Workflow Integration**: Embedded in iframe at `http://localhost:5000/workflow/posts/53/writing/images/section_illustrations`
- **API Dependencies**: Calls `http://localhost:5000/api/sections/${postId}` for section data
- **File Storage**: `static/content/posts/{post_id}/sections/{section_id}/raw/`

### **Target State**
- **Unified Interface**: Single dashboard handling all image types
- **Self-Contained**: No dependencies on other services
- **Enhanced Features**: Batch processing, progress tracking, statistics
- **Workflow Compatible**: Maintains iframe integration
- **Backward Compatible**: All existing functionality preserved

---

## 📋 **Implementation Phases**

### **Phase 1: API Integration & Backend Preparation**
**Priority**: Critical  
**Estimated Time**: 2-3 hours  
**Dependencies**: None  

#### **1.1 Add Section API to blog-images Service**
- [x] **File**: `blog-images/app.py`
- [x] **Endpoint**: `GET /api/sections/<post_id>`
- [x] **Purpose**: Eliminate dependency on port 5000 for section data
- [x] **Implementation**: 
  ```python
  @app.route('/api/sections/<int:post_id>')
  def get_sections(post_id):
      """Get all sections for a post from database"""
      # Query post_section table directly
      # Return JSON with sections array
  ```
- [x] **Database Query**: 
  ```sql
  SELECT id, section_heading, section_description, section_order, status
  FROM post_section 
  WHERE post_id = %s 
  ORDER BY section_order
  ```
- [x] **Response Format**: 
  ```json
  {
    "sections": [
      {
        "id": 710,
        "section_heading": "Ancient Celtic Story-telling",
        "section_description": "Overview of Celtic traditions",
        "section_order": 1,
        "status": "draft"
      }
    ]
  }
  ```

#### **1.2 Extend Upload API for Unified Interface**
- [x] **File**: `blog-images/app.py`
- [x] **Enhance**: Existing `/api/upload` endpoint
- [x] **Add Parameters**: `image_type` (header, section, featured)
- [x] **Update Logic**: 
  ```python
  def get_upload_path(post_id, image_type, section_id=None):
      if image_type == 'header':
          return f"static/content/posts/{post_id}/header/raw"
      elif image_type == 'section':
          return f"static/content/posts/{post_id}/sections/{section_id}/raw"
      elif image_type == 'featured':
          return f"static/content/posts/{post_id}/featured/raw"
  ```
- [x] **Maintain Backward Compatibility**: Default to section upload if no type specified
- [x] **Validation**: Ensure section_id provided for section uploads

#### **1.3 Add Image Management APIs**
- [x] **File**: `blog-images/app.py`
- [x] **New Endpoints**:
  - [x] `GET /api/images/<post_id>` - Get all images for a post
  - [x] `GET /api/images/<post_id>/<image_type>` - Get images by type
  - [ ] `POST /api/images/batch-process` - Batch processing
  - [ ] `DELETE /api/images/<image_id>` - Delete images
  - [x] `GET /api/images/stats/<post_id>` - Get image statistics

- [x] **Implementation Details**:
  ```python
  @app.route('/api/images/<int:post_id>')
  def get_all_images(post_id):
      """Get all images for a post across all types"""
      
  @app.route('/api/images/<int:post_id>/<image_type>')
  def get_images_by_type(post_id, image_type):
      """Get images for specific type (header, section, featured)"""
      
  @app.route('/api/images/batch-process', methods=['POST'])
  def batch_process_images():
      """Process multiple images with same settings"""
      
  @app.route('/api/images/stats/<int:post_id>')
  def get_image_stats(post_id):
      """Get image count, sizes, processing status"""
  ```

#### **1.4 Database Integration**
- [x] **File**: `blog-images/app.py`
- [x] **Add**: Database connection function
- [x] **Import**: `psycopg2` for PostgreSQL access
- [x] **Environment Variables**: 
  - `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- [x] **Connection Function**:
  ```python
  def get_db_conn():
      return psycopg2.connect(
          host=os.getenv('DB_HOST', 'localhost'),
          database=os.getenv('DB_NAME', 'blog'),
          user=os.getenv('DB_USER', 'nickfiddes'),
          password=os.getenv('DB_PASSWORD', '')
      )
  ```

---

### **Phase 2: Interface Migration**
**Priority**: High  
**Estimated Time**: 3-4 hours  
**Dependencies**: Phase 1 completion  

#### **2.1 Make Mockup the Main Interface**
- [x] **File**: `blog-images/templates/index.html`
- [x] **Action**: Replace current interface with enhanced mockup
- [x] **Source**: `blog-images/templates/mockup.html`
- [x] **Enhancements**:
  - [x] Add working upload functionality
  - [x] Integrate section data loading
  - [x] Add iframe communication for workflow
  - [x] Implement post selector functionality
  - [x] Add image type switching

#### **2.2 Preserve Upload Tab Functionality**
- [x] **Extract**: Upload functionality from current `index.html`
- [x] **Files to Reference**:
  - `blog-images/templates/index.html` (lines 300-550)
  - JavaScript functions: `uploadImage()`, `handleFileSelect()`, `loadSections()`
- [x] **Integrate**: Into new unified interface
- [x] **Features to Preserve**:
  - [x] Drag and drop file upload
  - [x] File preview functionality
  - [x] Section selection dropdown
  - [x] Upload progress feedback
  - [x] Existing images display
  - [x] Error handling and status messages

#### **2.3 Add Workflow Integration Features**
- [x] **File**: `blog-images/templates/index.html`
- [x] **Add**: Iframe communication for resizing
- [x] **Implementation**:
  ```javascript
  // Send height updates to parent iframe
  function updateIframeHeight() {
      if (window.parent !== window) {
          window.parent.postMessage({
              type: 'resize',
              source: 'blog-images',
              height: document.body.scrollHeight
          }, '*');
      }
  }
  ```
- [ ] **Add**: Post ID parameter handling from URL
- [ ] **Add**: Context detection (workflow vs standalone)
- [ ] **Enhance**: Responsive design for iframe embedding

#### **2.4 Enhanced Interface Features**
- [ ] **File**: `blog-images/templates/index.html`
- [ ] **Add**: Real-time section data loading
- [ ] **Add**: Image type switching (header/section/featured)
- [ ] **Add**: Batch processing controls
- [ ] **Add**: Progress tracking visualization
- [ ] **Add**: Statistics dashboard
- [ ] **Add**: Image management grid
- [ ] **Add**: Processing pipeline visualization

---

### **Phase 3: Enhanced Features**
**Priority**: Medium  
**Estimated Time**: 4-5 hours  
**Dependencies**: Phase 2 completion  

#### **3.1 Add Image Processing Pipeline**
- [ ] **File**: `blog-images/app.py`
- [ ] **New Endpoints**:
  - [ ] `POST /api/process/optimize` - Image optimization
  - [ ] `POST /api/process/watermark` - Add watermarks
  - [ ] `POST /api/process/caption` - Generate captions
  - [ ] `GET /api/process/status/<job_id>` - Check processing status

- [ ] **Implementation Details**:
  ```python
  @app.route('/api/process/optimize', methods=['POST'])
  def optimize_images():
      """Optimize images with specified quality settings"""
      
  @app.route('/api/process/watermark', methods=['POST'])
  def watermark_images():
      """Add watermarks to images"""
      
  @app.route('/api/process/caption', methods=['POST'])
  def generate_captions():
      """Generate captions for images using AI"""
  ```

- [ ] **Processing Queue**:
  - [ ] Implement job queue system
  - [ ] Add progress tracking
  - [ ] Add error handling and retry logic
  - [ ] Add job cancellation

#### **3.2 Add Image Management Features**
- [ ] **File**: `blog-images/app.py`
- [ ] **New Endpoints**:
  - [ ] `GET /api/images/<image_id>/preview` - Get image preview
  - [ ] `PUT /api/images/<image_id>/metadata` - Update metadata
  - [ ] `POST /api/images/<image_id>/duplicate` - Duplicate image
  - [ ] `GET /api/images/<image_id>/versions` - Get image versions

- [ ] **Features**:
  - [ ] Image preview and editing
  - [ ] Status tracking (raw, optimized, final)
  - [ ] Image metadata management
  - [ ] Bulk operations (select multiple, delete, process)
  - [ ] Image versioning

#### **3.3 Add Statistics and Monitoring**
- [ ] **File**: `blog-images/app.py`
- [ ] **New Endpoints**:
  - [ ] `GET /api/stats/overview` - Overall statistics
  - [ ] `GET /api/stats/processing` - Processing statistics
  - [ ] `GET /api/stats/storage` - Storage usage statistics

- [ ] **Statistics Dashboard**:
  - [ ] Image count by type and status
  - [ ] Total storage usage
  - [ ] Processing queue status
  - [ ] Error rates and performance metrics
  - [ ] Recent activity log

---

### **Phase 4: Testing & Deployment**
**Priority**: High  
**Estimated Time**: 2-3 hours  
**Dependencies**: Phase 3 completion  

#### **4.1 Backward Compatibility Testing**
- [ ] **Test**: Upload functionality still works
  - [ ] Section image uploads
  - [ ] File validation
  - [ ] Error handling
  - [ ] Progress feedback
- [ ] **Verify**: Workflow integration unchanged
  - [ ] Iframe embedding works
  - [ ] Height communication works
  - [ ] Post ID parameter handling
- [ ] **Check**: All existing features preserved
  - [ ] Drag and drop
  - [ ] File preview
  - [ ] Section selection
  - [ ] Existing images display
- [ ] **Validate**: API endpoints work as expected
  - [ ] `/api/upload` endpoint
  - [ ] `/api/images/<post_id>/<section_id>` endpoint
  - [ ] File serving endpoints

#### **4.2 New Features Testing**
- [ ] **Test**: Unified interface functionality
  - [ ] Image type switching
  - [ ] Post selection
  - [ ] Statistics display
  - [ ] Processing controls
- [ ] **Verify**: Batch processing works
  - [ ] Multiple image selection
  - [ ] Processing queue
  - [ ] Progress tracking
  - [ ] Error handling
- [ ] **Check**: Image management features
  - [ ] Image preview
  - [ ] Metadata editing
  - [ ] Bulk operations
  - [ ] Status updates
- [ ] **Validate**: Statistics and monitoring
  - [ ] Real-time updates
  - [ ] Data accuracy
  - [ ] Performance metrics

#### **4.3 Performance Testing**
- [ ] **Test**: Large file uploads
  - [ ] 16MB+ files
  - [ ] Multiple simultaneous uploads
  - [ ] Network interruption handling
- [ ] **Verify**: Batch processing performance
  - [ ] Queue management
  - [ ] Memory usage
  - [ ] Processing speed
- [ ] **Check**: Memory usage
  - [ ] Large image handling
  - [ ] Concurrent operations
  - [ ] Memory leaks
- [ ] **Validate**: Response times
  - [ ] API endpoint performance
  - [ ] Page load times
  - [ ] Interface responsiveness

---

## 🔧 **Technical Implementation Details**

### **File Structure Changes**
```
blog-images/
├── app.py                          # Main Flask application
├── templates/
│   ├── index.html                  # New unified interface
│   └── mockup.html                 # Original mockup (backup)
├── static/
│   └── content/
│       └── posts/
│           └── {post_id}/
│               ├── header/
│               │   ├── raw/
│               │   ├── optimized/
│               │   └── web/
│               ├── sections/
│               │   └── {section_id}/
│               │       ├── raw/
│               │       ├── optimized/
│               │       └── web/
│               └── featured/
│                   ├── raw/
│                   ├── optimized/
│                   └── web/
└── docs/
    └── temp/
        └── unified_image_interface_implementation_plan.md
```

### **Database Schema Requirements**
```sql
-- Existing tables used:
-- post_section: For section data
-- post: For post information
-- images: For image metadata (if exists)

-- New tables may be needed:
-- image_processing_jobs: For tracking processing jobs
-- image_metadata: For extended image metadata
-- processing_queue: For batch processing queue
```

### **API Endpoint Specifications**

#### **Existing Endpoints (Preserve)**
- `GET /` - Main interface
- `POST /api/upload` - Image upload (enhanced)
- `GET /api/images/<post_id>/<section_id>` - Get section images
- `GET /static/content/posts/<post_id>/sections/<section_id>/raw/<filename>` - Serve images

#### **New Endpoints (Add)**
- `GET /api/sections/<post_id>` - Get sections for post
- `GET /api/images/<post_id>` - Get all images for post
- `GET /api/images/<post_id>/<image_type>` - Get images by type
- `POST /api/images/batch-process` - Batch processing
- `DELETE /api/images/<image_id>` - Delete image
- `GET /api/images/stats/<post_id>` - Get image statistics
- `POST /api/process/optimize` - Optimize images
- `POST /api/process/watermark` - Watermark images
- `POST /api/process/caption` - Generate captions
- `GET /api/process/status/<job_id>` - Check processing status

### **Environment Variables**
```bash
# Database
DB_HOST=localhost
DB_NAME=blog
DB_USER=nickfiddes
DB_PASSWORD=

# Service Configuration
PORT=5005
UPLOAD_FOLDER=static/content/posts
MAX_CONTENT_LENGTH=16777216  # 16MB

# Processing Configuration
PROCESSING_QUEUE_SIZE=10
MAX_CONCURRENT_JOBS=3
```

### **Dependencies to Add**
```python
# Additional imports needed in app.py
import psycopg2
import psycopg2.extras
from datetime import datetime
import json
import logging
from werkzeug.utils import secure_filename
import os
```

---

## 🚨 **Risk Mitigation & Rollback Plan**

### **Backup Strategy**
- [ ] **Code Backup**: Git commit before each phase
- [ ] **Database Backup**: Full PostgreSQL dump before changes
- [ ] **File Backup**: Copy current templates before replacement
- [ ] **Configuration Backup**: Save current app.py before modifications

### **Rollback Plan**
- [ ] **Phase 1 Rollback**: Restore original app.py, remove new endpoints
- [ ] **Phase 2 Rollback**: Restore original index.html template
- [ ] **Phase 3 Rollback**: Remove new processing endpoints
- [ ] **Full Rollback**: Restore from git commit and database backup

### **Testing Strategy**
- [ ] **Development Testing**: Test each phase in isolation
- [ ] **Integration Testing**: Test with workflow integration
- [ ] **Performance Testing**: Load testing with multiple users
- [ ] **Compatibility Testing**: Test with existing data and workflows

---

## 📊 **Success Metrics**

### **Functional Requirements**
- [ ] All existing upload functionality preserved
- [ ] Workflow integration unchanged
- [ ] New unified interface operational
- [ ] Batch processing working
- [ ] Statistics dashboard functional

### **Performance Requirements**
- [ ] Upload response time < 2 seconds
- [ ] Page load time < 3 seconds
- [ ] Memory usage < 512MB
- [ ] Support for 10+ concurrent users

### **Quality Requirements**
- [ ] Zero data loss during migration
- [ ] 100% backward compatibility
- [ ] Comprehensive error handling
- [ ] Detailed logging and monitoring

---

## 📝 **Implementation Notes**

### **Critical Considerations**
1. **Database Connections**: Ensure proper connection pooling and error handling
2. **File Permissions**: Verify write permissions for new directory structures
3. **Cross-Origin Issues**: Handle iframe communication properly
4. **Memory Management**: Monitor memory usage during batch processing
5. **Error Handling**: Comprehensive error handling for all new endpoints

### **Future Enhancements**
1. **AI Integration**: Add AI-powered image generation
2. **Advanced Processing**: Add more image processing options
3. **User Management**: Add user authentication and permissions
4. **API Versioning**: Implement proper API versioning
5. **Caching**: Add Redis caching for performance

---

**Document Status**: Ready for Review  
**Next Action**: Git commit and database backup before implementation 