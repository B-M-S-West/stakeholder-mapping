import marimo

__generated_with = "0.15.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import kuzu
    import polars as pl
    import networkx as nx
    import plotly.graph_objects as go
    from pathlib import Path
    from dash import Dash, html, dcc, Output, Input
    import dash_cytoscape as cyto
    return Path, go, kuzu, mo, nx, pl


@app.cell
def _(Path, kuzu, mo):
    REPO_ROOT = Path(__file__).resolve().parent.parent  # repo root
    DB_PATH = REPO_ROOT / "govmap_db"
    print("Using DB at:", DB_PATH)
    db = kuzu.Database(DB_PATH)
    conn = kuzu.Connection(db)

    mo.md("## Government Organisation Knowledge Graph Explorer")
    return (conn,)


@app.cell
def _(mo):
    # Drop down filter to select what relationships should be shown
    rel_filter = mo.ui.multiselect(
        options=["oversight", "supplier", "consumer", "mission"], 
        value=["oversight", "supplier", "consumer", "mission"], # This is the default selection
        label="Filter relationships by type"
    )
    return (rel_filter,)


@app.cell
def _(conn, pl, rel_filter):
    # This query will run based upon the filters selected
    def get_filtered_edges(selected):
        placeholder = ",".join([f'"{t}"' for t in selected])
        query = f"""
        MATCH (a:Organisation)-[r:OrgRelation]->(b:Organisation)
        WHERE r.relationship_type IN [{placeholder}]
        RETURN a.org_id, a.org_name, b.org_id, b.org_name, r.relationship_type
        """
        result = conn.execute(query).get_as_pl()
        return pl.DataFrame(result, schema=["from_id", "from_name", "to_id", "to_name", "rel_type"])

    edges_df = get_filtered_edges(rel_filter.value)
    return (edges_df,)


@app.cell
def _(edges_df):
    print(edges_df)
    return


@app.cell
def _(edges_df, go, nx, pl):
    def plot_graph(df: pl.DataFrame):
        if df.is_empty():
            return go.Figure().update_layout(title="No relationships found")

        # Convert polars -> networkx edge list
        G = nx.from_pandas_edgelist(
            df.to_pandas(), 
            source="from_id", 
            target="to_id", 
            edge_attr="rel_type", 
            create_using=nx.DiGraph()
        )

        pos = nx.spring_layout(G, seed=42)

        rel_colors = {
            "oversight": "blue",
            "supplier": "green", 
            "consumer": "orange", 
            "mission": "red"
        }

        # Edges
        edge_x, edge_y, edge_color = [], [], []
        for u, v, d in G.edges(data=True):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
            edge_color.append(rel_colors.get(d["rel_type"], "grey"))

        fig = go.Figure()

        # Nodes
        fig.add_trace(go.Scatter(
            x=[pos[n][0] for n in G.nodes()],
            y=[pos[n][0] for n in G.nodes()],
            text=[G.nodes[n].get("org_name", n) for n in G.nodes()],
            mode="markers+text",
            marker=dict(size=12, color="lightgrey"),
            name="Organisations"
        ))

        # Edges
        fig.add_trace(go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=2, color="grey"),
            marker=dict(color=edge_color),
            name="Relationships"
        ))

        fig.update_layout(
            title="Knowledge Graph View", 
            showlegend=False, 
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    graph_plot = plot_graph(edges_df)
    return (graph_plot,)


@app.cell
def _(edges_df, graph_plot, mo, rel_filter):
    mo.vstack([
        mo.md("### Relationship Filter"), 
        rel_filter,
        mo.md("### Graph Visualisation"),
        graph_plot,
        mo.md("### Raw Edge Data"),
        mo.ui.table(edges_df.to_pandas())  # marimo ui.table currently expects pandas
    ])
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
