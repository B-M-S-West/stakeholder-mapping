from math import e
import kuzu
from pathlib import Path
from typing import List, Dict, Any
import config

class KuzuManager:
    def __init__(self, db_path: Path = config.KUZU_DB):
        self.db_path = db_path
        self.db = kuzu.Database(str(db_path))
        self.conn = kuzu.Connection(self.db)
        self.init_schema()

    def init_schema(self):
        """Create Kuzu schema if not exists."""
        try:
            # Create if tables exist, if not create them
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Organisation (
                    org_id INT64,
                    org_name STRING,
                    org_type STRING,
                    org_function STRING,
                    PRIMARY KEY (org_id)
                )
            """)

            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Stakeholder (
                    stakeholder_id INT64,
                    org_id INT64,
                    name STRING,
                    job_title STRING,
                    role STRING,
                    PRIMARY KEY (stakeholder_id)
                )
            """)

            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Commercial (
                    commercial_id INT64,
                    org_id INT64,
                    method STRING,
                    budget DOUBLE,
                    PRIMARY KEY (commercial_id)
                )
            """)

            # Relationships
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS OrgRelation (
                    FROM Organisation TO Organisation
                    relationship_type STRING
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS HasStakeholder (
                    FROM Organisation TO Stakeholder
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS HasPainPoint (
                    FROM Organisation TO PainPoint
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS ProcuresThrough (
                    FROM Organisation TO Commercial
                )
            """)

        except Exception as e:
            # Tables might already exist
            print(f"Error initializing schema: {e}")

