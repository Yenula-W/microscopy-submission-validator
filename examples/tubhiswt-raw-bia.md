# Submission check: BioImage Archive (EMBL-EBI)

**Overall: FAIL** — 5 pass, 1 warn, 2 fail, 26 skipped

- Dataset: `<scratch>/data/tubhiswt-4D` (86 images, 86 data files)
- Metadata: `none`
- Rules retrieved: 2026-11-02 · micro-validate 0.1.0

## Fix list

1. **[FAIL] BIA-META-001 Submission metadata file present** — Create submission.yaml in the dataset root (run `micro-validate --template bia > submission.yaml`).
   - no submission.yaml / submission.json found in dataset root
2. **[FAIL] BIA-FL-001 File list present** — Add a tab-separated file list named like file_list.tsv (one per study component).
   - no file list (*file_list*.tsv) found in dataset
3. **[WARN] BIA-IMG-002 Images carry OME metadata with pixel sizes** — Convert plain TIFFs to OME-TIFF and set PhysicalSizeX/Y (e.g. with microscopy-metadata-repair or bfconvert).
   - tubhiswt_C0_TP0.ome.tif: physical pixel size missing for axis x, y
   - tubhiswt_C0_TP1.ome.tif: physical pixel size missing for axis x, y
   - tubhiswt_C0_TP10.ome.tif: physical pixel size missing for axis x, y
   - tubhiswt_C0_TP11.ome.tif: physical pixel size missing for axis x, y
   - tubhiswt_C0_TP12.ome.tif: physical pixel size missing for axis x, y

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
| PASS | BIA-FMT-001 | Image formats |  | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) [2](https://www.ebi.ac.uk/bioimage-archive/submit) |
| PASS | BIA-IMG-001 | Image files readable |  | [1](https://www.ebi.ac.uk/bioimage-archive/submit) |
| WARN | BIA-IMG-002 | Images carry OME metadata with pixel sizes | tubhiswt_C0_TP0.ome.tif: physical pixel size missing for axis x, y; tubhiswt_C0_TP1.ome.tif: physical pixel size missing for axis x, y; tubhiswt_C0_TP10.ome.tif: physical pixel size missing for axis x, y … | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-IMG-003 | Consistent dimensions/channels/pixel sizes within a series |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |

## Images read

| File | Format | Readable | XYZCT | dtype | Pixel size x/y/z (µm) |
|---|---|---|---|---|---|
| `tubhiswt_C0_TP0.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP1.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP10.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP11.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP12.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP13.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP14.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP15.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP16.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP17.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP18.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP19.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP2.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP20.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP21.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP22.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP23.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP24.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP25.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP26.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP27.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP28.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP29.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP3.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP30.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP31.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP32.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP33.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP34.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP35.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP36.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP37.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP38.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP39.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP4.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP40.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP41.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP42.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP5.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP6.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP7.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP8.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C0_TP9.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP0.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP1.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP10.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP11.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP12.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP13.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP14.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP15.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP16.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP17.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP18.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP19.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP2.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP20.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP21.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP22.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP23.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP24.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP25.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP26.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP27.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP28.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP29.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP3.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP30.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP31.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP32.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP33.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP34.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP35.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP36.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP37.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP38.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP39.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP4.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP40.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP41.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP42.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP5.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP6.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP7.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP8.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `tubhiswt_C1_TP9.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |

## Sources

- **rembi-model**: [REMBI Model Reference (v1.5)](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/)
- **rembi-overview**: [REMBI Overview](https://www.ebi.ac.uk/bioimage-archive/rembi-help-overview/)
- **file-list**: [BioImage Archive File List Guide](https://www.ebi.ac.uk/bioimage-archive/help-file-list)
- **submit**: [Submitting data to the BioImage Archive](https://www.ebi.ac.uk/bioimage-archive/submit)
- **annotations**: [Submitting Annotations to the BioImage Archive](https://www.ebi.ac.uk/bioimage-archive/submit-annotations)
