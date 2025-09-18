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
    return Path, kuzu, mo, pl


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
def _(conn):
    # Query all organisations + relationships
    nodes_query = """
        MATCH (o:Organisation) RETURN o.org_id, o.org_name
    """
    edges_query = """
        MATCH (a:Organisation)-[r:OrgRelation]->(b:Organisation)
        RETURN a.org_id, b.org_id, r.relationship_type
    """

    nodes = conn.execute(nodes_query).get_as_pl()
    edges = conn.execute(edges_query).get_as_pl()
    return edges, nodes


@app.cell
def _(edges, nodes):
    # Display inside Marimo cell
    print(nodes)
    print(edges)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
