#!/usr/bin/env python3
"""
Product Selection Script with Category Diversity
Ensures no level 2/3 categories repeat within a month (4-5 weeks)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import json
import random

def get_product_level_2_3_categories(product_id, category_ids, cursor):
    """Get level 2 and 3 category IDs for a product."""
    if not category_ids:
        return []
    
    cat_ids_list = category_ids if isinstance(category_ids, list) else json.loads(category_ids) if isinstance(category_ids, str) else []
    if not cat_ids_list:
        return []
    
    placeholders = ','.join(['%s'] * len(cat_ids_list))
    cursor.execute(f'''
        SELECT id
        FROM clan_categories
        WHERE id IN ({placeholders})
        AND level IN (2, 3)
    ''', cat_ids_list)
    
    results = cursor.fetchall()
    return [r[0] if isinstance(r, tuple) else r.get('id') for r in results]

def calculate_selection_score(product, cursor):
    """Calculate selection score for a product."""
    desc_len = product.get('description_char_count', 0)
    blog = product.get('blog_profiled_at')
    newsletter = product.get('newsletter_launched_at')
    producer = product.get('producer_id')
    level = product.get('product_level')
    supplier = product.get('supplier_name')
    
    score = (
        (5 if desc_len > 2000 else 0) +
        (3 if desc_len > 1000 else 0) +
        (1 if desc_len > 500 else 0) +
        (5 if blog else 0) +
        (4 if newsletter else 0) +
        (3 if producer else 0) +
        (2 if level == 'luxury' else 0) +
        (1 if level == 'essential' else 0) +
        (1 if supplier else 0)
    )
    
    return score

def select_products_with_diversity(target_count=150, weeks_per_month=4):
    """Select products ensuring category diversity."""
    
    with db_manager.get_cursor() as cursor:
        # Get all candidate products with scores
        cursor.execute('''
            SELECT 
                id,
                name,
                category_ids,
                description_char_count,
                blog_profiled_at,
                newsletter_launched_at,
                producer_id,
                product_level,
                supplier_name
            FROM clan_products
            WHERE has_detailed_data = TRUE
            ORDER BY description_char_count DESC
        ''')
        
        all_products = cursor.fetchall()
        
        # Convert to list of dicts with scores
        candidates = []
        for p in all_products:
            prod_id = p[0] if isinstance(p, tuple) else p.get('id')
            name = p[1] if isinstance(p, tuple) else p.get('name')
            cat_ids = p[2] if isinstance(p, tuple) else p.get('category_ids')
            desc_len = p[3] if isinstance(p, tuple) else p.get('description_char_count', 0)
            blog = p[4] if isinstance(p, tuple) else p.get('blog_profiled_at')
            newsletter = p[5] if isinstance(p, tuple) else p.get('newsletter_launched_at')
            producer = p[6] if isinstance(p, tuple) else p.get('producer_id')
            level = p[7] if isinstance(p, tuple) else p.get('product_level')
            supplier = p[8] if isinstance(p, tuple) else p.get('supplier_name')
            
            # Get level 2/3 categories
            level_2_3_cats = get_product_level_2_3_categories(prod_id, cat_ids, cursor)
            
            score = calculate_selection_score({
                'description_char_count': desc_len,
                'blog_profiled_at': blog,
                'newsletter_launched_at': newsletter,
                'producer_id': producer,
                'product_level': level,
                'supplier_name': supplier
            }, cursor)
            
            candidates.append({
                'id': prod_id,
                'name': name,
                'category_ids': cat_ids,
                'level_2_3_categories': level_2_3_cats,
                'score': score,
                'description_char_count': desc_len
            })
        
        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Selection with diversity constraint
        selected = []
        used_category_sets = []  # Track category sets used in recent weeks
        month_window = weeks_per_month  # No category repeat within this window
        
        for candidate in candidates:
            if len(selected) >= target_count:
                break
            
            # Check if this product's categories conflict with recent selections
            candidate_cats = set(candidate['level_2_3_categories'])
            
            # Check last month_window selections
            recent_cats = set()
            for recent in selected[-month_window:]:
                recent_cats.update(recent['level_2_3_categories'])
            
            # If there's overlap, skip this candidate (unless we're running out of options)
            if candidate_cats & recent_cats:
                # Only skip if we have plenty of candidates left
                remaining_candidates = len(candidates) - candidates.index(candidate)
                if remaining_candidates > target_count - len(selected):
                    continue
            
            # Add this product
            selected.append(candidate)
        
        # If we don't have enough, fill with best remaining (relaxing constraint)
        if len(selected) < target_count:
            remaining = [c for c in candidates if c not in selected]
            needed = target_count - len(selected)
            selected.extend(remaining[:needed])
        
        return selected[:target_count]

if __name__ == '__main__':
    print("Selecting products with category diversity...")
    selected = select_products_with_diversity(150, weeks_per_month=4)
    
    print(f"\n✅ Selected {len(selected)} products")
    print(f"\nCategory diversity check (first 20):")
    for i, prod in enumerate(selected[:20], 1):
        cats = ', '.join([str(c) for c in prod['level_2_3_categories']]) if prod['level_2_3_categories'] else 'None'
        print(f"  {i}. {prod['name'][:40]}... (score: {prod['score']}, cats: {cats})")
    
    # Check for category repeats in first month
    print(f"\nChecking for category repeats in first month (4 weeks):")
    first_month = selected[:4]
    all_cats = []
    for prod in first_month:
        all_cats.extend(prod['level_2_3_categories'])
    
    from collections import Counter
    cat_counts = Counter(all_cats)
    repeats = {cat: count for cat, count in cat_counts.items() if count > 1}
    if repeats:
        print(f"  ⚠️  Found {len(repeats)} category repeats in first month")
        for cat, count in repeats.items():
            print(f"    Category {cat}: {count} times")
    else:
        print("  ✅ No category repeats in first month")

