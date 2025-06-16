# Development Environment Setup Guide

This document provides detailed instructions for setting up a development environment for the modular blog system. Follow these steps carefully to ensure a consistent development experience across all modules.

---

## System Requirements

### Hardware Requirements
- CPU: 2+ cores
- RAM: 8GB minimum (16GB recommended)
- Storage: 20GB free space
- Network: Stable internet connection

### Software Requirements
- macOS 10.15+ or Linux
- Python 3.9+
- PostgreSQL 13+
- Git 2.30+
- Node.js 16+ (for frontend development)
- npm 8+ (for frontend development)

---

## Initial Setup

### 1. Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/yourusername/blog.git
cd blog

# Initialize git submodules (if any)
git submodule update --init --recursive
```

### 2. Python Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb blog_dev

# Set environment variables
export DATABASE_URL="postgresql://localhost/blog_dev"
export FLASK_APP="app"
export FLASK_ENV="development"
```

### 4. Frontend Setup

```bash
# Install frontend dependencies
cd app/static
npm install
```

---

## Module Development Setup

### 1. Module Branch Setup

```bash
# Create and checkout module branch
git checkout -b module_name

# Create module directory structure
mkdir -p modules/module_name/{templates,static,scripts,tests}
```

### 2. Module Development Environment

```bash
# Create module-specific virtual environment (optional)
python -m venv venv_module_name
source venv_module_name/bin/activate

# Install module-specific dependencies
pip install -r modules/module_name/requirements.txt
```

### 3. Module Testing Setup

```bash
# Create test database
createdb blog_test_module_name

# Set test environment variables
export TEST_DATABASE_URL="postgresql://localhost/blog_test_module_name"
export TESTING=1
```

---

## Development Tools

### 1. Required Tools

#### Code Editor
- VS Code (recommended)
- Extensions:
  - Python
  - Pylance
  - Python Test Explorer
  - GitLens
  - ESLint
  - Prettier

#### Database Tools
- pgAdmin 4 or DBeaver
- Database connection:
  ```
  Host: localhost
  Port: 5432
  Database: blog_dev
  User: your_username
  ```

#### API Testing
- Postman or Insomnia
- Collection: `docs/api/postman_collection.json`

### 2. Development Scripts

#### Start Development Server
```bash
# Start Flask development server
./scripts/dev/restart_flask_dev.sh
```

#### Run Tests
```bash
# Run all tests
pytest

# Run specific module tests
pytest modules/module_name/tests/

# Run with coverage
pytest --cov=modules/module_name
```

#### Database Management
```bash
# Reset database
./scripts/db/reset_db.sh

# Run migrations
./scripts/db/migrate.sh
```

---

## Module Development Workflow

### 1. Starting a New Module

```bash
# 1. Create module branch
git checkout -b module_name

# 2. Create module structure
./scripts/create_module.sh module_name

# 3. Set up module environment
./scripts/setup_module.sh module_name

# 4. Start development
./scripts/dev/restart_flask_dev.sh
```

### 2. Module Development Process

1. **Development**
   ```bash
   # Start development server
   ./scripts/dev/restart_flask_dev.sh
   
   # Run tests in watch mode
   pytest-watch modules/module_name/tests/
   ```

2. **Testing**
   ```bash
   # Run unit tests
   pytest modules/module_name/tests/unit/
   
   # Run integration tests
   pytest modules/module_name/tests/integration/
   
   # Run end-to-end tests
   pytest modules/module_name/tests/e2e/
   ```

3. **Code Quality**
   ```bash
   # Run linters
   flake8 modules/module_name/
   pylint modules/module_name/
   
   # Run type checking
   mypy modules/module_name/
   ```

4. **Documentation**
   ```bash
   # Generate API documentation
   ./scripts/docs/generate_api_docs.sh module_name
   
   # Generate module documentation
   ./scripts/docs/generate_module_docs.sh module_name
   ```

### 3. Module Integration

1. **Local Integration Testing**
   ```bash
   # Mount module in HUB
   ./scripts/dev/mount_module.sh module_name
   
   # Run integration tests
   pytest tests/integration/module_name/
   ```

2. **Module Update**
   ```bash
   # Update module in HUB
   ./scripts/update_module.sh module_name
   
   # Verify integration
   ./scripts/verify_integration.sh module_name
   ```

---

## Common Development Tasks

### 1. Database Operations

```bash
# Create new migration
./scripts/db/create_migration.sh "description"

# Apply migrations
./scripts/db/migrate.sh

# Rollback migration
./scripts/db/rollback.sh
```

### 2. Testing

```bash
# Run specific test
pytest modules/module_name/tests/test_file.py::test_function

# Run tests with specific marker
pytest -m "integration"

# Generate coverage report
pytest --cov=modules/module_name --cov-report=html
```

### 3. Documentation

```bash
# Generate API documentation
./scripts/docs/generate_api_docs.sh

# Generate module documentation
./scripts/docs/generate_module_docs.sh

# Serve documentation locally
./scripts/docs/serve_docs.sh
```

---

## Troubleshooting

### 1. Common Issues

#### Database Connection Issues
```bash
# Check database connection
./scripts/db/check_connection.sh

# Reset database
./scripts/db/reset_db.sh
```

#### Module Integration Issues
```bash
# Check module integration
./scripts/verify_integration.sh module_name

# Reset module integration
./scripts/reset_integration.sh module_name
```

#### Development Server Issues
```bash
# Check server status
./scripts/dev/check_server.sh

# Restart server
./scripts/dev/restart_flask_dev.sh
```

### 2. Debugging

#### Python Debugging
```python
# Add debug breakpoint
import pdb; pdb.set_trace()

# Run with debugger
python -m pdb app.py
```

#### Database Debugging
```bash
# Check database logs
./scripts/db/check_logs.sh

# Monitor database queries
./scripts/db/monitor_queries.sh
```

#### Frontend Debugging
```bash
# Start frontend dev server
npm run dev

# Check frontend logs
npm run logs
```

---

## Best Practices

### 1. Code Organization
- Follow module structure
- Use proper imports
- Follow naming conventions
- Document code

### 2. Testing
- Write tests first
- Maintain test coverage
- Use proper test data
- Clean up test data

### 3. Documentation
- Keep docs up to date
- Document APIs
- Document configuration
- Document dependencies

### 4. Version Control
- Use feature branches
- Write clear commits
- Follow git flow
- Review code

### 5. Security
- Use environment variables
- Follow security guidelines
- Validate input
- Handle errors properly

---

## Additional Resources

### 1. Documentation
- [API Documentation](docs/api/README.md)
- [Module Documentation](docs/modules/README.md)
- [Database Documentation](docs/database/README.md)
- [Testing Documentation](docs/testing/README.md)

### 2. Tools
- [VS Code Setup](docs/tools/vscode.md)
- [Database Tools](docs/tools/database.md)
- [Testing Tools](docs/tools/testing.md)
- [Documentation Tools](docs/tools/documentation.md)

### 3. References
- [Python Style Guide](docs/references/python_style.md)
- [API Design Guide](docs/references/api_design.md)
- [Testing Guide](docs/references/testing.md)
- [Security Guide](docs/references/security.md) 