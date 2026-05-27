#!/usr/bin/env python
"""
Verification script for AutoSE Platform project structure.
This script checks that all required files and directories exist.
"""

import os
import sys
from pathlib import Path

def check_file_exists(path, description):
    """Check if a file exists and print status."""
    if Path(path).exists():
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} (MISSING)")
        return False

def check_directory_exists(path, description):
    """Check if a directory exists and print status."""
    if Path(path).exists() and Path(path).is_dir():
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} (MISSING)")
        return False

def main():
    """Main verification function."""
    print("=" * 60)
    print("AutoSE Platform Project Structure Verification")
    print("=" * 60)
    
    checks = []
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"✅ Python version: {sys.version}")
        checks.append(True)
    else:
        print(f"❌ Python version: {sys.version} (requires 3.8+)")
        checks.append(False)
    
    print()
    
    # Check required directories
    checks.append(check_directory_exists("src/autose_platform", "Source module directory"))
    checks.append(check_directory_exists("tests", "Tests directory"))
    
    print()
    
    # Check required files in src/autose_platform
    checks.append(check_file_exists("src/autose_platform/__init__.py", "Package init file"))
    checks.append(check_file_exists("src/autose_platform/main.py", "Main FastAPI app"))
    checks.append(check_file_exists("src/autose_platform/config.py", "Configuration module"))
    
    print()
    
    # Check required project files
    checks.append(check_file_exists("requirements.txt", "Requirements file"))
    checks.append(check_file_exists("pyproject.toml", "PyProject.toml"))
    checks.append(check_file_exists(".env.example", "Environment template"))
    checks.append(check_file_exists(".gitignore", "Git ignore file"))
    checks.append(check_file_exists("README.md", "README documentation"))
    checks.append(check_file_exists("Dockerfile", "Docker configuration"))
    checks.append(check_file_exists("docker-compose.yml", "Docker Compose config"))
    checks.append(check_file_exists("setup.py", "Setup script"))
    checks.append(check_file_exists("pytest.ini", "Pytest configuration"))
    
    print()
    
    # Check test files
    checks.append(check_file_exists("tests/__init__.py", "Test package init"))
    checks.append(check_file_exists("tests/test_config.py", "Config tests"))
    checks.append(check_file_exists("tests/test_main.py", "Main app tests"))
    
    print()
    print("=" * 60)
    
    # Summary
    total_checks = len(checks)
    passed_checks = sum(checks)
    
    if all(checks):
        print(f"🎉 SUCCESS: All {total_checks} checks passed!")
        print("\nProject structure is complete and ready for development.")
        return 0
    else:
        print(f"⚠️  WARNING: {passed_checks}/{total_checks} checks passed")
        print(f"   {total_checks - passed_checks} checks failed")
        print("\nPlease fix the missing items before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())