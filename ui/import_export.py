from os import error, sync
import streamlit as st
import pandas as pd
from pathlib import Path
from loguru import logger
import config
from database.sqlite_manager import SQLiteManager
from database.sync_manager import SyncManager

def render_import_export(sqlite_mgr: SQLiteManager, sync_mgr: SyncManager):
    """Render CSV import/export interface"""
    
    st.header("📁 Import/Export Data")

    tab1, tab2 = st.tabs(["Import CSV", "Export CSV"])

    # ========== Import CSV Tab ==========
    with tab1:
        st.subheader("Import Data from CSV")

        table_type = st.selectbox(
            "Select data type to import",
            ["Organisation", "Stakeholder", "PainPoint", "Commercial", "OrgRelationship"]
        )

        uploaded_file = st.file_uploader(
            f"Upload {table_type}.csv",
            type=["csv"],
            key=f"upload_{table_type.lower()}"
        )

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)

                st.write(f"Preview of uploaded data:")
                st.dataframe(df.head())

                st.write(f"**Rows:** {len(df)}")
                st.write(f"**Columns:** {', '.join(df.columns.tolist())}")

                # Validate columns
                expected_columns =config.TABLES[table_type]
                missing_columns = set(expected_columns) - set(df.columns)

                if missing_columns:
                    st.error(f"Missing required columns: {', '.join(missing_columns)}")
                else:
                    st.success("✅ All required columns are present.")

                    col1, col2 = st.columns(2)

                    with col1:
                        replace_existing = st.checkbox(
                            "Replace existing data",
                            help="If checked, existing records with same IDs will be updated"
                        )

                    with col2:
                        sync_to_kuzu = st.checkbox(
                            "Sync to graph database",
                            value=True,
                            help="Automatically sync imported data to the graph database"
                        )

                    if st.button("Import Data", type="primary"):
                        with st.spinner("Importing data..."):
                            success_count = 0
                            error_count = 0

                            if table_type == "Organisation":
                                for _, row in df.iterrows():
                                    success = sqlite_mgr.insert_organisation(
                                        int(row['org_id']),
                                        row['org_name'],
                                        row['org_type'],
                                        row['org_function'],
                                    )
                                    if success:
                                        success_count += 1
                                        if sync_to_kuzu:
                                            sync_mgr.sync_organisation(int(row['org_id']))
                                    else:
                                        error_count += 1
                                        logger.error(f"Failed to import Organisation: {row['org_id']}")

                            elif table_type == "Stakeholder":
                                for _, row in df.iterrows():
                                    success = sqlite_mgr.insert_stakeholder(
                                        int(row['stakeholder_id']),
                                        int(row['org_id']),
                                        row['name'],
                                        row['job_title'],
                                        row['role'],
                                    )
                                    if success:
                                        success_count += 1
                                        if sync_to_kuzu:
                                            sync_mgr.sync_stakeholder(int(row['stakeholder_id']))
                                    else:
                                        error_count += 1
                                        logger.error(f"Failed to import Stakeholder: {row['stakeholder_id']}")

                            elif table_type == "PainPoint":
                                for _, row in df.iterrows():
                                    success = sqlite_mgr.insert_painpoint(
                                        int(row['painpoint_id']),
                                        int(row['org_id']),
                                        row['description'],
                                        row['urgency'],
                                        row['severity'],
                                    )
                                    if success:
                                        success_count += 1
                                        if sync_to_kuzu:
                                            sync_mgr.sync_painpoint(int(row['painpoint_id']))
                                    else:
                                        error_count += 1
                                        logger.error(f"Failed to import PainPoint: {row['painpoint_id']}")

                            elif table_type == "Commercial":
                                for _, row in df.iterrows():
                                    success = sqlite_mgr.insert_commercial(
                                        int(row['commercial_id']),
                                        int(row['org_id']),
                                        row['method'],
                                        float(row['budget']),
                                    )
                                    if success:
                                        success_count += 1
                                        if sync_to_kuzu:
                                            sync_mgr.sync_commercial(int(row['commercial_id']))
                                    else:
                                        error_count += 1
                                        logger.error(f"Failed to import Commercial: {row['commercial_id']}")

                            elif table_type == "OrgRelationship":
                                for _, row in df.iterrows():
                                    success = sqlite_mgr.insert_org_relationship(
                                        int(row['from_org_id']),
                                        int(row['to_org_id']),
                                        row['relationship_type'],
                                    )
                                    if success:
                                        success_count += 1
                                        if sync_to_kuzu:
                                            sync_mgr.sync_relationship(
                                                int(row['from_org_id']),
                                                int(row['to_org_id']),
                                                row['relationship_type']
                                            )
                                    else:
                                        error_count += 1
                                        logger.error(f"Failed to import OrgRelationship: {row['from_org_id']} -> {row['to_org_id']}")

                            st.success(f"✅ Imported {success_count} records successfully!")

                            if error_count > 0:
                                st.warning(f"⚠️ {error_count} records failed (possibly duplicates)")

                            st.rerun()

            except Exception as e:
                st.error(f"Error reading CSV: {e}")

    # ========== Export CSV Tab ==========