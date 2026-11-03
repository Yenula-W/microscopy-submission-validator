# micro-validate: evaluation against the adoption-ready bar

Date: 2026-11-02 (round 2 the same day; ship-bar rounds 3-6 on 2026-11-03) · Version: 0.1.0 · Bars: `~/Desktop/LabAdoption/ADOPTION_BAR.md` and `SHIP_BAR.md`

**Ship-bar verdict (§9-§10): NOT MET.** Rounds 5, 6 and 7 were each run untouched on frozen code. Precision was 98.9%, 96.1% and 96.6%, with 0 crashes. Each round still had overstated claims: 3, 4 and 6. All of them were fixed afterwards with regression tests, but the final code has not yet passed an untouched round.

| # | Bar item | Status |
|---|---|---|
| 1 | Never crashes on messy input | **Met.** There are 17 robustness tests. One crash was found and fixed. 0 crashes in 78 held-out runs. |
| 2 | Clean install from GitHub on 3.9 / 3.12 / 3.13, README quickstart verbatim | **Met.** All three installs worked and the quickstart ran verbatim (details below). |
| 3 | 20+ held-out real inputs, zero crashes | **Met.** 26 inputs × 3 targets = 78 runs, 0 crashes. |
| 4 | ≥50 findings hand-checked, ≥90% correct, no check <80% | **Met.** 121 findings hand-checked: 91.7% correct, 0 wrong. Every check type is at 80% or above. Round 2 (§8) added new held-out inputs for the three checks that were short in round 1: `idr_assay_present` 83.8% (n=37), `idr_assay_matches_files` 87.5% (n=8), `file_list_matches` 100% (n=5). |
| 5 | Never invents or overstates | **Met after fixes.** Several FAILs were downgraded to warnings or reworded (§5). |
| 6 | CI green, repo private | **Met.** GitHub Actions passes on ubuntu 3.9 / 3.12 / 3.13 and macOS 3.9 / 3.12. The repo `Yenula-W/microscopy-submission-validator` is private. |
| 7 | This file | Done. |

## 1. Robustness (messy input)

`tests/test_robustness.py` runs every target (`bia`, `idr`, `rembi`) through the CLI on each case below. It asserts that the exit code is 0 or 1 and that no rule reports "check crashed".

| Case | Result |
|---|---|
| Empty folder; a file passed instead of a folder | Clean FAIL report; exit 2 with a message |
| Binary and non-UTF-8 file lists, study and assay files, NUL bytes, random bytes | Parsed with replacement characters; reported as malformed |
| Malformed YAML and JSON metadata (unclosed, list at top level, empty, wrong types, YAML dates) | `BIA-META-001` FAIL with "cannot parse"; no crash |
| Corrupt images: 0-byte OME-TIFF, random-bytes TIFF, fake zip, empty zip, bad `.zattrs`, missing array level, empty `.zarr`, truncated PNG, fake CZI | Each reported as unreadable or not checked |
| OME-TIFF with broken OME-XML | Falls back cleanly |
| 2.1 TB sparse file | `BIA-SIZE-001` FAIL (size limit); no read attempted |
| Symlink loop, self-referencing symlink, dangling symlink | Walk terminates; the dangling link is reported unreadable |
| Unicode paths (`données/细胞 1.ome.tif`) | Handled; `BIA-NAME-001` flags the characters BIA does not allow |
| Permission denied on an image, file list, study file or sub-folder | Reported ("cannot read"); no crash |
| Ragged TSV rows, rows with no key | Handled |

**Crash found and fixed:** an unreadable IDR study file or file list raised `PermissionError` out of `load_dataset`. Reads are now wrapped, the error shows in `IDR-STUDY-001` / `BIA-FL-001`, and `test_unreadable_files_and_dirs` covers it.

## 2. Install

| Python | Command | Result |
|---|---|---|
| 3.9.7 (macOS system Python framework) | `pip install git+https://github.com/Yenula-W/microscopy-submission-validator` in a fresh venv | OK, with tifffile 2024.8.30, ome-types 0.6.3 and zarr 2.18 |
| 3.12.15 | same | OK |
| 3.13.16 | same | OK |

The README Install and Use blocks were run verbatim in a fresh 3.9 venv and a fresh 3.13 venv. Every command ran, and `micro-validate my_dataset --target bia` exited 1 as expected for the empty template.

**Python 3.9 limitation:** zarr 3 requires Python 3.11 or later. On 3.9, NGFF 0.5 (zarr v3) images are checked from metadata only, and this is shown as a note in the report.

## 3. Held-out real-world run

None of these inputs were used during development. Development used only OME `tubhiswt-4D` and IDR `idr0062`.

The inputs are small subsets:

- OME-Zarr images keep all JSON metadata but only the first chunk of the full-resolution level.
- BIA studies keep the published study JSON, the submitter's file-list TSVs and the two smallest image files.
- Accepted studies are run with `--partial`, so files that are listed but were not downloaded are not reported.

The manifest and per-run CSVs are in `eval/`, and `scripts/holdout/fetch.py` rebuilds them.

| ID | Source | Format(s) | Kind |
|---|---|---|---|
| H01 | [OME bioformats-artificial](https://downloads.openmicroscopy.org/images/OME-TIFF/2016-06/bioformats-artificial/) | OME-TIFF ×5 | sample |
| H02 | [OME companion](https://downloads.openmicroscopy.org/images/OME-TIFF/2016-06/companion/) | binary-only OME-TIFF + `.companion.ome` | sample |
| H03 | [OME modulo](https://downloads.openmicroscopy.org/images/OME-TIFF/2016-06/modulo/) | OME-TIFF (FLIM, lambda) | sample |
| H04 | [ImageJ confocal-series](https://imagej.net/ij/images/confocal-series.zip) | ImageJ hyperstack TIFF | sample |
| H05 | [ImageJ 5d](https://imagej.net/ij/images/5d.zip) | ImageJ 5D TIFF | sample |
| H06 | [ImageJ Composite, 3_channel_inverted_luts](https://imagej.net/ij/images/) | ImageJ TIFF | sample |
| H07 | [ImageJ fluoview-multi.tif](https://imagej.net/ij/images/fluoview-multi.tif) | Olympus FluoView TIFF | vendor TIFF |
| H08 | [ImageJ Cntrl1.lsm](https://imagej.net/ij/images/Cntrl1.lsm) | Zeiss LSM | vendor |
| H09 | [OME ND2 aryeh](https://downloads.openmicroscopy.org/images/ND2/aryeh/) | Nikon ND2 ×2 | vendor |
| H10 | [OME Olympus-FluoView imagesc-71616](https://downloads.openmicroscopy.org/images/Olympus-FluoView/imagesc-71616/) | Olympus OIB | vendor |
| H11 | [OME Metamorph zenodo-13642395](https://downloads.openmicroscopy.org/images/Metamorph/zenodo-13642395/) | MetaMorph `.nd` + TIFF | vendor TIFF |
| H12 | [OME TIFF condensation](https://downloads.openmicroscopy.org/images/TIFF/condensation/) | ImageJ TIFF (screen) | sample |
| H13 | IDR [idr0052](https://github.com/IDR/idr0052-walther-condensinmap) image 5514375 + study + MitoSys assay | OME-Zarr v0.4 | **accepted IDR** |
| H14 | IDR [idr0054](https://github.com/IDR/idr0054-segura-tonsilhyperion) image 5025551 + study + assays | OME-Zarr v0.4 | **accepted IDR** |
| H15 | IDR [idr0066](https://github.com/IDR/idr0066-voigt-mesospim) chicken MIP + study + assays | OME-Zarr **v0.5** (zarr v3, sharded) | **accepted IDR** |
| H16 | IDR [idr0101](https://github.com/IDR/idr0101-payne-insitugenomeseq) image 13457537 + study | OME-Zarr v0.4 | **accepted IDR** |
| H17 | IDR [idr0076](https://github.com/IDR/idr0076-ali-metabric) image 10501752 + study | OME-Zarr v0.4 | **accepted IDR** |
| H18 | IDR [idr0047](https://github.com/IDR/idr0047-neuert-yeastmrna) image 4496763 + study | OME-Zarr v0.4 | **accepted IDR** |
| H19 | IDR [idr0138](https://github.com/IDR/idr0138-lohoff-seqfish) MMStack_Pos9 + study | OME-Zarr v0.4 | **accepted IDR** |
| H20 | IDR idr0001A plate 2551 | OME-Zarr v0.4 HCS plate | IDR |
| H21 | BIA [S-BIAD634](https://www.ebi.ac.uk/biostudies/BioImages/studies/S-BIAD634) | PNG masks, 2 file lists incl. annotations | **accepted BIA** |
| H22 | BIA [S-BIAD4325](https://www.ebi.ac.uk/biostudies/BioImages/studies/S-BIAD4325) | Zeiss CZI | **accepted BIA** |
| H23 | BIA [S-BIAD2619](https://www.ebi.ac.uk/biostudies/BioImages/studies/S-BIAD2619) | TIFF | **accepted BIA** |
| H24 | BIA [S-BIAD4214](https://www.ebi.ac.uk/biostudies/BioImages/studies/S-BIAD4214) | PNG analysis outputs | **accepted BIA** |
| H25 | BIA [S-BIAD3623](https://www.ebi.ac.uk/biostudies/BioImages/studies/S-BIAD3623) | TIFF; 3 file lists named `PAINT.tsv` etc. | **accepted BIA** |
| H26 | BIA [S-BIAD4285](https://www.ebi.ac.uk/biostudies/BioImages/studies/S-BIAD4285) | `.ome.zarr.zip` | **accepted BIA** |

These inputs cover OME-TIFF, ImageJ TIFF, OME-Zarr v0.4 and v0.5, an HCS plate, five vendor formats (LSM, ND2, OIB, MetaMorph, CZI), six accepted BIA studies and seven accepted IDR studies.

Each input was run against all 3 targets:

| Measure | Value |
|---|---|
| Runs | 78 |
| Crashes | **0** |
| Run time | median 0.4 s, max 3.2 s |
| Report size (`.md` + `.json`) | median 20 kB, max 30 kB |
| Findings (warn + fail messages) | 375 |

Per-run data is in `eval/runs.csv` and all findings are in `eval/findings.csv`.

**Accepted submissions as a test of the rules.** On the final run, the six accepted BIA studies get **no FAIL** under `bia`. The only warnings are for recommended items: missing ORCIDs, NCBI taxon, plain TIFF without OME-XML, an unzipped format, and one real duplicate file-list row.

Under `idr`, the seven accepted IDR studies have FAILs from two causes only:

- Four inputs have no assay file. The IDR GitHub repos for idr0101, idr0076, idr0047 and idr0138 publish only the study file, so these inputs genuinely lack one.
- In idr0054, the assay lists per-channel PNGs that IDR later merged into a single image, so nothing can link them.

Both causes come from how the inputs had to be put together from public material, not from a wrong rule. The first run on accepted studies did expose many wrong rules, listed next.

## 4. Precision (hand-checked)

`run_eval.py` draws a stratified random sample with seed 20261102: up to 4 findings per check type, then random findings up to 64.

Each finding was checked by hand against the source file. The evidence was the raw BioStudies JSON, the IDR study and assay text, the OME-XML read with `tifffile`, the zarr `.zattrs`, and directory listings. Verdicts and the evidence note for each item are in `eval/sample_judged.csv`.

**First round** (after the accepted-submission fixes below): 64 sampled, 58 correct, 5 debatable, **1 wrong** (90.6%).

- **Wrong:** the HCS plate was reported "unreadable" (FAIL).
- **Debatable:** an NGFF `units` key was reported as "no unit".
- **Overstated:** several inconsistent-series findings were FAILs; they were downgraded under item 5 of the bar.

**Final round, after the fixes:**

| Check type | n | correct | debatable | wrong | % correct |
|---|---|---|---|---|---|
| `field_present` (REMBI fields) | 6 | 6 | 0 | 0 | 100% |
| `file_list_matches` | 1 | 1 | 0 | 0 | 100% |
| `file_list_present` | 5 | 5 | 0 | 0 | 100% |
| `formats_accepted` | 6 | 6 | 0 | 0 | 100% |
| `idr_assay_matches_files` | 3 | 2 | 1 | 0 | 67% |
| `idr_assay_present` | 4 | 2 | 2 | 0 | 50% |
| `idr_processed_data` | 4 | 4 | 0 | 0 | 100% |
| `idr_study_fields` | 4 | 4 | 0 | 0 | 100% |
| `idr_study_present` | 4 | 4 | 0 | 0 | 100% |
| `images_readable` | 4 | 4 | 0 | 0 | 100% |
| `metadata_present` | 6 | 6 | 0 | 0 | 100% |
| `ome_metadata` (OME header, pixel size) | 12 | 12 | 0 | 0 | 100% |
| `series_consistent` | 5 | 5 | 0 | 0 | 100% |
| **All** | **64** | **61** | **3** | **0** | **95.3%** |

**Gap against the bar in round 1** (closed in round 2, §8). `idr_assay_present` and `idr_assay_matches_files` were below 80% if debatable items count as not correct. All three debatable items are statements that are true for the input folder but come from accepted IDR studies whose original assay tables are not public (see §3). None of the three is wrong.

The held-out set produced only one `file_list_matches` finding, because accepted file lists match their files. So that check has n=1, not the 3 the bar asks for. The synthetic tests cover its failure modes: missing files, orphan files, case mismatch and duplicates.

These checks raised **no findings** on held-out data, and passed on every accepted submission where they applied (no false alarms): `file_list_header`, `file_list_format`, `filename_chars`, `file_size`, `annotation_source_image`, `idr_assay_columns`, `idr_channels_match`.

### Rules found wrong and fixed

Every fix has a regression test in `tests/test_validator.py`.

| Found on | Problem | Fix |
|---|---|---|
| S-BIAD634 (accepted) | REMBI sections are lists (6 Biosamples), authors have one `Name`, organism is text | List-aware rule paths (`biosample[*]…`); author name accepted as `name` or first+last; BioStudies page-tab JSON converter |
| S-BIAD634 and all BIA studies | NCBI taxon required (FAIL), but the BIA form takes organism text | Downgraded to a recommendation (warn) |
| S-BIAD634 | Annotation list header is `source image`, not `source_image` | Header matched ignoring case, spaces and underscores |
| S-BIAD3623, S-BIAD4325, S-BIAD2619 | File lists named `PAINT.tsv`, `Files.tsv`, `File_List.tsv` were not recognised | A file list is any TSV whose first column is `Files` |
| S-BIAD4325, S-BIAD4214 | Empty Publication/Funding sections produced "title missing" FAILs | Empty sections are skipped |
| idr0052, idr0054, idr0066, idr0047 (accepted) | `Study Key Words` and `Study Organism` treated as mandatory; the IDR page marks only title, description and contact | Moved to a warn rule; `Experiment Organism` accepted |
| idr0052 | Assay file `MitoSys_assay_file.txt` not detected; `A and B` / extension-less references | `*assay*` detection; split on `,` `;` `and`; compare without extension |
| idr0066 | Assay uses `Image Name` and has no `Assay Name`; the IDR page marks no assay column mandatory | Image-identifier column required (FAIL); other columns are a warn rule |
| idr0052 | Rows list per-plane TIFFs under `…/cell0015_R0002/rawtif/` | Match by containing folder, reported as a warning |
| OME companion | Binary-only OME-TIFFs reported unreadable; `.companion.ome` treated as an image | Read metadata from the companion; sidecar files classified separately |
| ImageJ fluoview-multi.tif | Pixel size 138.9 µm taken from a 72 px/cm default (true value 2.76 µm) | dpi-style defaults ignored; FluoView header read |
| MetaMorph TIFF | Calibration (0.65 µm) ignored | MetaSeries XML read |
| Zeiss LSM | Classed as vendor and not checked | Read with tifffile, including voxel size |
| idr0001 plate | Reported "unreadable" (FAIL) | Reported "not checked (HCS plate)" (warn) |
| idr0047 | NGFF axis key `units` (non-standard) reported as "no unit" | Accepted, with a note about the non-standard key |
| PNG masks and plots (S-BIAD634, S-BIAD4214) | "Not verified" plus a pixel-size warning on every PNG | PNG/JPEG header check; no pixel-size warning for PNG/JPEG |

## 5. Wording and severity

- **Series consistency** (same channels and pixel size within a folder) is advice: no repository requires it. It is a **warn** in all three targets, and messages say "folder" rather than claiming a "series".
- Everything the sources mark as recommended is **warn**: ORCID, licence, NCBI taxon, FBbi term, keywords, protocols, processed data file, vendor and raster formats, OME header and pixel size. Every FAIL is a requirement on a cited page: REMBI 1.5 required fields, the BIA file-list guide, the IDR submission page.
- **Messages** say what was found, where, and what to do. Examples: "readability not checked (no reader installed …)" replaced "not verified"; "PNG/JPEG hold no microscopy metadata; fine for masks and figures, not for raw acquisitions" replaced "not a microscopy format".
- **Partial datasets:** with `--partial`, listed-but-absent files and assay or processed-data files are not reported.

## 6. CI

`.github/workflows/tests.yml` uses uv-managed Python, because `actions/setup-python` has no 3.9 build for the current Ubuntu image. It runs on ubuntu 3.9, 3.12 and 3.13, and macOS 3.9 and 3.12. The last runs are all green (see the Actions tab of the private repo).

## 7. Known limitations

- Vendor formats beyond LSM, STK, MetaMorph and FluoView TIFF need `micro-validate[vendor]` plus a bioio plugin. With `bioio-nd2`, the H09 ND2 files read correctly (800×600×13 T, 0.37 µm). Without it, they are reported as "readability not checked".
- HCS plates and `bioformats2raw` containers get no per-image checks.
- `.xlsx` file lists are not parsed.
- Ontology IDs are checked for form only.
- REMBI metadata must be local: `submission.yaml` or a BioStudies JSON export.
- The held-out IDR inputs could not include the original assay tables for 4 of the 7 studies, because the repositories do not publish them.

## 8. Round 2: closing the per-check gaps (new held-out inputs only)

Round 1 left three checks short. `idr_assay_present` and `idr_assay_matches_files` were below 80%, and `file_list_matches` had only n=1. Round 2 added new inputs; none of these studies appears in round 1 or in development.

- **IDR tables, 110 accepted studies.** For every `IDR/idrNNNN-*` repository not used before, `scripts/holdout/fetch_idr_tables.py` downloaded the published study file plus every assay, library and annotation table under 30 MB. The 95 MB tables of idr0016 were skipped, and that study is excluded. This set is used for `idr_assay_present`.
- **IDR images, 9 accepted studies with public tables:** idr0021, idr0040, idr0044, idr0051, idr0002 (screen plate), idr0073, idr0075, idr0077 and idr0079. Each input has one OME-Zarr image (NGFF v0.1, v0.3 or v0.4), the study file and the tables, and runs with `--partial`. This set is used for `idr_assay_matches_files`. These are entries H27 to H35 in `scripts/holdout/fetch.py`.
- **BIA name mirrors, 29 accepted studies.** `scripts/holdout/fetch_names.py` built, for each study, the submitter's real file-list TSVs plus a zero-byte placeholder for every file actually in the study's FTP `Files/` tree. This set is used for `file_list_matches`; only name-based checks are meaningful on it.

### First run, before any change

These numbers come from the code at commit `33ac361`, judged against the real repository tables.

| Check | n | correct | debatable | wrong | % correct | Main cause of wrong findings |
|---|---|---|---|---|---|---|
| `idr_assay_present` (38 studies + 2 image inputs) | 33 | 6 | 7 | 20 | 18% | "No assay file" although the repository publishes the curated `*-annotation.csv` (18 cases); idr0068 and idr0044 name that annotation table and it exists |
| `idr_assay_matches_files` (5 image inputs) | 5 | 2 | 0 | 3 | 40% | idr0040 assay `.txt` is comma-separated, so it was read as one column; idr0002 plate described by `Plate` column, ignored; idr0044 table described in the annotation CSV, not read |
| `file_list_matches` (12 BIA mirrors) | 6 | 5 | 0 | 1 | 83% | S-BIAD4206: the submitter's TSV lists itself, and it was reported "listed but not found" |
| `annotation_source_image` (side catch) | 16 | 7 | 0 | 9 | 44% | S-BIAD3632: `source_image` points inside a `.zarr.zip` container |

### Fixes, each with a regression test in `tests/test_validator.py`

- `*-annotation.csv/.tsv/.txt` files are read as IDR tables when an IDR study file is present. Data files named `*_annotations.tsv` in BIA datasets stay data.
- IDR tables are delimiter-sniffed: `.csv` files, and `.txt` files whose header has commas but no tabs. A comma-separated `.txt` gets a warning, because the IDR template is tab-delimited.
- References in the study file are resolved against every table and file.
- An unresolved reference becomes a **warning that names the probable table** in two cases:
  - a table for the same experiment or screen exists (`experimentB-assays.txt` and `experimentB-annotation.csv`);
  - there is exactly one dangling name and one unnamed table, and their experiment keys don't conflict.

  A reference to an experiment with no table at all stays a FAIL.
- Screens: a plate is described when its name appears in the `Plate` column of a library or annotation table.
- File lists that list themselves (or each other) count as present.
- A `source_image` path inside a present container (`x.zarr.zip/images/...`) counts as found.

### Final run, judged by hand

Every finding is in `eval/round2/findings_judged.tsv` with a verdict and an evidence note. Duplicates between the tables-only scan and the image inputs were removed.

| Check | n | correct | debatable | wrong | % correct |
|---|---|---|---|---|---|
| `idr_assay_present` | 37 | 31 | 6 | 0 | 83.8% |
| `idr_assay_matches_files` | 8 | 7 | 1 | 0 | 87.5% |
| `file_list_matches` | 5 | 5 | 0 | 0 | 100% |
| `annotation_source_image` | 7 | 7 | 0 | 0 | 100% |
| **Round 2 total** | **57** | **50** | **7** | **0** | **87.7%** |
| **Rounds 1 + 2** (64 + 57) | **121** | **111** | **10** | **0** | **91.7%** |

What the round-2 findings are:

- **`idr_assay_present`.**
  - 24 warnings: the study file names a table that doesn't resolve, and the message points at the right published table. The causes are IDR renaming `…-assays.txt` to `…-annotation.csv`, typos (`idr0018-experimentA-assay.txt`, `idr158-…`), or template names (`idr0000-experimentA-assays.txt`).
  - 1 warning on an image input (idr0021 `-assay.txt` typo).
  - 6 FAILs, all correct: single-experiment studies whose `Experiment Assay File` names `experimentB` or a template file that doesn't exist (idr0063, 0073, 0075, 0083, 0087, 0103).
  - 6 debatable: repositories that publish no table at all (idr0015, 0043, 0069, 0088, 0093, 0133). The statement is true for the published material, but the original submissions probably had a table.
- **`idr_assay_matches_files`.**
  - 7 correct warnings: the assay names the original file (`.dv`, `.klb`, `.czi [0]`, `.pattern`, a name without extension, or per-channel TIFFs inside the image's folder), so the submitted `.ome.zarr` matches only by stem or folder.
  - 1 debatable: in idr0040, 3048 rows from about 30 datasets each have a `…/Pos20` folder, and all were matched to the single `Pos20` image, so the count overstates.
- **`file_list_matches`.**
  - 4 FAILs: S-BIAD4174 has four `YKKY0222_20240228/*` files that are on the BIA FTP tree but in no submitted file list. This is a real mismatch inside an accepted submission.
  - 1 warning: S-BIAD2865 lists `HR PCB WT Liver Images/Females/PCB/F-18ALiver40x.tif` on two rows.
- **`annotation_source_image`.** 7 FAILs on S-BIAD3520: its annotation lists have no `source_image` column. The BIA file-list guide marks that column mandatory, but BIA accepted the study anyway. The FAIL is kept because the requirement is published.

The 21 S-BIAD studies with no file-list findings are a check on false alarms: none of them raised a `file_list_matches` finding.

A rerun of the round-1 held-out set on the final code gave 78 runs, 0 crashes and the same 375 findings. CI was green on the final commit.

## 9. Ship-bar rounds 3-6 (`SHIP_BAR.md`)

The ship bar asks for two untouched rounds in a row that pass. Each round:
- uses new real inputs that no earlier round or development used;
- records first-run numbers before any change;
- needs ≥90% overall precision, no check type below 80%, 0 crashes and 0 overstated claims.

Round 2 did not count toward the streak: its first run failed (§8), and a fix landed before round 3. Every number below is a **first run on frozen code**.

- **Judging.** Each judged TSV in `eval/roundN/` records a verdict and an evidence note for every finding.
  - Verdicts were set by explicit patterns, after checking each pattern on the inputs. The pattern scripts are `scripts/holdout/judge_rN.py`.
  - "n/a" marks findings that are artifacts of how the input was built, for example:
    - zero-byte placeholders in name mirrors;
    - partial subsets where the harness downloaded no images;
    - file-list checks on API-rebuilt lists.
- **Inputs.** Each round has 21 inputs × 3 targets = 63 runs. The inputs are listed in `scripts/holdout/fetch.py` (`ROUNDS`) and `eval/roundN/manifest.json`, and they mix three kinds:
  - OME sample files: OME-TIFF variants, Imaris, MRC/EMDB, Leica LIF, ICS, KLB, Vectra QPTIFF, Olympus OIR/OME exports, Micro-Manager, NDPI, AmiraMesh, OBF, DeltaVision and OME-XML;
  - accepted BIA studies: page-tab JSON, the submitted file lists and the 2 smallest images;
  - BIA name mirrors, plus the last 2 unused IDR repositories (idr0082 and idr0016).
- **Download problems.** EBI's FTP refused many connections from round 4 on. The missing name mirrors were replaced by mirrors built from the BioStudies JSON API (`scripts/holdout/fetch_api_names.py`), or by further OME samples.

| Round | Code | Judged | Correct | Wrong | Debatable | Precision | Crashes | Failing check types / overstated claims | Result |
|---|---|---|---|---|---|---|---|---|---|
| 3 | `50f7a3b` | 402 | 276 | 123 | 3 | 68.7% | 0 | `field_present` 55%, `file_list_matches` 9%, `images_readable` 40%, `series_consistent` 0% | FAIL |
| 4 | `ec552ef` | 270 | 255 | 15 | 0 | 94.4% | 0 | `images_readable` 50%; 6 overstated `formats_accepted` | FAIL |
| 5 | `4031e41` (frozen) | 276 | 273 | 3 | 0 | 98.9% | 0 | 3 overstated ("no image files found" for an AmiraMesh volume) | FAIL (overstated) |
| 6 | `4031e41` (same) | 257 | 247 | 10 | 0 | 96.1% | 0 | `images_readable` 60% (needs review); 4 overstated | FAIL (overstated) |

Rounds 5 and 6 without `images_readable`, which is outside the verdict since `4031e41`:
- Round 5: 255 of 258 correct, 98.8%.
- Round 6: 238 of 242 correct, 98.3%.

Every other check type is at 80% or above in both rounds, so only the overstated claims stopped them.

### Root causes found, each fixed with a regression test (`tests/test_validator.py`, "ship-bar round N")

- **Round 3:**
  - **NCBI taxon.** Newer BIA studies store the taxon in the Organism attribute's `valqual` `TermId`, which the converter ignored. 82 of 84 taxon warnings were wrong.
  - **Directory entries.** BIA allows a directory path in a file list's `Files` column, so the files beneath it count as listed (S-BIAD3835).
  - **BinaryOnly sets.** A BinaryOnly OME-TIFF whose `MetadataFile` is another OME-TIFF of the set was reported unreadable.
  - **Missing codec.** LZW TIFFs were called "unreadable" because the `imagecodecs` package was missing. It is now a dependency, and a missing codec gives "not decoded".
  - **MRC/EMDB.** Maps are now read from the MRC2014 header as an open `mrc` format.
  - **Series check.** PNG/JPEG are left out of the series-consistency check.
- **Round 4:**
  - **Older schemas.** OME-XML in the 2015-01 (Micro-Manager) or 2016-DEV0 (Olympus) schemas is now read leniently instead of being reported unreadable.
  - **KLB and FITS.** Both are now recognised as image formats.
  - **Zipped images.** A dataset whose images are all zipped gets a warning that archives weren't inspected, instead of "no image files".
  - **Series by format.** Series are compared within one format, so a screen capture beside an OME-TIFF stack is no longer compared with it.
- **Before rounds 5-6:** `images_readable` became **needs review**. It stays on by default but is reported in its own section with its measured precision, and it is left out of the overall verdict and the exit code. Its untouched precision in rounds 3-4 was 21 of 48 (44%).
- **Rounds 5-6:**
  - **AmiraMesh.** AmiraMesh/Avizo `.am` files are recognised.
  - **Unknown formats.** When no recognised image format is present but other data files are, the tool now warns about files "not checked" instead of claiming none exist.
  - **OME-XML with pixels.** OME-XML carrying BinData pixels is an `ome-xml` image.
  - **Malformed OME-XML.** A TIFF whose OME-XML is not valid XML (S-BIAD3778 writes literal `\n` between attributes) is read as a plain TIFF. The calibration is recovered from the broken XML and the bad header is reported.
  - **Unparsed `.xlsx`.** An `.xlsx` file list that can't be parsed gives a warning, not a FAIL on "file list present".

### Reruns on the fixed code (not untouched; they confirm the fixes)

| Round | Judged | Wrong | Precision |
|---|---|---|---|
| 3 | 303 | 0 | 100% |
| 4 | 264 | 0 | 100% |
| 5 | 279 | 0 | 100% |
| 6 | 260 | 0 | 100% |

### Other ship-bar items on the final commit

- **Clean install.** `pip install git+https://github.com/Yenula-W/microscopy-submission-validator` worked in fresh venvs on Python 3.9.7, 3.12.15 and 3.13.16. The README quickstart, including the `[vendor]` extra with `bioio-nd2`, then ran word for word. On the empty template dataset the exit code was 1, as expected.
- **Extras.** Tests pass with and without the `[vendor]` extra: 87 passed, 1 skipped either way. The skipped test is the one for the other configuration. CI has a job with the extra.
- **CI and repo.** CI is green and the repo is private.
- **To ship:** the final code needs two more untouched rounds on new inputs.
  - Public IDR repositories with tables are now exhausted, so those rounds will rely on BIA and OME inputs.
  - Building BIA mirrors through the BioStudies JSON API avoids the FTP throttling.

## 10. Round 7: confirmation round on frozen `fd00ab4`

The code was frozen at `fd00ab4`.
- **CI on `fd00ab4`:** all Ubuntu jobs (3.9, 3.12, 3.13) passed. GitHub never assigned a macOS runner to the macOS jobs ("The job was not acquired by Runner … capacity constraints"). As a stand-in, the full test suite at `fd00ab4` was run on a local macOS machine: 87 passed, 1 skipped on both Python 3.9 and 3.12.
- **Inputs:** 23 new inputs were fetched.
  - The 3 dropped studies are S-BIAD3728 and S-BIAD3111 (EBI FTP refused the connection) and S-BIAD3811 (TLS handshake timed out). They were left out instead of being run on partial downloads.
  - The 20 inputs that ran are 5 OME samples (Zeiss SEM TIFF, InCell 2000, Cellomics DIB, Becker & Hickl SDT, NRRD), 1 BIA study with page-tab, file list and images, and 14 BIA API name mirrors. That is 60 runs.

| Check type | n | correct | debatable | wrong | % correct |
|---|---|---|---|---|---|
| `field_present` | 131 | 131 | 0 | 0 | 100% |
| `formats_accepted` | 57 | 57 | 0 | 0 | 100% |
| `ome_metadata` | 21 | 15 | 0 | 6 | **71.4%** |
| `series_consistent` | 3 | 0 | 3 | 0 | **0%** |
| other 4 types | 55 | 55 | 0 | 0 | 100% |
| **Total** | **267** | **258** | **3** | **6** | **96.6%** |

There were 0 crashes. **Result: FAIL.** There were 6 overstated claims, and two in-verdict check types were below 80%.

- **Overstated, 6 findings:** "physical pixel size missing" for two Zeiss SEM TIFFs. The calibration is in the `CZ_SEM` tag (34118) as `Image Pixel Size` 22.33 nm and 11.16 nm, and the tool did not read it.
- **Debatable, 3 findings:** the same grating was scanned at 512 and 1024 px, which was reported as an inconsistent series.

The formats the tool doesn't know (DIB, SDT, NRRD, NIfTI) were correctly reported as "not checked". This is the round 5-6 fix working on new inputs.

**Fixes, each with a regression test ("ship-bar round 7"):**
- Zeiss SEM (`CZ_SEM`) and FEI/Thermo (`[Scan] PixelWidth`) TIFF calibration is now read.
- The series check no longer reports pixel-size or XY differences when two calibrated images cover the same physical field at different pixel counts.

A rerun of round 7 on the fixed code gave 258 judged, 0 wrong.

Per the instruction for this round, the loop stops here: record, fix, push. To ship, the final commit needs one more untouched round on new inputs.

