"""
This script loads cleaned CSV data from data/processed/into
a Kuzu knowledge graph.
Steps:
1. Connect or create the Kuzu database (govmap_db/ directory).
2. Read and execute the schema (graph/schema.cql) - defines ontology.
3. COPY cleaned CSVs into the defined node and relationship tables.
"""

import kuzu
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data/processed"
GRAPH = PROJECT_ROOT / "graph"
DB_PATH = PROJECT_ROOT / "govmap_db"

db = kuzu.Database(str(DB_PATH)) # Creates folder if not there
conn = kuzu.Connection(db)

schema_file = GRAPH / "schema.cql"
with open(schema_file, 'r') as f:
    lines = f.readlines()

# Join only non-comment lines
filtered_lines = [line for line in lines if not line.strip().startswith("--")]
schema_sql = "".join(filtered_lines)

for stmt in schema_sql.split(";"):
    if stmt.strip():
        print(f"Executing schema statement:\n{stmt.strip()[:80]}...")
        conn.execute(stmt)

print("✅ Schema created")

copy_commands = {
    "Organisation": "Organisation_clean.csv",
    "Stakeholder": "Stakeholder_clean.csv",
    "PainPoint": "PainPoint_clean.csv",
    "Commercial": "Commercial_clean.csv",
    "OrgRelation": "OrgRelationships_clean.csv"
}

for table, filename in copy_commands.items():
    file_path = DATA / filename
    if not file_path.exists():
        print(f"⚠️ Skipping {table}: {filename} not found.")
        continue

    sql = f"""
    COPY {table}
    FROM '{file_path}'
    (HEADER=true);
    """
    print(f"Loading {filename} into {table}...")
    conn.execute(sql)
    print(f"✅ Loaded {filename}")

print("🎉 Data loading complete. Database ready to query!")