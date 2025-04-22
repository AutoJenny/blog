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

## Configuration

Key environment variables to configure:

```bash
# Core Settings
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Database (for local content storage)
DATABASE_URL=sqlite:///instance/blog.db

# AI Features (Optional)
OPENAI_API_KEY=your-api-key

# Clan.com Integration
CLAN_API_KEY=your-clan-api-key
CLAN_API_ENDPOINT=https://api.clan.com/v1/blog
```

See `docs/configuration.md` for detailed configuration options.

## Documentation

Detailed documentation is available in the `/docs` directory:

- 📖 [Content Creation Guide](docs/user_guide.md) - Writing and preview workflow
- ⚙️ [Technical Setup](docs/technical_setup.md) - Local environment setup
- 🔧 [Development Guide](docs/development.md) - Contributing and extending
- 📊 [API Documentation](docs/api.md) - Integration with clan.com

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