#!/usr/bin/env python
"""
Simple runner script for AutoSE Platform.
This script provides an easy way to start the development server.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def check_environment():
    """Check if environment is properly set up."""
    print_header("Environment Check")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        print("   Creating from template...")
        env_example = Path(".env.example")
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("   Created .env file from template")
            print("   ⚠️  Remember to update with your DeepSeek API key")
        else:
            print("   ❌ .env.example template not found")
            return False
    
    # Check Python path
    python_path = Path("src")
    if not python_path.exists():
        print("❌ src directory not found")
        return False
    
    print("✅ Environment check passed")
    return True

def start_development_server():
    """Start the FastAPI development server."""
    print_header("Starting Development Server")
    
    print("Starting AutoSE Platform API...")
    print("\nAccess URLs:")
    print("  - API: http://localhost:8000")
    print("  - Documentation: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.autose_platform.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        return False
    
    return True

def show_help():
    """Show help information."""
    print_header("AutoSE Platform Runner")
    print("\nUsage:")
    print("  python run.py          Start development server")
    print("  python run.py --help   Show this help")
    print("\nCommands:")
    print("  start    Start development server (default)")
    print("  check    Check environment setup")
    print("  test     Run tests")
    print("\nExamples:")
    print("  python run.py start")
    print("  python run.py check")
    print("  python run.py test")

def run_tests():
    """Run the test suite."""
    print_header("Running Tests")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/", "-v"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print(f"❌ Tests failed with exit code: {result.returncode}")
            if result.stderr:
                print("\nError output:")
                print(result.stderr)
        
        return result.returncode == 0
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ["--help", "-h", "help"]:
            show_help()
            return 0
        elif command == "check":
            return 0 if check_environment() else 1
        elif command == "test":
            return 0 if run_tests() else 1
        elif command == "start":
            if check_environment():
                return 0 if start_development_server() else 1
            else:
                return 1
        else:
            print(f"❌ Unknown command: {command}")
            show_help()
            return 1
    else:
        # Default: start server
        if check_environment():
            return 0 if start_development_server() else 1
        else:
            return 1

if __name__ == "__main__":
    sys.exit(main())