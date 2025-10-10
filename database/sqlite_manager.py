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
    