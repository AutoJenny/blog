#!/usr/bin/env python3
"""Script to check for outdated dependencies and known vulnerabilities."""

import pkg_resources
import requests
import sys
import json
import logging
from packaging import version
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dependency_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_latest_versions():
    """Get latest versions of packages from PyPI."""
    packages = {
        'langchain': None,
        'langchain-community': None,
        'langchain-core': None,
        'openai': None,
        'flask': None,
        'sqlalchemy': None,
        'gunicorn': None,
        'redis': None,
        'celery': None
    }
    
    for package in packages:
        try:
            response = requests.get(f"https://pypi.org/pypi/{package}/json")
            if response.status_code == 200:
                data = response.json()
                packages[package] = data['info']['version']
        except Exception as e:
            logger.error(f"Error fetching version for {package}: {e}")
    
    return packages

def check_dependencies():
    """Check installed packages against latest versions."""
    latest_versions = get_latest_versions()
    outdated = []
    up_to_date = []
    errors = []
    
    for package, latest in latest_versions.items():
        if latest is None:
            continue
            
        try:
            installed = pkg_resources.get_distribution(package)
            if version.parse(installed.version) < version.parse(latest):
                outdated.append({
                    'package': package,
                    'installed': installed.version,
                    'latest': latest
                })
            else:
                up_to_date.append({
                    'package': package,
                    'version': installed.version
                })
        except pkg_resources.DistributionNotFound:
            errors.append({
                'package': package,
                'error': 'Package not found'
            })
        except Exception as e:
            errors.append({
                'package': package,
                'error': str(e)
            })
    
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'outdated': outdated,
        'up_to_date': up_to_date,
        'errors': errors
    }

def check_vulnerabilities():
    """Check known vulnerabilities in installed packages."""
    vulnerabilities = []
    
    for dist in pkg_resources.working_set:
        try:
            response = requests.get(
                f"https://pypi.org/pypi/{dist.key}/json",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'vulnerabilities' in data['info']:
                    for vuln in data['info']['vulnerabilities']:
                        if version.parse(dist.version) < version.parse(vuln['fixed_in']):
                            vulnerabilities.append({
                                'package': dist.key,
                                'installed_version': dist.version,
                                'vulnerability': vuln['description'],
                                'fixed_in': vuln['fixed_in']
                            })
        except Exception as e:
            logger.error(f"Error checking vulnerabilities for {dist.key}: {e}")
    
    return vulnerabilities

def main():
    """Run dependency checks and output results."""
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    results = {
        'dependency_check': check_dependencies(),
        'vulnerabilities': check_vulnerabilities()
    }
    
    # Log results
    logger.info("Dependency Check Results")
    logger.info("========================")
    
    if results['dependency_check']['outdated']:
        logger.info("\nOutdated Packages:")
        for pkg in results['dependency_check']['outdated']:
            logger.info(f"  - {pkg['package']}: {pkg['installed']} -> {pkg['latest']}")
    
    if results['dependency_check']['errors']:
        logger.warning("\nErrors:")
        for error in results['dependency_check']['errors']:
            logger.warning(f"  - {error['package']}: {error['error']}")
    
    if results['vulnerabilities']:
        logger.warning("\nVulnerabilities Found:")
        for vuln in results['vulnerabilities']:
            logger.warning(f"\n  Package: {vuln['package']} {vuln['installed_version']}")
            logger.warning(f"  Fixed in: {vuln['fixed_in']}")
            logger.warning(f"  Description: {vuln['vulnerability']}")
    
    # Save results to file
    with open('logs/dependency_check.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Exit with error if vulnerabilities found
    sys.exit(1 if results['vulnerabilities'] else 0)

if __name__ == '__main__':
    main() 