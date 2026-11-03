"""Round-4 hand judgments, applied as explicit per-pattern verdicts (each pattern verified on the inputs)."""
import csv, json, re, collections, sys
from pathlib import Path
rows = list(csv.DictReader(open("findings.csv")))
IMG = {"images_readable", "ome_metadata", "series_consistent"}
taxon = {}
for j in Path("inputs").glob("*/S-BIAD*.json"):
    taxon[j.parent.name] = bool(re.search(r"NCBITaxon_\d+", j.read_text()))
NO_IMG_SUBSET = {"R4-11-S-BIAD2499", "R4-13-S-BIAD3375", "R4-14-S-BIAD3578", "R4-15-S-BIAD3613", "R4-09-idr0016"}
out = []
for r in rows:
    i, rule, c, m, k, t = r["input"], r["rule"], r["check"], r["message"], r["kind"], r["target"]
    v, note = "correct", ""
    if k == "names" and c in IMG:
        v, note = "n/a", "zero-byte placeholder in names mirror"
    elif i in NO_IMG_SUBSET and (m == "no image files found in dataset" or c == "file_list_present"):
        v, note = "n/a", "harness subset holds no images / FTP crawl returned no files"
    elif k == "idrmeta" and t != "idr":
        v, note = "n/a", "tables-only input is not a BIA/REMBI submission"
    elif c == "images_readable" and ("Unsupported document namespace" in m or "outdated schema" in m):
        v, note = "wrong", "valid OME-TIFF written against an older/dev OME schema (2015-01, 2016-DEV0); ome-types refused it"
    elif i == "R4-02-klb" and m == "no image files found in dataset":
        v, note = "wrong", "img.klb is a KLB volume (Keller lab block, used by IDR idr0044); not recognised as an image"
    elif i == "R4-30-S-BIAD3450" and m == "no image files found in dataset":
        v, note = "wrong", "all 46 images are submitted inside .zip archives; 'no image files' overstates"
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
