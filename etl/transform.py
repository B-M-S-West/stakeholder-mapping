import polars as pl
from pathlib import Path

# Define file paths
RAW_DATA_PATH = Path("data/raw")
PROCESSED_DATA_PATH = Path("data/processed")
PROCESSED_DATA_PATH.mkdir(exist_ok=True)

def clean_organisations():
    """Read and lightly clean Organisations.csv"""
    df = pl.read_csv(RAW_DATA_PATH / "Organisation.csv")
    # Strip spaces, make type lowercase
    df = df.with_columns([
        pl.col("org_name").str.strip_chars().alias("org_name"),
        pl.col("org_type").str.strip_chars().str.to_lowercase().alias("org_type")
        ])
    return df

def clean_stakeholders():
    """Read Stakeholder.csv and return as-is in new folder"""
    df = pl.read_csv(RAW_DATA_PATH / "Stakeholder.csv")
    return df

def clean_painpoints():
    """Read PainPoint.csv and normalise severity/urgency columns"""
    df = pl.read_csv(RAW_DATA_PATH / "PainPoint.csv")
    df = df.with_columns([
        pl.col("severity").str.to_lowercase(),
        pl.col("urgency").str.to_lowercase()
    ])
    return df

def clean_commercial():
    """Read Commercial.csv and ensure budget is numeric."""
    df = pl.read_csv(RAW_DATA_PATH / "Commercial.csv")
    df = df.with_columns([
        pl.col("budget").cast(pl.Float64)
    ])
    return df

def clean_relationships(orgs):
    """Validate that relationships only reference valid org IDs."""
    df = pl.read_csv(RAW_DATA_PATH / "OrgRelationships.csv")

    # Check that from/to IDs exist in organisations
    invalid_from = df.filter(~pl.col("from_org_id").is_in(orgs["org_id"].implode()))
    invalid_to = df.filter(~pl.col("to_org_id").is_in(orgs["org_id"].implode()))

    if invalid_from.height > 0 or invalid_to.height > 0:
        print("⚠️ Warning: Some relationships reference invalid organisation IDs")
        print("Invalid from_org_id rows:\n", invalid_from)
        print("Invalid to_org_id rows:\n", invalid_to)

    return df

def save_processed(df: pl.DataFrame, filename: str):
    """Save the cleaned DataFrame to the processed data folder."""
    df.write_csv(PROCESSED_DATA_PATH / filename, include_header=True)

if __name__ == "__main__":
    orgs = clean_organisations()
    save_processed(orgs, "Organisation_clean.csv")

    stakeholders = clean_stakeholders()
    save_processed(stakeholders, "Stakeholder_clean.csv")

    painpoints = clean_painpoints()
    save_processed(painpoints, "PainPoint_clean.csv")

    commercial = clean_commercial()
    save_processed(commercial, "Commercial_clean.csv")

    relationships = clean_relationships(orgs)
    save_processed(relationships, "OrgRelationships_clean.csv")

    print("✅ ETL complete. Clean files saved to data/processed/")

