# Submission check: Generic REMBI completeness

**Overall: WARN** — 21 pass, 5 warn, 0 fail, 0 skipped

- Dataset: `<scratch>/sub/tubhiswt` (86 images, 86 data files)
- Metadata: `<scratch>/sub/tubhiswt/submission.yaml`
- File lists: `file_list.tsv`
- Rules retrieved: 2026-11-02 · micro-validate 0.1.0

## Fix list

1. **[WARN] REMBI-STUDY-007 Funding (recommended)** — Add funding statements and grant references.
   - missing or empty: study.funding
2. **[WARN] REMBI-STUDY-008 Related publication (recommended)** — Link the publication by DOI or PubMed ID.
   - none of these is filled in: study.publications[*].doi, study.publications[*].pubmed_id
3. **[WARN] REMBI-BIOS-004 Variables described (recommended)** — Describe intrinsic (genotype), extrinsic (treatment) or experimental variables.
   - none of these is filled in: biosample.intrinsic_variables, biosample.extrinsic_variables, biosample.experimental_variables
4. **[WARN] REMBI-SPEC-002 Growth protocol (recommended)** — Describe the growth protocol.
   - missing or empty: specimen.growth_protocol
5. **[WARN] REMBI-IMG-003 Image-level metadata (pixel sizes) present** — Record physical pixel sizes in the image metadata.
   - images/tubhiswt_C0_TP0.ome.tif: physical pixel size missing for axis x, y
   - images/tubhiswt_C0_TP1.ome.tif: physical pixel size missing for axis x, y
   - images/tubhiswt_C0_TP10.ome.tif: physical pixel size missing for axis x, y
   - images/tubhiswt_C0_TP11.ome.tif: physical pixel size missing for axis x, y
   - images/tubhiswt_C0_TP12.ome.tif: physical pixel size missing for axis x, y

## All rules

| Status | Rule | Check | Details | Source |
|---|---|---|---|---|
| PASS | REMBI-META-001 | Metadata file present |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-STUDY-001 | Study title |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) [2](https://doi.org/10.1038/s41592-021-01166-8) |
| PASS | REMBI-STUDY-002 | Study description |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-STUDY-003 | Keywords |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-STUDY-004 | Authors (name + affiliation) |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-STUDY-005 | Author last names |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-STUDY-006 | Licence (recommended) |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| WARN | REMBI-STUDY-007 | Funding (recommended) | missing or empty: study.funding | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| WARN | REMBI-STUDY-008 | Related publication (recommended) | none of these is filled in: study.publications[*].doi, study.publications[*].pubmed_id | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) [2](https://doi.org/10.1038/s41592-021-01166-8) |
| PASS | REMBI-COMP-001 | Study component(s) named and described |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) [2](https://www.ebi.ac.uk/bioimage-archive/rembi-help-overview/) |
| PASS | REMBI-BIOS-001 | Organism scientific name |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-BIOS-002 | Organism NCBI taxon |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-BIOS-003 | Biological entity |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| WARN | REMBI-BIOS-004 | Variables described (recommended) | none of these is filled in: biosample.intrinsic_variables, biosample.extrinsic_variables, biosample.experimental_variables | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) [2](https://doi.org/10.1038/s41592-021-01166-8) |
| PASS | REMBI-SPEC-001 | Sample preparation |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| WARN | REMBI-SPEC-002 | Growth protocol (recommended) | missing or empty: specimen.growth_protocol | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-ACQ-001 | Imaging method |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-ACQ-002 | Imaging method as ontology term (recommended) |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-ACQ-003 | Imaging instrument |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-ACQ-004 | Acquisition parameters |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-ANA-001 | Analysis overview (when analysis included) |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-CORR-001 | Correlation alignment (when correlation included) |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/) |
| PASS | REMBI-IMG-001 | Images readable |  | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-help-overview/) |
| PASS | REMBI-IMG-002 | Open formats (recommended) |  | [1](https://doi.org/10.1038/s41592-021-01166-8) |
| WARN | REMBI-IMG-003 | Image-level metadata (pixel sizes) present | images/tubhiswt_C0_TP0.ome.tif: physical pixel size missing for axis x, y; images/tubhiswt_C0_TP1.ome.tif: physical pixel size missing for axis x, y; images/tubhiswt_C0_TP10.ome.tif: physical pixel size missing for axis x, y … | [1](https://www.ebi.ac.uk/bioimage-archive/rembi-help-overview/) |
| PASS | REMBI-IMG-004 | Consistent series |  | [1](https://doi.org/10.1038/s41592-021-01166-8) |

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

- **rembi-paper**: [Sarkans et al. 2021, REMBI - Recommended Metadata for Biological Images, Nature Methods 18:1418](https://doi.org/10.1038/s41592-021-01166-8)
- **rembi-model**: [REMBI Model Reference (v1.5)](https://www.ebi.ac.uk/bioimage-archive/rembi-model-reference/)
- **rembi-overview**: [REMBI Overview](https://www.ebi.ac.uk/bioimage-archive/rembi-help-overview/)
