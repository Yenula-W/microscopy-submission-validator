# micro-validate

Check a microscopy dataset against public image repository requirements before you
submit it. You get a pass/warn/fail result for each rule, a fix list, and a source URL
for every rule.

Targets:

| Target | Repository | What is checked |
|---|---|---|
| `bia` | [BioImage Archive](https://www.ebi.ac.uk/bioimage-archive/) | REMBI 1.5 required fields, file list rules (`Files` header, exact paths, no orphans), allowed file-name characters, size limits, OME-Zarr zipping, image readability, OME pixel sizes, series consistency |
| `idr` | [Image Data Resource](https://idr.openmicroscopy.org/) | Study-file mandatory fields, assay/library columns, assay rows to image files (both directions), `Channels` against the image channel count, the OME-Zarr-only image requirement |
| `rembi` | Repository-neutral | REMBI completeness: required fields fail, recommended fields (licence, funding, publication, FBbi term, variables) warn |

Rules live in YAML (`src/micro_validate/rules/*.yaml`). Each rule cites the page it came
from, and the pages were retrieved on 2026-11-02. You can add a lab-specific rule set
with `--target path/to/rules.yaml`.

## Install

```bash
python3 -m venv mv-env
source mv-env/bin/activate
pip install git+https://github.com/Yenula-W/microscopy-submission-validator
micro-validate --list-targets
```

This works on Python 3.9 to 3.13 (CI tests 3.9, 3.12 and 3.13). The core dependencies are tifffile, ome-types, zarr, pyyaml and numpy.

To read vendor formats, add the optional `bioio` extra and a reader plugin, e.g. `bioio-nd2`:

```bash
pip install "micro-validate[vendor] @ git+https://github.com/Yenula-W/microscopy-submission-validator" bioio-nd2
```

Zeiss LSM, MetaMorph and FluoView TIFFs are read without this extra.

## Use

```bash
mkdir -p my_dataset                                           # your images go here
micro-validate --template bia > my_dataset/submission.yaml   # fill in, then:
micro-validate my_dataset --target bia
micro-validate my_dataset --target idr --out reports/idr     # writes reports/idr.md + reports/idr.json
micro-validate my_dataset --target rembi --json
micro-validate my_dataset --target bia --partial             # dataset is a pilot subset of the full submission
```

The exit code is 0 when nothing fails, 1 when any rule fails (with `--strict`, also on warnings), and 2 on a usage error.

Options:

- `--no-pixels` reads headers only and skips decoding one pixel block per image.
- `--partial` assumes you are checking a sample. It does not report files that a file list or assay table names but that are absent on disk. Every file that *is* present must still be described.

### Dataset layout

```
my_dataset/
  submission.yaml          # REMBI metadata (bia, rembi). Get a template with --template bia
  S-BIADnnn.json           # ...or a BioStudies page-tab JSON export (read automatically)
  file_list.tsv            # BIA file list: first column "Files", one row per file
  annotation_file_list.tsv # optional: BIA annotation list, needs a source_image column
  <name>-study.txt         # IDR study file (IDR template format)
  <name>-assays.txt        # IDR assay file (any *assay*.txt), or *library*.txt for screens
  images/...               # .ome.tif, .ome.zarr/, .ome.zarr.zip, vendor files, ...
```

A `*.zarr` directory counts as one file. Every other file under the folder is a data
file, and the BIA file-list check expects it to be listed. Sidecar metadata files such as
`.companion.ome` and MetaMorph `.nd` count as data files but not as images.

### Report

The Markdown report has these sections:

1. Overall status and counts.
2. **Fix list**: the failures first, then the warnings, each with example offending files.
3. A table of all rules with links to their sources.
4. The image metadata that was read: XYZCT, dtype, and pixel size in µm.

The JSON report has the same content, plus `images[]` with the full per-file details.

## Evaluation

[EVALUATION.md](EVALUATION.md) covers the evaluation. The tool was run on 26 held-out public inputs: OME-TIFF, ImageJ TIFF, Zeiss LSM/CZI, Nikon ND2, Olympus OIB, MetaMorph, IDR OME-Zarr v0.4/0.5, six accepted BioImage Archive studies and seven accepted IDR studies.

- Rounds 1-2: 78 runs, 0 crashes. 121 findings were hand-checked: 91.7% correct, 0 wrong. Round 2 covered 110 accepted IDR studies' published tables and 29 BioImage Archive upload trees.
- Ship-bar rounds 3-7: 104 new inputs, 312 runs, 0 crashes. Each round's first run was judged by hand before any change:

  | Round | Precision |
  |---|---|
  | 3 | 68.7% |
  | 4 | 94.4% |
  | 5 | 98.9% |
  | 6 | 96.1% |
  | 7 | 96.6% |

  Rounds 5 and 6 ran on the same frozen code, and round 7 on the next freeze. Every root cause found was fixed with a regression test, and reruns on the fixed code show 0 wrong.
- **Status:** the stricter ship bar, two untouched rounds in a row with no overstated claim, is **not yet met**. Rounds 5-7 each had a few overstated claims ("no images", "unreadable", Zeiss SEM pixel size "missing"), all now fixed. See EVALUATION.md §9-§10.
- **Needs review:** *Image files readable* is reported in its own "Needs review" section and does not affect the overall result or the exit code. Its untouched precision in rounds 3-4 was 44%.

`scripts/holdout/fetch.py` and `scripts/holdout/run_eval.py` reproduce the run. `scripts/real_data_check.sh` holds the original development-time checks.

## Tests

```bash
pip install -e '.[dev]' && pytest
```

There are 90 tests (one is skipped unless the `[vendor]` extra is installed, and one only when it is not), including messy-input robustness tests and regression tests for every rule fixed during the held-out evaluation. They build tiny synthetic OME-TIFFs and NGFF v0.4 OME-Zarrs (directory and zipped). They cover good and bad versions of each check type: missing or placeholder metadata, file-list header, format, missing and orphan files, case mismatch, bad characters, inconsistent channels and pixel sizes, plain TIFF, corrupt TIFF, unzipped zarr, annotation `source_image`, IDR hints, assay and channel mismatches, the CLI exit codes, and report output.

## Design

```
engine.py     rule loading, check registry, result aggregation   (no I/O assumptions; reusable)
checks.py     check functions referenced by name from YAML
dataset.py    folder discovery: metadata, file lists, IDR tables, data files
imageinfo.py  format classification + metadata via tifffile / ome-types / zarr (bioio optional)
report.py     JSON + Markdown
rules/*.yaml  bia, idr, rembi
```

The engine has no microscopy-specific code. A check is a function `(context, params) -> [Issue]`
registered with `@check("name")`. `microscopy-metadata-repair` can import
`micro_validate.engine` and register its own checks, or run these rule sets after a repair
to confirm the fix.

## Not done yet / known limits

- Excel (`.xlsx`) file lists are detected but not parsed. Export them as TSV.
- REMBI fields come from a local `submission.yaml` or a BioStudies page-tab JSON export. Nothing is fetched from the BIA web form.
- OME-Zarr HCS plates and `bioformats2raw` containers are reported as "not checked", with no per-image checks yet.
- Vendor formats other than LSM, STK, MetaMorph and FluoView TIFF need `micro-validate[vendor]` plus a bioio reader plugin. Without it they are reported as "readability not checked" (warn).
- PNG/JPEG files get a header check only.
- On Python 3.9 (zarr 2.x), zarr v3 / NGFF 0.5 arrays are checked from metadata only, with no pixel decode.
- Ontology terms (NCBITaxon, FBbi) are checked for form only, not looked up.
- Series consistency is checked per folder and per format. Unrelated images of the same format in one folder are reported as a warning.
- *Image files readable* is "needs review": a reader can still miss valid files in formats not seen in evaluation.
- Images inside `.zip` archives and files in formats the tool does not know (e.g. NRRD, HDF5) are listed as "not checked".
- The BioImage Archive does not publish a closed list of accepted formats. In the `bia` rules, OME-TIFF, zipped OME-Zarr and TIFF pass, and other formats warn.
