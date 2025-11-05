from hmac import new
import sqlite3
from click import Option
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import config
from utils import validators

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
            self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints to allow ON DELETE CASCADE to work
        return self.conn
    
    def init_database(self):
        """Create tables if they do not exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Organisation table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Organisation (
                org_id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_name TEXT NOT NULL UNIQUE,
                org_type TEXT NOT NULL,
                org_function TEXT
            )
        """)

        # Stakeholder table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Stakeholder (
                stakeholder_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                painpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                severity TEXT,
                urgency TEXT
            )
        """)

        # Commercial table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Commercial (
                commercial_id INTEGER PRIMARY KEY AUTOINCREMENT,
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

        # OrganisationPainPoint table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS OrganisationPainPoint (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                painpoint_id INTEGER NOT NULL,
                FOREIGN KEY (org_id) REFERENCES Organisation(org_id) ON DELETE CASCADE,
                FOREIGN KEY (painpoint_id) REFERENCES PainPoint(painpoint_id) ON DELETE CASCADE,
                UNIQUE(org_id, painpoint_id)
            )
        """)

        conn.commit()

# CRUD Operations

    # CREATE
    def insert_organisation(self, org_name: str, org_type: str, org_function: str, org_id: Optional[int] = None) -> Optional[int]:
        """Insert a new organisation. Returns the new org_id if successful"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            org_type_norm = validators.normalize_org_type(org_type)
            
            if org_id is None:
                # ID is None, let AUTOINCREMENT handle it
                cursor.execute("""
                    INSERT INTO Organisation (org_name, org_type, org_function)
                    VALUES (?, ?, ?)
                """, (org_name, org_type_norm, org_function))
                new_id = cursor.lastrowid
            else:
                # ID is provided, use it
                cursor.execute("""
                    INSERT INTO Organisation (org_id, org_name, org_type, org_function)
                    VALUES (?, ?, ?, ?)
                """, (org_id, org_name, org_type_norm, org_function))
                new_id = org_id

            conn.commit()
            return new_id
        except sqlite3.IntegrityError as e:
            print(f"Error inserting organisation: {e}")
            conn.rollback()
            return None
        
    def insert_stakeholder(self, org_id: int, name: str, job_title: str, role: str, stakeholder_id: Optional[int] = None) -> Optional[int]:
        """Insert a new stakeholder. Returns the new stakeholder_id if successful"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if stakeholder_id is None:
                # ID is None, let AUTOINCREMENT handle it
                cursor.execute("""
                    INSERT INTO Stakeholder (org_id, name, job_title, role)
                    VALUES (?, ?, ?, ?)
                """, (org_id, name, job_title, role))
                new_id = cursor.lastrowid
            else:
                # ID is provided, use it
                cursor.execute("""
                    INSERT INTO Stakeholder (stakeholder_id, org_id, name, job_title, role)
                    VALUES (?, ?, ?, ?, ?)
                """, (stakeholder_id, org_id, name, job_title, role))
            conn.commit()
            return new_id
        except sqlite3.IntegrityError as e:
            print(f"Error inserting stakeholder: {e}")
            conn.rollback()
            return None
        
    def insert_painpoint(self, description: str, severity: str, urgency: str, painpoint_id: Optional[int] = None) -> Optional[int]:
        """Insert a new pain point. Returns the new painpoint_id if successful"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if painpoint_id is None:
                # ID is None, let AUTOINCREMENT handle it
                cursor.execute("""
                    INSERT INTO PainPoint (description, severity, urgency)
                    VALUES (?, ?, ?)
                """, (description, severity, urgency))
                new_id = cursor.lastrowid
            else:
                # ID is provided, use it
                cursor.execute("""
                    INSERT INTO PainPoint (painpoint_id, description, severity, urgency)
                    VALUES (?, ?, ?, ?)
                """, (painpoint_id, description, severity, urgency))
            conn.commit()
            return new_id
        except sqlite3.IntegrityError as e:
            print(f"Error inserting pain point: {e}")
            conn.rollback()
            return None

    def insert_commercial(self, org_id: int, method: str, budget: float, commercial_id: Optional[int] = None) -> Optional[int]:
        """Insert a new commercial entry. Returns the new commercial_id if successful"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            budget_norm = validators.parse_budget(budget)

            if commercial_id is None:
                # ID is None, let AUTOINCREMENT handle it
                cursor.execute("""
                    INSERT INTO Commercial (org_id, method, budget)
                    VALUES (?, ?, ?)
                """, (org_id, method, budget_norm))
                new_id = cursor.lastrowid
            else:
                # ID is provided, use it
                cursor.execute("""
                    INSERT INTO Commercial (commercial_id, org_id, method, budget)
                    VALUES (?, ?, ?, ?)
                """, (commercial_id, org_id, method, budget_norm))
            conn.commit()
            return new_id
        except sqlite3.IntegrityError as e:
            print(f"Error inserting commercial entry: {e}")
            conn.rollback()
            return None
        
    def insert_org_relationship(self, from_org_id: int, to_org_id: int, relationship_type: str) -> bool:
        """Insert a new organization relationship."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            relationship_type_norm = validators.normalize_relationship_type(relationship_type)
            cursor.execute("""
                INSERT INTO OrgRelationships (from_org_id, to_org_id, relationship_type)
                VALUES (?, ?, ?)
            """, (from_org_id, to_org_id, relationship_type_norm))
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Error inserting organization relationship: {e}")
            conn.rollback()
            return False
        
    def insert_painpoint_assignment(self, org_id: int, painpoint_id: int) -> bool:
        """Insert a new organisation ↔ painpoint relationship"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO OrganisationPainPoint (org_id, painpoint_id)
                VALUES (?, ?)
            """, (org_id, painpoint_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Error inserting organisation ↔ painpoint assignment: {e}")
            conn.rollback()
            return False
        
    # READ
    def get_all_organisations(self) -> pd.DataFrame:
        """Get all organisations as DataFrame."""
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM Organisation ORDER BY org_name", conn)
        return df
    
    def get_all_stakeholders(self) -> pd.DataFrame:
        """Get all stakeholders with org names"""
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT s.*, o.org_name
            FROM Stakeholder s
            LEFT JOIN Organisation o ON s.org_id = o.org_id
            ORDER BY s.name
        """, conn)
        return df
    
    def get_all_painpoints(self) -> pd.DataFrame:
        """Get all pain points with org names"""
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT
                p.*,
                GROUP_CONCAT(o.org_name, ', ') AS org_names,
                GROUP_CONCAT(o.org_id) AS org_ids
            FROM PainPoint p
            LEFT JOIN OrganisationPainPoint opp ON p.painpoint_id = opp.painpoint_id
            LEFT JOIN Organisation o ON opp.org_id = o.org_id
            GROUP BY p.painpoint_id
            ORDER BY p.severity DESC, p.urgency DESC
        """, conn)
        return df
    
    def get_painpoint_assignments(self, painpoint_id: int) -> List[int]:
        """Get all organisation IDs assigned to a pain point."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT org_id
            FROM OrganisationPainPoint
            WHERE painpoint_id = ?
        """, (painpoint_id,))
        rows = cursor.fetchall()
        return [row['org_id'] for row in rows]
    
    def get_all_painpoint_assignments(self) -> pd.DataFrame:
        """Get all pain point assignments with org names"""
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT org_id, painpoint_id
            FROM OrganisationPainPoint
        """, conn)
        return df
    
    def get_all_commercials(self) -> pd.DataFrame:
        """Get all commercial entries with org names"""
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT c.*, o.org_name
            FROM Commercial c
            LEFT JOIN Organisation o ON c.org_id = o.org_id
            ORDER BY c.budget DESC
        """, conn)
        return df

    def get_all_org_relationships(self) -> pd.DataFrame:
        """Get all organization relationships with org names"""
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT
                r.id,
                r.from_org_id,
                o1.org_name AS from_org_name,
                r.to_org_id,
                o2.org_name AS to_org_name,
                r.relationship_type
            FROM OrgRelationships r
            LEFT JOIN Organisation o1 ON r.from_org_id = o1.org_id
            LEFT JOIN Organisation o2 ON r.to_org_id = o2.org_id
            ORDER BY o1.org_name
        """, conn)
        return df
    
    def get_organisation_by_id(self, org_id: int) -> Optional[Dict]:
        """Get an organisation by its ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Organisation WHERE org_id = ?", (org_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # UPDATE
    def update_organisation(self, org_id: int, org_name: str, org_type: str, org_function: str) -> bool:
        """Update an existing organisation."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Organisation
                SET org_name = ?, org_type = ?, org_function = ?
                WHERE org_id = ?
            """, (org_name, org_type, org_function, org_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            print(f"Error updating organisation: {e}")
            return False
        
    def update_stakeholder(self, stakeholder_id: int, org_id: int, name: str, job_title: str, role: str) -> bool:
        """Update an existing stakeholder."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Stakeholder
                SET org_id = ?, name = ?, job_title = ?, role = ?
                WHERE stakeholder_id = ?
            """, (org_id, name, job_title, role, stakeholder_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            print(f"Error updating stakeholder: {e}")
            return False
        
    def update_painpoint(self, painpoint_id: int, description: str, severity: str, urgency: str) -> bool:
        """Update an existing pain point."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE PainPoint
                SET description = ?, severity = ?, urgency = ?
                WHERE painpoint_id = ?
            """, (description, severity, urgency, painpoint_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            print(f"Error updating pain point: {e}")
            return False
        
    def update_painpoint_assignments(self, painpoint_id: int, org_ids: List[int]) -> bool:
        """Update the assignments of a pain point to organisations."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Delete existing assignments
            cursor.execute("DELETE FROM OrganisationPainPoint WHERE painpoint_id = ?", (painpoint_id,))
            # Insert new assignments
            for org_id in org_ids:
                cursor.execute("""
                    INSERT INTO OrganisationPainPoint (org_id, painpoint_id)
                    VALUES (?, ?)
                """, (org_id, painpoint_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Error updating pain point assignments: {e}")
            return False
        
    def update_commercial(self, commercial_id: int, org_id: int, method: str, budget: float) -> bool:   
        """Update an existing commercial entry."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Commercial
                SET org_id = ?, method = ?, budget = ?
                WHERE commercial_id = ?
            """, (org_id, method, budget, commercial_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            print(f"Error updating commercial entry: {e}")
            return False
    
    # DELETE
    def delete_organisation(self, org_id: int) -> bool:
        """Delete an organisation by its ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Organisation WHERE org_id = ?", (org_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting organisation: {e}")
            return False

    def delete_stakeholder(self, stakeholder_id: int) -> bool:
        """Delete a stakeholder by its ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Stakeholder WHERE stakeholder_id = ?", (stakeholder_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting stakeholder: {e}")
            return False

    def delete_painpoint(self, painpoint_id: int) -> bool:
        """Delete a pain point by its ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM PainPoint WHERE painpoint_id = ?", (painpoint_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting pain point: {e}")
            return False

    def delete_commercial(self, commercial_id: int) -> bool:
        """Delete a commercial entry by its ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Commercial WHERE commercial_id = ?", (commercial_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting commercial entry: {e}")
            return False
        
    def delete_org_relationship(self, relationship_id: int) -> bool:
        """Delete an organization relationship by its ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM OrgRelationships WHERE id = ?", (relationship_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting organization relationship: {e}")
            return False
        
    # UTILITY   
    def close_connection(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None