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

        # Org-to-Org Relationships
        org_rels = conn.execute("""
            MATCH (a:Organisation)-[r:OrgRelation]->(b:Organisation)
            RETURN a.org_id, b.org_id, r.realtionship_type
        """).get_as_python()
        for a, b, rtype in org_rels:
            org_edges.append({
                "data": {
                    "source": f"org{a}",
                    "target": f"org{b}",
                    "label": rtype,

                }
            })

        # Stakeholders
        stakeholders = conn.execute("""
            MATCH (o:Organisation)-[:HasStakeholder]->(s:Stakeholder)
            RETURN s.stakeholder_id, o.org_id, s.name, s.job_title, s.role
        """).get_as_python()
        for sid, oid, name, title, role in stakeholders:
            nodes.append({
                "data": {
                    "id": f"st{sid}",
                    "label": name,
                    "role": "stakeholder",
                    "job_title": title,
                    "role_desc": role
                }
            })
            edges.append({
                "data": {
                    "source": f"org{oid}",
                    "target": f"st{sid}",
                    "label": "stakeholder"
                }
            })

        # Pain Points
        pain_points = conn.execute("""
            MATCH (o:Organisation)-[:HasPainPoint]->(p:PainPoint)
            RETURN p.painpoint_id, o.org_id, p.description, p.severity, p.urgency
        """).get_as_python()
        for pid, oid, desc, sev, urg in pain_points:
            nodes.append({
                "data": {
                    "id": f"pp{pid}",
                    "label": desc,
                    "role": "painpoint",
                    "severity": sev,
                    "urgency": urg
                }
            })
            edges.append({
                "data": {
                    "source": f"org{oid}",
                    "target": f"pp{pid}",
                    "label": "painpoint"
                }
            })

        # Commercials
        commercials 