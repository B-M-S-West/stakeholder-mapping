from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"
RAW_DATA_DIR = DATA_DIR / "raw"
EXPORT_DIR = DATA_DIR / "exports"

# Database paths
SQLITE_DB = DATA_DIR / "govmap.db"
# Kuzu DB directory / file
KUZU_DB = DATA_DIR / "govmap.kuzu"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Table definitions
TABLES = {
    "Organisation": ["org_id", "org_name", "org_type", "org_function"],
    "Stakeholder": ["stakeholder_id", "org_id", "name", "job_title", "role"],
    "PainPoint": ["painpoint_id", "description", "severity", "urgency"],
    "Commercial": ["commercial_id", "org_id", "method", "budget"],
    "OrgRelationship": ["from_org_id", "to_org_id", "relationship_type"],
    "OrganisationPainPoint": ["org_id", "painpoint_id"],
}

# Organization types (canonical lowercase)
ORG_TYPES = ["department", "agency", "ndpb"]

# Relationship types
RELATIONSHIP_TYPES = ["oversight", "supplier", "consumer", "mission", "HAS_PAINPOINT"]

# Severity/Urgency levels
SEVERITY_LEVELS = ["Low", "Medium", "High"]
URGENCY_LEVELS = ["Low", "Medium", "High"]

# Commercial methods
COMMERCIAL_METHODS = ["Framework", "Direct Award", "Catalogue", "DPS"]