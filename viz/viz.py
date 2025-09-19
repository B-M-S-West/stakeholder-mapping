import dash
from dash import html, dcc
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
from graph.load_graph import DB_PATH
import kuzu

DB_PATH = "../govmap_db"
db = kuzu.Database(DB_PATH)
conn = kuzu.Connection(db)

