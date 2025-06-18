def get_llm_config():
    """Get LLM configuration from the database."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT provider, model, api_key, api_base, temperature, max_tokens
                FROM llm_config
                WHERE is_active = true
                ORDER BY id DESC
                LIMIT 1
            """)
            config = cur.fetchone()
            if not config:
                raise Exception("No active LLM configuration found")
            return dict(config)

def generate_basic_idea(title, llm_config):
    """Generate a basic idea using the LLM."""
    prompt = f"""Given the following blog post title, generate a concise and engaging basic idea for the post:

Title: {title}

The basic idea should:
1. Be clear and focused
2. Capture the main message or value proposition
3. Be engaging and interesting
4. Be no more than 2-3 sentences

Basic Idea:"""

    response = call_llm(prompt, llm_config)
    return response.strip()

def generate_themes_for_post(post, post_development, llm_config):
    """Generate main themes and sub-themes for a post using the LLM."""
    prompt = f"""Given the following blog post information, generate main themes and sub-themes:

Title: {post.title}
Basic Idea: {post_development.basic_idea if post_development else ''}

Please provide:
1. 3-5 main themes that represent the core topics or messages
2. 2-3 sub-themes for each main theme that explore specific aspects or angles

Format the response as:
Main Themes:
- Theme 1
  * Sub-theme 1.1
  * Sub-theme 1.2
- Theme 2
  * Sub-theme 2.1
  * Sub-theme 2.2
etc.

Themes:"""

    response = call_llm(prompt, llm_config)
    
    # Parse the response to separate main themes and sub-themes
    main_themes = []
    sub_themes = []
    current_theme = None
    
    for line in response.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            current_theme = line[2:]
            main_themes.append(current_theme)
        elif line.startswith('* '):
            if current_theme:
                sub_themes.append(f"{current_theme}: {line[2:]}")
    
    return '\n'.join(main_themes), '\n'.join(sub_themes)

def call_llm(prompt, config):
    """Call the LLM with the given prompt and configuration."""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {config['api_key']}"
    }
    
    data = {
        'model': config['model'],
        'prompt': prompt,
        'temperature': config['temperature'],
        'max_tokens': config['max_tokens']
    }
    
    response = requests.post(
        config['api_base'],
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"LLM API error: {response.text}")
    
    result = response.json()
    return result['choices'][0]['text'] 