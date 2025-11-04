from database.sqlite_manager import SQLiteManager
from database.kuzu_manager import KuzuManager
from loguru import logger
from typing import Dict, List, Optional

class SyncManager:
    """Manages synchronization between SQLite and Kuzu databases."""
    
    def __init__(self, sqlite_mgr: SQLiteManager, kuzu_mgr: KuzuManager):
        self.sqlite = sqlite_mgr
        self.kuzu = kuzu_mgr

    # ========== Sync Individual Records ==========

    def sync_organisation(self, org_id: int):
        """Sync a single organisation from SQLite to Kuzu."""
        org = self.sqlite.get_organisation_by_id(org_id)
        if org:
            self.kuzu.upsert_organisations(
                org['org_id'], 
                org['org_name'], 
                org['org_type'], 
                org['org_function']
            )

    def sync_stakeholder(self, stakeholder_id: int):
        """Sync a single stakeholder from SQLite to Kuzu."""
        df = self.sqlite.get_all_stakeholders()
        stakeholder = df[df['stakeholder_id'] == stakeholder_id]
        if not stakeholder.empty:
            row = stakeholder.iloc[0]
            self.kuzu.upsert_stakeholder(
                int(row['stakeholder_id']),
                int(row['org_id']),
                row['name'],
                row.get('job_title'),
                row.get('role'),
            )

    def sync_painpoint_node(self, painpoint_id: int):
        """Sync a single painpoint from SQLite to Kuzu."""
        df = self.sqlite.get_all_painpoints()
        painpoint = df[df['painpoint_id'] == painpoint_id]
        if not painpoint.empty:
            row = painpoint.iloc[0]
            self.kuzu.upsert_painpoint(
                int(row['painpoint_id']),
                row['description'],
                row.get('severity'),
                row.get('urgency'),
            )

    def sync_painpoint_assignments(self, painpoint_id: int, org_ids: Optional[List[int]] = None):
        """Sync organisation ↔ pain point links for a given pain point."""
        if org_ids is None:
            org_ids = self.sqlite.get_painpoint_assignments(painpoint_id)

        self.kuzu.clear_painpoint_assignments(painpoint_id)
        for org_id in org_ids:
            self.kuzu.sync_painpoint_assignment(int(org_id), int(painpoint_id))
        
    def sync_commercial(self, commercial_id: int):
        """Sync a single commercial from SQLite to Kuzu."""
        df = self.sqlite.get_all_commercials()
        commercial = df[df['commercial_id'] == commercial_id]
        if not commercial.empty:
            row = commercial.iloc[0]
            self.kuzu.upsert_commercial(
                int(row['commercial_id']),
                int(row['org_id']),
                row['method'],
                float(row['budget'])
            )

    def sync_relationship(self, from_org_id: int, to_org_id: int, relationship_type: str):
        """Sync a single relationship from SQLite to Kuzu."""
        self.kuzu.upsert_relationship(
            from_org_id, 
            to_org_id, 
            relationship_type
        )

    # ========== Sync All Records ==========

    def full_sync(self):
        """Perform a full sync of all data from SQLite to Kuzu."""
        logger.info("Starting full sync from SQLite to Kuzu.")
        
        # Sync Organisations
        logger.info("Syncing Organisations...")
        orgs = self.sqlite.get_all_organisations()
        for _, row in orgs.iterrows():
            self.kuzu.upsert_organisations(
                int(row['org_id']),
                row['org_name'],
                row['org_type'],
                row['org_function']
            )
        
        # Sync Stakeholders
        logger.info("Syncing Stakeholders...")
        stakeholders = self.sqlite.get_all_stakeholders()
        for _, row in stakeholders.iterrows():
            self.kuzu.upsert_stakeholder(
                int(row['stakeholder_id']),
                int(row['org_id']),
                row['name'],
                row.get('job_title'),
                row.get('role'),
            )
        
        # Sync Painpoints
        logger.info("Syncing Painpoints...")
        painpoints = self.sqlite.get_all_painpoints()
        for _, row in painpoints.iterrows():
            self.kuzu.upsert_painpoint(
                int(row['painpoint_id']),
                row['description'],
                row.get('severity'),
                row.get('urgency'),
            )
        
        # Sync Commercials
        logger.info("Syncing Commercials...")
        commercials = self.sqlite.get_all_commercials()
        for _, row in commercials.iterrows():
            self.kuzu.upsert_commercial(
                int(row['commercial_id']),
                int(row['org_id']),
                row['method'],
                float(row['budget'])
            )
        
        # Sync Relationships
        relationships = self.sqlite.get_all_org_relationships()
        logger.info("Syncing Relationships...")
        for _, row in relationships.iterrows():
            self.kuzu.upsert_relationship(
                int(row['from_org_id']),
                int(row['to_org_id']),
                row['relationship_type']
            )

        # Sync Painpoint Assignments
        logger.info("Syncing Painpoint Assignments...")
        assignments = self.sqlite.get_all_painpoint_assignments()
        if not assignments.empty:
            assignments_map: Dict[int, List[int]] = {}
            for _, row in assignments.iterrows():
                painpoint_id = int(row['painpoint_id'])
                org_id = int(row['org_id'])
                assignments_map.setdefault(painpoint_id, []).append(org_id)

            for painpoint_id, org_ids in assignments_map.items():
                self.sync_painpoint_assignments(painpoint_id, org_ids)

        logger.info("✅ Full sync completed.")

    # ========== Delete Sync Operations ==========

    def delete_organisation(self, org_id: int):
        """Delete an organisation and its related nodes from Kuzu."""
        self.kuzu.delete_organisation(org_id)

    def delete_stakeholder(self, stakeholder_id: int):
        """Delete a stakeholder and its related nodes from Kuzu."""
        self.kuzu.delete_stakeholder(stakeholder_id)

    def delete_painpoint(self, painpoint_id: int):
        """Delete a painpoint and its related nodes from Kuzu."""
        self.kuzu.delete_painpoint(painpoint_id)

    def delete_commercial(self, commercial_id: int):
        """Delete a commercial and its related nodes from Kuzu."""
        self.kuzu.delete_commercial(commercial_id)

    def delete_relationship(self, from_org_id: int, to_org_id: int, relationship_type: str):
        """Delete a relationship and its related nodes from Kuzu."""
        self.kuzu.delete_relationship(from_org_id, to_org_id, relationship_type)