"""
AutoSE Platform - Main Application Entry Point

This file provides a simple entry point to run the AutoSE Platform.
It integrates Chutes API for LLM calls while keeping all existing agent logic unchanged.
"""

import os
import sys
from pathlib import Path

# Add current directory and src directory to Python path
current_dir = Path(__file__).parent
src_path = current_dir / "src"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(src_path))

def main():
    """Main function to run the AutoSE Platform."""
    print("=" * 60)
    print("AutoSE Platform with Chutes API Integration")
    print("=" * 60)
    print()
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("Creating from template...")
        env_example = Path(".env.example")
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from template")
            print("⚠️  Please update .env with your CHUTES_API_KEY")
        else:
            print("❌ .env.example template not found")
            return 1
    
    # Check if Chutes API key is configured
    from dotenv import load_dotenv
    load_dotenv()
    
    chutes_api_key = os.getenv("CHUTES_API_KEY")
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not chutes_api_key and not deepseek_api_key:
        print("❌ No LLM API key configured")
        print("Please set either CHUTES_API_KEY or DEEPSEEK_API_KEY in .env file")
        print()
        print("For Chutes API:")
        print("  CHUTES_API_KEY=your_chutes_api_key_here")
        print("  CHUTES_API_URL=https://llm.chutes.ai/v1")
        print("  CHUTES_MODEL=deepseek-ai/DeepSeek-V3-0324")
        print()
        print("For DeepSeek API (legacy):")
        print("  DEEPSEEK_API_KEY=your_deepseek_api_key_here")
        print("  DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions")
        print("  DEEPSEEK_MODEL=deepseek-chat")
        return 1
    
    if chutes_api_key:
        print("✅ Using Chutes API with DeepSeek-V3-0324 model")
        print(f"   API URL: {os.getenv('CHUTES_API_URL', 'https://llm.chutes.ai/v1')}")
    elif deepseek_api_key:
        print("✅ Using DeepSeek API (legacy mode)")
        print(f"   API URL: {os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')}")
    
    print()
    print("Starting AutoSE Platform...")
    print()
    print("Available options:")
    print("1. Start FastAPI backend server")
    print("2. Start Streamlit frontend")
    print("3. Run demo")
    print("4. Run tests")
    print("5. Exit")
    print()
    
    try:
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == "1":
            # Start FastAPI backend
            print()
            print("Starting FastAPI backend...")
            print("API will be available at: http://localhost:8000")
            print("API Docs: http://localhost:8000/docs")
            print()
            print("Press Ctrl+C to stop the server")
            print("-" * 60)
            
            import subprocess
            subprocess.run([
                sys.executable, "-m", "uvicorn",
                "autose_platform.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ])
            
        elif choice == "2":
            # Start Streamlit frontend
            print()
            print("Starting Streamlit frontend...")
            print("Frontend will be available at: http://localhost:8501")
            print()
            
            import subprocess
            subprocess.run([
                sys.executable, "-m", "streamlit",
                "run", "streamlit_app.py",
                "--server.port", "8501"
            ])
            
        elif choice == "3":
            # Run demo
            print()
            print("Running demo...")
            print()
            
            import run_demo
            run_demo.main()
            
        elif choice == "4":
            # Run tests
            print()
            print("Running tests...")
            print()
            
            import subprocess
            result = subprocess.run([
                sys.executable, "test_implementation.py"
            ], capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
                
        elif choice == "5":
            print()
            print("Exiting...")
            return 0
            
        else:
            print()
            print("❌ Invalid choice")
            return 1
            
    except KeyboardInterrupt:
        print()
        print("\nOperation cancelled by user")
        return 0
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())