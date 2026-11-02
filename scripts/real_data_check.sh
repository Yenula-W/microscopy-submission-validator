#!/usr/bin/env bash
# Download two small public datasets and run micro-validate against them.
#   1. OME sample data tubhiswt-4D: multi-file OME-TIFF (86 files, ~240 MB), CC BY 4.0
#   2. IDR idr0062A image 6001240 (B1_C1, OME-Zarr v0.4, ~46 MB) + the real idr0062
#      study/assay files from github.com/IDR/idr0062-blin-nuclearsegmentation
# Usage: scripts/real_data_check.sh <scratch-dir>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:?scratch dir}"
MV="${MV:-micro-validate}"
mkdir -p "$OUT/data/tubhiswt-4D" "$OUT/sub/tubhiswt/images" "$OUT/sub/idr0062/Blastocysts" "$OUT/reports"

base=https://downloads.openmicroscopy.org/images/OME-TIFF/2016-06/tubhiswt-4D
if [ ! -f "$OUT/data/tubhiswt-4D/tubhiswt_C1_TP42.ome.tif" ]; then
  curl -s "$base/" | grep -o 'href="[^"]*\.ome\.tif"' | sed 's/href="//;s/"//' \
    | (cd "$OUT/data/tubhiswt-4D" && xargs -P 8 -I{} curl -s -O "$base/{}")
fi
[ -d "$OUT/data/6001240.zarr" ] || python3 -I "$HERE/fetch_zarr.py" \
  https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr "$OUT/data/6001240.zarr"

# tubhiswt as a BIA submission: REMBI metadata + generated file list
ln -sf "$OUT"/data/tubhiswt-4D/*.ome.tif "$OUT/sub/tubhiswt/images/"
cp "$HERE/../examples/tubhiswt-submission.yaml" "$OUT/sub/tubhiswt/submission.yaml"
(cd "$OUT/sub/tubhiswt" && { printf 'Files\tchannel\ttimepoint\n'
  for f in images/*.ome.tif; do b=${f##*/}; c=${b#tubhiswt_C}; c=${c%%_*}; t=${b##*_TP}; t=${t%.ome.tif}
    printf '%s\t%s\t%s\n' "$f" "$c" "$t"; done; } > file_list.tsv)

# idr0062 as an IDR submission: real curated study + assay tables, one converted image
rm -rf "$OUT/sub/idr0062/Blastocysts/B1_C1.ome.zarr"
cp -R "$OUT/data/6001240.zarr" "$OUT/sub/idr0062/Blastocysts/B1_C1.ome.zarr"
for f in idr0062-study.txt experimentA/idr0000-experiment{A,B,C,D,E}_assays.txt; do
  curl -s "https://raw.githubusercontent.com/IDR/idr0062-blin-nuclearsegmentation/master/$f" -o "$OUT/sub/idr0062/${f##*/}"
done

set +e
"$MV" "$OUT/data/tubhiswt-4D" -t bia   -o "$OUT/reports/tubhiswt-raw-bia"   >/dev/null; echo "tubhiswt raw      bia   exit $?"
"$MV" "$OUT/sub/tubhiswt"     -t bia   -o "$OUT/reports/tubhiswt-bia"       >/dev/null; echo "tubhiswt prepared bia   exit $?"
"$MV" "$OUT/sub/tubhiswt"     -t rembi -o "$OUT/reports/tubhiswt-rembi"     >/dev/null; echo "tubhiswt prepared rembi exit $?"
"$MV" "$OUT/sub/tubhiswt"     -t idr   -o "$OUT/reports/tubhiswt-idr"       >/dev/null; echo "tubhiswt prepared idr   exit $?"
"$MV" "$OUT/sub/idr0062"      -t idr   -o "$OUT/reports/idr0062-idr"        >/dev/null; echo "idr0062  prepared idr   exit $?"
"$MV" "$OUT/sub/idr0062"      -t bia   -o "$OUT/reports/idr0062-bia"        >/dev/null; echo "idr0062  prepared bia   exit $?"
