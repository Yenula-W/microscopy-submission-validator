# Submission check: BioImage Archive (EMBL-EBI)

**Overall: WARN** — 31 pass, 2 warn, 0 fail, 1 skipped

- Dataset: `<scratch>/sub/tubhiswt` (86 images, 86 data files)
- Metadata: `<scratch>/sub/tubhiswt/submission.yaml`
- File lists: `file_list.tsv`
- Rules retrieved: 2026-11-02 · micro-validate 0.1.0

## Fix list

1. **[WARN] BIA-AUTH-004 Author ORCIDs (recommended)** — Add ORCID iDs to authors.
   - missing or empty: study.authors[0].orcid
2. **[WARN] BIA-IMG-002 Images carry OME metadata with pixel sizes** — Convert plain TIFFs to OME-TIFF and set PhysicalSizeX/Y (e.g. with microscopy-metadata-repair or bfconvert).
   - images/tubhiswt_C0_TP0.ome.tif: physical pixel size missing for axis x, y
   - images/tubhiswt_C0_TP1.ome.tif: physical pixel size missing for axis x, y
   - images/tubhiswt_C0_TP10.ome.tif: physical pixel size missing for axis x, y
   - images/tubhiswt_C0_TP11.ome.tif: physical pixel size missing for axis x, y
   - images/tubhiswt_C0_TP12.ome.tif: physical pixel size missing for axis x, y

## All rules

| Status | Rule | Check | Details | Source |
|---|---|---|---|---|
| PASS | BIA-META-001 | Submission metadata file present |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) [2](https://www.ebi.ac.uk/bioimage-archive/submit) |
| PASS | BIA-STUDY-001 | Study title |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-STUDY-002 | Study description |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-STUDY-003 | Study keywords |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-STUDY-004 | Release date (private_until_date) |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-STUDY-005 | Licence stated |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-AUTH-001 | Authors with first and last names |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-AUTH-002 | Author first names |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-AUTH-003 | Author affiliations |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| WARN | BIA-AUTH-004 | Author ORCIDs (recommended) | missing or empty: study.authors[0].orcid | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-PUB-001 | Publication titles (when publications listed) |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-FUND-001 | Funding statement (when funding listed) |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-COMP-001 | Study component name and description |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) [2](https://www.ebi.ac.uk/bioimage-archive/rembi-help-overview/) |
| PASS | BIA-COMP-002 | Study component description |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-BIOS-001 | Biosample organism (scientific name) |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-BIOS-002 | Biosample organism NCBI taxon |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-BIOS-003 | Biological entity |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-SPEC-001 | Specimen sample preparation |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-ACQ-001 | Imaging method |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-ACQ-002 | Imaging instrument |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-ACQ-003 | Image acquisition parameters |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-ANA-001 | Image analysis overview (when analysis included) |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-ANN-001 | Annotation overview and method (when annotations included) |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) [2](https://www.ebi.ac.uk/bioimage-archive/submit-annotations) |
| PASS | BIA-FL-001 | File list present |  | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) [2](https://www.ebi.ac.uk/bioimage-archive/submit) |
| PASS | BIA-FL-002 | File list first column is "Files" |  | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) |
| PASS | BIA-FL-003 | File list rows well-formed |  | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) |
| PASS | BIA-FL-004 | File list matches files on disk (no missing, no orphans) |  | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) |
| SKIP | BIA-FL-005 | Annotation file lists have source_image | no annotation file list (file name containing 'annotation') | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) [2](https://www.ebi.ac.uk/bioimage-archive/submit-annotations) |
| PASS | BIA-NAME-001 | File names use allowed characters |  | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) [2](https://www.ebi.ac.uk/bioimage-archive/submit) |
| PASS | BIA-SIZE-001 | File sizes within limits |  | [1](https://www.ebi.ac.uk/bioimage-archive/submit) |
| PASS | BIA-FMT-001 | Image formats |  | [1](https://www.ebi.ac.uk/bioimage-archive/help-file-list) [2](https://www.ebi.ac.uk/bioimage-archive/submit) |
| PASS | BIA-IMG-001 | Image files readable |  | [1](https://www.ebi.ac.uk/bioimage-archive/submit) |
| WARN | BIA-IMG-002 | Images carry OME metadata with pixel sizes | images/tubhiswt_C0_TP0.ome.tif: physical pixel size missing for axis x, y; images/tubhiswt_C0_TP1.ome.tif: physical pixel size missing for axis x, y; images/tubhiswt_C0_TP10.ome.tif: physical pixel size missing for axis x, y … | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | BIA-IMG-003 | Consistent dimensions/channels/pixel sizes within a series |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |

## Images read

| File | Format | Readable | XYZCT | dtype | Pixel size x/y/z (µm) |
|---|---|---|---|---|---|
| `images/tubhiswt_C0_TP0.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP1.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP10.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP11.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP12.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP13.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP14.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP15.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP16.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP17.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP18.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP19.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP2.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP20.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP21.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP22.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP23.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP24.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP25.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP26.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP27.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP28.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP29.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP3.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP30.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP31.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP32.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP33.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP34.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP35.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP36.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP37.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP38.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP39.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP4.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP40.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP41.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP42.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP5.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP6.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP7.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP8.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C0_TP9.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP0.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP1.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP10.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP11.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP12.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP13.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP14.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP15.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP16.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP17.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP18.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP19.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP2.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP20.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP21.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP22.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP23.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP24.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP25.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP26.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP27.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP28.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP29.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP3.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP30.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP31.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP32.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP33.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP34.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP35.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP36.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP37.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP38.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP39.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP4.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP40.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP41.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP42.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP5.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP6.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP7.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP8.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |
| `images/tubhiswt_C1_TP9.ome.tif` | ome-tiff | yes | 512×512×10×2×43 | uint8 | -/-/- |

## Sources

- **rembi-model**: [REMBI Model Reference (v1.5)](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/)
- **rembi-overview**: [REMBI Overview](https://www.ebi.ac.uk/bioimage-archive/rembi-help-overview/)
- **file-list**: [BioImage Archive File List Guide](https://www.ebi.ac.uk/bioimage-archive/help-file-list)
- **submit**: [Submitting data to the BioImage Archive](https://www.ebi.ac.uk/bioimage-archive/submit)
- **annotations**: [Submitting Annotations to the BioImage Archive](https://www.ebi.ac.uk/bioimage-archive/submit-annotations)
