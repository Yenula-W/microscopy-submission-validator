"""Round-6 hand judgments, applied as explicit per-pattern verdicts (each pattern verified on the inputs)."""
import csv, json, re, collections, sys
from pathlib import Path
rows = list(csv.DictReader(open("findings.csv")))
IMG = {"images_readable", "ome_metadata", "series_consistent"}
taxon = {}
for j in Path("inputs").glob("*/S-BIAD*.json"):
    taxon[j.parent.name] = bool(re.search(r"NCBITaxon_\d+", j.read_text()))
NO_IMG_SUBSET = {"R6-10-S-BIAD3686", "R6-12-S-BIAD3931"}
APIFL = {"file_list_matches", "file_list_format", "file_list_header"}
out = []
for r in rows:
    i, rule, c, m, k, t = r["input"], r["rule"], r["check"], r["message"], r["kind"], r["target"]
    v, note = "correct", ""
    if k in ("names", "apinames") and c in IMG:
        v, note = "n/a", "zero-byte placeholder in names mirror"
    elif k == "apinames" and c in APIFL:
        v, note = "n/a", "API mirror: list rebuilt from the files API (merged columns, disk == list by construction)"
    elif i in NO_IMG_SUBSET and (m == "no image files found in dataset" or c == "file_list_present"):
        v, note = "n/a", "harness subset holds no images / FTP crawl returned no files"
    elif k == "idrmeta" and t != "idr":
        v, note = "n/a", "tables-only input is not a BIA/REMBI submission"
    elif i == "R6-03-ome-xml" and m == "no image files found in dataset":
        v, note = "wrong", "multi-channel-time-series.ome.xml holds its pixels as BinData; it is an image"
    elif i == "R6-11-S-BIAD3778" and c == "images_readable":
        v, note = "wrong", "OME-XML has literal '\\n' between attributes (not valid XML) but the TIFF pixels are fine; 'unreadable' overstates"
    elif i == "R6-29-S-BIAD2430" and rule.endswith("FL-001") and r["status"] == "fail":
        v, note = "wrong", "a TSV list is present; an extra .xlsx named *file_list* can't be parsed, which is no reason to FAIL 'file list present'"
    out.append({**r, "verdict": v, "note": note})
with open("findings_judged.tsv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]), delimiter="\t"); w.writeheader(); w.writerows(out)
tab = collections.defaultdict(collections.Counter)
for r in out:
    if r["verdict"] != "n/a":
        tab[r["check"]][r["verdict"]] += 1
tot = collections.Counter()
print("check\tn\tcorrect\tdebatable\twrong\t%correct")
for c, ct in sorted(tab.items()):
    n = sum(ct.values()); tot += ct
    print(f"{c}\t{n}\t{ct['correct']}\t{ct['debatable']}\t{ct['wrong']}\t{100*ct['correct']/n:.1f}")
n = sum(tot.values())
print(f"TOTAL\t{n}\t{tot['correct']}\t{tot['debatable']}\t{tot['wrong']}\t{100*tot['correct']/n:.1f}")
print("n/a", sum(r["verdict"] == "n/a" for r in out))
