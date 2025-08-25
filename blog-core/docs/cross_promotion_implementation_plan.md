# Cross-Promotion System Implementation Plan

## 🎯 **Project Overview**

Implementing product cross-promotion system for blog posts with two marketing elements:
1. **Category Cross-Sell**: Between 2nd and 3rd sections
2. **Product Cross-Sell**: Below the final section

**Widget Syntax:**
- Category: `{{widget type="swcatalog/widget_crossSell_category" category_id="24" title="Some Title"}}`
- Product: `{{widget type="swcatalog/widget_crossSell_product" product_id="52499" title="Some Title"}}`

## 🏗️ **Architecture & Framework**

### **Current Server Structure:**
- **Port 5000 (Blog Core)**: Main workflow, database operations, server management
- **Port 5001 (Blog Launchpad)**: Preview system, project management (EXPANSION TARGET)
- **Port 5002 (Blog LLM Actions)**: AI content generation
- **Port 5003 (Blog Post Sections)**: Section management
- **Port 5004 (Blog Post Info)**: Post metadata management
- **Port 5005 (Blog Images)**: Image processing pipeline

### **Implementation Strategy:**
- **Central Hub**: Blog-Launchpad (Port 5001) for marketing and syndication
- **Database**: Extend `post` table with cross-promotion fields
- **Preview**: Enhanced preview with widget placeholders
- **Export**: Clean HTML generation for clan.com

## 📊 **Database Schema Changes**

### **New Fields to Add to `post` Table:**
```sql
ALTER TABLE post ADD COLUMN cross_promotion_category_id INTEGER;
ALTER TABLE post ADD COLUMN cross_promotion_category_title TEXT;
ALTER TABLE post ADD COLUMN cross_promotion_product_id INTEGER;
ALTER TABLE post ADD COLUMN cross_promotion_product_title TEXT;
```

### **Field Descriptions:**
- `cross_promotion_category_id`: Magento category ID for cross-sell widget
- `cross_promotion_category_title`: Display title for category widget
- `cross_promotion_product_id`: Magento product ID for cross-sell widget
- `cross_promotion_product_title`: Display title for product widget

## 🔧 **Implementation Phases**

### **Phase 1: Database & Backend (COMPLETED)**
- [x] Add cross-promotion fields to `post` table
- [x] Update `blog-launchpad/app.py` to fetch cross-promotion data
- [x] Create API endpoints for cross-promotion management

### **Phase 2: Template Enhancement (COMPLETED)**
- [x] Modify `post_preview.html` to include widget placeholders
- [x] Add conditional logic for widget placement
- [x] Create separate export template for clan.com
- [x] Implement widget handling: raw for Magento, live data for local preview

### **Phase 3: Management Interface (COMPLETED)**
- [x] Create cross-promotion management page in blog-launchpad
- [x] Add form for selecting categories/products and titles
- [x] Implement preview functionality

### **Phase 4: Integration & Testing (PLANNED)**
- [ ] Test widget placement logic
- [ ] Validate export functionality
- [ ] Create documentation for clan.com integration

## 🎨 **Template Enhancement Strategy**

### **Current Template Structure:**
```html
<div class="sections">
    {% for section in sections %}
    <div class="section">
        <!-- Section content -->
    </div>
    {% endfor %}
</div>
```

### **Enhanced Structure with Widgets:**
```html
<div class="sections">
    {% for section in sections %}
    <div class="section">
        <!-- Section content -->
    </div>
    
    <!-- Insert category widget after 2nd section -->
    {% if loop.index == 2 and post.cross_promotion_category_id %}
    <div class="cross-promotion-widget category-widget">
        {% if request.args.get('export') %}
            <!-- Raw widget for Magento -->
            {{widget type="swcatalog/widget_crossSell_category" 
                    category_id="{{ post.cross_promotion_category_id }}" 
                    title="{{ post.cross_promotion_category_title }}"}}
        {% else %}
            <!-- Live data call for local preview -->
            <div class="widget-preview" data-widget-type="category" 
                 data-category-id="{{ post.cross_promotion_category_id }}"
                 data-title="{{ post.cross_promotion_category_title }}">
                <div class="widget-loading">Loading category products...</div>
            </div>
        {% endif %}
    </div>
    {% endif %}
    {% endfor %}
    
    <!-- Insert product widget after final section -->
    {% if post.cross_promotion_product_id %}
    <div class="cross-promotion-widget product-widget">
        {% if request.args.get('export') %}
            <!-- Raw widget for Magento -->
            {{widget type="swcatalog/widget_crossSell_product" 
                    product_id="{{ post.cross_promotion_product_id }}" 
                    title="{{ post.cross_promotion_product_title }}"}}
        {% else %}
            <!-- Live data call for local preview -->
            <div class="widget-preview" data-widget-type="product" 
                 data-product-id="{{ post.cross_promotion_product_id }}"
                 data-title="{{ post.cross_promotion_product_title }}">
                <div class="widget-loading">Loading related products...</div>
            </div>
        {% endif %}
    </div>
    {% endif %}
</div>
```

## 🔌 **Widget Handling Strategy**

### **Local Preview (Live Data):**
- **Category Widget**: Call `clan.com/api/category/{id}/products` to fetch live product data
- **Product Widget**: Call `clan.com/api/product/{id}/related` to fetch related products
- **Display**: Render as styled product cards with images, titles, prices
- **Fallback**: Show placeholder if API calls fail

### **Export Mode (Raw Widgets):**
- **URL Parameter**: `?export=true` triggers raw widget mode
- **Output**: Clean HTML with Magento widget syntax
- **Purpose**: Direct upload to clan.com for Magento processing

## 🎛️ **Management Interface Design**

### **Location:** `http://localhost:5001/cross-promotion/<post_id>`

### **Features:**
- **Category Selection**: Dropdown with available Magento categories
- **Product Selection**: Search/select interface for Magento products
- **Title Editing**: Text fields for widget display titles
- **Live Preview**: Toggle between preview modes
- **Export Button**: Generate clan.com-ready HTML
- **Save/Update**: API endpoints for persisting changes

### **UI Components:**
- **Widget Configuration Panel**: Form for setting up both widgets
- **Preview Toggle**: Switch between local preview and export mode
- **Product Search**: Autocomplete for finding products by name/SKU
- **Category Browser**: Tree view of available categories
- **Export Options**: Download HTML, copy to clipboard, etc.

## 🔄 **API Endpoints**

### **Blog-Launchpad (Port 5001):**
```
GET  /cross-promotion/<int:post_id>          # Management interface
GET  /api/cross-promotion/<int:post_id>      # Get cross-promotion data
POST /api/cross-promotion/<int:post_id>      # Update cross-promotion data
GET  /preview/<int:post_id>/export           # Export mode preview
GET  /api/clan/categories                    # Fetch available categories
GET  /api/clan/products                      # Search products
GET  /api/clan/category/<int:id>/products    # Get category products
GET  /api/clan/product/<int:id>/related      # Get related products
```

## 🎯 **Key Implementation Decisions**

### **Widget Placement Logic:**
- Use Jinja2 `loop.index` for accurate section counting
- Handle edge cases (empty sections, filtered content)
- Ensure widgets appear in correct positions regardless of content

### **Data Fetching Strategy:**
- **Local Preview**: Live API calls to clan.com for real-time data
- **Export Mode**: Raw widget syntax for Magento processing
- **Fallback Handling**: Graceful degradation if APIs are unavailable

### **User Experience:**
- **Visual Indicators**: Clear widget placement markers in preview
- **Toggle Controls**: Easy switching between preview modes
- **Error Handling**: Informative messages for missing data

## 🚀 **Next Steps**

### **Immediate (Current Session):**
1. ✅ Save implementation plan to docs
2. ✅ Implement database schema changes
3. ✅ Update blog-launchpad backend
4. ✅ Enhance preview template with widgets
5. ✅ Implement widget handling logic

### **Next Session:**
1. ✅ Design and implement management UI
2. 🔧 Create API endpoints for clan.com integration
3. 🧪 Test widget placement and data fetching
4. 📚 Document clan.com integration process

## 📝 **Technical Notes**

### **Environment Variables Needed:**
```
CLAN_API_BASE_URL=https://clan.com/api
CLAN_API_KEY=your_api_key_here
```

### **Dependencies to Add:**
- `requests` for API calls to clan.com
- `jinja2` for template enhancements (already available)

### **Error Handling:**
- API timeout handling for clan.com calls
- Graceful fallback for missing cross-promotion data
- Validation of category/product IDs

### **Performance Considerations:**
- Cache category/product data to reduce API calls
- Lazy loading of widget content
- Optimize database queries for cross-promotion data

---

**Last Updated:** Current session
**Status:** Phase 1, 2 & 3 completed, Phase 4 ready to start
**Next Milestone:** Integration & Testing
