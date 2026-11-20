# Barre Chart

Victoria's dance scene, in data: where the studios are, where the dancers come from, and what they dance.

The first page shows children aged 5-14 per dance studio in Melbourne's inner west. The site is the
static page in `docs/`.

## Data rule

Raw source data stays on your machine in `data/raw/`, which git ignores. Some sources, such as
competition results, name children. Only the aggregated, suburb-level files the site shows are
committed, and every chart credits its source.

## Rebuilding the data

`python scripts/build_data.py` fetches ABS population estimates and area boundaries, counts the
hand-checked studios in `data/raw/studios.csv`, and writes `docs/data/inner-west.geojson`. It stops
if a studio name would end up in the published file. Run the tests with
`python -m unittest discover -s scripts`.
