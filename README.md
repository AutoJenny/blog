# Blog Content Management System

A Flask-based content creation and preview system with AI assistance for clan.com/blog. This application helps create and preview blog content locally before publishing to the main clan.com platform.

## Key Features

- 📝 **Smart Content Creation** - AI-assisted writing and editing
- 👀 **Local Preview** - Review content exactly as it will appear on clan.com
- 🔄 **Clan.com Integration** - Seamless export to clan.com/blog
- 🚀 **Performance Optimized** - Redis caching for fast previews
- 🎨 **Theme Preview** - Match clan.com's styling locally

## Quick Start

1. Clone the repository:
```bash
git clone [repository-url]
cd blog
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment:
   - Copy `.env.example` to `.env`
   - Update the variables (see Configuration section below)
   - Never commit your `.env` file

5. Initialize the database:
```bash
flask db upgrade
```

6. Start the development server:
```bash
./run_server.sh
```

Visit `http://localhost:5000` to start creating content.

## Documentation

Our documentation is organized by user role and topic:

### For Content Creators
- 📖 [User Guide](docs/guides/user_guide.md) - Content creation and management
- 🖼️ [Media Guide](docs/api/media.md) - Image and file management
- 🤖 [LLM Features](docs/api/llm.md) - AI-assisted content creation

### For Developers
- ⚙️ [Technical Setup](docs/guides/technical_setup.md) - Development environment setup
- 🔌 [API Documentation](docs/api/README.md) - Complete API reference
- 💾 [Database Models](docs/database/README.md) - Data structure documentation

### For System Administrators
- 📊 [Monitoring](docs/api/monitoring.md) - System health and metrics
- 🔄 [Migration Guide](docs/guides/migration.md) - Data migration procedures
- 🏗️ [Architecture](docs/project/architecture.md) - System architecture

See the [documentation index](docs/README.md) for a complete overview of all available documentation.

## Core Operations

- **Content Creation**: Write and edit blog posts with AI assistance
- **Local Preview**: Review content with clan.com styling
- **Media Management**: Upload and manage images for posts
- **Export to Clan.com**: Push approved content to clan.com/blog
- **API Access**: Integration with clan.com's blog platform

## Support

- 🐛 Report issues via GitHub Issues
- 💡 Feature requests and discussions in GitHub Discussions
- 📧 Technical support: [support email]

## License

[Add your license information here]

## ⚠️ IMPORTANT NOTE ⚠️

**NO LOGIN FUNCTIONALITY SHOULD BE IMPLEMENTED**

This blog is intentionally designed to operate WITHOUT any authentication or login system. Do not attempt to add or fix any login-related features. The application should remain publicly accessible without any user authentication. 