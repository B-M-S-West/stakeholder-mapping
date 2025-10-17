import streamlit as st
from database.sqlite_manager import SQLiteManager
from database.sync_manager import SyncManager
import config

def render_crud_interface(sqlite_mgr: SQLiteManager, sync_mgr: SyncManager):
    """Render the CRUD interface using Streamlit."""

    st.header("📝 Data Management")

    # Entity selector
    entity_type = st.selectbox(
        "Select Entity Type",
        ["Organisations", "Stakeholders", "Pain Points", "Commercial", "Relationships"]
    )

    if entity_type == "Organisations":
        render_organisation_crud(sqlite_mgr, sync_mgr)
    elif entity_type == "Stakeholders":
        render_stakeholder_crud(sqlite_mgr, sync_mgr)
    elif entity_type == "Pain Points":
        render_painpoint_crud(sqlite_mgr, sync_mgr)
    elif entity_type == "Commercial":
        render_commercial_crud(sqlite_mgr, sync_mgr)
    elif entity_type == "Relationships":
        render_relationship_crud(sqlite_mgr, sync_mgr)

# ========= Organisation CRUD =========

def render_organisation_crud(sqlite_mgr: SQLiteManager, sync_mgr: SyncManager):
    """Render CRUD interface for Organisations."""

    st.subheader("🏢 Organisations")
    
    # Action tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View All", "➕ Add New", "✏️ Edit", "🗑️ Delete"])

    # View all
    with tab1:
        orgs_df = sqlite_mgr.get_all_organisations()

        if orgs_df.empty:
            st.info("No organisations found. Please add some.")
        else:
            st.write(f"**Total Organisations: {len(orgs_df)}**")

            # Filters
            col1, col2 = st.columns(2)
            with col1:
                org_type_filter = st.multiselect(
                    "Filter by Type",
                    options=config.ORG_TYPES,
                    default=config.ORG_TYPES
                )

            with col2:
                search_term = st.text_input("Search by name", "")

            # Apply filters
            filtered_df = orgs_df[orgs_df['org_type'].isin(org_type_filter)]
            if search_term:
                filtered_df = filtered_df[
                    filtered_df['org_name'].str.contains(search_term, case=False, na=False)
                    ]
                
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    hide_index=True
                )

                # Export filtered data
                if not filtered_df.empty:
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Export Filtered Data",
                        data=csv,
                        file_name='filtered_organisations.csv',
                        mime='text/csv'
                    )

    # Add new
    with tab2:
        with st.form("add_organisation"):
            st.write("### Add New Organisation")

            # Auto-generate next ID
            next_id = sqlite_mgr.get_next_id("Organisation", "org_id")
            org_id = st.number_input(
                "Organisation ID",
                min_value=1,
                value=next_id,
                step=1,
                help="Unique identifier for the organisation."
            )

            org_name = st.text_input(
                "Organisation Name",
                placeholder="Enter organisation name",
                help="Name of the organisation."
            )
            org_type = st.selectbox(
                "Organisation Type",
                options=config.ORG_TYPES,
                index=0,
                help="Type of the organisation."
            )

            org_function = st.text_area(
                "Function",
                placeholder="Describe the organisation's function",
                help="Brief description of the organisation's function."
            )

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Add Organisation", type="primary", use_container_width=True)
            with col2:
                sync_to_kuzu = st.checkbox("Sync to graph", value=True)
            
            if submit:
                if not org_name:
                    st.error("Organisation name is required!")
                else:
                    success = sqlite_mgr.insert_organisation(
                        org_id, org_name, org_type, org_function
                    )
                    
                    if success:
                        st.success(f"✅ Added organisation: {org_name}")
                        
                        if sync_to_kuzu:
                            sync_mgr.sync_organisation(org_id)
                            st.success("✅ Synced to graph database")
                        
                        st.rerun()
                    else:
                        st.error("❌ Failed to add organisation (ID or name may already exist)")
                        
    # Edit existing
    with tab3:
        orgs_df = sqlite_mgr.get_all_organisations()

        if orgs_df.empty:
            st.info("No organisations found. Please add some.")
        else:
            # Select organisation to edit
            org_options = {f"{row['org_name']} (ID: {row['org_id']})": row['org_id'] for _, row in orgs_df.iterrows()}

            selected_org = st.selectbox("Select Organisation to Edit", options=list(org_options.keys()))

            if selected_org:
                org_id = org_options[selected_org]
                org_data = sqlite_mgr.get_organisation_by_id(org_id)

                with st.form("edit_organisation"):
                    st.write(f"### Edit Organisation: {org_data['org_name']}")

                    org_name = st.text_input("Organisation Name*", value=org_data['org_name'])
                    org_type = st.selectbox(
                        "Type*",
                        options=config.ORG_TYPES,
                        index=config.ORG_TYPES.index(org_data['org_type'])
                    )
                    org_function = st.text_area("Function", value=org_data['org_function'] or "")

                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("Update Organisation", type="primary", use_container_width=True)
                    with col2:
                        sync_to_kuzu = st.checkbox("Sync to graph", value=True)

                    if submit:
                        if not org_name:
                            st.error("Organisation name is required!")
                        else:
                            success =sqlite_mgr.update_organisation(
                                org_id, org_name, org_type, org_function
                            )

                            if success:
                                st.success(f"✅ Updated organisation: {org_name}")

                                if sync_to_kuzu:
                                    sync_mgr.sync_organisation(org_id)
                                    st.success("✅ Synced to graph database")

                                st.rerun()
                            else:
                                st.error("❌ Failed to update organisation (name may already exist)")

    # Delete
    with tab4:
        orgs_df = sqlite_mgr.get_all_organisations()

        if orgs_df.empty:
            st.info("No organisations found. Please add some.")
        else:
            st.warning("⚠️ Deleting an organisation will also remove all associated stakeholders, pain points, commercial entries, and relationships.")

            org_options = {f"{row['org_name']} (ID: {row['org_id']})": row['org_id'] for _, row in orgs_df.iterrows()}

            selected_org = st.selectbox("Select Organisation to Delete", options=list(org_options.keys()))

            if selected_org:
                org_id = org_options[selected_org]
                org_data = sqlite_mgr.get_organisation_by_id(org_id)

                st.write(f"**Name:** {org_data['org_name']}")
                st.write(f"**Type:** {org_data['org_type']}")
                st.write(f"**Function:** {org_data['org_function']}")

                col1, col2 = st.columns(2)
                with col1:
                    confirm = st.checkbox("I understand this action cannot be undone")

                with col2:
                    sync_to_kuzu = st.checkbox("Delete from graph", value=True)

                if st.button("🗑️ Delete Organisation", type="primary", disabled=not confirm):
                    success = sqlite_mgr.delete_organisation(org_id)

                    if success:
                        st.success(f"✅ Deleted organisation: {org_data['org_name']}")

                        if sync_to_kuzu:
                            sync_mgr.delete_organisation_from_graph(org_id)
                            st.success("✅ Deleted from graph database")

                        st.rerun()
                    else:
                        st.error("❌ Failed to delete organisation")

# ========= Stakeholder CRUD =========

def render_stakeholder_crud(sqlite_mgr: SQLiteManager, sync_mgr: SyncManager):
    """Render CRUD interface for Stakeholders."""

    st.subheader("👤 Stakeholders")
    
    # Action tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View All", "➕ Add New", "✏️ Edit", "🗑️ Delete"])

    # View all
    with tab1:
        stakeholders_df = sqlite_mgr.get_all_stakeholders()

        if stakeholders_df.empty:
            st.info("No stakeholders found. Add one using the 'Add New' tab.")
        else:
            st.write(f"**Total Stakeholders: {len(stakeholders_df)}**")

            # Filters
            orgs_df = sqlite_mgr.get_all_organisations()
            org_filter = st.multiselect(
                "Filter by Organisation",
                options=orgs_df['org_name'].tolist(),
                default=[]
            )

            search_term = st.text_input("Search by name", "")

            # Apply filters
            filtered_df = stakeholders_df.copy()
            if org_filter:
                filtered_df = filtered_df[filtered_df['org_name'].isin(org_filter)]
            if search_term:
                filtered_df = filtered_df[
                    filtered_df['name'].str.contains(search_term, case=False, na=False)
                ]

            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True
            )

    # Add new
    with tab2:
        orgs_df = sqlite_mgr.get_all_organisations()

        if orgs_df.empty:
            st.warning("⚠️ Please add at least one organisation first!")
        else:
            with st.form("add_stakeholder"):
                st.write("### Add New Stakeholder")

                next_id = sqlite_mgr.get_next_id("Stakeholder", "stakeholder_id")
                stakeholder_id = st.number_input(
                    "Stakeholder ID",
                    min_value=1,
                    value=next_id,
                    step=1,
                    help="Unique identifier for the stakeholder."
                )

                # Select organisation
                org_options = {f"{row['org_name']}": row['org_id'] for _, row in orgs_df.iterrows()}
                selected_org = st.selectbox("Select Organisation*", options=list(org_options.keys()))
                org_id = org_options[selected_org]

                name = st.text_input("Name*", placeholder="Enter stakeholder name")
                job_title = st.text_input("Job Title", placeholder="Enter job title")
                role = st.text_input("Role", placeholder="Enter role")

                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("Add Stakeholder", type="primary", use_container_width=True)
                with col2:
                    sync_to_kuzu = st.checkbox("Sync to graph", value=True)

                if submit:
                    if not name:
                        st.error("Stakeholder name is required!")
                    else:
                        success = sqlite_mgr.insert_stakeholder(
                            stakeholder_id, org_id, name, job_title, role
                        )

                        if success:
                            st.success(f"✅ Added stakeholder: {name}")

                            if sync_to_kuzu:
                                sync_mgr.sync_stakeholder(stakeholder_id)
                                st.success("✅ Synced to graph database")

                            st.rerun()
                        else:
                            st.error("❌ Failed to add stakeholder (ID may already exist)")

    # Edit existing
    with tab3:
        stakeholders_df = sqlite_mgr.get_all_stakeholders()
        orgs_df = sqlite_mgr.get_all_organisations()

        if stakeholders_df.empty:
            st.info("No stakeholders found. Add one using the 'Add New' tab.")
        else:
            stakeholder_options = {f"{row['name']} - {row['org_name']} (ID: {row['stakeholder_id']})": row['stakeholder_id'] for _, row in stakeholders_df.iterrows()}

            selected_stakeholder = st.selectbox("Select Stakeholder to Edit", options=list(stakeholder_options.keys()))

            if selected_stakeholder:
                stakeholder_id = stakeholder_options[selected_stakeholder]
                stakeholder_data = stakeholders_df[stakeholders_df['stakeholder_id'] == stakeholder_id].iloc[0]

                with st.form("edit_stakeholder"):
                    st.write(f'### Edit Stakeholder: {stakeholder_data["name"]}')

                    # Select organisation
                    org_options = {f"{row['org_name']}": row['org_id'] for _, row in orgs_df.iterrows()}
                    current_org_name = stakeholder_data['org_name']
                    selected_org = st.selectbox("Select Organisation*", options=list(org_options.keys()), index=list(org_options.keys()).index(current_org_name) if current_org_name in org_options.keys() else 0)
                    org_id = org_options[selected_org]

                    name = st.text_input("Name*", value=stakeholder_data['name'])
                    job_title = st.text_input("Job Title", value=stakeholder_data['job_title'] or "")
                    role = st.text_input("Role", value=stakeholder_data['role'] or "")

                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("Update Stakeholder", type="primary", use_container_width=True)
                    with col2:
                        sync_to_kuzu = st.checkbox("Sync to graph", value=True)

                    if submit:
                        if not name:
                            st.error("Stakeholder name is required!")
                        else:
                            success = sqlite_mgr.update_stakeholder(
                                stakeholder_id, org_id, name, job_title, role
                            )

                            if success:
                                st.success(f"✅ Updated stakeholder: {name}")

                                if sync_to_kuzu:
                                    sync_mgr.sync_stakeholder(stakeholder_id)
                                    st.success("✅ Synced to graph database")

                                st.rerun()
                            else:
                                st.error("❌ Failed to update stakeholder")

    # Delete
    with tab4:
        stakeholders_df = sqlite_mgr.get_all_stakeholders()

        if stakeholders_df.empty:
            st.info("No stakeholders found. Add one using the 'Add New' tab.")
        else:
            stakeholder_options = {f"{row['name']} - {row['org_name']} (ID: {row['stakeholder_id']})": row['stakeholder_id'] for _, row in stakeholders_df.iterrows()}

            selected_stakeholder = st.selectbox("Select Stakeholder to Delete", options=list(stakeholder_options.keys()))

            if selected_stakeholder:
                stakeholder_id = stakeholder_options[selected_stakeholder]
                stakeholder_data = stakeholders_df[stakeholders_df['stakeholder_id'] == stakeholder_id].iloc[0]

                st.write(f"**Name:** {stakeholder_data['name']}")
                st.write(f"**Organisation:** {stakeholder_data['org_name']}")
                st.write(f"**Job Title:** {stakeholder_data['job_title']}")

                col1, col2 = st.columns(2)
                with col1:
                    confirm = st.checkbox("Confirm deletion (this action cannot be undone)")

                with col2:
                    sync_to_kuzu = st.checkbox("Delete from graph", value=True)

                if st.button("🗑️ Delete Stakeholder", type="primary", disabled=not confirm):
                    success = sqlite_mgr.delete_stakeholder(stakeholder_id)

                    if success:
                        st.success(f"✅ Deleted stakeholder: {stakeholder_data['name']}")

                        if sync_to_kuzu:
                            sync_mgr.delete_stakeholder_from_graph(stakeholder_id)
                            st.success("✅ Deleted from graph database")

                        st.rerun()
                    else:
                        st.error("❌ Failed to delete stakeholder")

# ========= Pain Point CRUD =========

def render_painpoint_crud(sqlite_mgr: SQLiteManager, sync_mgr: SyncManager):
    """Render CRUD interface for Pain Points."""

    st.subheader("⚠️ Pain Points")
    
    # Action tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View All", "➕ Add New", "✏️ Edit", "🗑️ Delete"])

    # View all
    with tab1:
        pain_points_df = sqlite_mgr.get_all_painpoints()

        if pain_points_df.empty:
            st.info("No pain points found. Add one using the 'Add New' tab.")
        else:
            st.write(f"**Total Pain Points: {len(pain_points_df)}**")

            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                severity_filter = st.multiselect(
                    "Filter by Severity",
                    options=config.SEVERITY_LEVELS,
                    default=config.SEVERITY_LEVELS
                )
            with col2:
                urgency_filter = st.multiselect(
                    "Filter by Urgency",
                    options=config.URGENCY_LEVELS,
                    default=config.URGENCY_LEVELS
                )
            with col3:
                orgs_df = sqlite_mgr.get_all_organisations()
                org_filter = st.multiselect(
                    "Filter by Organisation",
                    options=orgs_df['org_name'].tolist(),
                    default=[]
                )

            # Apply filters
            filtered_df = pain_points_df[pain_points_df['severity'].isin(severity_filter) & pain_points_df['urgency'].isin(urgency_filter)]
            if org_filter:
                filtered_df = filtered_df[filtered_df['org_name'].isin(org_filter)]

            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True
            )

    # Add new
    with tab2:
        orgs_df = sqlite_mgr.get_all_organisations()

        if orgs_df.empty:
            st.warning("⚠️ Please add at least one organisation first!")
        else:
            with st.form("add_painpoint"):
                st.write("### Add New Pain Point")

                next_id = sqlite_mgr.get_next_id("PainPoint", "painpoint_id")
                painpoint_id = st.number_input(
                    "Pain Point ID",
                    min_value=1,
                    value=next_id,
                    step=1,
                    help="Unique identifier for the pain point."
                )

                # Select organisation
                org_options = {f"{row['org_name']}": row['org_id'] for _, row in orgs_df.iterrows()}
                selected_org = st.selectbox("Select Organisation*", options=list(org_options.keys()))
                org_id = org_options[selected_org]

                description = st.text_area("Description*", placeholder="Describe the pain point")
                severity = st.selectbox("Severity*", options=config.SEVERITY_LEVELS, index=2)
                urgency = st.selectbox("Urgency*", options=config.URGENCY_LEVELS, index=2)

                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("Add Pain Point", type="primary", use_container_width=True)
                with col2:
                    sync_to_kuzu = st.checkbox("Sync to graph", value=True)

                if submit:
                    if not description:
                        st.error("Pain point description is required!")
                    else:
                        success = sqlite_mgr.insert_painpoint(
                            painpoint_id, org_id, description, severity, urgency
                        )

                        if success:
                            st.success(f"✅ Added pain point")

                            if sync_to_kuzu:
                                sync_mgr.sync_painpoint(painpoint_id)
                                st.success("✅ Synced to graph database")

                            st.rerun()
                        else:
                            st.error("❌ Failed to add pain point (ID may already exist)")

    # Edit existing
    with tab3:
        painpoints_df = sqlite_mgr.get_all_painpoints()
        orgs_df = sqlite_mgr.get_all_organisations()

        if painpoints_df.empty:
            st.info("No pain points found. Add one using the 'Add New' tab.")
        else:
            painpoint_options = {f"{row['description'][:50]}... - {row['org_name']} (ID: {row['painpoint_id']})": row['painpoint_id'] for _, row in painpoints_df.iterrows()}

            selected_painpoint = st.selectbox("Select Pain Point to Edit", options=list(painpoint_options.keys()))

            if selected_painpoint:
                painpoint_id = painpoint_options[selected_painpoint]
                painpoint_data = painpoints_df[painpoints_df['painpoint_id'] == painpoint_id].iloc[0]

                with st.form("edit_painpoint"):
                    st.write(f"### Edit Pain Point (ID: {painpoint_id})")

                    # Select organisation
                    org_options = {f"{row['org_name']}": row['org_id'] for _, row in orgs_df.iterrows()}
                    current_org_name = painpoint_data['org_name']
                    selected_org = st.selectbox("Select Organisation*", options=list(org_options.keys()), index=list(org_options.keys()).index(current_org_name) if current_org_name in org_options.keys() else 0)
                    org_id = org_options[selected_org]

                    description = st.text_area("Description*", value=painpoint_data['description'])

                    col1, col2 = st.columns(2)
                    with col1:
                        severity = st.selectbox("Severity*", options=config.SEVERITY_LEVELS, index=config.SEVERITY_LEVELS.index(painpoint_data['severity']))
                    with col2:
                        urgency = st.selectbox("Urgency*", options=config.URGENCY_LEVELS, index=config.URGENCY_LEVELS.index(painpoint_data['urgency']))

                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("Update Pain Point", type="primary", use_container_width=True)
                    with col2:
                        sync_to_kuzu = st.checkbox("Sync to graph", value=True)

                    if submit:
                        if not description:
                            st.error("Pain point description is required!")
                        else:
                            success = sqlite_mgr.update_painpoint(
                                painpoint_id, org_id, description, severity, urgency
                            )

                            if success:
                                st.success(f"✅ Updated pain point")

                                if sync_to_kuzu:
                                    sync_mgr.sync_painpoint(painpoint_id)
                                    st.success("✅ Synced to graph database")

                                st.rerun()
                            else:
                                st.error("❌ Failed to update pain point")

    # Delete
    with tab4:
        painpoints_df = sqlite_mgr.get_all_painpoints()

        if painpoints_df.empty:
            st.info("No pain points found. Add one using the 'Add New' tab.")
        else:
            painpoint_options = {f"{row['description'][:50]}... - {row['org_name']} (ID: {row['painpoint_id']})": row['painpoint_id'] for _, row in painpoints_df.iterrows()}

            selected_painpoint = st.selectbox("Select Pain Point to Delete", options=list(painpoint_options.keys()))

            if selected_painpoint:
                painpoint_id = painpoint_options[selected_painpoint]
                painpoint_data = painpoints_df[painpoints_df['painpoint_id'] == painpoint_id].iloc[0]

                st.write(f"**Description:** {painpoint_data['description']}")
                st.write(f"**Organisation:** {painpoint_data['org_name']}")
                st.write(f"**Severity:** {painpoint_data['severity']}")
                st.write(f"**Urgency:** {painpoint_data['urgency']}")

                col1, col2 = st.columns(2)
                with col1:
                    confirm = st.checkbox("Confirm deletion (this action cannot be undone)")

                with col2:
                    sync_to_kuzu = st.checkbox("Delete from graph", value=True)

                if st.button("🗑️ Delete Pain Point", type="primary", disabled=not confirm):
                    success = sqlite_mgr.delete_painpoint(painpoint_id)

                    if success:
                        st.success(f"✅ Deleted pain point")

                        if sync_to_kuzu:
                            sync_mgr.delete_painpoint(painpoint_id)
                            st.success("✅ Deleted from graph database")

                        st.rerun()
                    else:
                        st.error("❌ Failed to delete pain point")

# ========= Commercial CRUD =========

def render_commercial_crud(sqlite_mgr: SQLiteManager, sync_mgr: SyncManager):
    """Render CRUD interface for Commercial entries."""

    st.subheader("💼 Commercial Entries")
    
    # Action tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View All", "➕ Add New", "✏️ Edit", "🗑️ Delete"])

    # View all
    with tab1:
        commercial_df = sqlite_mgr.get_all_commercials()

        if commercial_df.empty:
            st.info("No commercial entries found. Add one using the 'Add New' tab.")
        else:
            st.write(f"**Total Commercial Entries: {len(commercial_df)}**")
            st.write(f"**Total Budget: ${commercial_df['budget'].sum():,.2f}**")

            # Filters
            col1, col2 = st.columns(2)
            with col1:
                method_filter = st.multiselect(
                    "Filter by method",
                    options=config.COMMERCIAL_METHODS,
                    default=config.COMMERCIAL_METHODS
                )
            with col2:
                orgs_df = sqlite_mgr.get_all_organisations()
                org_filter = st.multiselect(
                    "Filter by Organisation",
                    options=orgs_df['org_name'].tolist(),
                    default=[]
                )

            # Apply filters
            filtered_df = commercial_df[commercial_df['method'].isin(method_filter)]
            if org_filter:
                filtered_df = filtered_df[filtered_df['org_name'].isin(org_filter)]

            # Format budget for display
            display_df = filtered_df.copy()
            display_df['budget'] = display_df['budget'].apply(lambda x: f"£{x/1e6:.2f}m")

            st.dataFrame(
                display_df,
                use_container_width=True,
                hide_index=True
            )

    # Add new
    with tab2:
        orgs_df = sqlite_mgr.get_all_organisations()

        if orgs_df.empty:
            st.warning("⚠️ Please add at least one organisation first!")
        else:
            with st.form("add_commercial"):
                st.write("### Add New Commercial Entry")

                next_id = sqlite_mgr.get_next_id("Commercial", "commercial_id")
                commercial_id = st.number_input(
                    "Commercial ID",
                    min_value=1,
                    value=next_id,
                    step=1,
                    help="Unique identifier for the commercial entry."
                )

                # Select organisation
                org_options = {f"{row['org_name']}": row['org_id'] for _, row in orgs_df.iterrows()}
                selected_org = st.selectbox("Select Organisation*", options=list(org_options.keys()))
                org_id = org_options[selected_org]

                method = st.text_area("Method*", placeholder="Describe the commercial method")
                budget = st.number_input("Budget (£)*", min_value=0.0, format="%.2f", step=1000.0, help="Budget in GBP")

                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("Add Commercial Entry", type="primary", use_container_width=True)
                with col2:
                    sync_to_kuzu = st.checkbox("Sync to graph", value=True)

                if submit:
                    success = sqlite_mgr.insert_commercial(
                        commercial_id, org_id, method, budget
                    )

                    if success:
                        st.success(f"✅ Added commercial entry")

                        if sync_to_kuzu:
                            sync_mgr.sync_commercial(commercial_id)
                            st.success("✅ Synced to graph database")

                        st.rerun()
                    else:
                        st.error("❌ Failed to add commercial entry (ID may already exist)")

    # Edit existing
    with tab3:
        commercial_df = sqlite_mgr.get_all_commercials()
        orgs_df = sqlite_mgr.get_all_organisations()

        if commercial_df.empty:
            st.info("No commercial entries found. Add one using the 'Add New' tab.")
        else:
            commercial_options = {f"{row['method']} - {row['org_name']} - £{row['budget']/1e6:.2f}m (ID: {row['commercial_id']})": row['commercial_id'] for _, row in commercial_df.iterrows()}

            selected_commercial = st.selectbox("Select Commercial Entry to Edit", options=list(commercial_options.keys()))

            if selected_commercial:
                commercial_id = commercial_options[selected_commercial]
                commercial_data = commercial_df[commercial_df['commercial_id'] == commercial_id].iloc[0]

                with st.form("edit_commercial"):
                    st.write(f"### Edit Commercial Entry (ID: {commercial_id})")

                    # Select organisation
                    org_options = {f"{row['org_name']}": row['org_id'] for _, row in orgs_df.iterrows()}
                    current_org_name = commercial_data['org_name']
                    selected_org = st.selectbox("Select Organisation*", options=list(org_options.keys()), index=list(org_options.keys()).index(current_org_name) if current_org_name in org_options.keys() else 0)
                    org_id = org_options[selected_org]

                    method = st.selectbox("Method*", options=config.COMMERCIAL_METHODS, index=config.COMMERCIAL_METHODS.index(commercial_data['method']))
                    budget = st.number_input("Budget (£)*", min_value=0.0, value=float(commercial_data['budget']), format="%.2f", step=1000.0)

                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("Update Commercial Entry", type="primary", use_container_width=True)
                    with col2:
                        sync_to_kuzu = st.checkbox("Sync to graph", value=True)

                    if submit:
                        success = sqlite_mgr.update_commercial(
                            commercial_id, org_id, method, budget
                        )

                        if success:
                            st.success(f"✅ Updated commercial entry")

                            if sync_to_kuzu:
                                sync_mgr.sync_commercial(commercial_id)
                                st.success("✅ Synced to graph database")

                            st.rerun()
                        else:
                            st.error("❌ Failed to update commercial entry")

    # Delete
    with tab4:
        commercial_df = sqlite_mgr.get_all_commercials()

        if commercial_df.empty:
            st.info("No commercial entries found. Add one using the 'Add New' tab.")
        else:
            commercial_options = {f"{row['method']} - {row['org_name']} - £{row['budget']/1e6:.2f}m (ID: {row['commercial_id']})": row['commercial_id'] for _, row in commercial_df.iterrows()}

            selected_commercial = st.selectbox("Select Commercial Entry to Delete", options=list(commercial_options.keys()))

            if selected_commercial:
                commercial_id = commercial_options[selected_commercial]
                commercial_data = commercial_df[commercial_df['commercial_id'] == commercial_id].iloc[0]

                st.write(f"**Organisation:** {commercial_data['org_name']}")
                st.write(f"**Method:** {commercial_data['method']}")
                st.write(f"**Budget:** £{commercial_data['budget']/1e6:.2f}m")

                col1, col2 = st.columns(2)
                with col1:
                    confirm = st.checkbox("Confirm deletion (this action cannot be undone)")

                with col2:
                    sync_to_kuzu = st.checkbox("Delete from graph", value=True)

                if st.button("🗑️ Delete Commercial Entry", type="primary", disabled=not confirm):
                    success = sqlite_mgr.delete_commercial(commercial_id)

                    if success:
                        st.success(f"✅ Deleted commercial entry")

                        if sync_to_kuzu:
                            sync_mgr.delete_commercial_from_graph(commercial_id)
                            st.success("✅ Deleted from graph database")

                        st.rerun()
                    else:
                        st.error("❌ Failed to delete commercial entry")

# ============ RELATIONSHIP CRUD ============


def render_relationship_crud(sqlite_mgr: SQLiteManager, sync_mgr: SyncManager):
    """CRUD interface for organisation relationships"""

    st.subheader("🔗 Organisation Relationships")

    tab1, tab2, tab3 = st.tabs(["📋 View All", "➕ Add New", "🗑️ Delete"])

    # VIEW ALL
    with tab1:
        relationships_df = sqlite_mgr.get_all_org_relationships()

        if relationships_df.empty:
            st.info("No relationships found. Add one using the 'Add New' tab.")
        else:
            st.write(f"**Total Relationships:** {len(relationships_df)}")

            # Filters
            rel_type_filter = st.multiselect(
                "Filter by relationship type",
                options=config.RELATIONSHIP_TYPES,
                default=config.RELATIONSHIP_TYPES,
            )

            # Apply filters
            filtered_df = relationships_df[
                relationships_df["relationship_type"].isin(rel_type_filter)
            ]

            # Display
            display_df = filtered_df[
                ["from_org_name", "relationship_type", "to_org_name"]
            ].copy()
            display_df.columns = [
                "From Organisation",
                "Relationship Type",
                "To Organisation",
            ]

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Relationship statistics
            st.write("### Relationship Statistics")
            rel_counts = relationships_df["relationship_type"].value_counts()
            st.bar_chart(rel_counts)

    # ADD NEW
    with tab2:
        orgs_df = sqlite_mgr.get_all_organisations()

        if len(orgs_df) < 2:
            st.warning("⚠️ Please add at least two organisations first!")
        else:
            with st.form("add_relationship"):
                st.write("### Add New Relationship")

                org_names = orgs_df["org_name"].tolist()
                org_id_map = {
                    row["org_name"]: row["org_id"] for _, row in orgs_df.iterrows()
                }

                col1, col2 = st.columns(2)
                with col1:
                    from_org = st.selectbox(
                        "From Organisation*", options=org_names, key="from_org"
                    )
                with col2:
                    to_org = st.selectbox(
                        "To Organisation*", options=org_names, key="to_org"
                    )

                relationship_type = st.selectbox(
                    "Relationship Type*", config.RELATIONSHIP_TYPES
                )

                st.info(
                    f"This will create: **{from_org}** → [{relationship_type}] → **{to_org}**"
                )

                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button(
                        "Add Relationship", type="primary", use_container_width=True
                    )
                with col2:
                    sync_to_kuzu = st.checkbox("Sync to graph", value=True)

                if submit:
                    if from_org == to_org:
                        st.error(
                            "❌ Cannot create relationship from an organisation to itself!"
                        )
                    else:
                        from_org_id = org_id_map[from_org]
                        to_org_id = org_id_map[to_org]

                        success = sqlite_mgr.insert_relationship(
                            from_org_id, to_org_id, relationship_type
                        )

                        if success:
                            st.success(f"✅ Added relationship: {from_org} → {to_org}")

                            if sync_to_kuzu:
                                sync_mgr.sync_relationship(
                                    from_org_id, to_org_id, relationship_type
                                )
                                st.success("✅ Synced to graph database")

                            st.rerun()
                        else:
                            st.error(
                                "❌ Failed to add relationship (may already exist)"
                            )

    # DELETE
    with tab3:
        relationships_df = sqlite_mgr.get_all_org_relationships()

        if relationships_df.empty:
            st.info("No relationships to delete.")
        else:
            relationship_options = {
                f"{row['from_org_name']} → [{row['relationship_type']}] → {row['to_org_name']}": (
                    row["id"],
                    row["from_org_id"],
                    row["to_org_id"],
                    row["relationship_type"],
                )
                for _, row in relationships_df.iterrows()
            }

            selected_relationship = st.selectbox(
                "Select relationship to delete",
                options=list(relationship_options.keys()),
            )

            if selected_relationship:
                rel_id, from_org_id, to_org_id, rel_type = relationship_options[
                    selected_relationship
                ]

                st.write(f"**Relationship:** {selected_relationship}")

                col1, col2 = st.columns(2)
                with col1:
                    confirm = st.checkbox("Confirm deletion")
                with col2:
                    sync_to_kuzu = st.checkbox("Delete from graph", value=True)

                if st.button(
                    "🗑️ Delete Relationship", type="primary", disabled=not confirm
                ):
                    success = sqlite_mgr.delete_relationship(rel_id)

                    if success:
                        st.success(f"✅ Deleted relationship")

                        if sync_to_kuzu:
                            sync_mgr.delete_relationship_from_kuzu(
                                from_org_id, to_org_id, rel_type
                            )
                            st.success("✅ Deleted from graph database")

                        st.rerun()
                    else:
                        st.error("❌ Failed to delete relationship")