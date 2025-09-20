import dash
from dash import html, dcc
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
import kuzu
from pathlib import Path
import polars as pl

REPO_ROOT = Path(__file__).resolve().parent.parent  # repo root
DB_PATH = REPO_ROOT / "govmap_db"
print("Using DB at:", DB_PATH)
db = kuzu.Database(DB_PATH, read_only=True)
conn = kuzu.Connection(db)

def build_graph():
    nodes, edges, org_edges = [], [], []

    # Organisations
    orgs = list(conn.execute("""
        MATCH (o:Organisation)
        RETURN o.org_id, o.org_name, o.org_type, o.org_function
    """))
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
    org_rels = list(conn.execute("""
        MATCH (a:Organisation)-[r:OrgRelation]->(b:Organisation)
        RETURN a.org_id, b.org_id, r.relationship_type
    """))
    for a, b, rtype in org_rels:
        org_edges.append({
            "data": {
                "source": f"org{a}",
                "target": f"org{b}",
                "label": rtype,

            }
        })

    # Stakeholders
    stakeholders = list(conn.execute("""
        MATCH (o:Organisation)-[:HasStakeholder]->(s:Stakeholder)
        RETURN s.stakeholder_id, o.org_id, s.name, s.job_title, s.role
    """))
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
    pain_points = list(conn.execute("""
        MATCH (o:Organisation)-[:HasPainPoint]->(p:PainPoint)
        RETURN p.painpoint_id, o.org_id, p.description, p.severity, p.urgency
    """))
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
    commercials = list(conn.execute("""
        MATCH (o:Organisation)-[:ProcuresThrough]->(c:Commercial)
        RETURN c.commercial_id, o.org_id, c.method, c.budget
    """))
    for cid, oid, method, budget in commercials:
        nodes.append({
            "data": {
                "id": f"com{cid}",
                "label": f"{method} (£{budget/1e6:.1f}m)",
                "role": "commercial",
                "budget": budget
            }
        })
        edges.append({
            "data": {
                "source": f"org{oid}",
                "target": f"com{cid}",
                "label": "commercial"
            }
        })

    return nodes, edges, org_edges
    
# Initial load
all_nodes, all_edges, all_org_edges = build_graph()

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H3("Kùzu-backed Knowledge Graph Explorer"),

    # Dropdown filter for Org-to-Org rels
    dcc.Dropdown(
        id="relationship-filter",
        options=[
            {"label": "Mission", "value": "mission"},
            {"label": "Supplier", "value": "supplier"},
            {"label": "Consumer", "value": "consumer"},
            {"label": "Oversight", "value": "oversight"},
        ],
        value=["mission", "supplier", "consumer", "oversight"],
        multi=True
    ),
    # Legend
html.Div([
    html.H4("Legend"),
    html.Div([
        html.Span(style={"backgroundColor": "#2980b9", "display": "inline-block",
                         "width": "20px", "height": "20px", "marginRight": "8px"}),
        "Department"
    ]),
    html.Div([
        html.Span(style={"backgroundColor": "#16a085", "display": "inline-block",
                         "width": "20px", "height": "20px", "marginRight": "8px"}),
        "Agency"
    ]),
    html.Div([
        html.Span(style={"backgroundColor": "#d35400", "display": "inline-block",
                         "width": "20px", "height": "20px", "marginRight": "8px"}),
        "NDPB"
    ]),
    html.Br(),
    html.Div([
        html.Span("━━", style={"color": "#9b59b6", "marginRight": "8px"}),
        "Mission relationship"
    ]),
    html.Div([
        html.Span("━━", style={"color": "#27ae60", "marginRight": "8px"}),
        "Supplier relationship"
    ]),
    html.Div([
        html.Span("━━", style={"color": "#f39c12", "marginRight": "8px"}),
        "Consumer relationship"
    ]),
    html.Div([
        html.Span("━━", style={"color": "#e74c3c", "marginRight": "8px"}),
        "Oversight relationship"
    ]),
], style={"marginBottom": "20px", "fontSize": "14px"}),

    cyto.Cytoscape(
        id="graph",
        layout={"name": "cose"},
        style={"width": "100%", "height": "700px"},
        elements=all_nodes + all_edges + all_org_edges,
        stylesheet=[
            # Node styles
            {
                "selector": "node[role = 'org']", 
                "style": {
                    "background-color": "#2980b9", 
                    "label": "data(label)", 
                    "color": "black", 
                    "font-size": 14
                    }
                },
                # Organization type colors
                {
                    "selector": "node[role = 'org'][otype = 'department']",
                    "style": {"background-color": "#2980b9"}  # blue
                },
                {
                    "selector": "node[role = 'org'][otype = 'agency']",
                    "style": {"background-color": "#16a085"}  # teal
                },
                {
                    "selector": "node[role = 'org'][otype = 'ndpb']",
                    "style": {"background-color": "#d35400"}  # orange
                },
            {
                "selector": "node[role = 'stakeholder']", 
                "style": {
                    "background-color": "#27ae60", 
                    "label": "data(label)"
                }
            },
            {
                "selector": "node[role = 'painpoint']", 
                "style": {
                    "background-color": "#c0392b", 
                    "label": "data(label)"
                }
            },
            {
                "selector": "node[role = 'commercial']", 
                "style": {
                    "background-color": "#f39c12", 
                    "label": "data(label)"
                }
            },
            # Org-to-Org relationships by type
            # Default edge style
            {
                "selector": "edge", 
                "style": {
                    "curve-style": "bezier",
                    "target-arrow-shape": "triangle",
                    "arrow-scale": 1,
                    "width": 2,
                    "line-color": "#bdc3c7",
                    "target-arrow-color": "#bdc3c7"
                }
            },
            {
                "selector": "edge[label = 'mission']", 
                "style": {
                    "line-color": "#9b59b6", 
                    "target-arrow-color": "#9b59b6",
                    "width": 3
                }
            },
            {
                "selector": "edge[label = 'supplier']", 
                "style": {
                    "line-color": "#27ae60", 
                    "target-arrow-color": "#27ae60",
                    "width": 3
                }
            },
            {
                "selector": "edge[label = 'consumer']", 
                "style": {
                    "line-color": "#f39c12", 
                    "target-arrow-color": "#f39c12",
                    "width": 3
                }
            },
            {
                "selector": "edge[label = 'oversight']", 
                "style": {
                    "line-color": "#e74c3c", 
                    "target-arrow-color": "#e74c3c",
                    "width": 3
                }
            },
        ]
    )
])

@app.callback(
    Output("graph", "elements"),
    Input("relationship-filter", "value")
)
def update_graph(selected_rels):
    # Rebuild fresh each time (in case DB changed)
    nodes, edges, org_edges = build_graph()
    filtered_org_edges = [e for e in org_edges if e["data"]["label"] in selected_rels]
    return nodes + edges + filtered_org_edges

if __name__ == "__main__":
    app.run(debug=True)