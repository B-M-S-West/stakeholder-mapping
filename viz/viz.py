import dash
from dash import html, dcc
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
from graph.load_graph import DB_PATH
import kuzu

DB_PATH = "../govmap_db"
db = kuzu.Database(DB_PATH)
conn = kuzu.Connection(db)

def build_graph():
    nodes, edges, org_edges = [], [], []

    # Organisations
    orgs = conn.execute("""
        MATCH (o:Organisation)
        RETURN o.org_id, o.org_name, o.org_type, o.org_function
    """).get_as_python()
    for oid, name, otype, ofunc in orgs:
        nodes.append({
            "data": {
                "id": f"org{oid}",
                "label": name,
                "role": "org",
                "otype": otype,
                "function": ofunc
            }
        })

    