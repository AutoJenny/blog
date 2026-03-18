#!/usr/bin/env python3
"""
Data Quality Validation Script
Validates that all products have real images and category associations
"""

import psycopg2
from psycopg2.extras import DictCursor
import logging
import json
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataQualityValidator:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'blog',
            'user': 'postgres',
            'password': 'postgres'
        }
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def validate_images(self) -> Dict:
        """Validate that products have real images"""
        logger.info("🔍 Validating product images...")
        
        stats = {
            'total_products': 0,
            'real_images': 0,
            'placeholder_images': 0,
            'no_images': 0,
            'clan_images': 0,
            'other_images': 0
        }
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                
                cur.execute("SELECT id, sku, name, image_url FROM clan_products")
                products = cur.fetchall()
                
                stats['total_products'] = len(products)
                
                for product in products:
                    image_url = product['image_url']
                    
                    if not image_url:
                        stats['no_images'] += 1
                    elif 'essential.jpg' in image_url or 'placeholder' in image_url.lower():
                        stats['placeholder_images'] += 1
                    elif 'static.clan.com' in image_url:
                        stats['clan_images'] += 1
                        stats['real_images'] += 1
                    else:
                        stats['other_images'] += 1
                        stats['real_images'] += 1
                
                # Calculate percentages
                if stats['total_products'] > 0:
                    stats['real_image_percentage'] = (stats['real_images'] / stats['total_products']) * 100
                    stats['placeholder_percentage'] = (stats['placeholder_images'] / stats['total_products']) * 100
                    stats['clan_image_percentage'] = (stats['clan_images'] / stats['total_products']) * 100
                else:
                    stats['real_image_percentage'] = 0
                    stats['placeholder_percentage'] = 0
                    stats['clan_image_percentage'] = 0
                
        except Exception as e:
            logger.error(f"Error validating images: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def validate_categories(self) -> Dict:
        """Validate that products have category associations"""
        logger.info("🔍 Validating product categories...")
        
        stats = {
            'total_products': 0,
            'with_categories': 0,
            'no_categories': 0,
            'valid_categories': 0,
            'invalid_categories': 0,
            'category_errors': []
        }
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                
                cur.execute("SELECT id, sku, name, category_ids FROM clan_products")
                products = cur.fetchall()
                
                stats['total_products'] = len(products)
                
                for product in products:
                    category_ids = product['category_ids']
                    
                    if not category_ids:
                        stats['no_categories'] += 1
                    else:
                        stats['with_categories'] += 1
                        
                        try:
                            # Parse JSON category_ids
                            if isinstance(category_ids, str):
                                categories = json.loads(category_ids)
                            else:
                                categories = category_ids
                            
                            if isinstance(categories, list) and len(categories) > 0:
                                # Validate that category IDs exist in clan_categories table
                                valid_count = 0
                                for cat_id in categories:
                                    cur.execute("SELECT id FROM clan_categories WHERE id = %s", (cat_id,))
                                    if cur.fetchone():
                                        valid_count += 1
                                
                                if valid_count > 0:
                                    stats['valid_categories'] += 1
                                else:
                                    stats['invalid_categories'] += 1
                                    stats['category_errors'].append(f"SKU {product['sku']}: No valid categories found")
                            else:
                                stats['invalid_categories'] += 1
                                stats['category_errors'].append(f"SKU {product['sku']}: Invalid category format")
                                
                        except (json.JSONDecodeError, TypeError) as e:
                            stats['invalid_categories'] += 1
                            stats['category_errors'].append(f"SKU {product['sku']}: JSON parse error - {e}")
                
                # Calculate percentages
                if stats['total_products'] > 0:
                    stats['category_percentage'] = (stats['with_categories'] / stats['total_products']) * 100
                    stats['valid_category_percentage'] = (stats['valid_categories'] / stats['total_products']) * 100
                else:
                    stats['category_percentage'] = 0
                    stats['valid_category_percentage'] = 0
                
        except Exception as e:
            logger.error(f"Error validating categories: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def validate_category_tree(self) -> Dict:
        """Validate the category tree structure"""
        logger.info("🔍 Validating category tree...")
        
        stats = {
            'total_categories': 0,
            'top_level_categories': 0,
            'categories_with_parents': 0,
            'orphaned_categories': 0,
            'max_depth': 0
        }
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                
                # Get all categories
                cur.execute("SELECT id, name, level, parent_id FROM clan_categories ORDER BY level, id")
                categories = cur.fetchall()
                
                stats['total_categories'] = len(categories)
                
                for category in categories:
                    level = category['level']
                    parent_id = category['parent_id']
                    
                    if level == 1:
                        stats['top_level_categories'] += 1
                    elif parent_id:
                        stats['categories_with_parents'] += 1
                    else:
                        stats['orphaned_categories'] += 1
                    
                    stats['max_depth'] = max(stats['max_depth'], level)
                
        except Exception as e:
            logger.error(f"Error validating category tree: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def test_random_product_selection(self) -> Dict:
        """Test random product selection functionality"""
        logger.info("🔍 Testing random product selection...")
        
        stats = {
            'test_attempts': 10,
            'successful_selections': 0,
            'products_with_images': 0,
            'products_with_categories': 0,
            'selection_errors': []
        }
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                
                for i in range(stats['test_attempts']):
                    try:
                        # Simulate random product selection
                        cur.execute("""
                            SELECT p.*, c.name as category_name
                            FROM clan_products p
                            LEFT JOIN clan_categories c ON c.id = ANY(
                                SELECT json_array_elements_text(p.category_ids::json)::int
                            )
                            WHERE p.price IS NOT NULL AND p.price != ''
                            ORDER BY RANDOM()
                            LIMIT 1
                        """)
                        
                        product = cur.fetchone()
                        
                        if product:
                            stats['successful_selections'] += 1
                            
                            # Check if product has real image
                            if product['image_url'] and 'static.clan.com' in product['image_url']:
                                stats['products_with_images'] += 1
                            
                            # Check if product has categories
                            if product['category_ids']:
                                try:
                                    categories = json.loads(product['category_ids'])
                                    if isinstance(categories, list) and len(categories) > 0:
                                        stats['products_with_categories'] += 1
                                except:
                                    pass
                        else:
                            stats['selection_errors'].append(f"Attempt {i+1}: No product selected")
                    
                    except Exception as e:
                        stats['selection_errors'].append(f"Attempt {i+1}: {e}")
                
                # Calculate percentages
                if stats['test_attempts'] > 0:
                    stats['selection_success_rate'] = (stats['successful_selections'] / stats['test_attempts']) * 100
                    stats['image_success_rate'] = (stats['products_with_images'] / stats['successful_selections']) * 100 if stats['successful_selections'] > 0 else 0
                    stats['category_success_rate'] = (stats['products_with_categories'] / stats['successful_selections']) * 100 if stats['successful_selections'] > 0 else 0
                else:
                    stats['selection_success_rate'] = 0
                    stats['image_success_rate'] = 0
                    stats['category_success_rate'] = 0
                
        except Exception as e:
            logger.error(f"Error testing product selection: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def run(self):
        """Main execution method"""
        logger.info("🚀 Starting data quality validation...")
        
        # Validate images
        image_stats = self.validate_images()
        self.print_image_stats(image_stats)
        
        # Validate categories
        category_stats = self.validate_categories()
        self.print_category_stats(category_stats)
        
        # Validate category tree
        tree_stats = self.validate_category_tree()
        self.print_tree_stats(tree_stats)
        
        # Test random product selection
        selection_stats = self.test_random_product_selection()
        self.print_selection_stats(selection_stats)
        
        # Overall assessment
        self.print_overall_assessment(image_stats, category_stats, tree_stats, selection_stats)
    
    def print_image_stats(self, stats: Dict):
        """Print image validation statistics"""
        logger.info("📊 IMAGE VALIDATION RESULTS:")
        logger.info(f"Total products: {stats['total_products']}")
        logger.info(f"Real images: {stats['real_images']} ({stats['real_image_percentage']:.1f}%)")
        logger.info(f"Clan.com images: {stats['clan_images']} ({stats['clan_image_percentage']:.1f}%)")
        logger.info(f"Placeholder images: {stats['placeholder_images']} ({stats['placeholder_percentage']:.1f}%)")
        logger.info(f"No images: {stats['no_images']}")
        
        if stats['real_image_percentage'] >= 90:
            logger.info("✅ Image quality: EXCELLENT")
        elif stats['real_image_percentage'] >= 70:
            logger.info("✅ Image quality: GOOD")
        elif stats['real_image_percentage'] >= 50:
            logger.info("⚠️ Image quality: FAIR")
        else:
            logger.warning("❌ Image quality: POOR")
    
    def print_category_stats(self, stats: Dict):
        """Print category validation statistics"""
        logger.info("📊 CATEGORY VALIDATION RESULTS:")
        logger.info(f"Total products: {stats['total_products']}")
        logger.info(f"With categories: {stats['with_categories']} ({stats['category_percentage']:.1f}%)")
        logger.info(f"Valid categories: {stats['valid_categories']} ({stats['valid_category_percentage']:.1f}%)")
        logger.info(f"No categories: {stats['no_categories']}")
        logger.info(f"Invalid categories: {stats['invalid_categories']}")
        
        if stats['valid_category_percentage'] >= 90:
            logger.info("✅ Category quality: EXCELLENT")
        elif stats['valid_category_percentage'] >= 70:
            logger.info("✅ Category quality: GOOD")
        elif stats['valid_category_percentage'] >= 50:
            logger.info("⚠️ Category quality: FAIR")
        else:
            logger.warning("❌ Category quality: POOR")
    
    def print_tree_stats(self, stats: Dict):
        """Print category tree validation statistics"""
        logger.info("📊 CATEGORY TREE VALIDATION RESULTS:")
        logger.info(f"Total categories: {stats['total_categories']}")
        logger.info(f"Top-level categories: {stats['top_level_categories']}")
        logger.info(f"Categories with parents: {stats['categories_with_parents']}")
        logger.info(f"Orphaned categories: {stats['orphaned_categories']}")
        logger.info(f"Maximum depth: {stats['max_depth']}")
        
        if stats['orphaned_categories'] == 0 and stats['max_depth'] > 1:
            logger.info("✅ Category tree: EXCELLENT")
        elif stats['orphaned_categories'] <= 5:
            logger.info("✅ Category tree: GOOD")
        else:
            logger.warning("❌ Category tree: NEEDS ATTENTION")
    
    def print_selection_stats(self, stats: Dict):
        """Print product selection test statistics"""
        logger.info("📊 PRODUCT SELECTION TEST RESULTS:")
        logger.info(f"Test attempts: {stats['test_attempts']}")
        logger.info(f"Successful selections: {stats['successful_selections']} ({stats['selection_success_rate']:.1f}%)")
        logger.info(f"Products with images: {stats['products_with_images']} ({stats['image_success_rate']:.1f}%)")
        logger.info(f"Products with categories: {stats['products_with_categories']} ({stats['category_success_rate']:.1f}%)")
        
        if stats['selection_success_rate'] >= 90 and stats['image_success_rate'] >= 80 and stats['category_success_rate'] >= 80:
            logger.info("✅ Product selection: EXCELLENT")
        elif stats['selection_success_rate'] >= 70 and stats['image_success_rate'] >= 60 and stats['category_success_rate'] >= 60:
            logger.info("✅ Product selection: GOOD")
        else:
            logger.warning("❌ Product selection: NEEDS IMPROVEMENT")
    
    def print_overall_assessment(self, image_stats: Dict, category_stats: Dict, tree_stats: Dict, selection_stats: Dict):
        """Print overall data quality assessment"""
        logger.info("🎯 OVERALL DATA QUALITY ASSESSMENT:")
        
        # Calculate overall score
        image_score = min(image_stats['real_image_percentage'], 100)
        category_score = min(category_stats['valid_category_percentage'], 100)
        selection_score = min(selection_stats['selection_success_rate'], 100)
        
        overall_score = (image_score + category_score + selection_score) / 3
        
        logger.info(f"Overall Score: {overall_score:.1f}/100")
        
        if overall_score >= 90:
            logger.info("🏆 DATA QUALITY: EXCELLENT - Ready for production!")
        elif overall_score >= 80:
            logger.info("✅ DATA QUALITY: GOOD - Minor improvements needed")
        elif overall_score >= 70:
            logger.info("⚠️ DATA QUALITY: FAIR - Some improvements needed")
        elif overall_score >= 50:
            logger.info("⚠️ DATA QUALITY: POOR - Significant improvements needed")
        else:
            logger.warning("❌ DATA QUALITY: CRITICAL - Major issues need fixing")
        
        # Recommendations
        logger.info("💡 RECOMMENDATIONS:")
        if image_score < 80:
            logger.info("  - Run image update script to improve image quality")
        if category_score < 80:
            logger.info("  - Run category update script to improve category associations")
        if selection_score < 80:
            logger.info("  - Check database indexes and query performance")
        
        logger.info("✅ Data quality validation completed!")

if __name__ == "__main__":
    validator = DataQualityValidator()
    validator.run()
