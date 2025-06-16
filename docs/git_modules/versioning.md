# Module Versioning & Deployment Guide

This document outlines the versioning and deployment procedures for modules in the blog system, with a focus on database schema management and deployment workflows.

---

## Version Control

### 1. Module Versioning

#### Version Structure
```python
def get_module_version(module_name):
    """Get module version information."""
    return {
        'name': module_name,
        'version': get_version_from_git(module_name),
        'schema_version': get_schema_version(module_name),
        'dependencies': get_module_dependencies(module_name)
    }
```

#### Version Tracking
```python
def track_module_version(module_name, version_info):
    """Track module version information."""
    query = """
    INSERT INTO module_version 
    (module_name, version, schema_version, dependencies)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (module_name) 
    DO UPDATE SET 
        version = EXCLUDED.version,
        schema_version = EXCLUDED.schema_version,
        dependencies = EXCLUDED.dependencies,
        updated_at = NOW()
    """
    execute_query(query, (
        module_name,
        version_info['version'],
        version_info['schema_version'],
        json.dumps(version_info['dependencies'])
    ))
```

### 2. Database Schema Versioning

#### Schema Version Tracking
```python
def get_schema_version():
    """Get current database schema version."""
    query = """
    SELECT version, applied_at
    FROM schema_version
    ORDER BY applied_at DESC
    LIMIT 1
    """
    return execute_query(query)
```

#### Schema Update
```python
def update_schema_version(version, description):
    """Update schema version after migration."""
    query = """
    INSERT INTO schema_version 
    (version, description, applied_at)
    VALUES (%s, %s, NOW())
    """
    execute_query(query, (version, description))
```

---

## Deployment Procedures

### 1. Pre-Deployment Checks

#### Environment Check
```python
def check_deployment_environment():
    """Check deployment environment."""
    checks = {
        'database': check_database_connection(),
        'modules': check_module_dependencies(),
        'config': check_environment_variables(),
        'permissions': check_file_permissions()
    }
    
    if not all(checks.values()):
        raise DeploymentError("Environment checks failed")
    
    return checks
```

#### Backup Check
```python
def verify_backup_exists():
    """Verify backup exists before deployment."""
    backup_file = f'blog_backup_{datetime.now().strftime("%Y%m%d")}.sql'
    
    if not os.path.exists(backup_file):
        raise DeploymentError(f"Required backup {backup_file} not found")
    
    return backup_file
```

### 2. Deployment Process

#### Module Deployment
```python
def deploy_module(module_name, version):
    """Deploy module with version control."""
    try:
        # Check environment
        check_deployment_environment()
        
        # Verify backup
        verify_backup_exists()
        
        # Deploy module
        deploy_module_files(module_name, version)
        
        # Update database
        update_module_database(module_name, version)
        
        # Update version info
        track_module_version(module_name, {
            'version': version,
            'schema_version': get_schema_version(module_name),
            'dependencies': get_module_dependencies(module_name)
        })
        
        # Verify deployment
        verify_module_deployment(module_name, version)
    except Exception as e:
        rollback_deployment(module_name, version)
        raise DeploymentError(f"Deployment failed: {str(e)}")
```

#### Database Deployment
```python
def deploy_database_changes(changes):
    """Deploy database changes with version control."""
    try:
        # Create backup
        backup_file = backup_database()
        
        # Apply changes
        for change in changes:
            execute_query(change['query'], change.get('params'))
        
        # Update schema version
        update_schema_version(changes[-1]['version'], changes[-1]['description'])
        
        # Verify changes
        verify_database_changes(changes)
    except Exception as e:
        restore_database(backup_file)
        raise DeploymentError(f"Database deployment failed: {str(e)}")
```

---

## Backup and Restore

### 1. Backup Procedures

#### Database Backup
```python
def backup_database():
    """Create database backup with version info."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'blog_backup_{timestamp}.sql'
    
    # Get version info
    version_info = {
        'schema_version': get_schema_version(),
        'module_versions': get_all_module_versions(),
        'timestamp': timestamp
    }
    
    # Create backup
    subprocess.run([
        'pg_dump',
        '-U', os.getenv('DB_USER'),
        '-d', os.getenv('DB_NAME'),
        '-f', backup_file
    ], check=True)
    
    # Save version info
    with open(f'{backup_file}.json', 'w') as f:
        json.dump(version_info, f)
    
    return backup_file
```

#### Module Backup
```python
def backup_module(module_name):
    """Backup module files and configuration."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f'backups/{module_name}_{timestamp}'
    
    # Create backup directory
    os.makedirs(backup_dir)
    
    # Copy module files
    shutil.copytree(f'modules/{module_name}', f'{backup_dir}/files')
    
    # Save version info
    with open(f'{backup_dir}/version.json', 'w') as f:
        json.dump(get_module_version(module_name), f)
    
    return backup_dir
```

### 2. Restore Procedures

#### Database Restore
```python
def restore_database(backup_file):
    """Restore database from backup with version verification."""
    # Load version info
    with open(f'{backup_file}.json', 'r') as f:
        version_info = json.load(f)
    
    # Restore database
    subprocess.run([
        'psql',
        '-U', os.getenv('DB_USER'),
        '-d', os.getenv('DB_NAME'),
        '-f', backup_file
    ], check=True)
    
    # Verify schema version
    current_version = get_schema_version()
    if current_version != version_info['schema_version']:
        raise RestoreError("Schema version mismatch after restore")
    
    return version_info
```

#### Module Restore
```python
def restore_module(backup_dir):
    """Restore module from backup with version verification."""
    # Load version info
    with open(f'{backup_dir}/version.json', 'r') as f:
        version_info = json.load(f)
    
    # Restore module files
    shutil.copytree(f'{backup_dir}/files', f'modules/{version_info["name"]}')
    
    # Verify module version
    current_version = get_module_version(version_info['name'])
    if current_version != version_info:
        raise RestoreError("Module version mismatch after restore")
    
    return version_info
```

---

## Best Practices

### 1. Version Control
- Use semantic versioning
- Track schema versions
- Document dependencies
- Maintain version history
- Verify versions

### 2. Deployment
- Check environment
- Create backups
- Deploy systematically
- Verify deployment
- Document process

### 3. Backup/Restore
- Regular backups
- Version tracking
- Verify backups
- Test restores
- Document procedures

### 4. Documentation
- Version changes
- Deployment steps
- Backup procedures
- Restore procedures
- Troubleshooting

---

## Common Issues

### 1. Version Issues
- Version conflicts
- Schema mismatches
- Dependency issues
- Version tracking
- Update failures

### 2. Deployment Issues
- Environment issues
- Backup failures
- Update errors
- Verification failures
- Rollback issues

### 3. Backup/Restore Issues
- Backup failures
- Restore errors
- Version mismatches
- Data corruption
- Permission issues

---

## References

### 1. Version Control
- [Module Versioning](docs/modules/versioning.md)
- [Schema Versioning](docs/database/versioning.md)

### 2. Deployment
- [Deployment Guide](docs/deployment/guide.md)
- [Environment Setup](docs/deployment/environment.md)

### 3. Backup/Restore
- [Backup Procedures](docs/database/backup.md)
- [Restore Procedures](docs/database/restore.md) 