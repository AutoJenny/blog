#!/usr/bin/env python3
"""
Configuration CLI Tool
Command-line interface for managing BlogForge configuration
"""

import argparse
import sys
import os
from config.config_manager import ConfigManager

def main():
    parser = argparse.ArgumentParser(description='BlogForge Configuration Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show configuration')
    show_parser.add_argument('--section', help='Show specific configuration section')
    show_parser.add_argument('--format', choices=['json', 'yaml', 'summary'], default='summary', help='Output format')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration')
    validate_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export configuration')
    export_parser.add_argument('--file', '-f', help='Output file name')
    export_parser.add_argument('--format', choices=['json', 'yaml'], default='json', help='Output format')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test configuration')
    test_parser.add_argument('--database', action='store_true', help='Test database connection')
    test_parser.add_argument('--redis', action='store_true', help='Test Redis connection')
    test_parser.add_argument('--ai', action='store_true', help='Test AI services')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize configuration')
    init_parser.add_argument('--env', choices=['development', 'production', 'staging'], default='development', help='Environment')
    init_parser.add_argument('--force', action='store_true', help='Force overwrite existing files')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize config manager
    config_manager = ConfigManager()
    
    if args.command == 'show':
        show_config(config_manager, args)
    elif args.command == 'validate':
        validate_config(config_manager, args)
    elif args.command == 'export':
        export_config(config_manager, args)
    elif args.command == 'test':
        test_config(config_manager, args)
    elif args.command == 'init':
        init_config(config_manager, args)

def show_config(config_manager, args):
    """Show configuration"""
    if args.section:
        try:
            method = getattr(config_manager, f'get_{args.section}_config')
            config_data = method()
        except AttributeError:
            print(f"Unknown section: {args.section}")
            return
    else:
        config_data = config_manager.get_all_config()
    
    if args.format == 'json':
        import json
        print(json.dumps(config_data, indent=2))
    elif args.format == 'yaml':
        try:
            import yaml
            print(yaml.dump(config_data, default_flow_style=False))
        except ImportError:
            print("PyYAML not installed. Install with: pip install pyyaml")
    else:  # summary
        if args.section:
            print(f"{args.section.upper()} Configuration:")
            print("=" * 50)
            for key, value in config_data.items():
                if isinstance(value, dict):
                    print(f"{key}:")
                    for subkey, subvalue in value.items():
                        print(f"  {subkey}: {subvalue}")
                else:
                    print(f"{key}: {value}")
        else:
            print(config_manager.get_config_summary())

def validate_config(config_manager, args):
    """Validate configuration"""
    validation = config_manager.validate_config()
    
    if validation['valid']:
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors")
    
    if validation['errors']:
        print("\nErrors:")
        for error in validation['errors']:
            print(f"  ❌ {error}")
    
    if validation['warnings']:
        print("\nWarnings:")
        for warning in validation['warnings']:
            print(f"  ⚠️  {warning}")
    
    if args.verbose:
        print(f"\nTotal errors: {len(validation['errors'])}")
        print(f"Total warnings: {len(validation['warnings'])}")

def export_config(config_manager, args):
    """Export configuration"""
    filename = args.file or f"config_export_{config_manager.config_name}.json"
    
    try:
        exported_file = config_manager.export_config(filename)
        print(f"Configuration exported to: {exported_file}")
    except Exception as e:
        print(f"Error exporting configuration: {e}")

def test_config(config_manager, args):
    """Test configuration"""
    if args.database:
        test_database_connection(config_manager)
    
    if args.redis:
        test_redis_connection(config_manager)
    
    if args.ai:
        test_ai_services(config_manager)
    
    if not any([args.database, args.redis, args.ai]):
        # Test all if no specific tests requested
        test_database_connection(config_manager)
        test_redis_connection(config_manager)
        test_ai_services(config_manager)

def test_database_connection(config_manager):
    """Test database connection"""
    print("Testing database connection...")
    try:
        from config.database import db_manager
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

def test_redis_connection(config_manager):
    """Test Redis connection"""
    print("Testing Redis connection...")
    try:
        import redis
        redis_config = config_manager.get_redis_config()
        r = redis.Redis(host=redis_config['host'], port=redis_config['port'], db=redis_config['db'])
        r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

def test_ai_services(config_manager):
    """Test AI services"""
    print("Testing AI services...")
    ai_config = config_manager.get_ai_config()
    
    if ai_config['openai_api_key']:
        print("✅ OpenAI API key configured")
    else:
        print("⚠️  OpenAI API key not configured")
    
    if ai_config['ollama_host']:
        print("✅ Ollama host configured")
    else:
        print("⚠️  Ollama host not configured")
    
    if ai_config['anthropic_api_key']:
        print("✅ Anthropic API key configured")
    else:
        print("⚠️  Anthropic API key not configured")

def init_config(config_manager, args):
    """Initialize configuration"""
    print(f"Initializing {args.env} configuration...")
    
    # Create .env file if it doesn't exist
    env_file = '.env'
    if os.path.exists(env_file) and not args.force:
        print(f"❌ {env_file} already exists. Use --force to overwrite.")
        return
    
    # Copy from template
    template_file = 'config/env.template'
    if os.path.exists(template_file):
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Update environment
        content = content.replace('FLASK_ENV=development', f'FLASK_ENV={args.env}')
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Created {env_file}")
    else:
        print(f"❌ Template file {template_file} not found")
    
    # Create production-specific files
    if args.env == 'production':
        print("Creating production-specific configuration files...")
        # Add production-specific setup here

if __name__ == '__main__':
    main()
