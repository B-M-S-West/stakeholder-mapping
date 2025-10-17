import kuzu
from pathlib import Path
from typing import List, Dict, Any
import config
from utils import validators

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

            # PainPoint node table (was missing which caused binder errors when creating rels)
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS PainPoint (
                    painpoint_id INT64,
                    org_id INT64,
                    description STRING,
                    severity STRING,
                    urgency STRING,
                    PRIMARY KEY (painpoint_id)
                )
            """)

            # Relationships
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS OrgRelation (
                    FROM Organisation TO Organisation,
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

# ======= Sync Operations (called by sync_manager) =======

    def upsert_organisations(self, org_id: int, org_name: str, org_type: str, org_function: str):
        """Insert or update an organisation."""
        # Delete if exists
        self.conn.execute("""
            MATCH (o:Organisation {org_id: $org_id})
            DELETE o
        """, {'org_id': org_id})

        # Insert new
        self.conn.execute("""
            CREATE (o:Organisation {
                org_id: $org_id,
                org_name: $org_name,
                org_type: $org_type,
                org_function: $org_function
            })
        """, {
            'org_id': org_id,
            'org_name': org_name,
            'org_type': org_type,
            'org_function': org_function
        })

    def upsert_stakeholder(self, stakeholder_id: int, org_id: int, name: str, job_title: str, role: str):
        """Insert or update a stakeholder."""
        # Delete if exists
        self.conn.execute("""
            MATCH (s:Stakeholder {stakeholder_id: $stakeholder_id})
            DELETE s
        """, {'stakeholder_id': stakeholder_id})

        # Insert new
        self.conn.execute("""
            CREATE (s:Stakeholder {
                stakeholder_id: $stakeholder_id,
                org_id: $org_id,
                name: $name,
                job_title: $job_title,
                role: $role
            })
        """, {
            'stakeholder_id': stakeholder_id,
            'org_id': org_id,
            'name': name,
            'job_title': job_title,
            'role': role
        })

        # Create relationship
        self.conn.execute("""
            MATCH (o:Organisation {org_id: $org_id}), (s:Stakeholder {stakeholder_id: $stakeholder_id})
            MERGE (o)-[:HasStakeholder]->(s)
        """, {
            'org_id': org_id,
            'stakeholder_id': stakeholder_id
        })

    def upsert_painpoint(self, painpoint_id: int, org_id: int, description: str, severity: str, urgency: str):
        """Insert or update a pain point."""
        # Delete if exists
        self.conn.execute("""
            MATCH (p:PainPoint {painpoint_id: $painpoint_id})
            DELETE p
        """, {'painpoint_id': painpoint_id})

        # Insert new
        self.conn.execute("""
            CREATE (p:PainPoint {
                painpoint_id: $painpoint_id,
                org_id: $org_id,
                description: $description,
                severity: $severity,
                urgency: $urgency
            })
        """, {
            'painpoint_id': painpoint_id,
            'org_id': org_id,
            'description': description,
            'severity': severity,
            'urgency': urgency
        })

        # Create relationship
        self.conn.execute("""
            MATCH (o:Organisation {org_id: $org_id}), (p:PainPoint {painpoint_id: $painpoint_id})
            MERGE (o)-[:HasPainPoint]->(p)
        """, {
            'org_id': org_id,
            'painpoint_id': painpoint_id
        })

    def upsert_commercial(self, commercial_id: int, org_id: int, method: str, budget: float):
        """Insert or update a commercial."""
        # Delete if exists
        self.conn.execute("""
            MATCH (c:Commercial {commercial_id: $commercial_id})
            DELETE c
        """, {'commercial_id': commercial_id})

        # Insert new
        self.conn.execute("""
            CREATE (c:Commercial {
                commercial_id: $commercial_id,
                org_id: $org_id,
                method: $method,
                budget: $budget
            })
        """, {
            'commercial_id': commercial_id,
            'org_id': org_id,
            'method': method,
            'budget': budget
        })

        # Create relationship
        self.conn.execute("""
            MATCH (o:Organisation {org_id: $org_id}), (c:Commercial {commercial_id: $commercial_id})
            MERGE (o)-[:ProcuresThrough]->(c)
        """, {
            'org_id': org_id,
            'commercial_id': commercial_id
        })

    def upsert_relationship(self, from_org_id: int, to_org_id: int, relationship_type: str):
        """Insert or update an organisation relationship."""
        # Delete if exists
        self.conn.execute("""
            MATCH (a:Organisation {org_id: $from_org_id})-[r:OrgRelation {relationship_type: $relationship_type}]->(b:Organisation {org_id: $to_org_id})
            DELETE r
        """, {
            'from_org_id': from_org_id,
            'to_org_id': to_org_id,
            'relationship_type': relationship_type
        })

        # Create relationship
        self.conn.execute("""
            MATCH (a:Organisation {org_id: $from_org_id}), (b:Organisation {org_id: $to_org_id})
            CREATE (a)-[:OrgRelation {relationship_type: $relationship_type}]->(b)
        """, {
            'from_org_id': from_org_id,
            'to_org_id': to_org_id,
            'relationship_type': relationship_type
        })

    def delete_organisation(self, org_id: int):
        """Delete an organisation and its related nodes."""
        self.conn.execute("""
            MATCH (o:Organisation {org_id: $org_id})
            DETACH DELETE o
        """, {'org_id': org_id})

    def delete_stakeholder(self, stakeholder_id: int):
        """Delete a stakeholder."""
        self.conn.execute("""
            MATCH (s:Stakeholder {stakeholder_id: $stakeholder_id})
            DETACH DELETE s
        """, {'stakeholder_id': stakeholder_id})

    def delete_painpoint(self, painpoint_id: int):
        """Delete a pain point."""
        self.conn.execute("""
            MATCH (p:PainPoint {painpoint_id: $painpoint_id})
            DETACH DELETE p
        """, {'painpoint_id': painpoint_id})

    def delete_commercial(self, commercial_id: int):
        """Delete a commercial."""
        self.conn.execute("""
            MATCH (c:Commercial {commercial_id: $commercial_id})
            DETACH DELETE c
        """, {'commercial_id': commercial_id})

    def delete_relationship(self, from_org_id: int, to_org_id: int, relationship_type: str):
        """Delete specific organisation relationship."""
        self.conn.execute("""
            MATCH (a:Organisation {org_id: $from_org_id})-[r:OrgRelation {relationship_type: $relationship_type}]->(b:Organisation {org_id: $to_org_id})
            DELETE r
        """, {
            'from_org_id': from_org_id,
            'to_org_id': to_org_id,
            'relationship_type': relationship_type
        })

    # ======= Graph Query Operations (called by graph_manager) =======

    def get_graph_data(self, relationship_filters: List[str] = None) -> Dict[str, List]:
        """Get all graph data for visualization."""
        if relationship_filters is None:
            relationship_filters = config.RELATIONSHIP_TYPES

        # sanitize relationship filters against allowed set
        relationship_filters = validators.safe_rel_filter_list(relationship_filters, config.RELATIONSHIP_TYPES)
        if not relationship_filters:
            relationship_filters = [r.lower() for r in config.RELATIONSHIP_TYPES]

        nodes = []
        edges = []

        # Get organisations
        orgs = self.conn.execute("""
            MATCH (o:Organisation)
            RETURN o.org_id, o.org_name, o.org_type, o.org_function
        """).get_as_df()

        for _, row in orgs.iterrows():
            org_type = validators.normalize_org_type(row['o.org_type'])
            nodes.append({
                'id': f"org{row['o.org_id']}",
                'label': row['o.org_name'],
                'type': 'organisation',
                'org_type': org_type,
                'function': row['o.org_function']
            })

        # Get org relationships (filtered)
        rel_filter_str = ", ".join([f"'{r}'" for r in relationship_filters])
        org_rels = self.conn.execute(f"""
            MATCH (a:Organisation)-[r:OrgRelation]->(b:Organisation)
            WHERE r.relationship_type IN [{rel_filter_str}]
            RETURN a.org_id, b.org_id, r.relationship_type
        """).get_as_df()

        for _, row in org_rels.iterrows():
            edges.append({
                'from': f"org{row['a.org_id']}",
                'to': f"org{row['b.org_id']}",
                'label': validators.normalize_relationship_type(row['r.relationship_type']),
                'type': 'org_relation'
            })

        # Get stakeholders
        stakeholders = self.conn.execute("""
            MATCH (o:Organisation)-[:HasStakeholder]->(s:Stakeholder)
            RETURN s.stakeholder_id, o.org_id, s.name, s.job_title, s.role
        """).get_as_df()

        for _, row in stakeholders.iterrows():
            nodes.append({
                'id': f"st{row['s.stakeholder_id']}",
                'label': row['s.name'],
                'type': 'stakeholder',
                'job_title': row['s.job_title'],
                'role': row['s.role']
            })
            edges.append({
                'from': f"org{row['o.org_id']}",
                'to': f"st{row['s.stakeholder_id']}",
                'label': 'has_stakeholder',
                'type': 'has_stakeholder'
            })

        # Get pain points
        painpoints = self.conn.execute("""
            MATCH (o:Organisation)-[:HasPainPoint]->(p:PainPoint)
            RETURN p.painpoint_id, o.org_id, p.description, p.severity, p.urgency
        """).get_as_df()

        for _, row in painpoints.iterrows():
            nodes.append({
                'id': f"pp{row['p.painpoint_id']}",
                'label': row['p.description'][:50] + '...' if len(row['p.description']) > 50 else row['p.description'],
                'type': 'painpoint',
                'severity': row['p.severity'],
                'urgency': row['p.urgency']
            })
            edges.append({
                'from': f"org{row['o.org_id']}",
                'to': f"pp{row['p.painpoint_id']}",
                'label': 'has_painpoint',
                'type': 'has_painpoint'
            })
        
        # Get commercials
        commercials = self.conn.execute("""
            MATCH (o:Organisation)-[:ProcuresThrough]->(c:Commercial)
            RETURN c.commercial_id, o.org_id, c.method, c.budget
        """).get_as_df()

        for _, row in commercials.iterrows():
            method = row['c.method']
            budget = validators.parse_budget(row['c.budget'])
            nodes.append({
                'id': f"com{row['c.commercial_id']}",
                'label': f"{method} (£{(budget or 0)/1e6:.1f}m)",
                'type': 'commercial',
                'method': method,
                'budget': budget
            })
            edges.append({
                'from': f"org{row['o.org_id']}",
                'to': f"com{row['c.commercial_id']}",
                'label': 'procures_through',
                'type': 'procures_through'
            })

        return {'nodes': nodes, 'edges': edges}
    
    def get_organisation_neighborhood(self, org_id: int, depth: int = 1) -> Dict[str, List]:
        """Get neighbourhood of an organisation up to a certain depth."""
        # Get nodes and edges using variable length relationships
        query = f"""
            MATCH path = (o:Organisation {{org_id: $org_id}})-[*1..{depth}]-(connected)
            RETURN path
        """
        result = self.conn.execute(query, {'org_id': org_id})
        # Process and return nodes/edges from paths
        # Implementation depends on your needs
        pass

    def find_shortest_path(self, from_org_id: int, to_org_id: int) -> List[Dict]:
        """Find shortest path between two organisations."""
        query = """
            MATCH path = shortestPath((a:Organisation {org_id: $from_org_id})-[*]-(b:Organisation {org_id: $to_org_id}))
            RETURN path
        """
        result = self.conn.execute(query, {
            'from_org_id': from_org_id,
            'to_org_id': to_org_id
        })
        # Process and return path
        pass