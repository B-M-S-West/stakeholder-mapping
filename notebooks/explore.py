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
    return kuzu, mo


@app.cell
def _(kuzu, mo):
    DB_PATH = "../govmap_db"
    db = kuzu.Database(DB_PATH)
    conn = kuzu.Connection(db)

    mo.md("## Government Organisation Knowledge Graph Explorer")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
