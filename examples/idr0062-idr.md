# Submission check: Image Data Resource (IDR)

**Overall: FAIL** — 12 pass, 2 warn, 2 fail, 1 skipped

- Dataset: `<scratch>/sub/idr0062` (1 images, 1 data files)
- Metadata: `none`
- IDR study: `idr0062-study.txt`; assays: `idr0000-experimentD_assays.txt`, `idr0000-experimentA_assays.txt`, `idr0000-experimentC_assays.txt`, `idr0000-experimentE_assays.txt`, `idr0000-experimentB_assays.txt`
- Rules retrieved: 2026-11-02 · micro-validate 0.1.0

## Fix list

1. **[FAIL] IDR-STUDY-002 Mandatory study description fields** — Fill in the Study Title, Study Description, Study Key Words and Study Organism lines (replace '#' hints).
   - idr0062-study.txt: 'Study Key Words' missing or still a template hint
2. **[FAIL] IDR-ASSAY-003 Every image described by an assay row, every row resolves to an image** — Add a row per image (exact file name) and remove rows for images not submitted.
   - 1 row(s) matched only by name stem (different extension); update 'Image File' to the submitted file names
   - idr0000-experimentD_assays.txt: Image File 'E75_Zone_1.tif' not found in dataset
   - idr0000-experimentD_assays.txt: Image File 'E75_Zone_2.tif' not found in dataset
   - idr0000-experimentD_assays.txt: Image File '161202_E75.tif' not found in dataset
   - idr0000-experimentA_assays.txt: Image File '130520_Neural_Rosettes.tif' not found in dataset
3. **[WARN] IDR-EXP-004 Processed data file declared** — Listed as mandatory on the IDR experiments page, though IDR has accepted datasets without one. Declare and include the processed data file (summary results / hit list) and describe its columns.
   - study file declares no 'Processed Data File Name'
4. **[WARN] IDR-ASSAY-004 Channels column agrees with image channel count** — List one label:target pair per channel, separated by ';'.
   - B1_C1.tif: Channels lists 1 channel(s) but image has C=2

## All rules

| Status | Rule | Check | Details | Source |
|---|---|---|---|---|
| PASS | IDR-STUDY-001 | Study file present |  | [1](https://idr.openmicroscopy.org/about/submission.html) [2](https://github.com/IDR/idr0000-lastname-example) |
| FAIL | IDR-STUDY-002 | Mandatory study description fields | idr0062-study.txt: 'Study Key Words' missing or still a template hint | [1](https://idr.openmicroscopy.org/about/experiments.html) [2](https://github.com/IDR/idr0000-lastname-example) |
| PASS | IDR-STUDY-003 | Primary contact |  | [1](https://idr.openmicroscopy.org/about/experiments.html) [2](https://github.com/IDR/idr0000-lastname-example) |
| PASS | IDR-STUDY-004 | Licence stated |  | [1](https://idr.openmicroscopy.org/about/submission.html) [2](https://github.com/IDR/idr0000-lastname-example) |
| PASS | IDR-STUDY-005 | Publication reference |  | [1](https://idr.openmicroscopy.org/about/submission.html) |
| PASS | IDR-EXP-001 | Experiment/screen description |  | [1](https://idr.openmicroscopy.org/about/experiments.html) [2](https://idr.openmicroscopy.org/about/screens.html) |
| PASS | IDR-EXP-002 | Imaging method stated |  | [1](https://github.com/IDR/idr0000-lastname-example) |
| PASS | IDR-EXP-003 | Protocols described |  | [1](https://idr.openmicroscopy.org/about/experiments.html) |
| WARN | IDR-EXP-004 | Processed data file declared | study file declares no 'Processed Data File Name' | [1](https://idr.openmicroscopy.org/about/submission.html) [2](https://idr.openmicroscopy.org/about/experiments.html) |
| PASS | IDR-ASSAY-001 | Assay or library file present and linked from study file |  | [1](https://idr.openmicroscopy.org/about/submission.html) [2](https://idr.openmicroscopy.org/about/experiments.html) |
| PASS | IDR-ASSAY-002 | Assay file has required annotation columns |  | [1](https://idr.openmicroscopy.org/about/experiments.html) [2](https://github.com/IDR/idr0000-lastname-example) |
| FAIL | IDR-ASSAY-003 | Every image described by an assay row, every row resolves to an image | 1 row(s) matched only by name stem (different extension); update 'Image File' to the submitted file names; idr0000-experimentD_assays.txt: Image File 'E75_Zone_1.tif' not found in dataset; idr0000-experimentD_assays.txt: Image File 'E75_Zone_2.tif' not found in dataset … | [1](https://idr.openmicroscopy.org/about/experiments.html) |
| WARN | IDR-ASSAY-004 | Channels column agrees with image channel count | B1_C1.tif: Channels lists 1 channel(s) but image has C=2 | [1](https://idr.openmicroscopy.org/about/experiments.html) |
| PASS | IDR-FMT-001 | Images are OME-Zarr |  | [1](https://idr.openmicroscopy.org/about/submission.html) |
| PASS | IDR-IMG-001 | Image files readable |  | [1](https://idr.openmicroscopy.org/about/submission.html) |
| PASS | IDR-IMG-002 | Images carry physical pixel sizes |  | [1](https://idr.openmicroscopy.org/about/submission.html) |
| SKIP | IDR-IMG-003 | Consistent dimensions/channels/pixel sizes within a dataset | no series with 2+ readable images to compare | [1](https://idr.openmicroscopy.org/about/experiments.html) |

## Images read

| File | Format | Readable | XYZCT | dtype | Pixel size x/y/z (µm) |
|---|---|---|---|---|---|
| `Blastocysts/B1_C1.ome.zarr` | ome-zarr | yes | 271×275×236×2×1 | uint16 | 0.3604/0.3604/0.5002 |

## Sources

- **idr-submission**: [IDR - Submitting data](https://idr.openmicroscopy.org/about/submission.html)
- **idr-experiments**: [IDR - Experiment (non-screen) submission files](https://idr.openmicroscopy.org/about/experiments.html)
- **idr-screens**: [IDR - Screen submission files](https://idr.openmicroscopy.org/about/screens.html)
- **idr-templates**: [IDR example submission templates (idr0000-lastname-example)](https://github.com/IDR/idr0000-lastname-example)
