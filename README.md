Architecture Overview

┌─────────────────────────────────────────────────────────┐
│                  Streamlit Application                  │
├─────────────────────────────────────────────────────────┤
│  Sidebar Navigation:                                    │
│  ├─ 📊 Dashboard                                        │
│  ├─ 📝 Data Management (CRUD)                           │
│  ├─ 📁 Import/Export CSV                                │
│  ├─ 🕸️  Graph Explorer                                  │
│  └─ 📈 Analytics                                        │
├─────────────────────────────────────────────────────────┤
│  Main Area (dynamic based on selection)                │
└─────────────────────────────────────────────────────────┘
         ↓                              ↓
    SQLite DB                       Kuzu DB
   (govmap.db)                   (govmap_kuzu/)
   - CRUD operations              - Graph queries
   - Table views                  - Relationship traversal
   - Data validation              - Path finding
         ↓                              ↑
         └──────── Sync Layer ──────────┘
              (on insert/update/delete)