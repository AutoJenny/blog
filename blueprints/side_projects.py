from flask import Blueprint, render_template, request, jsonify
from config.database import db_manager
from modules.llm_service import LLMService
import logging
import json
import re
from html.parser import HTMLParser

logger = logging.getLogger(__name__)

bp = Blueprint('side_projects', __name__, url_prefix='/side-projects')
llm_service = LLMService()

class HTMLStripper(HTMLParser):
    """Simple HTML tag stripper."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_text(self):
        return ' '.join(self.text)

def strip_html(html_text):
    """Strip HTML tags from text."""
    if not html_text:
        return ""
    s = HTMLStripper()
    s.feed(html_text)
    return s.get_text().strip()

def count_words(text):
    """Count words in text (handles HTML and plain text)."""
    if not text:
        return 0
    clean_text = strip_html(text)
    words = [w for w in re.split(r'\s+', clean_text) if w.strip()]
    return len(words)

def is_price_related_key(key):
    """Check if a key is related to pricing."""
    if not key:
        return False
    key_lower = str(key).lower()
    price_indicators = ['price', 'cost', 'pricing', '£', '$', 'eur', 'euro', 'dollar', 'pound', 'amount', 'fee', 'charge']
    return any(indicator in key_lower for indicator in price_indicators)

def get_product_description_system_prompt():
    """Get the system prompt for product description generation from llm_prompt table."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT system_prompt 
            FROM llm_prompt 
            WHERE name = 'Product Description Generation - System Prompt'
            LIMIT 1
        """)
        result = cursor.fetchone()
        if result and result.get('system_prompt'):
            return result['system_prompt']
    
    # Fallback to hardcoded prompt if not found in database
    logger.warning("Product Description Generation system prompt not found in database, using fallback")
    return """You are a professional product description writer for a Scottish heritage and tartan products retailer. 
Your task is to write clear, factual product descriptions that focus on features and benefits.

CRITICAL STYLE GUIDELINES:
- Use UK-British English spellings (e.g., "colour" not "color", "organised" not "organized", "centre" not "center", "realise" not "realize", "travelling" not "traveling")
- Be factual and focus on specific features and benefits
- Avoid marketing fluff and empty phrases
- NEVER use words like "Elevate", "Discover", "Unleash", "Transform", "Revolutionary", "Groundbreaking"
- Use clear, direct language that informs the customer
- Pay close attention to materials and be completely accurate. NEVER guess or infer material information that is not explicitly provided in the product data. Only state material facts that are clearly specified.
- Highlight materials, craftsmanship, dimensions, and practical benefits
- If the product is made in Scotland or the UK, mention this factually
- For products with Irish or Welsh heritage indicators (such as shamrock motifs, dragon motifs, or other Irish/Welsh symbols), use "Celtic heritage" rather than "Scottish heritage" when describing the cultural context.
- Keep descriptions informative but engaging

FORMATTING REQUIREMENTS:
- Start with bullet points (using simple HTML <ul> and <li> tags) summarising key features and benefits
- Use HTML paragraph tags (<p>) to break up text every 2-3 sentences for better readability

CRITICAL: NEVER include pricing information, price references, or cost-related content in the description. Focus solely on product features, materials, craftsmanship, and benefits."""

def get_product_with_category_context(product_id, cursor):
    """Get product data and build category context. Returns (product, category_context) tuple."""
    cursor.execute("""
        SELECT 
            id, sku, name, description, short_description,
            image_url, category_ids, supplier_name, supplier_description,
            additional_data, dimensions, configurable_options,
            specifications, product_type_data, product_level, price
        FROM clan_products
        WHERE id = %s
    """, (product_id,))
    product = cursor.fetchone()
    
    if not product:
        return None, None
    
    # Build category context
    category_context = ""
    if product.get('category_ids'):
        for cat_id in product['category_ids']:
            breadcrumbs = []
            current_id = cat_id
            visited = set()
            
            while current_id and current_id not in visited:
                visited.add(current_id)
                cursor.execute("""
                    SELECT id, name, parent_id, level, description, heritage_data
                    FROM clan_categories
                    WHERE id = %s
                """, (current_id,))
                cat = cursor.fetchone()
                if not cat:
                    break
                breadcrumbs.insert(0, cat)
                current_id = cat.get('parent_id')
            
            if breadcrumbs:
                path = ' > '.join([c['name'] for c in breadcrumbs])
                descriptions = [c.get('description', '') for c in breadcrumbs if c.get('description')]
                category_context += f"Category: {path}\n"
                if descriptions:
                    category_context += f"Category descriptions: {' | '.join(descriptions)}\n"
                
                # Add category heritage data if available
                heritage_descriptions = []
                for c in breadcrumbs:
                    if c.get('heritage_data'):
                        heritage = c['heritage_data']
                        if isinstance(heritage, dict):
                            for key in ['historical_origins', 'cultural_significance', 'evolution']:
                                if heritage.get(key):
                                    if isinstance(heritage[key], dict):
                                        narrative = heritage[key].get('narrative', '')
                                        if narrative:
                                            heritage_descriptions.append(f"{key.replace('_', ' ').title()}: {narrative}")
                                    elif isinstance(heritage[key], str):
                                        heritage_descriptions.append(f"{key.replace('_', ' ').title()}: {heritage[key]}")
                if heritage_descriptions:
                    category_context += f"Category heritage context: {' | '.join(heritage_descriptions)}\n"
    
    return product, category_context

def build_product_description_user_prompt(product, category_context):
    """Build the user prompt for product description generation."""
    user_prompt = f"""Write an improved product description for the following product.

PRODUCT TITLE: {product['name']}
SKU: {product['sku']}

{category_context}

SHORT DESCRIPTION (BLURB):
{product.get('short_description', 'None provided')}

CURRENT DESCRIPTION:
{product.get('description', 'None provided')}

ADDITIONAL CONTEXT:
"""
    
    if product.get('supplier_name'):
        user_prompt += f"Supplier/Manufacturer: {product['supplier_name']}\n"
    
    if product.get('dimensions'):
        user_prompt += f"Dimensions: {product['dimensions']}\n"
    
    # Add specifications (excluding price-related fields)
    if product.get('specifications'):
        try:
            specs = product['specifications']
            if isinstance(specs, str):
                specs = json.loads(specs)
            
            if specs:
                user_prompt += "\nSPECIFICATIONS:\n"
                if isinstance(specs, dict):
                    for key, value in specs.items():
                        if value and not is_price_related_key(key):
                            user_prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
                elif isinstance(specs, list):
                    for spec in specs:
                        if isinstance(spec, dict):
                            for key, value in spec.items():
                                if value and not is_price_related_key(key):
                                    user_prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
                        else:
                            if not is_price_related_key(str(spec)):
                                user_prompt += f"- {spec}\n"
                user_prompt += "\n"
        except Exception as e:
            logger.warning(f"Error parsing specifications: {e}")
    
    # Add additional_data (excluding price-related fields)
    if product.get('additional_data'):
        additional = product['additional_data']
        if isinstance(additional, dict):
            user_prompt += "\nADDITIONAL PRODUCT ATTRIBUTES:\n"
            for key, value in additional.items():
                if value and not is_price_related_key(key):
                    user_prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
            user_prompt += "\n"
    
    # Add product_type_data (excluding price-related fields)
    if product.get('product_type_data'):
        try:
            type_data = product['product_type_data']
            if isinstance(type_data, str):
                type_data = json.loads(type_data)
            
            if type_data and isinstance(type_data, dict):
                user_prompt += "\nPRODUCT TYPE DATA:\n"
                for key, value in type_data.items():
                    if value and not is_price_related_key(key):
                        user_prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
                user_prompt += "\n"
        except Exception as e:
            logger.warning(f"Error parsing product_type_data: {e}")
    
    # Add supplier description
    if product.get('supplier_description'):
        user_prompt += f"\nSUPPLIER/MANUFACTURER INFORMATION:\n{product['supplier_description']}\n\n"
    
    # Add configurable options
    if product.get('configurable_options'):
        try:
            options = product['configurable_options']
            if isinstance(options, str):
                options = json.loads(options)
            
            if options:
                user_prompt += "\nPRODUCT OPTIONS (Sizes, Colours, Decorations, etc.):\n"
                if isinstance(options, list):
                    for option in options:
                        if isinstance(option, dict):
                            option_type = option.get('type') or option.get('name') or 'Option'
                            option_values = option.get('values') or option.get('options') or []
                            if option_values:
                                values_str = ', '.join([str(v) for v in option_values])
                                user_prompt += f"- {option_type}: {values_str}\n"
                        elif isinstance(option, str):
                            user_prompt += f"- {option}\n"
                elif isinstance(options, dict):
                    for key, value in options.items():
                        if isinstance(value, list):
                            values_str = ', '.join([str(v) for v in value])
                            user_prompt += f"- {key}: {values_str}\n"
                        else:
                            user_prompt += f"- {key}: {value}\n"
                user_prompt += "\n"
        except Exception as e:
            logger.warning(f"Error parsing configurable_options: {e}")
    
    user_prompt += """
Write a comprehensive product description that:
1. Expands on the current description if it's too short
2. Maintains factual accuracy
3. Uses UK-British English spellings throughout
4. Focuses on features, materials, and benefits
5. Pay close attention to materials - only state material information that is explicitly provided, never guess
6. Avoids marketing clichés and empty phrases
7. Is informative and helpful to potential customers
8. For items with Irish or Welsh heritage (e.g., shamrocks, dragon motifs), use "Celtic heritage" terminology rather than "Scottish"
9. NEVER includes pricing information, price references, or cost-related content

Return ONLY the product description text, no additional commentary."""
    
    return user_prompt

@bp.route('/')
def index():
    """Side projects landing page"""
    return render_template('side-projects/index.html', page_title="Side Projects")

@bp.route('/tartan-design/')
def tartan_design():
    """Tartan Design Descriptions project homepage"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get tartan_designs_clan data
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tartan_designs_clan' 
                ORDER BY ordinal_position
            """)
            headers = [row['column_name'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM tartan_designs_clan ORDER BY id")
            tartan_data = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) as count FROM tartan_designs_clan")
            total_count = cursor.fetchone()['count']
            
            # Get tartan_designs_register data
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tartan_designs_register' 
                ORDER BY ordinal_position
            """)
            register_headers = [row['column_name'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM tartan_designs_register ORDER BY id")
            register_data = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) as count FROM tartan_designs_register")
            register_total_count = cursor.fetchone()['count']
            
        return render_template('side-projects/tartan-design/index.html', 
                             page_title="Tartan Design Descriptions",
                             headers=headers,
                             tartan_data=tartan_data,
                             total_count=total_count,
                             register_headers=register_headers,
                             register_data=register_data,
                             register_total_count=register_total_count)
    except Exception as e:
        # If database error, still render template but without data
        return render_template('side-projects/tartan-design/index.html', 
                             page_title="Tartan Design Descriptions",
                             headers=[],
                             tartan_data=None,
                             total_count=0,
                             register_headers=[],
                             register_data=None,
                             register_total_count=0,
                             error=str(e))

@bp.route('/product-description-generation/')
def product_description_generation():
    """Product Description Generation project homepage"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_products,
                    COUNT(CASE WHEN description_word_count < 30 THEN 1 END) as products_under_30_words,
                    AVG(description_word_count) as avg_word_count,
                    MIN(description_word_count) as min_word_count,
                    MAX(description_word_count) as max_word_count
                FROM clan_products
                WHERE description IS NOT NULL AND description != ''
            """)
            stats = cursor.fetchone()
            
            # Count existing generations
            cursor.execute("""
                SELECT COUNT(DISTINCT product_id) as generated_count
                FROM product_description_generations
            """)
            gen_stats = cursor.fetchone()
            
        return render_template('side-projects/product-description-generation/index.html',
                             page_title="Product Description Generation",
                             stats=stats,
                             generated_count=gen_stats.get('generated_count', 0) if gen_stats else 0)
    except Exception as e:
        logger.error(f"Error loading product description generation page: {e}")
        return render_template('side-projects/product-description-generation/index.html',
                             page_title="Product Description Generation",
                             stats=None,
                             generated_count=0,
                             error=str(e))

@bp.route('/product-description-generation/api/products')
def api_products_short_descriptions():
    """Get products with descriptions under specified word count"""
    try:
        word_threshold = request.args.get('threshold', 30, type=int)
        limit = request.args.get('limit', 1000, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search', '', type=str)
        
        with db_manager.get_cursor() as cursor:
            query = """
                SELECT 
                    p.id, p.sku, p.name, 
                    p.description, p.description_word_count, p.description_char_count,
                    p.short_description, p.short_description_word_count,
                    p.image_url,
                    CASE WHEN COUNT(gen.id) > 0 THEN true ELSE false END as has_generation,
                    COUNT(gen.id) as generation_count
                FROM clan_products p
                LEFT JOIN product_description_generations gen ON p.id = gen.product_id
                WHERE p.description IS NOT NULL 
                AND p.description != ''
                AND p.description_word_count < %s
            """
            params = [word_threshold]
            
            if search:
                query += " AND (p.name ILIKE %s OR p.sku ILIKE %s)"
                params.extend([f'%{search}%', f'%{search}%'])
            
            query += " GROUP BY p.id, p.sku, p.name, p.description, p.description_word_count, p.description_char_count, p.short_description, p.short_description_word_count, p.image_url"
            query += " ORDER BY p.description_word_count ASC, p.name ASC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            products = cursor.fetchall()
            
            # Get total count
            count_query = """
                SELECT COUNT(*) as total
                FROM clan_products
                WHERE description IS NOT NULL 
                AND description != ''
                AND description_word_count < %s
            """
            count_params = [word_threshold]
            if search:
                count_query += " AND (name ILIKE %s OR sku ILIKE %s)"
                count_params.extend([f'%{search}%', f'%{search}%'])
            
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['total']
            
            return jsonify({
                'success': True,
                'products': products,
                'total': total,
                'threshold': word_threshold
            })
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/product-description-generation/api/products/<int:product_id>')
def api_product_details(product_id):
    """Get full product details including category breadcrumbs"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get product - include all available descriptive fields
            cursor.execute("""
                SELECT 
                    id, sku, name, description, short_description,
                    description_word_count, description_char_count,
                    short_description_word_count, short_description_char_count,
                    image_url, url, supplier_name, supplier_description,
                    category_ids, additional_data, dimensions, configurable_options,
                    specifications, product_type_data, product_level, price
                FROM clan_products
                WHERE id = %s
            """, (product_id,))
            product = cursor.fetchone()
            
            if not product:
                return jsonify({'success': False, 'error': 'Product not found'}), 404
            
            # Get category breadcrumbs with full descriptions
            category_breadcrumbs = []
            category_descriptions = []
            if product.get('category_ids'):
                for cat_id in product['category_ids']:
                    breadcrumbs = []
                    current_id = cat_id
                    visited = set()
                    
                    while current_id and current_id not in visited:
                        visited.add(current_id)
                        cursor.execute("""
                            SELECT id, name, parent_id, level, description, heritage_data
                            FROM clan_categories
                            WHERE id = %s
                        """, (current_id,))
                        cat = cursor.fetchone()
                        if not cat:
                            break
                        
                        cat_info = {
                            'id': cat['id'],
                            'name': cat['name'],
                            'level': cat.get('level', 0),
                            'description': cat.get('description', ''),
                            'heritage_data': cat.get('heritage_data')
                        }
                        breadcrumbs.insert(0, cat_info)
                        
                        # Collect category descriptions for fallback context
                        if cat.get('description'):
                            category_descriptions.append({
                                'category': cat['name'],
                                'description': cat['description']
                            })
                        
                        current_id = cat.get('parent_id')
                    
                    if breadcrumbs:
                        category_breadcrumbs.append(breadcrumbs)
            
            # Get existing generations
            cursor.execute("""
                SELECT 
                    id, generated_description, llm_provider, llm_model,
                    temperature, max_tokens, prompt_used, system_prompt,
                    include_image, word_count, char_count, created_at, notes
                FROM product_description_generations
                WHERE product_id = %s
                ORDER BY created_at DESC
            """, (product_id,))
            generations = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'product': product,
                'category_breadcrumbs': category_breadcrumbs,
                'category_descriptions': category_descriptions,
                'generations': generations
            })
    except Exception as e:
        logger.error(f"Error fetching product details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/product-description-generation/api/preview-prompt', methods=['POST'])
def api_preview_prompt():
    """Preview the prompt that would be sent to the LLM without actually calling it"""
    try:
        data = request.json
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'success': False, 'error': 'product_id required'}), 400
        
        with db_manager.get_cursor() as cursor:
            product, category_context = get_product_with_category_context(product_id, cursor)
            
            if not product:
                return jsonify({'success': False, 'error': 'Product not found'}), 404
            
            # Get system prompt from database
            system_prompt = get_product_description_system_prompt()
            
            # Build user prompt using shared helper
            user_prompt = build_product_description_user_prompt(product, category_context)
            
            return jsonify({
                'success': True,
                'system_prompt': system_prompt,
                'user_prompt': user_prompt
            })
            
    except Exception as e:
        logger.error(f"Error previewing prompt: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/product-description-generation/api/generate', methods=['POST'])
def api_generate_description():
    """Generate a product description using LLM"""
    try:
        data = request.json
        product_id = data.get('product_id')
        provider = data.get('provider', 'ollama')
        model = data.get('model', 'llama3.2:latest')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 2000))
        include_image = data.get('include_image', False)
        
        if not product_id:
            return jsonify({'success': False, 'error': 'product_id required'}), 400
        
        with db_manager.get_cursor() as cursor:
            product, category_context = get_product_with_category_context(product_id, cursor)
            
            if not product:
                return jsonify({'success': False, 'error': 'Product not found'}), 404
            
            # Get system prompt from database
            system_prompt = get_product_description_system_prompt()
            
            # Build user prompt using shared helper
            user_prompt = build_product_description_user_prompt(product, category_context)
            
            # Prepare messages
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            # Call LLM
            # Note: intercept_context requires post_id, but we store prompts ourselves
            # Using dummy post_id=-1 (non-zero, non-falsy) to satisfy the requirement
            response = llm_service.execute_llm_request(
                provider, model, messages,
                intercept_context={'post_id': -1, 'product_id': product_id}
            )
            
            if 'error' in response:
                return jsonify({'success': False, 'error': response['error']}), 500
            
            generated_description = response.get('content', '').strip()
            
            # Calculate word/char counts
            gen_word_count = count_words(generated_description)
            gen_char_count = len(strip_html(generated_description))
            
            # Store generation
            cursor.execute("""
                INSERT INTO product_description_generations
                (product_id, generated_description, llm_provider, llm_model,
                 temperature, max_tokens, prompt_used, system_prompt,
                 include_image, word_count, char_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
            """, (
                product_id, generated_description, provider, model,
                temperature, max_tokens, user_prompt, system_prompt,
                include_image, gen_word_count, gen_char_count
            ))
            
            generation = cursor.fetchone()
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'generated_description': generated_description,
                'word_count': gen_word_count,
                'char_count': gen_char_count,
                'generation_id': generation['id'],
                'created_at': generation['created_at'].isoformat(),
                'prompt_used': user_prompt,
                'system_prompt': system_prompt
            })
            
    except Exception as e:
        logger.error(f"Error generating description: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/product-description-generation/api/bulk-generate', methods=['POST'])
def api_bulk_generate():
    """Bulk generate descriptions for multiple products"""
    try:
        data = request.json
        product_ids = data.get('product_ids', [])
        provider = data.get('provider', 'ollama')
        model = data.get('model', 'llama3.2:latest')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 2000))
        include_image = data.get('include_image', False)
        
        if not product_ids:
            return jsonify({'success': False, 'error': 'product_ids required'}), 400
        
        results = []
        total_products = len(product_ids)
        logger.info(f"Starting bulk generation for {total_products} products")
        
        with db_manager.get_cursor() as cursor:
            # Get system prompt once (shared for all products)
            system_prompt = get_product_description_system_prompt()
            
            for idx, product_id in enumerate(product_ids, 1):
                logger.info(f"Processing product {idx}/{total_products}: {product_id}")
                try:
                    # Get product and category context using shared helper
                    product, category_context = get_product_with_category_context(product_id, cursor)
                    
                    if not product:
                        results.append({
                            'product_id': product_id,
                            'title': 'N/A',
                            'sku': 'N/A',
                            'short_description': '',
                            'old_description': '',
                            'new_description': '',
                            'error': 'Product not found'
                        })
                        continue
                    
                    # Build user prompt using shared helper
                    user_prompt = build_product_description_user_prompt(product, category_context)
                    
                    # Call LLM
                    messages = [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ]
                    
                    response = llm_service.execute_llm_request(
                        provider, model, messages,
                        intercept_context={'post_id': -1, 'product_id': product_id}
                    )
                    
                    if 'error' in response:
                        results.append({
                            'product_id': product_id,
                            'title': product.get('name', 'N/A'),
                            'sku': product.get('sku', 'N/A'),
                            'short_description': product.get('short_description', ''),
                            'old_description': product.get('description', ''),
                            'new_description': '',
                            'error': response['error']
                        })
                        continue
                    
                    generated_description = response.get('content', '').strip()
                    
                    # Store generation - use the same helper functions from this file
                    gen_word_count = count_words(generated_description)
                    gen_char_count = len(strip_html(generated_description))
                    
                    cursor.execute("""
                        INSERT INTO product_description_generations
                        (product_id, generated_description, llm_provider, llm_model,
                         temperature, max_tokens, prompt_used, system_prompt,
                         include_image, word_count, char_count)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        product_id, generated_description, provider, model,
                        temperature, max_tokens, user_prompt, system_prompt,
                        include_image, gen_word_count, gen_char_count
                    ))
                    cursor.fetchone()
                    
                    results.append({
                        'product_id': product_id,
                        'title': product.get('name', ''),
                        'sku': product.get('sku', ''),
                        'short_description': product.get('short_description', ''),
                        'old_description': product.get('description', ''),
                        'new_description': generated_description
                    })
                    logger.info(f"Successfully generated description for product {product_id} ({idx}/{total_products})")
                    
                except Exception as e:
                    logger.error(f"Error generating description for product {product_id} ({idx}/{total_products}): {e}", exc_info=True)
                    results.append({
                        'product_id': product_id,
                        'title': product.get('name', 'N/A') if product else 'Error',
                        'sku': product.get('sku', 'N/A') if product else 'N/A',
                        'short_description': product.get('short_description', '') if product else '',
                        'old_description': product.get('description', '') if product else '',
                        'new_description': '',
                        'error': str(e)
                    })
            
            cursor.connection.commit()
        
        logger.info(f"Bulk generation completed: {len(results)} results out of {total_products} products")
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in bulk generate: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/product-description-generation/api/recent-generations')
def api_recent_generations():
    """Get recent bulk generation results"""
    try:
        limit = request.args.get('limit', 1000, type=int)
        minutes = request.args.get('minutes', 1440, type=int)  # Last N minutes (default 24 hours = 1440 minutes)
        
        with db_manager.get_cursor() as cursor:
            # Get recent generations with product info
            cursor.execute("""
                SELECT 
                    gen.id,
                    gen.product_id,
                    gen.generated_description,
                    gen.llm_provider,
                    gen.llm_model,
                    gen.temperature,
                    gen.word_count,
                    gen.char_count,
                    gen.created_at,
                    p.name as product_name,
                    p.sku,
                    p.description as old_description,
                    p.short_description
                FROM product_description_generations gen
                JOIN clan_products p ON gen.product_id = p.id
                WHERE gen.created_at >= NOW() - (INTERVAL '1 minute' * %s)
                ORDER BY gen.created_at DESC
                LIMIT %s
            """, (minutes, limit))
            
            generations = cursor.fetchall()
            
            # Group by product and format results
            results = []
            for gen in generations:
                results.append({
                    'product_id': gen['product_id'],
                    'title': gen['product_name'],
                    'sku': gen['sku'],
                    'short_description': gen['short_description'] or '',
                    'old_description': gen['old_description'] or '',
                    'new_description': gen['generated_description'],
                    'generation_id': gen['id'],
                    'created_at': gen['created_at'].isoformat() if gen['created_at'] else None,
                    'llm_provider': gen['llm_provider'],
                    'llm_model': gen['llm_model']
                })
            
            return jsonify({
                'success': True,
                'results': results,
                'count': len(results)
            })
            
    except Exception as e:
        logger.error(f"Error fetching recent generations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<project_name>')
def project_detail(project_name):
    """Individual project page - placeholder for future projects"""
    return render_template('side-projects/project.html', 
                         project_name=project_name,
                         page_title=f"{project_name.title()} - Side Projects")
