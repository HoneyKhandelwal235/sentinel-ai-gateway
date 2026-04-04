import sqlite3
import hashlib
import uuid
import re
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

class IdentityVault:
    """
    Enterprise-grade Identity Vault for PII management with SQLite backend.
    Supports persistent placeholder mapping and Indian ID detection (PAN/Aadhaar).
    """
    
    def __init__(self, db_path: str = "identity_vault.db"):
        """Initialize the identity vault with enhanced PII patterns."""
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        
        # Initialize Presidio with error handling
        try:
            self._initialize_presidio()
        except Exception as e:
            print(f"Warning: Presidio initialization failed: {e}")
            # Set up basic patterns as fallback
            self.analyzer = None
            self.anonymizer = None
        
        # Enhanced PII detection patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\+?91[-\s]?(\d{10}|\d{3}[-\s]?\d{3}[-\s]?\d{4})')
        
        # Enhanced Aadhaar patterns for different formats
        self.aadhaar_patterns = [
            re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),  # XXXX-XXXX-XXXX or XXXX XXXX XXXX
            re.compile(r'\b\d{12}\b'),  # XXXXXXXXXXXX (12 digits)
            re.compile(r'\b\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{2}\b')  # XX-XXXX-XXXX-XX
        ]
        self.pan_pattern = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')
        
    def _initialize_presidio(self):
        """Initialize Presidio analyzer and anonymizer with error handling."""
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            print("Presidio initialized successfully")
        except ImportError as e:
            print(f"Presidio not available: {e}")
            self.analyzer = None
            self.anonymizer = None
        except Exception as e:
            print(f"Presidio initialization error: {e}")
            self.analyzer = None
            self.anonymizer = None
    
    def _create_tables(self):
        """Initialize SQLite database with required tables for multi-tenant architecture."""
        cursor = self.conn.cursor()
        
        # Create Users Table FIRST (required for foreign keys)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create PII Mappings Table (depends on users)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pii_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                placeholder TEXT UNIQUE NOT NULL,
                real_value TEXT NOT NULL,
                pii_type TEXT NOT NULL,
                hash_value TEXT NOT NULL,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Create Audit Log Table (depends on users)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                operation TEXT NOT NULL,
                pii_type TEXT,
                placeholder TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Create Chat History Table (depends on users)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                pii_detected TEXT,
                processing_time REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Create Privacy Stats Table (depends on users) - SIMPLIFIED VERSION
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS privacy_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT NOT NULL,
                pii_type TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        self.conn.commit()
    
    def _generate_placeholder(self, pii_type: str) -> str:
        """Generate unique placeholder for PII."""
        return f"[{pii_type}_{uuid.uuid4().hex[:8]}]"
    
    def _hash_value(self, value: str) -> str:
        """Generate SHA-256 hash for PII value."""
        return hashlib.sha256(value.encode()).hexdigest()
    
    def detect_indian_ids(self, text: str, user_id: int) -> List[Tuple[str, str, str]]:
        """
        Detect Indian IDs (PAN and Aadhaar) in text with enhanced patterns (user-isolated).
        Returns: List of tuples (value, type, placeholder)
        """
        detections = []
        
        # Detect PAN numbers
        for match in self.pan_pattern.finditer(text):
            pan_value = match.group()
            placeholder = self._get_or_create_placeholder(pan_value, "PAN", user_id)
            detections.append((pan_value, "PAN", placeholder))
        
        # Detect Aadhaar numbers with multiple patterns
        for pattern in self.aadhaar_patterns:
            for match in pattern.finditer(text):
                aadhaar_value = re.sub(r'[-\s]', '', match.group())  # Remove spaces and dashes
                if len(aadhaar_value) == 12:  # Validate length
                    placeholder = self._get_or_create_placeholder(aadhaar_value, "AADHAAR", user_id)
                    detections.append((match.group(), "AADHAAR", placeholder))
        
        return detections
    
    def detect_pii(self, text: str, user_id: int) -> List[Tuple[str, str, str]]:
        """
        Detect all PII types including Indian IDs (user-isolated).
        Returns: List of tuples (value, type, placeholder)
        """
        detections = []
        
        # Detect Indian IDs
        detections.extend(self.detect_indian_ids(text, user_id))
        
        # Detect emails
        for match in self.email_pattern.finditer(text):
            email_value = match.group()
            placeholder = self._get_or_create_placeholder(email_value, "EMAIL", user_id)
            detections.append((email_value, "EMAIL", placeholder))
        
        # Detect phone numbers
        for match in self.phone_pattern.finditer(text):
            phone_value = match.group()
            placeholder = self._get_or_create_placeholder(phone_value, "PHONE", user_id)
            detections.append((phone_value, "PHONE", placeholder))
        
        return detections
    
    def _get_or_create_placeholder(self, real_value: str, pii_type: str, user_id: int) -> str:
        """Get existing placeholder or create new one for PII (user-isolated)."""
        hash_value = self._hash_value(real_value)
        cursor = self.conn.cursor()
        
        # Check if PII already exists for this user
        cursor.execute(
            "SELECT placeholder FROM pii_mappings WHERE hash_value = ? AND pii_type = ? AND user_id = ?",
            (hash_value, pii_type, user_id)
        )
        result = cursor.fetchone()
        
        if result:
            placeholder = result[0]
            # Update access count
            cursor.execute(
                "UPDATE pii_mappings SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE placeholder = ?",
                (placeholder,)
            )
        else:
            placeholder = self._generate_placeholder(pii_type)
            cursor.execute(
                "INSERT INTO pii_mappings (placeholder, real_value, pii_type, hash_value, user_id) VALUES (?, ?, ?, ?, ?)",
                (placeholder, real_value, pii_type, hash_value, user_id)
            )
        
        self.conn.commit()
        return placeholder
    
    def redact_with_mapping(self, text: str, user_id: int, session_id: str = None) -> Tuple[str, Dict[str, str]]:
        """
        Redact PII from text and return mapping (user-isolated).
        Returns: (redacted_text, {placeholder: real_value})
        """
        detections = self.detect_pii(text, user_id)
        mapping = {}
        redacted_text = text
        
        for value, pii_type, placeholder in detections:
            mapping[placeholder] = value
            redacted_text = redacted_text.replace(value, placeholder)
            
            # Log operation
            self._log_operation("REDACT", pii_type, placeholder, user_id, session_id)
            self._update_stats(pii_type, user_id)
        
        return redacted_text, mapping
    
    def rehydrate_text(self, text: str, mapping: Dict[str, str], session_id: str = None) -> str:
        """
        Re-hydrate text by replacing placeholders with real values.
        """
        rehydrated_text = text
        
        for placeholder, real_value in mapping.items():
            rehydrated_text = rehydrated_text.replace(placeholder, real_value)
            # Log operation
            self._log_operation("REHYDRATE", self._get_pii_type(placeholder), placeholder, session_id)
        
        return rehydrated_text
    
    def _get_pii_type(self, placeholder: str) -> str:
        """Extract PII type from placeholder."""
        match = re.match(r'\[([A-Z_]+)_', placeholder)
        return match.group(1) if match else "UNKNOWN"
    
    def _log_operation(self, operation: str, pii_type: str, placeholder: str, user_id: int, session_id: str = None):
        """Log privacy operations for audit trail (user-isolated)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO audit_log (operation, pii_type, placeholder, user_id, session_id) VALUES (?, ?, ?, ?, ?)",
            (operation, pii_type, placeholder, user_id, session_id)
        )
        self.conn.commit()
    
    def _update_stats(self, pii_type: str, user_id: int):
        """Update daily privacy statistics (user-isolated)."""
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute(
            "INSERT OR REPLACE INTO privacy_stats (user_id, date, pii_type, count) VALUES (?, ?, ?, COALESCE((SELECT count FROM privacy_stats WHERE user_id = ? AND date = ? AND pii_type = ?), 0) + 1)",
            (user_id, today, pii_type, user_id, today, pii_type)
        )
        self.conn.commit()
    
    def get_privacy_stats(self, user_id: int) -> Dict[str, int]:
        """Get current privacy statistics for a specific user."""
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute(
            "SELECT pii_type, count FROM privacy_stats WHERE date = ? AND user_id = ?",
            (today, user_id)
        )
        
        stats = {row[0]: row[1] for row in cursor.fetchall()}
        return stats
    
    def get_vault_summary(self, user_id: int) -> Dict:
        """Get comprehensive vault summary for a specific user."""
        cursor = self.conn.cursor()
        
        # Total mappings for user
        cursor.execute("SELECT COUNT(*) FROM pii_mappings WHERE user_id = ?", (user_id,))
        total_mappings = cursor.fetchone()[0]
        
        # PII type breakdown for user
        cursor.execute("SELECT pii_type, COUNT(*) FROM pii_mappings WHERE user_id = ? GROUP BY pii_type", (user_id,))
        type_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Recent activity for user
        cursor.execute("""
            SELECT operation, pii_type, timestamp 
            FROM audit_log 
            WHERE user_id = ?
            ORDER BY timestamp DESC 
            LIMIT 10
        """, (user_id,))
        recent_activity = cursor.fetchall()
        
        return {
            "total_mappings": total_mappings,
            "type_breakdown": type_breakdown,
            "recent_activity": recent_activity,
            "today_stats": self.get_privacy_stats(user_id)
        }
    
    # ===== USER AUTHENTICATION FUNCTIONS =====
    
    def create_user(self, username: str, password: str, email: str = None) -> bool:
        """
        Create a new user with hashed password.
        Raises ValueError on failure.
        Returns True on success.
        """
        cursor = self.conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            raise ValueError("Username already exists")
        
        # Check if email already exists
        if email:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                raise ValueError("Email already exists")
        
        # Hash password
        password_hash = self._hash_password(password)
        
        # Create user
        cursor.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            (username, password_hash, email)
        )
        self.conn.commit()
        return True
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt."""
        import hashlib
        salt = "sentinel_ai_gateway_salt_2024"  # Fixed salt for consistency
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return self._hash_password(password) == hashed
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username and password."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, email, is_active, created_at, last_login FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        
        if user and user[4]:  # Check if user is active
            stored_hash = user[2]
            if self.verify_password(password, stored_hash):
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user[0],)
                )
                self.conn.commit()
                
                return {
                    "id": user[0],
                    "username": user[1],
                    "email": user[3],
                    "is_active": user[4],
                    "created_at": user[5],
                    "last_login": user[6]
                }
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user information by ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, username, email, is_active, created_at, last_login FROM users WHERE id = ?",
            (user_id,)
        )
        user = cursor.fetchone()
        
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "is_active": user[3],
                "created_at": user[4],
                "last_login": user[5]
            }
        return None
    
    def save_chat_message(self, user_id: int, message_type: str, content: str, 
                          pii_detected: str = None, processing_time: float = None, 
                          session_id: str = None):
        """Save chat message with robust error handling and fallback."""
        try:
            # Validate user_id exists before proceeding
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            user_exists = cursor.fetchone()
            
            if not user_exists:
                print(f"DEBUG: User ID {user_id} not found in database")
                # Don't raise error, just return silently to avoid breaking chat
                return
            
            # Insert chat message
            cursor.execute('''
                INSERT INTO chat_history 
                (user_id, message_type, content, pii_detected, processing_time, timestamp, session_id)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (user_id, message_type, content, pii_detected, processing_time, session_id))
            
            self.conn.commit()
            print(f"DEBUG: Chat message saved successfully for user {user_id}")
            
        except Exception as e:
            print(f"DEBUG: Error saving chat message: {e}")
            self.conn.rollback()
            # Don't raise error to avoid breaking chat flow
            return
    
    def get_chat_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get chat history for user."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT message_type, content, pii_detected, processing_time, timestamp, session_id FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        
        messages = []
        for row in cursor.fetchall():
            pii_detected = json.loads(row[2]) if row[2] else []
            messages.append({
                "message_type": row[0],
                "content": row[1],
                "pii_detected": pii_detected,
                "processing_time": row[3],
                "timestamp": row[4],
                "session_id": row[5]
            })
        
        return messages
    
    def clear_user_chat_history(self, user_id: int):
        """Clear chat history for user."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        self.conn.commit()
    
    def get_audit_log_for_user(self, user_id: int, limit: int = 1000) -> List[Dict]:
        """Export audit log for specific user."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT operation, pii_type, placeholder, timestamp, session_id FROM audit_log WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        
        columns = [description[0] for description in cursor.description]
        audit_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return audit_data
    
    def export_audit_log_for_user(self, user_id: int, limit: int = 1000) -> List[Dict]:
        """Export audit log for specific user (alias for compatibility)."""
        return self.get_audit_log_for_user(user_id, limit)
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

# --- TEST ---
if __name__ == "__main__":
    import json
    
    vault = IdentityVault()
    
    # Test user creation
    print("=== USER AUTHENTICATION TEST ===")
    success, message = vault.create_user("testuser", "testpass123", "test@example.com")
    print(f"User creation: {success} - {message}")
    
    # Test authentication
    user = vault.authenticate_user("testuser", "testpass123")
    if user:
        print(f"Authentication successful: {user}")
        
        # Test PII detection for user
        test_text = "My name is John Doe. Email: john.doe@example.com, Phone: +91-9876543210. PAN: ABCDE1234F, Aadhaar: 2345 6789 0123"
        
        print("\n=== PII DETECTION TEST ===")
        print(f"Original: {test_text}")
        
        redacted, mapping = vault.redact_with_mapping(test_text, user['id'], "test_session")
        print(f"Redacted: {redacted}")
        print(f"Mapping: {mapping}")
        
        # Save chat message
        vault.save_chat_message(user['id'], "user", test_text, list(mapping.values()), 1.5, "test_session")
        vault.save_chat_message(user['id'], "ai", "This is a response", [], 0.8, "test_session")
        
        # Get chat history
        print("\n=== CHAT HISTORY ===")
        history = vault.get_chat_history(user['id'])
        for msg in history:
            print(f"{msg['message_type']}: {msg['content'][:50]}...")
        
        # Get vault summary
        print("\n=== VAULT SUMMARY ===")
        summary = vault.get_vault_summary(user['id'])
        print(f"Total mappings: {summary['total_mappings']}")
        print(f"PII types: {summary['type_breakdown']}")
        print(f"Today's stats: {summary['today_stats']}")
        
    else:
        print("Authentication failed")
    
    vault.close()
