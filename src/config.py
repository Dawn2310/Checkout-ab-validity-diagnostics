"""Project configuration paths and constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "dataset"
OUTPUT_DIR = ROOT / "output"
FIG_DIR = OUTPUT_DIR / "figures"
TABLE_DIR = OUTPUT_DIR / "tables"
PROCESSED_DIR = OUTPUT_DIR / "processed"

for d in (FIG_DIR, TABLE_DIR, PROCESSED_DIR):
    d.mkdir(parents=True, exist_ok=True)

CONTROL_FILE = DATA_DIR / "control_group.csv"
TEST_FILE = DATA_DIR / "test_group.csv"

COL_MAP = {
    "Campaign Name": "campaign",
    "Date": "date",
    "Spend [USD]": "spend",
    "# of Impressions": "impressions",
    "Reach": "reach",
    "# of Website Clicks": "clicks",
    "# of Searches": "searches",
    "# of View Content": "view_content",
    "# of Add to Cart": "add_to_cart",
    "# of Purchase": "purchase",
}

FUNNEL_STEPS = ["impressions", "clicks", "view_content", "add_to_cart", "purchase"]

ALPHA = 0.05
POWER_TARGET = 0.80
BOOTSTRAP_ITERS = 10_000
RNG_SEED = 42

ASSUMED_AOV_USD = 50.0
