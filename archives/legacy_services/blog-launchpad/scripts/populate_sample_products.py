#!/usr/bin/env python3
"""
Populate sample products for the Daily Product Posts pathfinder project.
This script adds sample Clan.com products to the database for testing.
"""

import sys
import os
import psycopg2
from datetime import datetime

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import get_db_connection

def populate_sample_products():
    """Add sample products to the database."""
    
    sample_products = [
        {
            'clan_product_id': 'CLAN001',
            'name': 'Highland Whisky Glencairn Glass Set',
            'description': 'Premium crystal whisky glasses designed specifically for tasting single malt Scotch whisky. Set of 2 glasses with elegant presentation box.',
            'category': 'Glassware',
            'price': 24.99,
            'image_url': 'https://via.placeholder.com/400x400/8B4513/FFFFFF?text=Whisky+Glass',
            'product_url': 'https://clan.com/products/highland-whisky-glencairn-glass-set',
            'is_active': True
        },
        {
            'clan_product_id': 'CLAN002',
            'name': 'Tartan Wool Scarf - Royal Stewart',
            'description': 'Authentic Scottish tartan scarf in Royal Stewart pattern. 100% pure wool, hand-woven in Scotland. Perfect for any occasion.',
            'category': 'Clothing',
            'price': 45.00,
            'image_url': 'https://via.placeholder.com/400x400/DC143C/FFFFFF?text=Tartan+Scarf',
            'product_url': 'https://clan.com/products/tartan-wool-scarf-royal-stewart',
            'is_active': True
        },
        {
            'clan_product_id': 'CLAN003',
            'name': 'Celtic Knot Silver Pendant',
            'description': 'Handcrafted silver pendant featuring intricate Celtic knotwork design. Comes with 18-inch sterling silver chain. Made in Scotland.',
            'category': 'Jewelry',
            'price': 89.99,
            'image_url': 'https://via.placeholder.com/400x400/C0C0C0/000000?text=Celtic+Pendant',
            'product_url': 'https://clan.com/products/celtic-knot-silver-pendant',
            'is_active': True
        },
        {
            'clan_product_id': 'CLAN004',
            'name': 'Scottish Heather Honey',
            'description': 'Pure Scottish heather honey collected from the Highlands. 340g jar with traditional tartan label. A taste of Scotland.',
            'category': 'Food & Drink',
            'price': 12.50,
            'image_url': 'https://via.placeholder.com/400x400/FFD700/000000?text=Heather+Honey',
            'product_url': 'https://clan.com/products/scottish-heather-honey',
            'is_active': True
        },
        {
            'clan_product_id': 'CLAN005',
            'name': 'Highland Games Caber Toss Game',
            'description': 'Miniature caber toss game for indoor fun. Wooden caber and target board. Perfect for Scottish-themed parties and events.',
            'category': 'Games & Toys',
            'price': 35.00,
            'image_url': 'https://via.placeholder.com/400x400/8B4513/FFFFFF?text=Caber+Toss',
            'product_url': 'https://clan.com/products/highland-games-caber-toss-game',
            'is_active': True
        },
        {
            'clan_product_id': 'CLAN006',
            'name': 'Loch Ness Monster Plush Toy',
            'description': 'Adorable Nessie plush toy, 12 inches tall. Soft and cuddly, perfect for children or Nessie enthusiasts. Made in Scotland.',
            'category': 'Toys',
            'price': 18.99,
            'image_url': 'https://via.placeholder.com/400x400/228B22/FFFFFF?text=Nessie+Plush',
            'product_url': 'https://clan.com/products/loch-ness-monster-plush-toy',
            'is_active': True
        },
        {
            'clan_product_id': 'CLAN007',
            'name': 'Scottish Shortbread Tin',
            'description': 'Traditional Scottish shortbread in decorative tartan tin. 500g of buttery, crumbly shortbread made to original recipe.',
            'category': 'Food & Drink',
            'price': 15.99,
            'image_url': 'https://via.placeholder.com/400x400/DEB887/000000?text=Shortbread',
            'product_url': 'https://clan.com/products/scottish-shortbread-tin',
            'is_active': True
        },
        {
            'clan_product_id': 'CLAN008',
            'name': 'Highland Cow Mug',
            'description': 'Ceramic mug featuring adorable Highland cow design. 350ml capacity, dishwasher safe. Perfect for your morning coffee or tea.',
            'category': 'Home & Kitchen',
            'price': 22.00,
            'image_url': 'https://via.placeholder.com/400x400/8B4513/FFFFFF?text=Highland+Cow+Mug',
            'product_url': 'https://clan.com/products/highland-cow-mug',
            'is_active': True
        },
        {
            'clan_product_id': 'CLAN009',
            'name': 'Tartan Blanket Throw',
            'description': 'Luxurious tartan blanket throw in traditional MacLeod pattern. 100% wool, perfect for cozy evenings by the fire.',
            'category': 'Home & Living',
            'price': 75.00,
            'image_url': 'https://via.placeholder.com/400x400/4169E1/FFFFFF?text=Tartan+Blanket',
            'product_url': 'https://clan.com/products/tartan-blanket-throw',
            'is_active': True
        },
        {
            'clan_product_id': 'CLAN010',
            'name': 'Scottish Thistle Brooch',
            'description': 'Elegant silver brooch featuring the Scottish thistle, national flower of Scotland. Perfect for special occasions and formal wear.',
            'category': 'Jewelry',
            'price': 65.00,
            'image_url': 'https://via.placeholder.com/400x400/C0C0C0/000000?text=Thistle+Brooch',
            'product_url': 'https://clan.com/products/scottish-thistle-brooch',
            'is_active': True
        }
    ]
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Clear existing sample products (optional - remove if you want to keep existing data)
            cur.execute("DELETE FROM products WHERE clan_product_id LIKE 'CLAN%'")
            
            # Insert sample products
            for product in sample_products:
                cur.execute("""
                    INSERT INTO products (clan_product_id, name, description, category, price, image_url, product_url, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (clan_product_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        price = EXCLUDED.price,
                        image_url = EXCLUDED.image_url,
                        product_url = EXCLUDED.product_url,
                        is_active = EXCLUDED.is_active,
                        last_updated = CURRENT_TIMESTAMP
                """, (
                    product['clan_product_id'],
                    product['name'],
                    product['description'],
                    product['category'],
                    product['price'],
                    product['image_url'],
                    product['product_url'],
                    product['is_active']
                ))
            
            conn.commit()
            print(f"Successfully populated {len(sample_products)} sample products!")
            
            # Show what was added
            cur.execute("SELECT name, price, category FROM products WHERE clan_product_id LIKE 'CLAN%' ORDER BY name")
            products = cur.fetchall()
            
            print("\nSample products added:")
            for product in products:
                print(f"  - {product[0]} (£{product[1]}) - {product[2]}")
                
    except Exception as e:
        print(f"Error populating sample products: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Populating sample products for Daily Product Posts...")
    success = populate_sample_products()
    if success:
        print("\n✅ Sample products populated successfully!")
    else:
        print("\n❌ Failed to populate sample products.")
        sys.exit(1)
