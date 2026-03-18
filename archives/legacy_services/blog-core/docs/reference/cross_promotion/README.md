# Cross-Promotion System Documentation

## Overview

This directory contains comprehensive documentation for the Cross-Promotion System, a marketing feature that displays clan.com products and categories within blog posts to drive traffic and sales.

## Documentation Structure

### Core Documentation
- **[cross_promotion_system.md](cross_promotion_system.md)** - Comprehensive guide to the cross-promotion system
  - Architecture overview and system components
  - Database schema and API endpoints
  - Widget features and implementation details
  - User interface and data management
  - Performance optimization and troubleshooting

## System Components

### Core Services
- **Blog Launchpad** (`http://localhost:5001`) - Main user interface and content management
- **Blog Clan API** (`http://localhost:5007`) - External API proxy for clan.com
- **PostgreSQL Database** - Local storage of clan.com products and categories

### Key Features
- **Product Widgets** - Display 3 products in responsive grid layout
- **Category-Based Promotion** - Show products from specific categories
- **Product-Based Promotion** - Show selected product with related items
- **Random Selection** - Display random products from entire catalog
- **Hover Effects** - Interactive product cards with description overlays
- **Real-Time Data** - Live product data from clan.com API
- **Local Caching** - Fast widget rendering with cached data

## Quick Start

### 1. System Overview
The Cross-Promotion System integrates clan.com products into blog posts through:
- **Product Data Caching** - Stores product information locally
- **Widget Rendering** - Displays products in attractive layouts
- **Management Interface** - Configure promotion settings per post

### 2. Key Components
- **Database Tables**: `clan_products`, `clan_categories`, post cross-promotion fields
- **API Endpoints**: Product data, cache management, cross-promotion settings
- **User Interface**: Management page, preview functionality, statistics

### 3. Widget Types
- **Category Widgets**: 3 random products from selected category
- **Product Widgets**: Selected product + 2 related products
- **Random Widgets**: 3 random products from entire catalog

## Architecture

### Data Flow
```
Blog Preview (5001) → Blog Clan API (5007) → Clan.com API
                ↓
        PostgreSQL Database (Local Cache)
```

### Database Schema
- **clan_products**: Product information with detailed data flags
- **clan_categories**: Category hierarchy and relationships
- **post table**: Cross-promotion settings (category_id, product_id, enabled)

## API Endpoints

### Blog Launchpad
- `GET /cross-promotion` - Management interface
- `GET /api/cross-promotion/<post_id>` - Get settings
- `POST /api/cross-promotion/<post_id>` - Update settings
- `GET /api/clan/categories` - Available categories
- `GET /api/clan/products` - Search products
- `POST /api/clan/cache/refresh` - Refresh cache

### Blog Clan API
- `GET /api/products` - Get products with filtering
- `GET /api/categories` - Get category tree
- `POST /api/products/download-all-basic` - Download basic data
- `POST /api/products/populate-details` - Populate detailed data

## Widget Features

### Product Cards
- **Layout**: 3 items across on desktop, responsive on mobile
- **Image**: Square product images with hover effects
- **Price**: Formatted with currency symbol (£), 2 decimal places only if not .00
- **Description**: Hover overlay with truncated text and gradient fade
- **Clickability**: Entire card is clickable, links to product URL

### Visual Design
- **Grid Layout**: CSS Grid with `repeat(3, 1fr)` on desktop
- **Responsive**: Stacks to single column on mobile
- **Hover Effects**: Description overlay with smooth transitions
- **Loading States**: Loading indicators while fetching data

## Data Management

### Cache Population
1. **Basic Data Download**: Fetch all product SKUs from clan.com API
2. **Detailed Data Population**: Get image URLs, prices, descriptions for each product
3. **Incremental Updates**: Process products with `has_detailed_data = FALSE`

### Random Selection
- **Database Query**: `ORDER BY RANDOM()` for true randomness
- **Category Filtering**: Join with category tables for category-based selection
- **Performance**: Indexed queries for fast selection

## User Interface

### Cross-Promotion Management
- **Post Selection**: Dropdown to select blog posts
- **Category Selection**: Dropdown with all available categories
- **Product Selection**: Search and select specific products
- **Enable/Disable**: Toggle cross-promotion for posts
- **Preview**: Link to preview post with widgets

### Blog Launchpad Integration
- **Landing Page Module**: Active status with statistics
- **Management Link**: Direct access to cross-promotion interface
- **Example Preview**: Link to sample post with widgets

## Performance Optimization

### Database Indexing
- `idx_clan_products_detailed` - For random product selection
- `idx_product_categories` - For category-based queries
- `idx_clan_products_name` - For product search

### Caching Strategy
- **Product Data**: Cached in PostgreSQL for fast access
- **Category Data**: Cached with parent-child relationships
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

## Monitoring and Maintenance

### Health Checks
- **Service Health**: `/health` endpoint for service status
- **Database Connection**: Verify PostgreSQL connectivity
- **API Connectivity**: Test clan.com API access

### Cache Statistics
- **Product Count**: Total products in cache
- **Detailed Data**: Products with complete information
- **Category Count**: Available categories
- **Cache Status**: Last refresh time and success/failure

### Logging
- **Application Logs**: Service-specific logging
- **API Errors**: Rate limiting and authentication issues
- **Database Errors**: Connection and query issues

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

## Quick Reference

### Key Files
- **Main Script**: `blog-launchpad/app.py` - Flask application
- **API Client**: `blog-launchpad/clan_api.py` - Clan.com API integration
- **Database**: `blog-launchpad/clan_cache.py` - Database operations
- **Templates**: `blog-launchpad/templates/cross_promotion.html` - Management interface
- **CSS**: `blog-launchpad/static/css/dist/clan_blog.css` - Widget styling

### Key Endpoints
- **Management**: `http://localhost:5001/cross-promotion`
- **Preview**: `http://localhost:5001/preview/53`
- **API Stats**: `http://localhost:5001/api/clan/cache/stats`
- **Health Check**: `http://localhost:5001/health`

### Database Tables
- **clan_products**: Product information and metadata
- **clan_categories**: Category hierarchy
- **post**: Blog posts with cross-promotion settings

## Support

For questions about the cross-promotion system:
1. Review the comprehensive documentation in `cross_promotion_system.md`
2. Check the troubleshooting section for common issues
3. Use the debug commands to diagnose problems
4. Examine the API endpoints and database schema
5. Test the management interface at `http://localhost:5001/cross-promotion`
