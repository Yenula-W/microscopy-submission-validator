"""Round-5 hand judgments, applied as explicit per-pattern verdicts (each pattern verified on the inputs)."""
import csv, json, re, collections, sys
from pathlib import Path
rows = list(csv.DictReader(open("findings.csv")))
IMG = {"images_readable", "ome_metadata", "series_consistent"}
taxon = {}
for j in Path("inputs").glob("*/S-BIAD*.json"):
    taxon[j.parent.name] = bool(re.search(r"NCBITaxon_\d+", j.read_text()))
NO_IMG_SUBSET = {"R5-11-S-BIAD3802", "R5-12-S-BIAD2500", "R5-13-S-BIAD3897", "R5-15-S-BIAD4158"}
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
    elif i == "R5-04-amiramesh" and m == "no image files found in dataset":
        v, note = "wrong", "test.am is an AmiraMesh lattice (image/label volume); not recognised as an image"
    elif rule == "BIA-FL-004" and i == "R5-20-S-BIAD3949":
        v, note = "correct", "each zip is listed 15 times (one row per mouse); BIA lists each file once - unzip or use one row per archive"
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
