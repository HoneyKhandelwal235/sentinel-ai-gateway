import sqlite3
import re
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class IdentityVault:
    """
    Enterprise-grade Identity Vault for PII management with SQLite backend.
    Supports persistent placeholder mapping and Indian ID detection (PAN/Aadhaar).
    """
    
    def __init__(self, db_path: str = "identity_vault.db"):
        self.db_path = db_path
        self.conn = None
        self._initialize_database()
        
        # Indian ID Regex Patterns
        self.pan_pattern = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')
        self.aadhaar_pattern = re.compile(r'\b[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b')
        
        # PII Patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\b(?:\+91[-\s]?|0)?[6-9]\d{9}\b')
        
    def _initialize_database(self):
        """Initialize SQLite database with required tables."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        # PII Mappings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pii_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                placeholder TEXT UNIQUE NOT NULL,
                real_value TEXT NOT NULL,
                pii_type TEXT NOT NULL,
                hash_value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            )
        ''')
        
        # Audit Log Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                pii_type TEXT NOT NULL,
                placeholder TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT
            )
        ''')
        
        # Statistics Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS privacy_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                pii_type TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                UNIQUE(date, pii_type)
            )
        ''')
        
        self.conn.commit()
    
    def _generate_placeholder(self, pii_type: str) -> str:
        """Generate unique placeholder for PII."""
        return f"[{pii_type}_{uuid.uuid4().hex[:8]}]"
    
    def _hash_value(self, value: str) -> str:
        """Generate SHA-256 hash for PII value."""
        return hashlib.sha256(value.encode()).hexdigest()
    
    def detect_indian_ids(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Detect Indian IDs (PAN and Aadhaar) in text.
        Returns: List of tuples (value, type, placeholder)
        """
        detections = []
        
        # Detect PAN numbers
        for match in self.pan_pattern.finditer(text):
            pan_value = match.group()
            placeholder = self._get_or_create_placeholder(pan_value, "PAN")
            detections.append((pan_value, "PAN", placeholder))
        
        # Detect Aadhaar numbers
        for match in self.aadhaar_pattern.finditer(text):
            aadhaar_value = re.sub(r'\s', '', match.group())  # Remove spaces
            if len(aadhaar_value) == 12:  # Validate length
                placeholder = self._get_or_create_placeholder(aadhaar_value, "AADHAAR")
                detections.append((match.group(), "AADHAAR", placeholder))
        
        return detections
    
    def detect_pii(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Detect all PII types including Indian IDs.
        Returns: List of tuples (value, type, placeholder)
        """
        detections = []
        
        # Detect Indian IDs
        detections.extend(self.detect_indian_ids(text))
        
        # Detect emails
        for match in self.email_pattern.finditer(text):
            email_value = match.group()
            placeholder = self._get_or_create_placeholder(email_value, "EMAIL")
            detections.append((email_value, "EMAIL", placeholder))
        
        # Detect phone numbers
        for match in self.phone_pattern.finditer(text):
            phone_value = match.group()
            placeholder = self._get_or_create_placeholder(phone_value, "PHONE")
            detections.append((phone_value, "PHONE", placeholder))
        
        return detections
    
    def _get_or_create_placeholder(self, real_value: str, pii_type: str) -> str:
        """Get existing placeholder or create new one for PII."""
        hash_value = self._hash_value(real_value)
        cursor = self.conn.cursor()
        
        # Check if PII already exists
        cursor.execute(
            "SELECT placeholder FROM pii_mappings WHERE hash_value = ? AND pii_type = ?",
            (hash_value, pii_type)
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
                "INSERT INTO pii_mappings (placeholder, real_value, pii_type, hash_value) VALUES (?, ?, ?, ?)",
                (placeholder, real_value, pii_type, hash_value)
            )
        
        self.conn.commit()
        return placeholder
    
    def redact_with_mapping(self, text: str, session_id: str = None) -> Tuple[str, Dict[str, str]]:
        """
        Redact PII from text and return mapping.
        Returns: (redacted_text, {placeholder: real_value})
        """
        detections = self.detect_pii(text)
        mapping = {}
        redacted_text = text
        
        for value, pii_type, placeholder in detections:
            mapping[placeholder] = value
            redacted_text = redacted_text.replace(value, placeholder)
            
            # Log operation
            self._log_operation("REDACT", pii_type, placeholder, session_id)
            self._update_stats(pii_type)
        
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
    
    def _log_operation(self, operation: str, pii_type: str, placeholder: str, session_id: str = None):
        """Log privacy operations for audit trail."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO audit_log (operation, pii_type, placeholder, session_id) VALUES (?, ?, ?, ?)",
            (operation, pii_type, placeholder, session_id)
        )
        self.conn.commit()
    
    def _update_stats(self, pii_type: str):
        """Update daily privacy statistics."""
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute(
            "INSERT OR REPLACE INTO privacy_stats (date, pii_type, count) VALUES (?, ?, COALESCE((SELECT count FROM privacy_stats WHERE date = ? AND pii_type = ?), 0) + 1)",
            (today, pii_type, today, pii_type)
        )
        self.conn.commit()
    
    def get_privacy_stats(self) -> Dict[str, int]:
        """Get current privacy statistics."""
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute(
            "SELECT pii_type, count FROM privacy_stats WHERE date = ?",
            (today,)
        )
        
        stats = {row[0]: row[1] for row in cursor.fetchall()}
        return stats
    
    def get_vault_summary(self) -> Dict:
        """Get comprehensive vault summary."""
        cursor = self.conn.cursor()
        
        # Total mappings
        cursor.execute("SELECT COUNT(*) FROM pii_mappings")
        total_mappings = cursor.fetchone()[0]
        
        # PII type breakdown
        cursor.execute("SELECT pii_type, COUNT(*) FROM pii_mappings GROUP BY pii_type")
        type_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Recent activity
        cursor.execute("""
            SELECT operation, pii_type, timestamp 
            FROM audit_log 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        recent_activity = cursor.fetchall()
        
        return {
            "total_mappings": total_mappings,
            "type_breakdown": type_breakdown,
            "recent_activity": recent_activity,
            "today_stats": self.get_privacy_stats()
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

# --- TEST ---
if __name__ == "__main__":
    vault = IdentityVault()
    
    # Test with Indian IDs and PII
    test_text = """
    My name is John Doe. Email: john.doe@example.com, Phone: +91-9876543210.
    PAN: ABCDE1234F, Aadhaar: 2345 6789 0123
    """
    
    print("=== ORIGINAL TEXT ===")
    print(test_text)
    
    redacted, mapping = vault.redact_with_mapping(test_text, "test_session")
    
    print("\n=== REDACTED TEXT ===")
    print(redacted)
    
    print("\n=== MAPPING ===")
    for placeholder, real_value in mapping.items():
        print(f"{placeholder} -> {real_value}")
    
    print("\n=== VAULT SUMMARY ===")
    summary = vault.get_vault_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    vault.close()
