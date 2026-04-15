"""
Helper script to prepare the environment and start the Emergency Response System.
"""

import os
import subprocess
import platform
import sqlite3

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Print colored message
def print_colored(message, color):
    print(f"{color}{message}{Colors.ENDC}")

# Check if the database exists
def check_database():
    db_path = os.path.join(os.path.dirname(__file__), 'emergency_response.db')
    exists = os.path.exists(db_path)
    
    if exists:
        print_colored(f"✓ Database found: {db_path}", Colors.GREEN)
        
        # Check if tables exist
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            
            if tables:
                table_names = [table[0] for table in tables]
                print_colored(f"✓ Tables found: {', '.join(table_names)}", Colors.GREEN)
            else:
                print_colored("✗ No tables found in database!", Colors.RED)
                return False
        except sqlite3.Error as e:
            print_colored(f"✗ Error checking database tables: {e}", Colors.RED)
            return False
    else:
        print_colored(f"✗ Database not found at: {db_path}", Colors.RED)
        return False
    
    return True

# Verify directory structure
def check_directories():
    base_dir = os.path.dirname(__file__)
    frontend_dir = os.path.join(base_dir, 'frontend')
    
    dirs_to_check = [
        (frontend_dir, 'frontend'),
        (os.path.join(frontend_dir, 'callcenter'), 'frontend/callcenter'),
        (os.path.join(frontend_dir, 'ambulance_app'), 'frontend/ambulance_app'),
        (os.path.join(frontend_dir, 'location_share'), 'frontend/location_share')
    ]
    
    files_to_check = [
        (os.path.join(frontend_dir, 'callcenter', 'index.html'), 'frontend/callcenter/index.html'),
        (os.path.join(frontend_dir, 'ambulance_app', 'index.html'), 'frontend/ambulance_app/index.html'),
        (os.path.join(frontend_dir, 'location_share', 'index.html'), 'frontend/location_share/index.html')
    ]
    
    all_good = True
    
    # Check directories
    for path, name in dirs_to_check:
        if os.path.exists(path) and os.path.isdir(path):
            print_colored(f"✓ Directory exists: {name}", Colors.GREEN)
        else:
            print_colored(f"✗ Directory missing: {name}", Colors.RED)
            os.makedirs(path, exist_ok=True)
            print_colored(f"  Created directory: {name}", Colors.YELLOW)
            all_good = False
    
    # Check files
    for path, name in files_to_check:
        if os.path.exists(path) and os.path.isfile(path):
            print_colored(f"✓ File exists: {name}", Colors.GREEN)
        else:
            print_colored(f"✗ File missing: {name}", Colors.RED)
            all_good = False
    
    return all_good

# Initialize database if needed
def initialize_database():
    script_path = os.path.join(os.path.dirname(__file__), 'simple_init_db.py')
    
    if not os.path.exists(script_path):
        print_colored(f"✗ Database initialization script not found: {script_path}", Colors.RED)
        return False
    
    print_colored("Initializing database...", Colors.BLUE)
    
    try:
        result = subprocess.run(['python', script_path], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        
        if result.returncode == 0:
            print_colored("✓ Database initialized successfully", Colors.GREEN)
            print(result.stdout)
            return True
        else:
            print_colored(f"✗ Error initializing database: {result.stderr}", Colors.RED)
            return False
    except Exception as e:
        print_colored(f"✗ Error running database initialization script: {e}", Colors.RED)
        return False

# Start the application
def start_application():
    app_path = os.path.join(os.path.dirname(__file__), 'simple_app.py')
    
    if not os.path.exists(app_path):
        print_colored(f"✗ Application script not found: {app_path}", Colors.RED)
        return False
    
    print_colored("\nStarting Emergency Response System application...", Colors.BLUE)
    
    try:
        if platform.system() == 'Windows':
            os.system(f'start python "{app_path}"')
        else:
            os.system(f'python "{app_path}" &')
        
        print_colored("\n✓ Application started successfully", Colors.GREEN)
        print_colored("\nAccess points:", Colors.BOLD)
        print_colored("- Call Center Dashboard: http://localhost:5000/", Colors.BLUE)
        print_colored("- Ambulance Driver App: http://localhost:5000/api/ambulance/app", Colors.BLUE)
        print_colored("- Test endpoint: http://localhost:5000/test", Colors.BLUE)
        
        return True
    except Exception as e:
        print_colored(f"✗ Error starting application: {e}", Colors.RED)
        return False

# Main function
def main():
    print_colored("\n" + "="*60, Colors.BOLD)
    print_colored("EMERGENCY RESPONSE SYSTEM - SETUP AND START", Colors.BOLD)
    print_colored("="*60 + "\n", Colors.BOLD)
    
    # Check directories
    print_colored("Checking directory structure...", Colors.BLUE)
    dirs_ok = check_directories()
    if not dirs_ok:
        print_colored("Some directories or files are missing. Created the missing directories, but you may need to create the missing files.", Colors.YELLOW)
    
    # Check database
    print_colored("\nChecking database...", Colors.BLUE)
    db_ok = check_database()
    
    # Initialize database if needed
    if not db_ok:
        print_colored("\nDatabase needs to be initialized.", Colors.YELLOW)
        db_init_ok = initialize_database()
        if not db_init_ok:
            print_colored("Failed to initialize database. Please fix the issues before starting the application.", Colors.RED)
            return
    
    # Start application
    print_colored("\nAll checks completed.", Colors.BLUE)
    start_application()

if __name__ == "__main__":
    main()