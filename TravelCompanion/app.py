import os
import sys
import subprocess
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def initialize_database():
    """Create database and run migrations if needed"""
    print("Initializing database...")
    try:
        # Make migrations
        subprocess.run([sys.executable, "manage.py", "makemigrations"], check=True)
        # Apply migrations
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        print("Database initialization complete.")
    except subprocess.CalledProcessError as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)

def run_server():
    """Run the Django development server"""
    print("Starting development server...")
    try:
        # Run the server on 0.0.0.0 to make it accessible from outside
        subprocess.run([
            sys.executable, "manage.py", "runserver", "0.0.0.0:5000"
        ])
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Initialize the database
    initialize_database()
    
    # Run the server
    run_server()