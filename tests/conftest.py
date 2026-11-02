"""Builders for tiny synthetic submission folders."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import tifffile
import yaml

GOOD_META = {
    "study": {
        "title": "Synthetic nuclei",
        "description": "Test dataset",
        "keywords": ["nuclei"],
        "private_until_date": "2026-11-02",
        "license": "CC0",
        "authors": [{"first_name": "Ada", "last_name": "Lovelace", "orcid": "0000-0000-0000-0000",
                     "affiliation": {"name": "Test Lab"}}],
        "funding": [{"funding_statement": "Funded by Test Trust"}],
        "publications": [{"title": "A paper", "doi": "10.1000/xyz"}],
    },
    "study_components": [{"name": "c1", "description": "all images"}],
    "biosample": {
        "organism": [{"scientific_name": "Homo sapiens", "ncbi_taxon": "NCBITaxon_9606"}],
        "biological_entity": "HeLa cells",
        "experimental_variables": "siRNA",
    },
    "specimen": {"sample_preparation": "PFA fixed, DAPI", "growth_protocol": "DMEM"},
    "image_acquisition": {
        "imaging_method": {"value": "confocal microscopy", "ontology_name": "FBbi", "ontology_id": "FBbi_00000251"},
        "imaging_instrument": "Zeiss LSM 880, 63x/1.4",
        "image_acquisition_parameters": "0.1 um pixels",
    },
}


def write_ome_tiff(path: Path, shape=(2, 16, 16), px=0.1, dtype="uint16", ome=True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.arange(np.prod(shape), dtype=dtype).reshape(shape)
    if ome:
        tifffile.imwrite(path, data, ome=True, metadata={"axes": "CYX", "PhysicalSizeX": px, "PhysicalSizeY": px})
    else:
        tifffile.imwrite(path, data)
    return path


def write_ome_zarr(path: Path, shape=(2, 16, 16), px=0.1) -> Path:
    import zarr

    path.mkdir(parents=True)
    (path / ".zgroup").write_text(json.dumps({"zarr_format": 2}))
    attrs = {"multiscales": [{
        "version": "0.4",
        "axes": [{"name": "c", "type": "channel"}, {"name": "y", "type": "space", "unit": "micrometer"},
                 {"name": "x", "type": "space", "unit": "micrometer"}],
        "datasets": [{"path": "0", "coordinateTransformations": [{"type": "scale", "scale": [1, px, px]}]}],
    }], "omero": {"channels": [{"label": f"ch{i}"} for i in range(shape[0])]}}
    (path / ".zattrs").write_text(json.dumps(attrs))
    arr = zarr.open_array(str(path / "0"), mode="w", shape=shape, chunks=shape, dtype="uint16", zarr_format=2)
    arr[:] = 1
    return path


def write_file_list(root: Path, files: list[str], name="file_list.tsv", header="Files", extra="condition") -> None:
    lines = [f"{header}\t{extra}"] + [f"{f}\tcontrol" for f in files]
    (root / name).write_text("\n".join(lines) + "\n")


@pytest.fixture
def bia_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "ds"
    files = ["series1/img_01.ome.tif", "series1/img_02.ome.tif"]
    for f in files:
        write_ome_tiff(root / f)
    (root / "submission.yaml").write_text(yaml.safe_dump(GOOD_META))
    write_file_list(root, files)
    return root


IDR_STUDY = """# comment line
Study Title\tSynthetic study
Study Description\tTest
Study Key Words\tnuclei
Study Organism\tHomo sapiens
Study PubMed ID\t12345
Study Person Last Name\tLovelace
Study Person First Name\tAda
Study Person Email\tada@example.org
Study License\tCC BY 4.0
Experiment Description\tOne experiment
Experiment Imaging Method\tconfocal microscopy
Experiment Assay File\tidrtest-assays.txt
Protocol Description\tgrown\timaged
Processed Data File Name\tidrtest-processed.txt
"""


@pytest.fixture
def idr_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "idr"
    root.mkdir()
    write_ome_zarr(root / "images" / "a.ome.zarr")
    write_ome_zarr(root / "images" / "b.ome.zarr")
    (root / "idrtest-study.txt").write_text(IDR_STUDY)
    header = ["Source Name", "Characteristics [Organism]", "Assay Name", "Dataset Name", "Image File",
              "Comment [Image File Path]", "Channels"]
    rows = [["s1", "Homo sapiens", "a1", "ds1", "a.ome.zarr", "images", "DAPI:DNA;GFP:protein"],
            ["s2", "Homo sapiens", "a2", "ds1", "b.ome.zarr", "images", "DAPI:DNA;GFP:protein"]]
    (root / "idrtest-assays.txt").write_text("\n".join("\t".join(r) for r in [header] + rows) + "\n")
    (root / "idrtest-processed.txt").write_text("image\tcount\na.ome.zarr\t3\n")
    return root
