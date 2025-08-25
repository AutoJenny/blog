# Cross-Promotion System

## Overview

The Cross-Promotion System is a comprehensive marketing feature that displays clan.com products and categories within blog posts to drive traffic and sales. The system integrates with the clan.com API to fetch real product data and displays it in attractive, clickable widgets throughout blog content.

## Architecture

### System Components

#### 1. Blog Launchpad (Frontend/Cache)
- **Service**: `http://localhost:5001`
- **Purpose**: Main user interface and content management
- **Function**: Serves blog previews, manages cross-promotion settings, caches product data

#### 2. Blog Clan API (External API Proxy)
- **Service**: `http://localhost:5007`
- **Purpose**: Proxies requests to clan.com API
- **Function**: Transforms API responses, handles rate limiting, provides product data

#### 3. PostgreSQL Database
- **Purpose**: Local storage of clan.com products and categories
- **Function**: Persistent cache for product data, enables fast widget rendering

### Data Flow

```
Blog Preview (5001) → Blog Clan API (5007) → Clan.com API
                ↓
        PostgreSQL Database (Local Cache)
```

## Database Schema

### Clan Products Table
```sql
CREATE TABLE clan_products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    sku VARCHAR(100),
    url VARCHAR(500),
    image_url VARCHAR(500),
    price DECIMAL(10,2),
    description TEXT,
    has_detailed_data BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Clan Categories Table
```sql
CREATE TABLE clan_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    parent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Post Cross-Promotion Settings
```sql
-- Fields added to post table
cross_promotion_category_id INTEGER,
cross_promotion_product_id INTEGER,
cross_promotion_enabled BOOLEAN DEFAULT FALSE
```

## API Endpoints

### Blog Launchpad Endpoints

#### Cross-Promotion Management
- `GET /cross-promotion` - Cross-promotion management interface
- `GET /api/cross-promotion/<post_id>` - Get cross-promotion settings for a post
- `POST /api/cross-promotion/<post_id>` - Update cross-promotion settings

#### Product Data
- `GET /api/clan/categories` - Get available categories
- `GET /api/clan/products` - Search products
- `GET /api/clan/category/<id>/products` - Get products in category
- `GET /api/clan/product/<id>/related` - Get related products

#### Cache Management
- `POST /api/clan/cache/refresh` - Refresh product cache
- `GET /api/clan/cache/stats` - Get cache statistics
- `POST /api/clan/cache/save-product` - Save individual product

### Blog Clan API Endpoints

#### Product Endpoints
- `GET /api/products` - Get products with optional filtering
- `GET /api/products/<id>` - Get specific product details
- `GET /api/categories` - Get category tree
- `GET /api/categories/<id>/products` - Get products in category
- `GET /api/products/<id>/related` - Get related products

#### Cache Population
- `POST /api/products/download-all-basic` - Download all basic product data
- `POST /api/products/populate-details` - Populate detailed product data

## Cross-Promotion Widget Features

### Widget Types

#### 1. Category-Based Widgets
- **Trigger**: `cross_promotion_category_id` set on post
- **Display**: 3 random products from the selected category
- **Location**: Between sections and at end of post

#### 2. Product-Based Widgets
- **Trigger**: `cross_promotion_product_id` set on post
- **Display**: Selected product + 2 related products
- **Location**: Between sections and at end of post

#### 3. Random Widgets
- **Trigger**: No specific category/product selected
- **Display**: 3 random products from entire catalog
- **Location**: Between sections and at end of post

### Widget Display Features

#### Product Cards
- **Layout**: 3 items across on desktop, responsive on mobile
- **Image**: Square product images with hover effects
- **Price**: Formatted with currency symbol (£), 2 decimal places only if not .00
- **Description**: Hover overlay with truncated text and gradient fade
- **Clickability**: Entire card is clickable, links to product URL

#### Visual Design
- **Grid Layout**: CSS Grid with `repeat(3, 1fr)` on desktop
- **Responsive**: Stacks to single column on mobile
- **Hover Effects**: Description overlay with smooth transitions
- **Loading States**: Loading indicators while fetching data

## Implementation Details

### Product Data Population

#### Phase 1: Basic Data Download
```python
# Download all basic product SKUs
POST /api/products/download-all-basic
```
- Fetches all product SKUs from clan.com API
- Stores basic information (ID, name, SKU, URL)
- Sets `has_detailed_data = FALSE`

#### Phase 2: Detailed Data Population
```python
# Populate detailed data incrementally
POST /api/products/populate-details
```
- Iterates through products with `has_detailed_data = FALSE`
- Calls `getProductData` API for each product
- Updates with image URLs, prices, descriptions
- Sets `has_detailed_data = TRUE`

### Random Product Selection

#### Database Query
```python
def get_random_products(count=3):
    """Get random products from database"""
    cursor.execute("""
        SELECT id, name, sku, url, image_url, price, description
        FROM clan_products 
        WHERE has_detailed_data = TRUE
        ORDER BY RANDOM() 
        LIMIT %s
    """, (count,))
```

#### Category-Based Selection
```python
def get_category_products(category_id, count=3):
    """Get random products from specific category"""
    cursor.execute("""
        SELECT p.id, p.name, p.sku, p.url, p.image_url, p.price, p.description
        FROM clan_products p
        JOIN clan_product_categories pc ON p.id = pc.product_id
        WHERE pc.category_id = %s AND p.has_detailed_data = TRUE
        ORDER BY RANDOM() 
        LIMIT %s
    """, (category_id, count))
```

### Frontend Integration

#### Template Integration
```html
<!-- Cross-promotion widget in post template -->
{% if post.cross_promotion_enabled %}
    <div class="cross-promotion-widget">
        <div class="product-grid">
            {% for product in cross_promotion_products %}
            <a href="{{ product.url }}" class="product-card" target="_blank">
                <div class="product-image">
                    <img src="{{ product.image_url }}" alt="{{ product.name }}">
                </div>
                <h4>{{ product.name }}</h4>
                <div class="price">£{{ product.price }}</div>
                <div class="product-description-overlay">
                    {{ product.description }}
                </div>
                <div class="btn">View Product</div>
            </a>
            {% endfor %}
        </div>
    </div>
{% endif %}
```

#### CSS Styling
```css
.product-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin: 30px 0;
}

.product-card {
    max-width: 250px;
    margin: 0 auto;
    border: 1px solid #eee;
    border-radius: 8px;
    overflow: hidden;
    text-decoration: none;
    color: inherit;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.product-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.product-description-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.8));
    color: white;
    padding: 20px 15px 15px;
    opacity: 0;
    transition: opacity 0.3s ease;
    pointer-events: none;
    overflow: hidden;
    max-height: 60px;
}

.product-card:hover .product-description-overlay {
    opacity: 1;
}
```

#### JavaScript Price Formatting
```javascript
function formatPrice(price) {
    if (!price) return '£29.99';
    
    const numPrice = parseFloat(price);
    if (isNaN(numPrice)) return '£29.99';
    
    const formatted = numPrice.toFixed(2);
    if (formatted.endsWith('.00')) {
        return `£${numPrice.toFixed(0)}`;
    } else {
        return `£${formatted}`;
    }
}
```

## User Interface

### Cross-Promotion Management Page

#### Features
- **Post Selection**: Dropdown to select blog posts
- **Category Selection**: Dropdown with all available categories
- **Product Selection**: Search and select specific products
- **Enable/Disable**: Toggle cross-promotion for posts
- **Preview**: Link to preview post with widgets

#### Interface Elements
```html
<div class="cross-promotion-controls">
    <select id="post-selector">
        <option value="">Select a post...</option>
        {% for post in posts %}
        <option value="{{ post.id }}">{{ post.title }}</option>
        {% endfor %}
    </select>
    
    <div class="promotion-type">
        <label>
            <input type="radio" name="promotion-type" value="category">
            Category-based promotion
        </label>
        <select id="category-selector" disabled>
            <option value="">Select category...</option>
        </select>
    </div>
    
    <div class="promotion-type">
        <label>
            <input type="radio" name="promotion-type" value="product">
            Product-based promotion
        </label>
        <input type="text" id="product-search" placeholder="Search products..." disabled>
        <select id="product-selector" disabled>
            <option value="">Select product...</option>
        </select>
    </div>
    
    <button id="save-settings">Save Settings</button>
    <a href="/preview/{{ selected_post.id }}" target="_blank">Preview Post</a>
</div>
```

### Blog Launchpad Integration

#### Landing Page Module
- **Status**: Active (green indicator)
- **Stats**: Shows total posts and configured posts
- **Actions**: Manage Cross-Promotion, View Example
- **Integration**: Links to cross-promotion management interface

## Data Management

### Cache Refresh Process

#### Manual Refresh
```python
@app.route('/api/clan/cache/refresh', methods=['POST'])
def refresh_clan_cache():
    """Manually refresh the cache from the API."""
    try:
        from clan_api import refresh_cache
        stats = refresh_cache()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

#### Automatic Population
```python
@app.route('/api/products/populate-details', methods=['POST'])
def populate_product_details():
    """Populate detailed data for all products."""
    try:
        # Get products without detailed data
        products = get_products_without_details()
        
        for product in products:
            # Fetch detailed data from API
            detailed_data = get_product_details(product['id'])
            
            # Save to database
            save_product_details(product['id'], detailed_data)
            
            # Rate limiting
            time.sleep(0.5)
        
        return jsonify({'success': True, 'processed': len(products)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Error Handling

#### API Error Handling
```python
def handle_api_error(response, endpoint):
    """Handle API errors with appropriate logging and fallbacks."""
    if response.status_code == 429:
        logger.warning(f"Rate limit exceeded for {endpoint}")
        time.sleep(60)  # Wait 1 minute
        return None
    elif response.status_code == 403:
        logger.error(f"Authentication failed for {endpoint}")
        return None
    else:
        logger.error(f"API error {response.status_code} for {endpoint}")
        return None
```

#### Fallback Data
```python
def get_fallback_products():
    """Return fallback products when API is unavailable."""
    return [
        {
            'id': 1,
            'name': 'Sample Product',
            'price': '29.99',
            'image_url': '/static/images/placeholder.jpg',
            'url': '#'
        }
    ]
```

## Performance Optimization

### Database Indexing
```sql
-- Index for random product selection
CREATE INDEX idx_clan_products_detailed ON clan_products(has_detailed_data);

-- Index for category-based queries
CREATE INDEX idx_product_categories ON clan_product_categories(category_id, product_id);

-- Index for product search
CREATE INDEX idx_clan_products_name ON clan_products(name);
```

### Caching Strategy
- **Product Data**: Cached in PostgreSQL for fast access
- **Category Data**: Cached in PostgreSQL with parent-child relationships
- **API Responses**: Transformed and stored locally
- **Widget Rendering**: Server-side rendering with cached data

### Rate Limiting
- **API Calls**: 0.5 second delay between individual product requests
- **Batch Processing**: 0.1 second delay between batches
- **Error Handling**: Exponential backoff for failed requests
- **Timeout**: 60 second timeout for API requests

## Configuration

### Environment Variables
```bash
# Database Configuration
DB_HOST=localhost
DB_NAME=blog
DB_USER=nickfiddes
DB_PASSWORD=

# Clan.com API Configuration
CLAN_API_BASE_URL=https://clan.com/clan/api
CLAN_API_USER=blog
CLAN_API_KEY=your_api_key_here

# Service Configuration
BLOG_LAUNCHPAD_PORT=5001
BLOG_CLAN_API_PORT=5007
```

### Service Configuration
```python
# blog-launchpad configuration
app.config['CLAN_API_URL'] = 'http://localhost:5007'

# blog-clan-api configuration
app.config['CLAN_API_BASE_URL'] = 'https://clan.com/clan/api'
app.config['CLAN_API_USER'] = 'blog'
app.config['CLAN_API_KEY'] = os.getenv('CLAN_API_KEY')
```

## Monitoring and Maintenance

### Health Checks
```python
@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'blog-launchpad',
        'database': check_database_connection(),
        'clan_api': check_clan_api_connection()
    })
```

### Cache Statistics
```python
@app.route('/api/clan/cache/stats')
def get_clan_cache_stats():
    """Get cache statistics."""
    try:
        from clan_cache import ClanCache
        cache = ClanCache()
        stats = cache.get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

## Troubleshooting

### Common Issues

#### 1. No Products Displaying
- **Check**: Database has products with `has_detailed_data = TRUE`
- **Solution**: Run cache refresh and populate details
- **Command**: `curl -X POST http://localhost:5001/api/clan/cache/refresh`

#### 2. Broken Product Images
- **Check**: Image URLs in database are valid
- **Solution**: Re-populate product details
- **Command**: `curl -X POST http://localhost:5007/api/products/populate-details`

#### 3. API Rate Limiting
- **Check**: API response status codes
- **Solution**: Implement longer delays between requests
- **Log**: Check application logs for 429 errors

#### 4. Database Connection Issues
- **Check**: Database service is running
- **Solution**: Verify connection parameters
- **Test**: `psql -h localhost -U nickfiddes -d blog`

### Debug Commands

#### Check Cache Status
```bash
curl http://localhost:5001/api/clan/cache/stats
```

#### Test API Connectivity
```bash
curl http://localhost:5007/api/categories
```

#### Check Product Count
```bash
psql -h localhost -U nickfiddes -d blog -c "SELECT COUNT(*) FROM clan_products WHERE has_detailed_data = TRUE;"
```

#### View Cross-Promotion Settings
```bash
psql -h localhost -U nickfiddes -d blog -c "SELECT id, title, cross_promotion_enabled, cross_promotion_category_id, cross_promotion_product_id FROM post WHERE cross_promotion_enabled = TRUE;"
```

## Future Enhancements

### Planned Features
1. **A/B Testing**: Test different product combinations
2. **Analytics**: Track click-through rates and conversions
3. **Dynamic Pricing**: Show real-time pricing from API
4. **Personalization**: Show products based on user behavior
5. **Scheduling**: Schedule different promotions for different times

### Technical Improvements
1. **Redis Caching**: Add Redis for faster data access
2. **Background Jobs**: Use Celery for cache population
3. **API Versioning**: Support multiple clan.com API versions
4. **Microservice Architecture**: Split into separate services
5. **Containerization**: Docker deployment for all services

## Summary

The Cross-Promotion System provides a robust, scalable solution for integrating clan.com products into blog content. With comprehensive caching, error handling, and user-friendly interfaces, it enables effective product marketing while maintaining excellent performance and reliability.

**Key Features:**
- ✅ Real-time product data from clan.com API
- ✅ Local caching for fast widget rendering
- ✅ Flexible category and product-based promotion
- ✅ Responsive design with hover effects
- ✅ Comprehensive error handling and fallbacks
- ✅ User-friendly management interface
- ✅ Performance optimized with database indexing
- ✅ Health monitoring and statistics
