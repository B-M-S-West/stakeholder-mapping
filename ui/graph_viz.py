import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
from database.kuzu_manager import KuzuManager
from database.sqlite_manager import SQLiteManager
import config
from utils import validators
from ui.graph_utils import get_base_html_from_network, inject_custom_js, get_delete_node_js


def render_graph_explorer(kuzu_mgr: KuzuManager, sqlite_mgr: SQLiteManager):
    """Render interactive graph visualization"""

    st.header("🕸️ Graph Explorer")

    # Sidebar filters
    with st.sidebar:
        st.subheader("Graph Filters")

        # Relationship type filter
        relationship_filters = st.multiselect(
            "Relationship Types",
            options=config.RELATIONSHIP_TYPES,
            default=config.RELATIONSHIP_TYPES,
        )

        # Node type filter
        st.write("**Show Node Types:**")
        show_orgs = st.checkbox("Organisations", value=True)
        show_stakeholders = st.checkbox("Stakeholders", value=True)
        show_painpoints = st.checkbox("Pain Points", value=True)
        show_commercials = st.checkbox("Commercial", value=True)

        # Organization type filter
        if show_orgs:
            org_type_filter = st.multiselect(
                "Organisation Types", options=config.ORG_TYPES, default=config.ORG_TYPES
            )
        else:
            org_type_filter = []

        # Layout options
        st.subheader("Layout Options")
        physics_enabled = st.checkbox("Enable Physics", value=True)

        layout_algorithm = st.selectbox(
            "Layout Algorithm", ["barnes_hut", "force_atlas_2based", "hierarchical"]
        )

        # Refresh button
        if st.button("🔄 Refresh Graph", width='stretch'):
            st.rerun()

        # -- Neighbourhood explorer --
        st.markdown("---")
        st.subheader("Explore by Organisation")
        # get org list from SQLite (searchable selectbox)
        try:
            orgs_df = sqlite_mgr.get_all_organisations()
            org_names = orgs_df['org_name'].tolist()
        except Exception:
            org_names = []

        selected_org = st.selectbox("Start Organisation (searchable)", options=org_names)
        depth = st.selectbox("Depth (org hops)", options=[0, 1, 2, 3, 4], index=1)

        if st.button("🔎 Explore Neighbourhood", key="explore_neighborhood"):
            if selected_org:
                # Map name -> id via sqlite
                org_row = orgs_df[orgs_df['org_name'] == selected_org]
                if not org_row.empty:
                    org_id = int(org_row.iloc[0]['org_id'])
                    st.session_state['neighborhood_query'] = {'org_id': org_id, 'depth': int(depth)}
                    # rerun so main area will pick up session state and render the neighbourhood
                    st.rerun()
                else:
                    st.error("Selected organisation not found in local DB.")

        if st.button("❌ Clear neighbourhood view", key="clear_neighborhood"):
            st.session_state.pop('neighborhood_query', None)
            st.rerun()

    # If user requested a neighbourhood query (via sidebar) use that dataset;
    # otherwise fall back to global graph data.
    try:
        if st.session_state.get('neighborhood_query'):
            q = st.session_state['neighborhood_query']
            graph_data = kuzu_mgr.get_organisation_neighborhood(q['org_id'], q['depth'])
        else:
            graph_data = kuzu_mgr.get_graph_data(relationship_filters)

        nodes = graph_data["nodes"]
        edges = graph_data["edges"]

        # Filter nodes based on user selection
        filtered_nodes = []
        filtered_node_ids = set()

        for node in nodes:
            include = False
            # Normalize type/org_type for robust comparisons
            ntype = validators.normalize_node_type(node.get("type"))
            org_type = validators.normalize_org_type(node.get("org_type"))

            if ntype == "organisation" and show_orgs:
                if org_type in [validators.normalize_org_type(x) for x in org_type_filter]:
                    include = True
            elif ntype == "stakeholder" and show_stakeholders:
                include = True
            elif ntype == "painpoint" and show_painpoints:
                include = True
            elif ntype == "commercial" and show_commercials:
                include = True

            if include:
                filtered_nodes.append(node)
                filtered_node_ids.add(node["id"])

        # Filter edges to only include those between visible nodes
        filtered_edges = [
            edge
            for edge in edges
            if edge["from"] in filtered_node_ids and edge["to"] in filtered_node_ids
        ]

        # Display statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Nodes", len(filtered_nodes))
        with col2:
            st.metric("Edges", len(filtered_edges))
        with col3:
            org_count = sum(1 for n in filtered_nodes if validators.normalize_node_type(n.get("type")) == "organisation")
            st.metric("Organisations", org_count)
        with col4:
            stakeholder_count = sum(
                1 for n in filtered_nodes if validators.normalize_node_type(n.get("type")) == "stakeholder"
            )
            st.metric("Stakeholders", stakeholder_count)

        # Create PyVis network
        net = Network(
            height="700px",
            width="100%",
            bgcolor="#222222",
            font_color="white",
            notebook=False,
        )

        # Configure physics
        if physics_enabled:
            if layout_algorithm == "force_atlas_2based":
                net.barnes_hut()
            elif layout_algorithm == "barnes_hut":
                net.force_atlas_2based()
            elif layout_algorithm == "hierarchical":
                net.show_buttons(filter_=["physics"])
        else:
            net.toggle_physics(False)

        # Add nodes
        for node in filtered_nodes:
            # Determine color based on type
            ntype = validators.normalize_node_type(node.get("type"))
            org_type = validators.normalize_org_type(node.get("org_type"))

            if ntype == "organisation":
                if org_type == "department":
                    color = "#2980b9"  # Blue
                elif org_type == "agency":
                    color = "#16a085"  # Teal
                elif org_type == "ndpb":
                    color = "#d35400"  # Orange
                else:
                    color = "#7f8c8d"  # Gray
                size = 30
                shape = "dot"
            elif ntype == "stakeholder":
                color = "#27ae60"  # Green
                size = 20
                shape = "dot"
            elif ntype == "painpoint":
                color = "#c0392b"  # Red
                size = 15
                shape = "triangle"
            elif ntype == "commercial":
                color = "#f39c12"  # Orange
                size = 15
                shape = "square"
            else:
                color = "#95a5a6"
                size = 15
                shape = "dot"

            # Create hover title with details (no HTML; use \n for new lines)
            lines = [f"{node['label']}"]  # No <b> or </b>
            if ntype == "organisation":
                lines.append(f"Type: {org_type}")
                lines.append(f"Function: {node.get('function', 'N/A')}")
            elif ntype == "stakeholder":
                lines.append(f"Job Title: {node.get('job_title', 'N/A')}")
                lines.append(f"Role: {node.get('role', 'N/A')}")
            elif ntype == "painpoint":
                lines.append(f"Severity: {node.get('severity', 'N/A')}")
                lines.append(f"Urgency: {node.get('urgency', 'N/A')}")
            elif ntype == "commercial":
                lines.append(f"Method: {node.get('method', 'N/A')}")
                lines.append(f"Budget: £{node.get('budget', 0) / 1e6:.2f}m")

            title = "\n".join(lines)

            net.add_node(
                node["id"],
                label=node["label"],
                title=title,
                color=color,
                size=size,
                shape=shape,
            )

        # Add edges
        for edge in filtered_edges:
            # Determine edge color based on type
            etype = validators.normalize_node_type(edge.get("type"))
            elabel = validators.normalize_relationship_type(edge.get("label"))

            if etype == "org_relation":
                if elabel == "mission":
                    color = "#9b59b6"  # Purple
                elif elabel == "supplier":
                    color = "#27ae60"  # Green
                elif elabel == "consumer":
                    color = "#f39c12"  # Orange
                elif elabel == "oversight":
                    color = "#e74c3c"  # Red
                else:
                    color = "#bdc3c7"  # Gray
                width = 2
            else:
                color = "#7f8c8d"  # Gray for other relationships
                width = 1

            net.add_edge(
                edge["from"],
                edge["to"],
                title=edge["label"],
                color=color,
                width=width,
                arrows="to",
            )

        # Generate HTML in memory
        html_content = get_base_html_from_network(net)

        # Inject delete functionality
        delete_js = get_delete_node_js()
        html_content = inject_custom_js(html_content, delete_js)

        # Display in Streamlit
        components.html(html_content, height=750)

        # Legend
        with st.expander("📖 Legend", expanded=False):
            st.write("### Node Types")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("🔵 **Department** - Blue circle")
                st.markdown("🟢 **Agency** - Teal circle")
                st.markdown("🟠 **NDPB** - Orange circle")
                st.markdown("🟢 **Stakeholder** - Green circle")

            with col2:
                st.markdown("🔺 **Pain Point** - Red triangle")
                st.markdown("🟨 **Commercial** - Orange square")

            st.write("### Relationship Types")
            st.markdown("🟣 **Mission** - Purple arrow")
            st.markdown("🟢 **Supplier** - Green arrow")
            st.markdown("🟠 **Consumer** - Orange arrow")
            st.markdown("🔴 **Oversight** - Red arrow")

        # Node details panel
        st.subheader("📊 Organisation Details")

        # Filter for organisations only
        org_nodes = [
            node for node in nodes if validators.normalize_node_type(node.get("type")) == "organisation"
        ]

        # Create a searchable dropdown of all nodes
        node_options = {
            f"{node['label']} ({validators.normalize_org_type(node.get('org_type', 'N/A'))})": node for node in org_nodes
        }
        
        selected_node_label = st.selectbox(
            "Select an Organisation to view details", options=list(node_options.keys())
        )

        if selected_node_label:
            selected_node = node_options[selected_node_label]

            col1, col2 = st.columns(2)

            with col1:
                sel_type = validators.normalize_node_type(selected_node.get('type'))
                sel_org_type = validators.normalize_org_type(selected_node.get('org_type'))
                st.write(f"**Type:** {sel_type.title()}")
                st.write(f"**Label:** {selected_node['label']}")

                if sel_type == "organisation":
                    st.write(f"**Org Type:** {sel_org_type}")
                    st.write(f"**Function:** {selected_node.get('function', 'N/A')}")
                elif sel_type == "stakeholder":
                    st.write(f"**Job Title:** {selected_node.get('job_title', 'N/A')}")
                    st.write(f"**Role:** {selected_node.get('role', 'N/A')}")
                elif sel_type == "painpoint":
                    st.write(f"**Severity:** {selected_node.get('severity', 'N/A')}")
                    st.write(f"**Urgency:** {selected_node.get('urgency', 'N/A')}")
                elif sel_type == "commercial":
                    st.write(f"**Method:** {selected_node.get('method', 'N/A')}")
                    st.write(
                        f"**Budget:** £{(selected_node.get('budget', 0) or 0) / 1e6:.2f}m"
                    )

            with col2:
                # Find connected nodes
                connected_edges = [
                    e
                    for e in edges
                    if e["from"] == selected_node["id"]
                    or e["to"] == selected_node["id"]
                ]
                st.write(f"**Connections:** {len(connected_edges)}")

                # Map nodes by id for quick lookup
                nodes_by_id = {n["id"]: n for n in nodes}

                # Collect connected node ids and categorize
                connected_node_ids = set()
                for e in connected_edges:
                    connected_node_ids.add(e["from"])
                    connected_node_ids.add(e["to"])
                # Remove the selected node itself
                connected_node_ids.discard(selected_node["id"])

                # Build lists
                connected_nodes = [nodes_by_id[nid] for nid in connected_node_ids if nid in nodes_by_id]
                stakeholder_nodes = [n for n in connected_nodes if validators.normalize_node_type(n.get("type")) == "stakeholder"]
                painpoint_nodes = [n for n in connected_nodes if validators.normalize_node_type(n.get("type")) == "painpoint"]

                # Quick summary + truncated list (as before)
                if connected_edges:
                    st.write("**Connected to (sample):**")
                    shown = 0
                    for edge in connected_edges:
                        if shown >= 5:
                            break
                        if edge["from"] == selected_node["id"]:
                            target_node = nodes_by_id.get(edge["to"])
                            if target_node:
                                st.write(f"→ {target_node['label']} ({edge['label']})")
                                shown += 1
                        else:
                            source_node = nodes_by_id.get(edge["from"])
                            if source_node:
                                st.write(f"← {source_node['label']} ({edge['label']})")
                                shown += 1

                    if len(connected_edges) > 5:
                        st.write(f"... and {len(connected_edges) - 5} more")

            # Collapsible detailed lists so UI stays compact
            with st.expander(f"👥 Connected Stakeholders ({len(stakeholder_nodes)})", expanded=False):
                if stakeholder_nodes:
                    # Prepare display rows
                    rows = []
                    for n in stakeholder_nodes:
                        rows.append({
                            "Name": n.get("label"),
                            "Job Title": n.get("job_title", "N/A"),
                            "Role": n.get("role", "N/A"),
                        })
                    st.table(rows)

            with st.expander(f"⚠️ Connected Pain Points ({len(painpoint_nodes)})", expanded=False):
                if painpoint_nodes:
                    rows = []
                    for n in painpoint_nodes:
                        desc = n.get("label") or ""
                        rows.append({
                            "Description": desc,
                            "Severity": n.get("severity", "N/A"),
                            "Urgency": n.get("urgency", "N/A"),
                        })
                    st.table(rows)

    except Exception as e:
        st.error(f"Error loading graph: {e}")
        st.write("Please ensure the graph database is synced with the latest data.")
