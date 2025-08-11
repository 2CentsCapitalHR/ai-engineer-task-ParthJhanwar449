# setup.py
import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr.strip()}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 8:
        print("❌ Python 3.8+ required. Please upgrade Python.")
        return False
    
    print("✅ Python version is compatible")
    return True

def setup_environment():
    """Set up the development environment"""
    print("🚀 Setting up ADGM Corporate Agent environment...\n")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create virtual environment
    if not os.path.exists('venv'):
        if not run_command('python -m venv venv', 'Creating virtual environment'):
            return False
    else:
        print("✅ Virtual environment already exists")
    
    # Determine activation command based on OS
    if os.name == 'nt':  # Windows
        activate_cmd = 'venv\\Scripts\\activate'
        pip_cmd = 'venv\\Scripts\\pip'
        python_cmd = 'venv\\Scripts\\python'
    else:  # Unix/Linux/MacOS
        activate_cmd = 'source venv/bin/activate'
        pip_cmd = 'venv/bin/pip'
        python_cmd = 'venv/bin/python'
    
    # Install requirements
    if not run_command(f'{pip_cmd} install --upgrade pip', 'Upgrading pip'):
        return False
    
    if not run_command(f'{pip_cmd} install -r requirements.txt', 'Installing Python packages'):
        return False
    
    # Create necessary directories
    directories = ['resources', 'resources/adgm', 'examples', 'temp_output']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print(f"✅ Created directories: {', '.join(directories)}")
    
    # Create sample configuration
    create_sample_config()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Add ADGM PDF documents to resources/adgm/")
    print("2. Set your OPENAI_API_KEY environment variable")
    print("3. Run: python scripts/build_adgm_index.py")
    print("4. Run: python src/app.py")
    
    return True

def create_sample_config():
    """Create sample configuration files"""
    
    # Sample .env file
    env_content = """# ADGM Corporate Agent Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_EMBED_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini

# RAG Configuration
ADGM_INDEX_PATH=resources/adgm_index.faiss
ADGM_META_PATH=resources/adgm_meta.json

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=7860
"""
    
    with open('.env.example', 'w') as f:
        f.write(env_content)
    
    # Sample ADGM documents list
    adgm_docs = {
        "required_documents": [
            "ADGM_Companies_Regulations_2020.pdf",
            "ADGM_Rulebook_2023.pdf", 
            "ADGM_Employment_Regulations_2020.pdf",
            "ADGM_Commercial_Licensing_Regulations_2020.pdf"
        ],
        "download_sources": [
            "https://www.adgm.com/doing-business/regulations/",
            "https://www.adgm.com/legal-framework/"
        ],
        "note": "Download these official ADGM documents and place them in resources/adgm/ directory"
    }
    
    with open('resources/adgm_documents_list.json', 'w') as f:
        json.dump(adgm_docs, f, indent=2)
    
    print("✅ Created sample configuration files")

def check_setup():
    """Check if the setup is complete and working"""
    print("\n🔍 Checking setup status...\n")
    
    checks = []
    
    # Check virtual environment
    venv_exists = os.path.exists('venv')
    checks.append(("Virtual environment", venv_exists))
    
    # Check requirements installation
    try:
        import gradio, openai, faiss
        requirements_installed = True
    except ImportError:
        requirements_installed = False
    checks.append(("Required packages", requirements_installed))
    
    # Check directories
    dirs_exist = all(os.path.exists(d) for d in ['resources', 'resources/adgm', 'examples'])
    checks.append(("Directory structure", dirs_exist))
    
    # Check for ADGM documents
    adgm_files = list(Path('resources/adgm').glob('*.pdf'))
    adgm_docs_exist = len(adgm_files) > 0
    checks.append(("ADGM documents", adgm_docs_exist))
    
    # Check for RAG index
    index_exists = os.path.exists('resources/adgm_index.faiss')
    checks.append(("RAG index built", index_exists))
    
    # Check API key
    api_key_set = os.getenv('OPENAI_API_KEY') is not None
    checks.append(("OpenAI API key", api_key_set))
    
    # Print results
    for check_name, status in checks:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check_name}")
    
    all_good = all(status for _, status in checks)
    
    if not all_good:
        print("\n⚠️  Some setup steps are incomplete:")
        if not adgm_docs_exist:
            print("   - Add ADGM PDF documents to resources/adgm/")
        if not index_exists and adgm_docs_exist:
            print("   - Run: python scripts/build_adgm_index.py")
        if not api_key_set:
            print("   - Set OPENAI_API_KEY environment variable")
    else:
        print("\n🎉 Setup is complete! Run: python src/app.py")
    
    return all_good

def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ADGM Corporate Agent Setup')
    parser.add_argument('--check', action='store_true', help='Check setup status')
    parser.add_argument('--install', action='store_true', help='Install dependencies')
    
    args = parser.parse_args()
    
    if args.check:
        check_setup()
    elif args.install:
        setup_environment()
    else:
        print("ADGM Corporate Agent Setup")
        print("Usage:")
        print("  python setup.py --install    # Set up environment")
        print("  python setup.py --check      # Check setup status")

if __name__ == '__main__':
    main()