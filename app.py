import streamlit as st
from database.sqlite_manager import SQLiteManager
from database.kuzu_manager import KuzuManager
from database.sync_manager import SyncManager
from ui.crud_forms import render_crud_interface
from ui.graph_viz import render_graph_explorer
from ui.import_export import render_import_export
import os
from dotenv import load_dotenv

load_dotenv()

# Basic security settings
def check_password():
    """Returns True if the user has entered the correct password."""
    
    correct_password = os.getenv("TESTING_PASSWORD")
    if not correct_password:
        st.error("❌ No password set in environment variables!")
        st.stop()

    # Check if the user is already authenticated
    if st.session_state.get("password_correct"):
        return True
    
    # If not, show password input
    with st.form("password_form"):
        password = st.text_input("Enter password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if password == correct_password:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
    return False

# Page configuration
st.set_page_config(
    page_title="Stakeholder Map",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Check password
if not check_password():
    st.stop()

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize database managers
@st.cache_resource
def init_databases():
    """Initialize database connections"""
    sqlite_mgr = SQLiteManager()
    kuzu_mgr = KuzuManager()
    sync_mgr = SyncManager(sqlite_mgr, kuzu_mgr)
    return sqlite_mgr, kuzu_mgr, sync_mgr

try:
    sqlite_mgr, kuzu_mgr, sync_mgr = init_databases()
except Exception as e:
    st.error("❌ **Error initializing databases!**")
    st.error("The app cannot start. Please check database files and dependencies.")
    st.exception(e)  # This will display the full error traceback
    st.stop()  # This stops the script gracefully

# Sidebar navigation
with st.sidebar:
    st.title("🕸️ Stakeholder Map")
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "📝 Data Management", "🕸️ Graph Explorer", "📁 Import/Export", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Quick stats
    st.subheader("Quick Stats")
    try:
        orgs_count = len(sqlite_mgr.get_all_organisations())
        stakeholders_count = len(sqlite_mgr.get_all_stakeholders())
        painpoints_count = len(sqlite_mgr.get_all_painpoints())
        
        st.metric("Organisations", orgs_count)
        st.metric("Stakeholders", stakeholders_count)
        st.metric("Pain Points", painpoints_count)
    except Exception as e:
        st.error(f"Error loading stats: {e}")
    
    st.markdown("---")
    st.caption("Built with Streamlit + SQLite + Kuzu")

# Main content area
if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        orgs_df = sqlite_mgr.get_all_organisations()
        stakeholders_df = sqlite_mgr.get_all_stakeholders()
        painpoints_df = sqlite_mgr.get_all_painpoints()
        commercials_df = sqlite_mgr.get_all_commercials()
        relationships_df = sqlite_mgr.get_all_org_relationships()
        
        with col1:
            st.metric("Total Organisations", len(orgs_df))
        with col2:
            st.metric("Total Stakeholders", len(stakeholders_df))
        with col3:
            st.metric("Total Pain Points", len(painpoints_df))
        with col4:
            st.metric("Total Relationships", len(relationships_df))
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Organisations by Type")
            if not orgs_df.empty:
                org_type_counts = orgs_df['org_type'].value_counts()
                st.bar_chart(org_type_counts)
            else:
                st.info("No data available")
        
        with col2:
            st.subheader("Pain Points by Severity")
            if not painpoints_df.empty:
                severity_counts = painpoints_df['severity'].value_counts()
                st.bar_chart(severity_counts)
            else:
                st.info("No data available")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Relationships by Type")
            if not relationships_df.empty:
                rel_type_counts = relationships_df['relationship_type'].value_counts()
                st.bar_chart(rel_type_counts)
            else:
                st.info("No data available")
        
        with col2:
            st.subheader("Commercial Budget by Organisation")
            if not commercials_df.empty:
                budget_by_org = commercials_df.groupby('org_name')['budget'].sum().sort_values(ascending=False).head(10)
                budget_by_org = budget_by_org / 1e6  # Convert to millions
                st.bar_chart(budget_by_org)
            else:
                st.info("No data available")
        
        st.markdown("---")
        
        # Recent activity
        st.subheader("Recent Data")
        
        tab1, tab2, tab3 = st.tabs(["Recent Organisations", "Recent Stakeholders", "Recent Pain Points"])
        
        with tab1:
            if not orgs_df.empty:
                st.dataframe(orgs_df.tail(5), width='stretch', hide_index=True)
            else:
                st.info("No organisations yet")
        
        with tab2:
            if not stakeholders_df.empty:
                st.dataframe(stakeholders_df[['name', 'org_name', 'job_title']].tail(5), width='stretch', hide_index=True)
            else:
                st.info("No stakeholders yet")
        
        with tab3:
            if not painpoints_df.empty:
                st.dataframe(painpoints_df[['description', 'org_names', 'severity', 'urgency']].tail(5), width='stretch', hide_index=True)
            else:
                st.info("No pain points yet")
    
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

elif page == "📝 Data Management":
    render_crud_interface(sqlite_mgr, sync_mgr)

elif page == "🕸️ Graph Explorer":
    # pass sqlite manager so graph explorer can map org name → id for neighborhood searches
    render_graph_explorer(kuzu_mgr, sqlite_mgr)

elif page == "📁 Import/Export":
    render_import_export(sqlite_mgr, sync_mgr)

elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    
    st.subheader("Database Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Sync Operations")
        
        if st.button("🔄 Full Sync (SQLite → Kuzu)", width='stretch'):
            with st.spinner("Syncing all data to graph database..."):
                try:
                    sync_mgr.full_sync()
                    st.success("✅ Full sync completed successfully!")
                except Exception as e:
                    st.error(f"❌ Full sync failed: {e}")