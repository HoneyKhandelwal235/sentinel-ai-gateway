#!/usr/bin/env python3
"""
Database Reset Script
Forces a complete database reset by bypassing file locks
"""

import os
import sqlite3
import time
import shutil

def reset_database():
    """Force reset the database file"""
    db_path = "identity_vault.db"
    
    print("🔧 Forcing database reset...")
    
    # Try multiple methods to delete the database
    methods = [
        lambda: os.remove(db_path) if os.path.exists(db_path) else None,
        lambda: os.unlink(db_path) if os.path.exists(db_path) else None,
        lambda: shutil.rmtree(db_path, ignore_errors=True) if os.path.exists(db_path) else None,
    ]
    
    for i, method in enumerate(methods):
        try:
            method()
            print(f"✅ Method {i+1} successful")
            break
        except Exception as e:
            print(f"❌ Method {i+1} failed: {e}")
            continue
    
    # Check if file still exists
    if os.path.exists(db_path):
        print("❌ Database file still exists, trying manual deletion...")
        try:
            # Last resort - create a backup and delete
            backup_path = f"{db_path}.backup.{int(time.time())}"
            shutil.move(db_path, backup_path)
            print(f"✅ Moved to backup: {backup_path}")
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    # Verify deletion
    if not os.path.exists(db_path):
        print("✅ Database successfully deleted!")
        
        # Test creating a new database
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.commit()
            conn.close()
            
            # Clean up test table
            conn = sqlite3.connect(db_path)
            conn.execute("DROP TABLE test")
            conn.commit()
            conn.close()
            
            print("✅ New database created successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to create new database: {e}")
            return False
    else:
        print("❌ Database file still exists")
        return False

if __name__ == "__main__":
    success = reset_database()
    if success:
        print("🎉 Database reset complete! You can now restart the app.")
    else:
        print("❌ Database reset failed. Please manually delete identity_vault.db")
