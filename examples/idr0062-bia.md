# Submission check: BioImage Archive (EMBL-EBI)

**Overall: FAIL** — 4 pass, 1 warn, 2 fail, 27 skipped

- Dataset: `<scratch>/sub/idr0062` (1 images, 1 data files)
- Metadata: `none`
- IDR study: `idr0062-study.txt`; assays: `idr0000-experimentD_assays.txt`, `idr0000-experimentA_assays.txt`, `idr0000-experimentC_assays.txt`, `idr0000-experimentE_assays.txt`, `idr0000-experimentB_assays.txt`
- Rules retrieved: 2026-11-02 · micro-validate 0.1.0

## Fix list

1. **[FAIL] BIA-META-001 Submission metadata file present** — Create submission.yaml in the dataset root (run `micro-validate --template bia > submission.yaml`).
   - no submission.yaml / submission.json found in dataset root
2. **[FAIL] BIA-FL-001 File list present** — Add a tab-separated file list named like file_list.tsv (one per study component).
   - no file list (*file_list*.tsv) found in dataset
3. **[WARN] BIA-FMT-001 Image formats** — Zip OME-Zarr folders (.ome.zarr.zip); prefer open OME formats over vendor files.
   - 1 ome-zarr file(s): OME-Zarr must be zipped and uploaded as .ome.zarr.zip: Blastocysts/B1_C1.ome.zarr

## All rules

| Status | Rule | Check | Details | Source |
|---|---|---|---|---|
| FAIL | BIA-META-001 | Submission metadata file present | no submission.yaml / submission.json found in dataset root | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) [2](https://www.ebi.ac.uk/bioimage-archive/submit) |
| SKIP | BIA-STUDY-001 | Study title | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-STUDY-002 | Study description | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-STUDY-003 | Study keywords | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-STUDY-004 | Release date (private_until_date) | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-STUDY-005 | Licence stated | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-AUTH-001 | Authors with first and last names | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-AUTH-002 | Author first names | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-AUTH-003 | Author affiliations | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-AUTH-004 | Author ORCIDs (recommended) | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-PUB-001 | Publication titles (when publications listed) | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-FUND-001 | Funding statement (when funding listed) | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-COMP-001 | Study component name and description | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) [2](https://www.ebi.ac.uk/bioimage-archive/rembi-help-overview/) |
| SKIP | BIA-COMP-002 | Study component description | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-BIOS-001 | Biosample organism (scientific name) | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-BIOS-002 | Biosample organism NCBI taxon | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-BIOS-003 | Biological entity | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-SPEC-001 | Specimen sample preparation | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-ACQ-001 | Imaging method | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-ACQ-002 | Imaging instrument | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-ACQ-003 | Image acquisition parameters | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-ANA-001 | Image analysis overview (when analysis included) | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-ANN-001 | Annotation overview and method (when annotations included) | no readable submission metadata file (see metadata rule) | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) [2](https://www.ebi.ac.uk/bioimage-archive/submit-annotations) |
| FAIL | BIA-FL-001 | File list present | no file list (*file_list*.tsv) found in dataset | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) [2](https://www.ebi.ac.uk/bioimage-archive/submit) |
| SKIP | BIA-FL-002 | File list first column is "Files" | no file list found (see file list rule) | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) |
| SKIP | BIA-FL-003 | File list rows well-formed | no file list found (see file list rule) | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) |
| SKIP | BIA-FL-004 | File list matches files on disk (no missing, no orphans) | no file list found (see file list rule) | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) |
| SKIP | BIA-FL-005 | Annotation file lists have source_image | no annotation file list (file name containing 'annotation') | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) [2](https://www.ebi.ac.uk/bioimage-archive/submit-annotations) |
| PASS | BIA-NAME-001 | File names use allowed characters |  | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) [2](https://www.ebi.ac.uk/bioimage-archive/submit) |
| PASS | BIA-SIZE-001 | File sizes within limits |  | [1](https://www.ebi.ac.uk/bioimage-archive/submit) |
| WARN | BIA-FMT-001 | Image formats | 1 ome-zarr file(s): OME-Zarr must be zipped and uploaded as .ome.zarr.zip: Blastocysts/B1_C1.ome.zarr | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) [2](https://www.ebi.ac.uk/bioimage-archive/submit) |
| PASS | BIA-IMG-001 | Image files readable |  | [1](https://www.ebi.ac.uk/bioimage-archive/submit) |
| PASS | BIA-IMG-002 | Images carry OME metadata with pixel sizes |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| SKIP | BIA-IMG-003 | Consistent dimensions/channels/pixel sizes within a series | no series with 2+ readable images to compare | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |

## Images read

| File | Format | Readable | XYZCT | dtype | Pixel size x/y/z (µm) |
|---|---|---|---|---|---|
| `Blastocysts/B1_C1.ome.zarr` | ome-zarr | yes | 271×275×236×2×1 | uint16 | 0.3604/0.3604/0.5002 |

## Sources

- **rembi-model**: [REMBI Model Reference (v1.5)](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/)
- **rembi-overview**: [REMBI Overview](https://www.ebi.ac.uk/bioimage-archive/rembi-help-overview/)
- **file-list**: [BioImage Archive File List Guide](https://www.ebi.ac.uk/bioimage-archive/help-file-list)
- **submit**: [Submitting data to the BioImage Archive](https://www.ebi.ac.uk/bioimage-archive/submit)
- **annotations**: [Submitting Annotations to the BioImage Archive](https://www.ebi.ac.uk/bioimage-archive/submit-annotations)
