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
pip install -e .            # tifffile, ome-types, zarr, pyyaml, numpy
pip install -e '.[vendor]'  # optional: bioio, to read vendor formats (add a reader plugin, e.g. bioio-czi)
```

This needs Python 3.10 or later.

## Use

```bash
micro-validate my_dataset --target bia
micro-validate my_dataset --target idr --out reports/idr   # writes reports/idr.md + reports/idr.json
micro-validate my_dataset --target rembi --json
micro-validate --list-targets
micro-validate --template bia > my_dataset/submission.yaml
```

The exit code is 0 when nothing fails, 1 when any rule fails (with `--strict`, also on warnings), and 2 on a usage error.
Use `--no-pixels` to read headers only and skip decoding a pixel block per image.

### Dataset layout

```
my_dataset/
  submission.yaml          # REMBI metadata (bia, rembi). Get a template with --template bia
  file_list.tsv            # BIA file list: first column "Files", one row per file
  annotation_file_list.tsv # optional: BIA annotation list, needs a source_image column
  <name>-study.txt         # IDR study file (IDR template format)
  <name>-assays.txt        # IDR assay file, or *library*.txt for screens
  images/...               # .ome.tif, .ome.zarr/, .ome.zarr.zip, vendor files, ...
```

A `*.zarr` directory counts as one file. Every other file under the folder is a data
file, and the BIA file-list check expects it to be listed.

### Report

The Markdown report has these sections:

1. Overall status and counts.
2. **Fix list**: the failures first, then the warnings, each with example offending files.
3. A table of all rules with links to their sources.
4. The image metadata that was read: XYZCT, dtype, and pixel size in µm.

The JSON report has the same content, plus `images[]` with the full per-file details.

## Tested on real public data

`scripts/real_data_check.sh <scratch-dir>` downloads the data and repeats these runs:

| Dataset | Target | Result | What it found |
|---|---|---|---|
| OME sample `tubhiswt-4D` (86-file multi-file OME-TIFF, 512×512×10×2×43), raw folder | bia | FAIL | No REMBI metadata and no file list. Also found that **the OME-XML has no PhysicalSizeX/Y**: this is real, as the `<Pixels>` element has no physical sizes. |
| same, with `submission.yaml` and a generated `file_list.tsv` | bia / rembi | WARN | Only pixel sizes and ORCID remain. All 86 files are listed and readable, and the series is consistent. |
| same | idr | FAIL | IDR now requires OME-Zarr, so all 86 OME-TIFFs fail. There are also no study or assay files. |
| IDR `idr0062A` image 6001240 (OME-Zarr v0.4, 271×275×236×2) as `B1_C1.ome.zarr`, plus the **real** idr0062 study and assay files from GitHub | idr | FAIL | The study file has no `Study Key Words` line (it predates the template). The assays list 20+ images that are not in this one-image subset. `B1_C1.tif` matched the converted `.ome.zarr` by stem only. `Channels` holds `LaminB1 / Dapi` (1 entry) for a 2-channel image. No processed data file is declared. |
| same | bia | FAIL | Unzipped OME-Zarr (BIA wants `.ome.zarr.zip`), no metadata, no file list. |

`examples/` holds Markdown reports from these runs.

## Tests

```bash
pip install -e '.[dev]' && pytest
```

There are 30 tests. They build tiny synthetic OME-TIFFs and NGFF v0.4 OME-Zarrs (directory and zipped). They cover good and bad versions of each check type: missing or placeholder metadata, file-list header, format, missing and orphan files, case mismatch, bad characters, inconsistent channels and pixel sizes, plain TIFF, corrupt TIFF, unzipped zarr, annotation `source_image`, IDR hints, assay and channel mismatches, the CLI exit codes, and report output.

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

- Excel file lists (`.xlsx`) are detected but not parsed. Export them as TSV.
- The BIA web-form metadata is not fetched. REMBI fields come from your local `submission.yaml`, which mirrors the form.
- IDR HCS plates (OME-Zarr `plate` layout) and `bioformats2raw.layout` containers are reported as unreadable for per-image checks.
- Vendor formats can only be verified when `bioio` and a matching reader plugin are installed. Otherwise they are marked "unverified" (warn).
- Ontology terms (NCBITaxon, FBbi) are checked for form only, not looked up.
- The BioImage Archive does not publish a closed list of accepted formats. In the `bia` rules, OME-TIFF, zipped OME-Zarr and TIFF pass, and other formats warn.
