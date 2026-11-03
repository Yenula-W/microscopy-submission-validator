"""Round-3 hand judgments, applied as explicit per-pattern verdicts (each pattern verified on the inputs)."""
import csv, json, re, collections, sys
from pathlib import Path
rows = list(csv.DictReader(open("findings.csv")))
IMG = {"images_readable", "ome_metadata", "series_consistent"}
taxon = {}
for j in Path("inputs").glob("*/S-BIAD*.json"):
    taxon[j.parent.name] = bool(re.search(r"NCBITaxon_\d+", j.read_text()))
NO_IMG_SUBSET = {"R3-10-S-BIAD3373", "R3-11-S-BIAD3657", "R3-13-S-BIAD4011", "R3-21-S-BIAD3774", "R3-09-idr0082"}
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
    elif c == "field_present" and "ncbi_taxon" in m:
        v, note = ("wrong", "page-tab Organism carries NCBITaxon_* in valqual TermId; converter ignored it") if taxon.get(i) else ("correct", "no taxon id anywhere in the study")
    elif rule == "BIA-FL-004" and m.startswith(("on disk but not", "... and")) and i == "R3-26-S-BIAD3835":
        v, note = "wrong", "Files column lists directory Source_Images; BIA allows a directory path, so files under it are listed"
    elif c == "images_readable" and "Could not parse XML from 'II*" in m:
        v, note = "wrong", "BinaryOnly OME-TIFF whose MetadataFile is another OME-TIFF (multifile-Z1); readable"
    elif c == "images_readable" and "requires the 'imagecodecs' package" in m:
        v, note = "wrong", "LZW TIFF is valid; the tool lacks the codec, not evidence the file is bad"
    elif i == "R3-05-emdb-map" and m == "no image files found in dataset":
        v, note = "wrong", "EMD-2225.map is an MRC-format EM volume; not recognised as an image"
    elif c == "series_consistent" and i == "R3-15-S-BIAD4056":
        v, note = "debatable", "photos of different leaves; differing XY is expected, not a defect"
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
