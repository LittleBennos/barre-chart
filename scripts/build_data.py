"""Build docs/data/inner-west.geojson: children aged 5-14 per dance studio in Melbourne's inner west.

Reads ABS population estimates and SA2 boundaries from public ABS services, plus the
hand-checked studio list in data/raw/studios.csv. That list stays local (git ignores
data/raw/): only per-area counts are written, and the build stops if any studio name
would reach the published file.

Run from the repo root: python scripts/build_data.py
"""
import csv
import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIOS_CSV = ROOT / "data" / "raw" / "studios.csv"
OUT = ROOT / "docs" / "data" / "inner-west.geojson"

# ABS SA3s Hobsons Bay (21302) and Maribyrnong (21303): the 12 SA2s of the inner west.
SA3_CODES = ("21302", "21303")
EXPECTED_AREAS = 12
YEAR = "2025"

SA2_URL = (
    "https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA2/MapServer/0/query"
    "?where=sa3_code_2021+IN+({sa3})&outFields=sa2_code_2021,sa2_name_2021"
    "&returnGeometry=true&outSR=4326&f=geojson&maxAllowableOffset=0.0003&geometryPrecision=5"
)
# Persons (SEX 3) aged 5-9 (A59) and 10-14 (A10), estimated resident population at 30 June.
ERP_URL = (
    "https://data.api.abs.gov.au/rest/data/ABS,ERP_ASGS2021,1.0.0/"
    "ERP.3.A59+A10.SA2.{codes}.A?format=csvfile&startPeriod={year}&endPeriod={year}"
)


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read().decode("utf-8")


def children_by_sa2(erp_csv, codes):
    """Children aged 5-14 per SA2 code: the 5-9 row plus the 10-14 row."""
    totals, rows = Counter(), Counter()
    for row in csv.DictReader(erp_csv.splitlines()):
        totals[row["ASGS_2021"]] += int(row["OBS_VALUE"])
        rows[row["ASGS_2021"]] += 1
    partial = [c for c in codes if rows[c] != 2]
    if partial:
        raise ValueError(f"expected 2 age rows per area; missing or partial: {partial}")
    return totals


def read_studios(path, codes):
    """Return (studios counted per SA2 code, every studio name, latest checked date)."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    counted = [r for r in rows if r["counted"].strip().lower() == "yes"]
    outside = sorted({r["sa2_code"] for r in counted} - set(codes))
    if outside:
        raise ValueError(f"studios.csv counts studios in SA2s outside the region: {outside}")
    checked = max(r["checked"] for r in counted) if counted else ""
    return Counter(r["sa2_code"] for r in counted), [r["name"] for r in rows], checked


def children_per_studio(children, studios):
    return round(children / studios) if studios else None


def leaked_names(text, names):
    """Studio names (case-insensitive) that appear anywhere in text."""
    low = text.lower()
    return [n for n in names if n.strip() and n.strip().lower() in low]


def main():
    sa3 = ",".join(f"'{c}'" for c in SA3_CODES)
    geo = json.loads(fetch(SA2_URL.format(sa3=sa3)))
    codes = [f["properties"]["sa2_code_2021"] for f in geo["features"]]
    if len(codes) != EXPECTED_AREAS:
        raise ValueError(f"expected {EXPECTED_AREAS} SA2s, got {len(codes)}")

    children = children_by_sa2(fetch(ERP_URL.format(codes="+".join(codes), year=YEAR)), codes)
    studios, names, checked = read_studios(STUDIOS_CSV, codes)

    for f in geo["features"]:
        code = f["properties"]["sa2_code_2021"]
        f["properties"] = {
            "sa2_code": code,
            "sa2_name": f["properties"]["sa2_name_2021"],
            "children_5_14": children[code],
            "studios": studios[code],
            "children_per_studio": children_per_studio(children[code], studios[code]),
        }
    geo["meta"] = {"population_year": YEAR, "studios_checked": checked}

    text = json.dumps(geo, separators=(",", ":"))
    leaks = leaked_names(text, names)
    if leaks:
        sys.exit(f"Refusing to publish: studio names found in output: {leaks}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text + "\n", encoding="utf-8")

    for f in sorted(geo["features"], key=lambda f: f["properties"]["sa2_name"]):
        p = f["properties"]
        print(f'{p["sa2_name"]:<28} children {p["children_5_14"]:>5}  studios {p["studios"]}  per studio {p["children_per_studio"]}')
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text):,} bytes)")


if __name__ == "__main__":
    main()
