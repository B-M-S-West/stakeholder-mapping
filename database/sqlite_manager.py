import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import config

class SQLiteManager:
    def __init__(self, db_path: Path = config.SQLITE_DB):
        self.db_path = db_path
        self.conn = None
        self.init_database()

    def get_connection(self):
        """Get or create database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row # Return rows as dictionaries
        return self.conn
    
    def init_database(self):
        """Create tables if they do not exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Organisation table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Organisation (
                org_id INTEGER PRIMARY KEY,
                org_name TEXT NOT NULL UNIQUE,
                org_type TEXT NOT NULL,
                org_function TEXT
            )
        """)

        # Stakeholder table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Stakeholder (
                stakeholder_id INTEGER PRIMARY KEY,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                job_title TEXT,
                role TEXT,
                FOREIGN KEY (org_id) REFERENCES Organisation(org_id) ON DELETE CASCADE
            )
        """)

        # PainPoint table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS PainPoint (
                painpoint_id INTEGER PRIMARY KEY,
                org_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                severity TEXT,
                urgency TEXT,
                FOREIGN KEY (org_id) REFERENCES Organisation(org_id) ON DELETE CASCADE
            )
        """)

        # Commercial table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Commercial (
                commercial_id INTEGER PRIMARY KEY,
                org_id INTEGER NOT NULL,
                method TEXT NOT NULL,
                budget REAL,
                FOREIGN KEY (org_id) REFERENCES Organisation(org_id) ON DELETE CASCADE
            )
        """)

        # OrgRelationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS OrgRelationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_org_id INTEGER NOT NULL,
                to_org_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                FOREIGN KEY (from_org_id) REFERENCES Organisation(org_id) ON DELETE CASCADE,
                FOREIGN KEY (to_org_id) REFERENCES Organisation(org_id) ON DELETE CASCADE,
                UNIQUE(from_org_id, to_org_id, relationship_type)
            )
        """)

        conn.commit()

# CRUD Operations

    # CREATE
    def insert_organisation(self, org_id: int, org_name: str, org_type: str, org_function: str) -> bool:
        """Insert a new organisation."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Organisation (org_id, org_name, org_type, org_function)
                VALUES (?, ?, ?, ?)
            """, (org_id, org_name, org_type, org_function))
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Error inserting organisation: {e}")
            return False
        
    def insert_stakeholder(self, stakeholder_id: int, org_id: int, name: str, job_title: str, role: str) -> bool:
        """Insert a new stakeholder."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Stakeholder (stakeholder_id, org_id, name, job_title, role)
                VALUES (?, ?, ?, ?, ?)
            """, (stakeholder_id, org_id, name, job_title, role))
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Error inserting stakeholder: {e}")
            return False
        
    def insert_painpoint(self, painpoint_id: int, org_id: int, description: str, severity: str, urgency: str) -> bool:
        """Insert a new pain point."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO PainPoint (painpoint_id, org_id, description, severity, urgency)
                VALUES (?, ?, ?, ?, ?)
            """, (painpoint_id, org_id, description, severity, urgency))
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Error inserting pain point: {e}")
            return False
        
    def insert_commercial(self, commercial_id: int, org_id: int, method: str, budget: float) -> bool:
        """Insert a new commercial entry."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Commercial (commercial_id, org_id, method, budget)
                VALUES (?, ?, ?, ?)
            """, (commercial_id, org_id, method, budget))
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Error inserting commercial entry: {e}")
            return False
        
    def insert_org_relationship(self, from_org_id: int, to_org_id: int, relationship_type: str) -> bool:
        """Insert a new organization relationship."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO OrgRelationships (from_org_id, to_org_id, relationship_type)
                VALUES (?, ?, ?)
            """, (from_org_id, to_org_id, relationship_type))
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Error inserting organization relationship: {e}")
            return False
        
    # READ