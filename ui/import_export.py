import streamlit as st
import pandas as pd
from pathlib import Path
from loguru import logger
import config
from database.sqlite_manager import SQLiteManager
from database.sync_manager import SyncManager
import zipfile
import io

def render_import_export(sqlite_mgr: SQLiteManager, sync_mgr: SyncManager):
    """Render CSV import/export interface"""
    
    st.header("📁 Import/Export Data")

    tab1, tab2 = st.tabs(["Import CSV", "Export CSV"])

    # ========== Import CSV Tab ==========
    with tab1:
        st.subheader("Import Data from CSV")

        table_type = st.selectbox(
            "Select data type to import",
            ["Organisation", "Stakeholder", "PainPoint", "Commercial", "OrgRelationship", "OrganisationPainPoint"]
        )

        uploaded_file = st.file_uploader(
            f"Upload {table_type}.csv",
            type=["csv"],
            key=f"upload_{table_type.lower()}"
        )

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)

                st.write("Preview of uploaded data:")
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
                                        int(row.get('painpoint_id')),
                                        row.get('description'),
                                        row.get('severity'),
                                        row.get('urgency'),
                                    )
                                    if success:
                                        success_count += 1
                                        if sync_to_kuzu:
                                            sync_mgr.sync_painpoint_assignments(int(row['painpoint_id']))
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
                            
                            elif table_type == "OrganisationPainPoint":
                                for _, row in df.iterrows():
                                    org_id = int(row['org_id'])
                                    painpoint_id = int(row['painpoint_id'])
                                    success = sqlite_mgr.assign_painpoint_to_organisation(
                                        org_id,
                                        painpoint_id
                                    )
                                    if success:
                                        success_count += 1
                                        if sync_to_kuzu:
                                            sync_mgr.sync_painpoint_assignment(
                                                org_id,
                                                painpoint_id
                                            )
                                    else:
                                        error_count += 1
                                        logger.error(f"Failed to import OrganisationPainPoint: {org_id} - {painpoint_id}")

                            st.success(f"✅ Imported {success_count} records successfully!")

                            if error_count > 0:
                                st.warning(f"⚠️ {error_count} records failed (possibly duplicates)")

                            st.rerun()

            except Exception as e:
                st.error(f"Error reading CSV: {e}")

    # ========== Export CSV Tab ==========
    with tab2:
        st.subheader("Export Data to CSV")

        export_type = st.selectbox(
            "Select data to export",
            ["Organisation", "Stakeholder", "PainPoint", "Commercial", "OrgRelationship", "OrganisationPainPoint", "All Tables"]
        )

        if st.button("Generate CSV", type="primary"):
            try:
                if export_type == "Organisation":
                    df = sqlite_mgr.get_all_organisations()
                    filename = "organisations_export.csv"
                
                elif export_type == "Stakeholder":
                    df = sqlite_mgr.get_all_stakeholders()
                    df = df.drop(columns=['org_name'], errors='ignore')  
                    # Drop org_name as join column
                    filename = "stakeholders_export.csv"

                elif export_type == "PainPoint":
                    df = sqlite_mgr.get_all_painpoints()
                    df = df.drop(columns=['org_name'], errors='ignore')  
                    # Drop org_name as join column
                    filename = "painpoints_export.csv"

                elif export_type == "Commercial":
                    df = sqlite_mgr.get_all_commercials()
                    df = df.drop(columns=['org_name'], errors='ignore')  
                    # Drop org_name as join column
                    filename = "commercials_export.csv"

                elif export_type == "OrgRelationship":
                    df = sqlite_mgr.get_all_org_relationships()
                    df = df[['from_org_id', 'to_org_id', 'relationship_type']]  
                    # Only keep relevant columns
                    filename = "org_relationships_export.csv"

                elif export_type == "OrganisationPainPoint":
                    df = sqlite_mgr.get_all_painpoint_assignments()
                    filename = "organisation_painpoints_export.csv"

                elif export_type == "All Tables":
                    # Export all tables as a zip file
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
                        for table in ["Organisation", "Stakeholder", "PainPoint", "Commercial", "OrgRelationship", "OrganisationPainPoint"]:
                            if table == "Organisation":
                                df = sqlite_mgr.get_all_organisations()
                            elif table == "Stakeholder":
                                df = sqlite_mgr.get_all_stakeholders()
                                df = df.drop(columns=['org_name'], errors='ignore')
                            elif table == "PainPoint":
                                df = sqlite_mgr.get_all_painpoints()
                                df = df.drop(columns=['org_name'], errors='ignore')
                            elif table == "Commercial":
                                df = sqlite_mgr.get_all_commercials()
                                df = df.drop(columns=['org_name'], errors='ignore')
                            elif table == "OrgRelationship":
                                df = sqlite_mgr.get_all_org_relationships()
                                df = df[['from_org_id', 'to_org_id', 'relationship_type']]
                            elif table == "OrganisationPainPoint":
                                df = sqlite_mgr.get_all_painpoint_assignments()

                            csv_data = df.to_csv(index=False)
                            zip_file.writestr(f"{table.lower()}_export.csv", csv_data)

                    st.download_button(
                        label="📥 Download All Tables (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="stakeholder_map_export.zip",
                        mime="application/zip"
                    )
                    st.success("✅ Export package ready!")
                    return  # Exit after handling all tables
                
                # Single table export
                csv_data = df.to_csv(index=False)

                st.download_button(
                    label=f"📥 Download {filename}",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )

                st.success(f"✅ Exported {len(df)} records!")
                st.dataframe(df.head())
            
            except Exception as e:
                st.error(f"❌ Error exporting {filename}: {e}")
