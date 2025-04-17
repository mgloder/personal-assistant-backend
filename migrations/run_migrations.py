#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import psycopg2

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

def wait_for_postgres():
    """Wait for PostgreSQL to be ready."""
    print("Waiting for PostgreSQL to be ready...")
    while True:
        try:
            # Try to connect to our database
            conn = psycopg2.connect(
                dbname="little_dragon",
                user="postgres",
                password="postgres",
                host="postgres",
                port="5432"
            )
            conn.close()
            print("PostgreSQL is ready!")
            break
        except psycopg2.OperationalError as e:
            print(f"PostgreSQL is not ready yet... Error: {e}")
            time.sleep(1)

def run_migrations():
    """Run database migrations using Alembic."""
    print("Running database migrations...")
    try:
        # Set the PYTHONPATH environment variable
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        
        subprocess.run(["alembic", "upgrade", "head"], check=True, env=env)
        print("Migrations completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)

def main():
    """Main function to run migrations and start the application."""
    wait_for_postgres()
    run_migrations()
    
    # Start the application
    print("Starting the application...")
    os.execvp("uvicorn", ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"])

if __name__ == "__main__":
    main() 