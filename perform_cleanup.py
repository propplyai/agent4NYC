#!/usr/bin/env python3
"""
Repository Cleanup Script for Propply AI - ACTUAL CLEANUP
Removes non-essential files for deployment
"""

import os
import shutil
from pathlib import Path

def perform_cleanup():
    """Perform actual repository cleanup"""
    
    repo_path = Path('/Users/art3a/agent4NYC')
    
    print("🧹 Starting repository cleanup...")
    print(f"📁 Working directory: {repo_path}")
    
    # Files to remove (non-essential files)
    files_to_remove = [
        # Test files
        'test_*.py',
        
        # Generated reports and logs
        'compliance_report_*.json',
        'comprehensive_compliance_report_*.json', 
        'property_report_*.json',
        'ai_analysis_*.json',
        'flask.log',
        'ngrok.log',
        
        # Development/debug files
        'debug_app.py',
        'propply_app.py',  # Keep app.py instead
        'examples.py',
        'utils.py',
        
        # Research and investigation files
        'investigate_*.py',
        'explore_*.py',
        'show_columns.py',
        'verify_real_data.py',
        'corrected_*.py',
        'improved_*.py',
        'quick_*.py',
        'generate_*.py',
        
        # FDNY specific research files
        'fdny_*.py',
        'complete_fdny_dataset_finder.py',
        'comprehensive_fdny_parser.py',
        
        # Other development files
        'demo_ai_report.py',
        'address_to_supabase.py',
        'apify_integration.py',
        'property_inspection_deadlines.py',
        
        # Enhanced versions (keep simple ones)
        'enhanced_vendor_marketplace.py',
        'simple_vendor_marketplace.py',  # Remove this too, keep vendor_marketplace.py
        
        # Alternative client files
        'nyc_property_finder.py',  # Keep nyc_opendata_client.py
        'ai_compliance_analyzer.py',  # Using webhook instead
        
        # Requirements alternatives
        'requirements_apify.txt',
        
        # Deployment alternatives
        'render.yaml',
        'deploy.sh',
        'setup-server.sh',
        
        # Documentation files (keep README.md)
        'DEPLOYMENT.md',
        'BOILER_SEARCH_FINDINGS.md',
        'FDNY_DATASETS_RESEARCH_SUMMARY.md',
        'ai_agent_prompt.md',
        
        # Cleanup script itself
        'cleanup_repo.py'
    ]
    
    # Directories to remove
    dirs_to_remove = [
        'fdny_pdfs',
        'fdny_comprehensive'
    ]
    
    # Template files to remove (keep only propply_report.html)
    template_files_to_remove = [
        'templates/404.html',
        'templates/500.html', 
        'templates/compliance_dashboard.html',
        'templates/index.html',
        'templates/index_improved.html',
        'templates/propply_clean.html',
        'templates/propply_dashboard.html',
        'templates/propply_simple.html',
        'templates/propply/'  # Remove entire propply subdirectory
    ]
    
    removed_count = 0
    
    # Remove individual files using glob patterns
    for pattern in files_to_remove:
        matches = list(repo_path.glob(pattern))
        for file_path in matches:
            if file_path.exists() and file_path.is_file():
                try:
                    file_path.unlink()
                    print(f"✅ Removed: {file_path.name}")
                    removed_count += 1
                except Exception as e:
                    print(f"❌ Error removing {file_path.name}: {e}")
    
    # Remove directories
    for dir_name in dirs_to_remove:
        dir_path = repo_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            try:
                shutil.rmtree(dir_path)
                print(f"✅ Removed directory: {dir_name}/")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing {dir_name}/: {e}")
    
    # Remove template files
    for template_file in template_files_to_remove:
        file_path = repo_path / template_file
        if file_path.exists():
            try:
                if file_path.is_file():
                    file_path.unlink()
                    print(f"✅ Removed template: {template_file}")
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    print(f"✅ Removed template directory: {template_file}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing {template_file}: {e}")
    
    # Clean up JSON files in static directory
    static_path = repo_path / 'static'
    if static_path.exists():
        json_files = list(static_path.glob('*.json'))
        for json_file in json_files:
            try:
                json_file.unlink()
                print(f"✅ Removed static file: static/{json_file.name}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing static/{json_file.name}: {e}")
    
    # Clean up __pycache__ directories
    pycache_dirs = list(repo_path.rglob('__pycache__'))
    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
            print(f"✅ Removed: {pycache_dir.relative_to(repo_path)}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Error removing {pycache_dir.relative_to(repo_path)}: {e}")
    
    print(f"\n🎉 Cleanup complete! Removed {removed_count} items")
    
    # Show final essential files
    print(f"\n✅ Essential files remaining:")
    essential_files = [
        'app.py',
        'comprehensive_property_compliance.py',
        'nyc_opendata_client.py', 
        'webhook_service.py',
        'vendor_marketplace.py',
        'vendor_service.py',
        'config.py',
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'nginx.conf',
        'Procfile',
        'README.md',
        '.env.example',
        '.dockerignore',
        'templates/propply_report.html'
    ]
    
    for file_name in essential_files:
        file_path = repo_path / file_name
        if file_path.exists():
            print(f"   ✅ {file_name}")
        else:
            print(f"   ❌ {file_name} (MISSING!)")

if __name__ == "__main__":
    print("⚠️  This will permanently delete non-essential files!")
    response = input("Continue with cleanup? (y/N): ").strip().lower()
    
    if response == 'y':
        perform_cleanup()
    else:
        print("❌ Cleanup cancelled.")
