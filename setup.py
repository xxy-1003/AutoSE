#!/usr/bin/env python
"""
Setup script for AutoSE Platform.
This script helps with initial project setup and environment configuration.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def check_python_version():
    """Check if Python version is compatible."""
    print_header("Checking Python Version")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ is required. Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version} is compatible")
    return True

def setup_virtual_environment():
    """Create and activate virtual environment."""
    print_header("Setting Up Virtual Environment")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install project dependencies."""
    print_header("Installing Dependencies")
    
    # Determine pip path based on platform
    if os.name == "nt":  # Windows
        pip_path = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        pip_path = "venv/bin/pip"
    
    try:
        # Install base dependencies
        subprocess.run([pip_path, "install", "-e", "."], check=True)
        print("✅ Base dependencies installed")
        
        # Install development dependencies
        subprocess.run([pip_path, "install", "-e", ".[dev]"], check=True)
        print("✅ Development dependencies installed")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment_file():
    """Create .env file from template."""
    print_header("Setting Up Environment Configuration")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print("❌ .env.example template not found")
        return False
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    try:
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Remember to update .env with your DeepSeek API key")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def run_tests():
    """Run initial test suite to verify setup."""
    print_header("Running Initial Tests")
    
    # Determine pytest path based on platform
    if os.name == "nt":  # Windows
        pytest_path = "venv\\Scripts\\pytest"
    else:  # Unix/Linux/Mac
        pytest_path = "venv/bin/pytest"
    
    try:
        result = subprocess.run([pytest_path, "tests/", "-v"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            print(result.stdout)
        else:
            print("⚠️  Some tests failed:")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

def print_next_steps():
    """Print next steps for the user."""
    print_header("Setup Complete!")
    
    print("\n🎉 AutoSE Platform has been set up successfully!")
    
    print("\n📋 Next Steps:")
    print("1. Update your .env file with your DeepSeek API key")
    print("2. Activate the virtual environment:")
    
    if os.name == "nt":  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/Mac
        print("   source venv/bin/activate")
    
    print("\n3. Start the development server:")
    print("   uvicorn src.autose_platform.main:app --reload")
    
    print("\n4. Access the API at:")
    print("   - http://localhost:8000")
    print("   - Documentation: http://localhost:8000/docs")
    
    print("\n5. Run tests:")
    print("   pytest tests/")
    
    print("\n6. Format code:")
    print("   black src/ tests/")
    print("   isort src/ tests/")

def main():
    """Main setup function."""
    print_header("AutoSE Platform Setup")
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Virtual Environment Setup", setup_virtual_environment),
        ("Dependency Installation", install_dependencies),
        ("Environment Configuration", setup_environment_file),
        ("Test Verification", run_tests),
    ]
    
    all_passed = True
    
    for step_name, step_function in steps:
        if not step_function():
            all_passed = False
            print(f"\n❌ Setup failed at: {step_name}")
            break
    
    if all_passed:
        print_next_steps()
        return 0
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())