from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from conftest import GOOD_META, write_file_list, write_ome_tiff, write_ome_zarr
from micro_validate import checks  # noqa: F401
from micro_validate.checks import resolve
from micro_validate.cli import main
from micro_validate.dataset import load_dataset
from micro_validate.engine import CHECKS, list_targets, load_ruleset, run_rules


def run(root: Path, target: str) -> dict[str, str]:
    results = run_rules(load_ruleset(target), load_dataset(root))
    return {r.rule_id: r for r in results}


def statuses(res) -> dict[str, str]:
    return {k: v.status for k, v in res.items()}


# ------------------------------------------------------------- engine / rule files


@pytest.mark.parametrize("target", ["bia", "idr", "rembi"])
def test_rulesets_load_with_sources(target):
    rs = load_ruleset(target)
    assert rs.rules
    for r in rs.rules:
        assert r.check in CHECKS, r.id
        assert r.sources, f"{r.id} cites no source"
        assert all(rs.sources[s]["url"].startswith("https://") for s in r.sources)
        assert r.fix, f"{r.id} has no fix text"


def test_list_targets():
    assert set(list_targets()) >= {"bia", "idr", "rembi"}


def test_unknown_target():
    with pytest.raises(ValueError):
        load_ruleset("nope")


def test_custom_rules_file(tmp_path, bia_dataset):
    f = tmp_path / "mine.yaml"
    f.write_text(yaml.safe_dump({
        "target": "lab", "name": "Lab", "sources": {"s": {"title": "t", "url": "https://x.org"}},
        "rules": [{"id": "LAB-1", "title": "t", "check": "field_present", "params": {"path": "study.lab_code"},
                   "sources": ["s"], "fix": "add"}]}))
    res = run(bia_dataset, str(f))
    assert res["LAB-1"].status == "fail"


def test_resolve_fans_out_lists():
    meta = {"a": [{"b": 1}, {"c": 2}], "d": {"e": "x"}}
    assert list(resolve(meta, "a[*].b")) == [("a[0].b", 1), ("a[1].b", None)]
    assert list(resolve(meta, "d[*].e")) == [("d[0].e", "x")]
    assert list(resolve(meta, "z[*].e")) == [("z", None)]


# ------------------------------------------------------------- BIA


def test_bia_good_dataset_passes(bia_dataset):
    res = run(bia_dataset, "bia")
    bad = {k: (v.status, v.messages) for k, v in res.items() if v.status == "fail"}
    assert not bad
    assert res["BIA-IMG-003"].status == "pass"
    assert res["BIA-IMG-001"].status == "pass"


def test_bia_missing_metadata_fields(bia_dataset):
    meta = json.loads(json.dumps(GOOD_META))
    del meta["study"]["title"]
    meta["biosample"]["organism"][0]["ncbi_taxon"] = "# e.g. NCBITaxon_9606"
    meta["study"]["authors"].append({"first_name": "Bob"})
    (bia_dataset / "submission.yaml").write_text(yaml.safe_dump(meta))
    res = run(bia_dataset, "bia")
    assert res["BIA-STUDY-001"].status == "fail"
    assert res["BIA-BIOS-002"].status == "warn"  # recommended: accepted BIA studies give organism as text only
    assert res["BIA-AUTH-001"].status == "fail"
    assert "study.authors[1].last_name" in res["BIA-AUTH-001"].messages[0]


def test_bia_no_metadata(bia_dataset):
    (bia_dataset / "submission.yaml").unlink()
    res = run(bia_dataset, "bia")
    assert res["BIA-META-001"].status == "fail"
    assert res["BIA-STUDY-001"].status == "skip"


def test_bia_template_is_incomplete(tmp_path, bia_dataset):
    from micro_validate.cli import _template

    (bia_dataset / "submission.yaml").write_text(_template("bia"))
    res = run(bia_dataset, "bia")
    assert res["BIA-STUDY-001"].status == "fail"
    assert res["BIA-STUDY-003"].status == "fail"  # empty keywords list


def test_bia_file_list_missing_and_orphans(bia_dataset):
    write_ome_tiff(bia_dataset / "series1" / "img_03.ome.tif")
    write_file_list(bia_dataset, ["series1/img_01.ome.tif", "series1/IMG_02.ome.tif", "series1/gone.ome.tif"])
    msgs = " ".join(run(bia_dataset, "bia")["BIA-FL-004"].messages)
    assert "listed but not found: series1/gone.ome.tif" in msgs
    assert "case differs" in msgs
    assert "not in any file list: series1/img_03.ome.tif" in msgs


def test_bia_file_list_header_and_format(bia_dataset):
    (bia_dataset / "file_list.tsv").write_text(
        "Filename\tcondition\n./series1/img_01.ome.tif\tcontrol\n\nseries1\\img_02.ome.tif\t\n")
    res = run(bia_dataset, "bia")
    assert res["BIA-FL-002"].status == "fail"
    msgs = " ".join(res["BIA-FL-003"].messages)
    assert "blank line" in msgs and "backslash" in msgs and "relative" in msgs and "empty attribute" in msgs


def test_bia_no_file_list(bia_dataset):
    (bia_dataset / "file_list.tsv").unlink()
    res = run(bia_dataset, "bia")
    assert res["BIA-FL-001"].status == "fail"
    assert res["BIA-FL-004"].status == "skip"


def test_bia_bad_filename_chars(bia_dataset):
    write_ome_tiff(bia_dataset / "series1" / "img#3 é.ome.tif")
    res = run(bia_dataset, "bia")
    assert res["BIA-NAME-001"].status == "fail"
    assert "'#é'" in res["BIA-NAME-001"].messages[0]


def test_bia_inconsistent_series(bia_dataset):  # warn: advice, not a repository rule
    write_ome_tiff(bia_dataset / "series1" / "img_02.ome.tif", shape=(3, 16, 16), px=0.2)
    res = run(bia_dataset, "bia")
    msgs = " ".join(res["BIA-IMG-003"].messages)
    assert res["BIA-IMG-003"].status == "warn"  # advice, not a repository requirement
    assert "C=3 vs 2" in msgs and "pixel size x=0.2" in msgs


def test_series_grouped_by_directory(bia_dataset):
    # a different setup in another folder is a different series, so no conflict
    write_ome_tiff(bia_dataset / "series2" / "x.ome.tif", shape=(3, 8, 8), px=0.5)
    write_file_list(bia_dataset, ["series1/img_01.ome.tif", "series1/img_02.ome.tif", "series2/x.ome.tif"])
    assert run(bia_dataset, "bia")["BIA-IMG-003"].status == "pass"


def test_plain_tiff_warns_and_corrupt_fails(bia_dataset):
    write_ome_tiff(bia_dataset / "plain" / "p.tif", ome=False)
    (bia_dataset / "plain" / "broken.ome.tif").write_bytes(b"II*\x00garbage")
    write_file_list(bia_dataset, ["series1/img_01.ome.tif", "series1/img_02.ome.tif", "plain/p.tif", "plain/broken.ome.tif"])
    res = run(bia_dataset, "bia")
    assert res["BIA-IMG-001"].status == "fail"
    assert "plain/broken.ome.tif" in res["BIA-IMG-001"].messages[0]
    assert res["BIA-IMG-002"].status == "warn"
    assert any("no OME-XML" in m for m in res["BIA-IMG-002"].messages)


def test_bia_unzipped_zarr_warns(bia_dataset):
    write_ome_zarr(bia_dataset / "z" / "img.ome.zarr")
    write_file_list(bia_dataset, ["series1/img_01.ome.tif", "series1/img_02.ome.tif", "z/img.ome.zarr"])
    res = run(bia_dataset, "bia")
    assert res["BIA-FMT-001"].status == "warn"
    assert ".ome.zarr.zip" in res["BIA-FMT-001"].messages[0]
    assert res["BIA-FL-004"].status == "pass"  # zarr dir counted as one file, not its chunks


def test_zipped_zarr_readable(bia_dataset):
    import shutil

    z = write_ome_zarr(bia_dataset.parent / "tmpz" / "img.ome.zarr")
    shutil.make_archive(str(bia_dataset / "z" / "img.ome.zarr"), "zip", z.parent, z.name)
    write_file_list(bia_dataset, ["series1/img_01.ome.tif", "series1/img_02.ome.tif", "z/img.ome.zarr.zip"])
    ds = load_dataset(bia_dataset)
    info = ds.image_info("z/img.ome.zarr.zip")
    assert info.readable and info.sizes["C"] == 2 and info.pixel_size_um["x"] == pytest.approx(0.1)
    assert run(bia_dataset, "bia")["BIA-FMT-001"].status == "pass"


def test_annotation_file_list_needs_source_image(bia_dataset):
    (bia_dataset / "masks").mkdir()
    (bia_dataset / "masks" / "m1.png").write_bytes(b"\x89PNG")
    (bia_dataset / "annotation_file_list.tsv").write_text("Files\ttype\nmasks/m1.png\tmask\n")
    assert run(bia_dataset, "bia")["BIA-FL-005"].status == "fail"
    (bia_dataset / "annotation_file_list.tsv").write_text("Files\tsource_image\nmasks/m1.png\tseries1/img_01.ome.tif\n")
    assert run(bia_dataset, "bia")["BIA-FL-005"].status == "pass"


# ------------------------------------------------------------- IDR


def test_idr_good_dataset(idr_dataset):
    res = run(idr_dataset, "idr")
    bad = {k: (v.status, v.messages) for k, v in res.items() if v.status in ("fail", "warn")}
    assert not bad
    assert res["IDR-ASSAY-004"].status == "pass"


def test_idr_rejects_ome_tiff(idr_dataset):
    write_ome_tiff(idr_dataset / "images" / "c.ome.tif")
    res = run(idr_dataset, "idr")
    assert res["IDR-FMT-001"].status == "fail"
    assert any("c.ome.tif" in m for m in res["IDR-ASSAY-003"].messages)


def test_idr_study_hints_count_as_missing(idr_dataset):
    text = (idr_dataset / "idrtest-study.txt").read_text().replace("Study Title\tSynthetic study", "Study Title\t# fill in")
    (idr_dataset / "idrtest-study.txt").write_text(text)
    res = run(idr_dataset, "idr")
    assert res["IDR-STUDY-002"].status == "fail"
    assert "Study Title" in res["IDR-STUDY-002"].messages[0]


def test_idr_assay_problems(idr_dataset):
    p = idr_dataset / "idrtest-assays.txt"
    text = p.read_text().replace("b.ome.zarr\timages\tDAPI:DNA;GFP:protein", "missing.ome.zarr\timages\tDAPI:DNA")
    text = text.replace("a.ome.zarr\timages\tDAPI:DNA;GFP:protein", "a.ome.zarr\timages\tDAPI:DNA")
    p.write_text(text)
    res = run(idr_dataset, "idr")
    msgs = " ".join(res["IDR-ASSAY-003"].messages)
    assert "missing.ome.zarr" in msgs and "images/b.ome.zarr" in msgs
    assert res["IDR-ASSAY-004"].status == "warn"


def test_idr_stem_match_and_comma_assay_list(idr_dataset):
    # real IDR files list the original .tif name and comma-join assay files in one cell
    p = idr_dataset / "idrtest-assays.txt"
    p.write_text(p.read_text().replace("a.ome.zarr\timages", "a.tif\t/images"))
    s = idr_dataset / "idrtest-study.txt"
    s.write_text(s.read_text().replace("Experiment Assay File\tidrtest-assays.txt",
                                       "Experiment Assay File\tidrtest-assays.txt, other-assays.txt"))
    res = run(idr_dataset, "idr")
    assert res["IDR-ASSAY-003"].status == "warn"
    assert "only by file-name stem" in res["IDR-ASSAY-003"].messages[0]
    assert res["IDR-ASSAY-001"].messages == ["study file names assay file 'other-assays.txt' but it is not in the dataset"]


def test_idr_missing_tables(tmp_path):
    root = tmp_path / "bare"
    write_ome_zarr(root / "a.ome.zarr")
    res = run(root, "idr")
    assert res["IDR-STUDY-001"].status == "fail"
    assert res["IDR-ASSAY-001"].status == "fail"
    assert res["IDR-ASSAY-003"].status == "skip"


# ------------------------------------------------------------- REMBI + CLI


def test_rembi_good(bia_dataset):
    res = run(bia_dataset, "rembi")
    assert not [k for k, v in res.items() if v.status == "fail"]


def test_cli_writes_reports_and_exit_codes(bia_dataset, tmp_path, capsys):
    out = tmp_path / "rep" / "report"
    assert main([str(bia_dataset), "--target", "bia", "--out", str(out)]) == 0
    data = json.loads(out.with_suffix(".json").read_text())
    assert data["overall"] in ("pass", "warn")
    assert data["summary"]["fail"] == 0
    md = out.with_suffix(".md").read_text()
    assert md.startswith("# Submission check: BioImage Archive")
    assert "## All rules" in md and "https://www.ebi.ac.uk/bioimage-archive/help-file-list" in md

    (bia_dataset / "file_list.tsv").unlink()
    assert main([str(bia_dataset), "-t", "bia"]) == 1
    md = capsys.readouterr().out
    assert "## Fix list" in md and "BIA-FL-001" in md


def test_cli_json_and_errors(bia_dataset, capsys):
    assert main([str(bia_dataset), "-t", "rembi", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["target"]["id"] == "rembi"
    assert main([str(bia_dataset / "nope"), "-t", "bia"]) == 2
    assert main([str(bia_dataset), "-t", "nope"]) == 2


# ------------------------------------------------------------- regressions from the held-out real-data run


PAGETAB = {
    "accno": "S-BIAD9999",
    "attributes": [{"name": "Title", "value": "T"}, {"name": "ReleaseDate", "value": "2023-03-07"}],
    "section": {"type": "Study", "attributes": [
        {"name": "Title", "value": "Accepted study"}, {"name": "Description", "value": "D"},
        {"name": "Keywords", "value": "AI"}, {"name": "Keywords", "value": "nucleus"}, {"name": "License", "value": "CC0"}],
        "subsections": [
            {"type": "author", "attributes": [{"name": "Name", "value": "Ada M. Lovelace"},
                                              {"name": "affiliation", "value": "o1", "reference": True}]},
            {"type": "organisation", "accno": "o1", "attributes": [{"name": "Name", "value": "EBI"}]},
            [{"type": "Biosample", "attributes": [{"name": "Organism", "value": "Homo sapiens (human)"},
                                                 {"name": "Biological entity", "value": "HeLa"}]},
             {"type": "Biosample", "attributes": [{"name": "Organism", "value": "Mus musculus (mouse)"},
                                                 {"name": "Biological entity", "value": "ESC"}]}],
            {"type": "Specimen", "attributes": [{"name": "Sample preparation protocol", "value": "PFA"}]},
            {"type": "Image acquisition", "attributes": [{"name": "Imaging method", "value": "confocal"},
                                                         {"name": "Imaging instrument", "value": "LSM 780"},
                                                         {"name": "Image acquisition parameters", "value": "63x"}]},
            {"type": "Study Component", "attributes": [{"name": "Name", "value": "c"},
                                                       {"name": "Description", "value": "d"}]},
        ]},
}


def test_biostudies_pagetab_metadata(bia_dataset):
    """Accepted BIA studies: list-valued sections, single author Name, organism as text (S-BIAD634)."""
    (bia_dataset / "submission.yaml").unlink()
    (bia_dataset / "S-BIAD9999.json").write_text(json.dumps(PAGETAB))
    ds = load_dataset(bia_dataset)
    assert ds.metadata["biosample"][1]["organism"][0] == {
        "scientific_name": "Mus musculus", "common_name": "mouse", "ncbi_taxon": None}
    assert ds.metadata["study"]["authors"][0]["affiliation"] == {"name": "EBI"}
    res = run(bia_dataset, "bia")
    assert not [k for k, v in res.items() if v.status == "fail"], {k: v.messages for k, v in res.items() if v.status == "fail"}
    assert res["BIA-BIOS-002"].status == "warn"
    assert "S-BIAD9999.json" not in load_dataset(bia_dataset).data_files


def test_annotation_source_image_column_spelling(bia_dataset):
    """S-BIAD634's accepted annotation list uses a 'source image' header."""
    (bia_dataset / "masks").mkdir()
    (bia_dataset / "masks" / "m1.png").write_bytes(b"\x89PNG")
    (bia_dataset / "file_list_annotations.tsv").write_text("Files\tsource image\nmasks/m1.png\tseries1/img_01.ome.tif\n")
    assert run(bia_dataset, "bia")["BIA-FL-005"].status == "pass"


def test_partial_mode_skips_absent_listed_files(bia_dataset):
    write_file_list(bia_dataset, ["series1/img_01.ome.tif", "series1/img_02.ome.tif", "series2/not_downloaded.tif"])
    assert run(bia_dataset, "bia")["BIA-FL-004"].status == "fail"
    res = run_rules(load_ruleset("bia"), load_dataset(bia_dataset, partial=True))
    assert next(r for r in res if r.rule_id == "BIA-FL-004").status == "pass"


def test_idr_singular_assay_file_name(idr_dataset):
    """idr0052 publishes experimentA/MitoSys_assay_file.txt."""
    (idr_dataset / "idrtest-assays.txt").rename(idr_dataset / "MitoSys_assay_file.txt")
    s = idr_dataset / "idrtest-study.txt"
    s.write_text(s.read_text().replace("idrtest-assays.txt", "MitoSys_assay_file.txt"))
    res = run(idr_dataset, "idr")
    assert res["IDR-ASSAY-001"].status == "pass" and res["IDR-ASSAY-003"].status == "pass"


def test_ngff_v05_zarr3_image(tmp_path):
    """NGFF 0.5 (zarr v3, attributes under 'ome'), e.g. IDR's v0.5 samples."""
    import numpy as np
    import zarr

    from micro_validate.imageinfo import read_info

    z = tmp_path / "img.ome.zarr"
    z.mkdir()
    attrs = {"ome": {"version": "0.5", "multiscales": [{
        "axes": [{"name": "c", "type": "channel"}, {"name": "y", "type": "space", "unit": "micrometer"},
                 {"name": "x", "type": "space", "unit": "micrometer"}],
        "datasets": [{"path": "0", "coordinateTransformations": [{"type": "scale", "scale": [1, 0.5, 0.5]}]}]}]}}
    (z / "zarr.json").write_text(json.dumps({"zarr_format": 3, "node_type": "group", "attributes": attrs}))
    meta = {"zarr_format": 3, "node_type": "array", "shape": [2, 8, 8], "data_type": "uint8",
            "chunk_grid": {"name": "regular", "configuration": {"chunk_shape": [2, 8, 8]}},
            "chunk_key_encoding": {"name": "default", "configuration": {"separator": "/"}},
            "fill_value": 0, "codecs": [{"name": "bytes"}], "attributes": {}}
    (z / "0").mkdir()
    (z / "0" / "zarr.json").write_text(json.dumps(meta))
    info = read_info(z, "img.ome.zarr")
    assert info.readable, info.error
    assert info.sizes["C"] == 2 and info.dtype == "uint8" and info.pixel_size_um["x"] == 0.5
    if int(zarr.__version__.split(".")[0]) < 3:
        assert any("zarr v3" in n for n in info.notes)


def test_binary_only_ome_tiff_with_companion(tmp_path):
    """OME sample 'companion': BinaryOnly OME-TIFFs + .companion.ome are valid, not unreadable."""
    import numpy as np
    import tifffile

    from micro_validate.imageinfo import classify, read_info

    ns = 'xmlns="http://www.openmicroscopy.org/Schemas/OME/2016-06"'
    stub = f'<?xml version="1.0"?><OME {ns} UUID="urn:uuid:1"><BinaryOnly MetadataFile="set.companion.ome" UUID="urn:uuid:0"/></OME>'
    tifffile.imwrite(tmp_path / "set-Z1.ome.tiff", np.zeros((6, 4), "uint8"), description=stub, metadata=None)
    (tmp_path / "set.companion.ome").write_text(
        f'<OME {ns}><Image ID="Image:0"><Pixels ID="Pixels:0" DimensionOrder="XYZCT" Type="uint8" SizeX="4" SizeY="6" '
        'SizeZ="1" SizeC="1" SizeT="1" PhysicalSizeX="0.2" PhysicalSizeY="0.2"><Channel ID="Channel:0"/>'
        '<TiffData/></Pixels></Image></OME>')
    info = read_info(tmp_path / "set-Z1.ome.tiff", "set-Z1.ome.tiff")
    assert info.readable and info.is_ome and info.pixel_size_um["x"] == 0.2, info
    assert classify(tmp_path / "set.companion.ome") == "sidecar"
    (tmp_path / "set.companion.ome").unlink()
    info = read_info(tmp_path / "set-Z1.ome.tiff", "set-Z1.ome.tiff")
    assert info.readable and "not found" in info.notes[0]


def test_dpi_default_resolution_is_not_a_pixel_size(tmp_path):
    """Olympus FluoView sample stored 72 px/cm; that is not a 138.9 µm pixel."""
    import numpy as np
    import tifffile

    from micro_validate.imageinfo import read_info

    tifffile.imwrite(tmp_path / "a.tif", np.zeros((4, 4), "uint8"), resolution=(72, 72), resolutionunit="CENTIMETER")
    assert read_info(tmp_path / "a.tif", "a.tif").pixel_size_um["x"] is None
    tifffile.imwrite(tmp_path / "b.tif", np.zeros((4, 4), "uint8"), resolution=(10000 / 0.5, 10000 / 0.5), resolutionunit="CENTIMETER")
    assert read_info(tmp_path / "b.tif", "b.tif").pixel_size_um["x"] == pytest.approx(0.5)


def test_metaseries_calibration(tmp_path):
    """MetaMorph TIFFs keep calibration in MetaSeries XML (OME sample zenodo-13642395: 0.65 µm)."""
    import numpy as np
    import tifffile

    from micro_validate.imageinfo import read_info

    desc = ('<MetaData><PlaneInfo>'
            '<prop id="spatial-calibration-x" type="float" value="0.65"/>'
            '<prop id="spatial-calibration-y" type="float" value="0.65"/>'
            '<prop id="spatial-calibration-units" type="string" value="um"/>'
            '</PlaneInfo></MetaData>')
    tifffile.imwrite(tmp_path / "m.tif", np.zeros((4, 4), "uint16"), description=desc, metadata=None)
    info = read_info(tmp_path / "m.tif", "m.tif")
    assert info.pixel_size_um["x"] == pytest.approx(0.65)


def test_file_list_recognised_by_header(bia_dataset):
    """Accepted BIA studies name lists freely (S-BIAD3623: PAINT.tsv, TEM.tsv)."""
    (bia_dataset / "file_list.tsv").rename(bia_dataset / "PAINT.tsv")
    ds = load_dataset(bia_dataset)
    assert [t.path for t in ds.file_lists] == ["PAINT.tsv"]
    assert run(bia_dataset, "bia")["BIA-FL-004"].status == "pass"


def test_png_jpeg_header_check(tmp_path):
    """BIA studies ship PNG masks (S-BIAD634, S-BIAD4214): verify headers instead of 'unverified'."""
    import struct
    import zlib

    from micro_validate.imageinfo import read_info

    raw = b"\x00" + b"\x00" * 3
    ihdr = struct.pack(">IIBBBBB", 3, 1, 8, 0, 0, 0, 0)
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    (tmp_path / "m.png").write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    info = read_info(tmp_path / "m.png", "m.png")
    assert info.readable and info.sizes["X"] == 3 and info.sizes["C"] == 1
    (tmp_path / "bad.png").write_bytes(b"\x89PNG\r\n")
    assert read_info(tmp_path / "bad.png", "bad.png").readable is False
    (tmp_path / "bad.jpg").write_bytes(b"\xff\xd8\xff\xe0garbage")
    assert read_info(tmp_path / "bad.jpg", "bad.jpg").readable is False


def test_idr_accepted_study_conventions(idr_dataset):
    """Patterns from accepted IDR studies (idr0052, idr0054, idr0066, idr0101) must not fail."""
    s = idr_dataset / "idrtest-study.txt"
    text = s.read_text()
    text = text.replace("Study Key Words\tnuclei\n", "").replace("Study Organism\tHomo sapiens\n", "Experiment Organism\tHomo sapiens\n")
    text = text.replace("Experiment Assay File\tidrtest-assays.txt", "Experiment Assay File\tidrtest-assays and idrtest-assays.txt")
    s.write_text(text)
    a = idr_dataset / "idrtest-assays.txt"
    a.write_text(a.read_text().replace("Assay Name", "Comment [x]").replace("Image File\t", "Image Name\t"))
    res = run(idr_dataset, "idr")
    assert res["IDR-STUDY-002"].status == "pass"
    assert res["IDR-STUDY-006"].status == "warn"  # keywords missing: recommended only
    assert res["IDR-ASSAY-001"].status == "pass"
    assert res["IDR-ASSAY-002"].status == "pass"
    assert res["IDR-ASSAY-003"].status == "pass"


def test_idr_fileset_folder_matches_converted_image(idr_dataset):
    """idr0052: rows list per-plane TIFFs inside a cell folder; the converted image is named after the folder."""
    a = idr_dataset / "idrtest-assays.txt"
    a.write_text(a.read_text().replace("a.ome.zarr\timages", "plane_T0001.tif\timages/a/rawtif"))
    res = run(idr_dataset, "idr")
    assert res["IDR-ASSAY-003"].status == "warn"
    assert "only by file-name stem" in res["IDR-ASSAY-003"].messages[0]


def test_hcs_plate_is_not_checked_rather_than_unreadable(tmp_path, capsys):
    """IDR idr0001A/2551.zarr is a valid plate; it must not be reported as unreadable."""
    p = tmp_path / "plate.zarr"
    p.mkdir()
    (p / ".zattrs").write_text(json.dumps({"plate": {"wells": [{"path": "A/1"}], "version": "0.4"}}))
    res = run(tmp_path, "rembi")
    assert res["REMBI-IMG-001"].status == "warn"
    assert "per-image checks are not supported" in res["REMBI-IMG-001"].messages[0]


def test_ngff_units_typo_accepted_with_note(tmp_path):
    """idr0047 writes {'units': 'micrometer'}; read it, but note the non-standard key."""
    from micro_validate.imageinfo import read_info

    z = write_ome_zarr(tmp_path / "a.ome.zarr")
    attrs = json.loads((z / ".zattrs").read_text())
    for ax in attrs["multiscales"][0]["axes"][1:]:
        ax["units"] = ax.pop("unit")
    (z / ".zattrs").write_text(json.dumps(attrs))
    info = read_info(z, "a.ome.zarr")
    assert info.pixel_size_um["x"] == pytest.approx(0.1)
    assert any("non-standard key 'units'" in n for n in info.notes)


# ------------------------------------------------------------- regressions from round 2 (accepted IDR/BIA tables)


def test_idr_curated_annotation_csv_is_the_assay_table(idr_dataset):
    """Most accepted IDR repos publish *-annotation.csv and the study file references it (idr0068)."""
    a = idr_dataset / "idrtest-assays.txt"
    rows = [line.split("\t") for line in a.read_text().splitlines()]
    (idr_dataset / "idrtest-experimentA-annotation.csv").write_text("\n".join(",".join(r) for r in rows) + "\n")
    a.unlink()
    s = idr_dataset / "idrtest-study.txt"
    s.write_text(s.read_text().replace("idrtest-assays.txt", "idrtest-experimentA-annotation"))
    res = run(idr_dataset, "idr")
    assert res["IDR-ASSAY-001"].status == "pass", res["IDR-ASSAY-001"].messages
    assert res["IDR-ASSAY-003"].status == "pass", res["IDR-ASSAY-003"].messages


def test_annotation_named_data_is_not_an_idr_table_without_study(bia_dataset):
    """BIA data such as '*_manual_annotations.tsv' (no IDR study file) stays a data file."""
    (bia_dataset / "x_manual_annotations.tsv").write_text("cell\tlabel\n1\ta\n")
    ds = load_dataset(bia_dataset)
    assert "x_manual_annotations.tsv" in ds.data_files and not ds.idr_assays


def test_idr_comma_separated_txt_assay(idr_dataset):
    """idr0040's accepted assay file is comma-separated despite '.txt'."""
    a = idr_dataset / "idrtest-assays.txt"
    a.write_text(a.read_text().replace("\t", ","))
    res = run(idr_dataset, "idr")
    assert res["IDR-ASSAY-003"].status == "pass", res["IDR-ASSAY-003"].messages
    assert res["IDR-ASSAY-002"].status == "warn"
    assert "comma-separated" in res["IDR-ASSAY-002"].messages[0]


def test_idr_reference_typo_still_reported(idr_dataset):
    """idr0018/idr0050 study files say '...-assay.txt' for '...-assays.txt': a real, reportable mismatch."""
    s = idr_dataset / "idrtest-study.txt"
    s.write_text(s.read_text().replace("Experiment Assay File\tidrtest-assays.txt", "Experiment Assay File\tidrtest-assay.txt"))
    res = run(idr_dataset, "idr")
    assert res["IDR-ASSAY-001"].status == "warn"  # reported, with the table it most likely means
    assert "'idrtest-assay.txt'" in res["IDR-ASSAY-001"].messages[0]
    assert "'idrtest-assays.txt' looks like the table it means" in res["IDR-ASSAY-001"].messages[0]


def test_idr_plate_described_by_library_plate_column(tmp_path):
    """idr0002: a screen library describes plates (Plate/Well), not image files."""
    root = tmp_path / "scr"
    p = root / "plate1_1_013.ome.zarr"
    p.mkdir(parents=True)
    (p / ".zattrs").write_text(json.dumps({"plate": {"wells": [{"path": "A/1"}]}}))
    (root / "s-study.txt").write_text("Study Title\tT\nStudy Description\tD\nScreen Library File\ts-library.txt\n")
    (root / "s-library.txt").write_text("Plate\tWell\nplate1_1_013\tA1\n")
    assert run(root, "idr")["IDR-ASSAY-003"].status == "pass"


def test_file_list_that_lists_itself(bia_dataset):
    """S-BIAD4206: a submitter's TSV lists itself; it exists, so it is not 'listed but not found'."""
    write_file_list(bia_dataset, ["series1/img_01.ome.tif", "series1/img_02.ome.tif", "file_list.tsv"])
    assert run(bia_dataset, "bia")["BIA-FL-004"].status == "pass"


def test_unlisted_upload_reported(bia_dataset):
    """S-BIAD4174: files uploaded for a second sample but missing from the only file list."""
    write_ome_tiff(bia_dataset / "sample2" / "x.ome.tif")
    msgs = run(bia_dataset, "bia")["BIA-FL-004"].messages
    assert msgs == ["on disk but not in any file list: sample2/x.ome.tif"]


def test_source_image_inside_container(bia_dataset):
    """S-BIAD3632: source_image points inside a SpatialData .zarr.zip."""
    import zipfile

    with zipfile.ZipFile(bia_dataset / "PLA4.zarr.zip", "w") as z:
        z.writestr("images/a/.zattrs", "{}")
    (bia_dataset / "annotation_file_list.tsv").write_text("Files\tsource_image\nPLA4.zarr.zip\tPLA4.zarr.zip/images/a\n")
    assert run(bia_dataset, "bia")["BIA-FL-005"].status == "pass"


def test_idr_reference_to_renamed_table_is_a_warning(idr_dataset):
    """idr0086/idr0095: study names 'experimentB-assays.txt', the table present is 'experimentB-annotation.csv'."""
    a = idr_dataset / "idrtest-assays.txt"
    a.rename(idr_dataset / "idrtest-experimentB-annotation.csv")
    t = idr_dataset / "idrtest-experimentB-annotation.csv"
    t.write_text(t.read_text().replace("\t", ","))
    s = idr_dataset / "idrtest-study.txt"
    s.write_text(s.read_text().replace("idrtest-assays.txt", "ExperimentB_Assays, idrtest-experimentC-assays.txt"))
    res = run(idr_dataset, "idr")
    msgs = res["IDR-ASSAY-001"].messages
    assert res["IDR-ASSAY-001"].status == "fail"  # experiment C has no table at all
    assert any("looks like the table it means" in m and "ExperimentB_Assays" in m for m in msgs)
    assert any(m == "study file names assay file 'idrtest-experimentC-assays.txt' but it is not in the dataset" for m in msgs)


def test_idr_single_dangling_reference_pairs_with_single_table(idr_dataset):
    """idr0109: study names 'assayFile_27APR2021.txt'; the one table present is the curated annotation CSV."""
    s = idr_dataset / "idrtest-study.txt"
    s.write_text(s.read_text().replace("idrtest-assays.txt", "assayFile_27APR2021.txt"))
    res = run(idr_dataset, "idr")
    assert res["IDR-ASSAY-001"].status == "warn"
    assert "'idrtest-assays.txt' looks like the table it means" in res["IDR-ASSAY-001"].messages[0]


# ------------------------------------------------------------- regressions from ship-bar round 3


def test_file_list_may_name_a_directory(bia_dataset):
    """S-BIAD3835 lists the folder 'Source_Images'; BIA allows a directory path, so files under it are listed."""
    write_file_list(bia_dataset, ["series1"])
    res = run(bia_dataset, "bia")["BIA-FL-004"]
    assert res.status == "pass", res.messages
    write_file_list(bia_dataset, ["series1", "series1"])
    assert run(bia_dataset, "bia")["BIA-FL-004"].messages == ["listed more than once: series1"]
    write_file_list(bia_dataset, ["series2"])  # a directory that isn't there is still reported
    assert any("listed but not found: series2" in m for m in run(bia_dataset, "bia")["BIA-FL-004"].messages)


def test_pagetab_organism_taxon_from_valqual(bia_dataset):
    """Newer BIA studies put the NCBI taxon in the Organism attribute's valqual TermId."""
    page = json.loads(json.dumps(PAGETAB))
    org = page["section"]["subsections"][2][0]["attributes"][0]
    org["valqual"] = [{"name": "Ontology", "value": "NCBITaxon"}, {"name": "TermId", "value": "NCBITaxon_9606"}]
    (bia_dataset / "submission.yaml").unlink()
    (bia_dataset / "S-BIAD9999.json").write_text(json.dumps(page))
    bios = load_dataset(bia_dataset).metadata["biosample"]
    assert bios[0]["organism"][0]["ncbi_taxon"] == "NCBITaxon_9606"
    assert bios[1]["organism"][0]["ncbi_taxon"] is None


def test_binary_only_ome_tiff_whose_metadata_file_is_a_tiff(tmp_path):
    """OME sample 'binaryonly': Z2..Z5 point MetadataFile at multifile-Z1.ome.tiff, which holds the full OME-XML."""
    import numpy as np
    import tifffile

    from micro_validate.imageinfo import read_info

    ns = 'xmlns="http://www.openmicroscopy.org/Schemas/OME/2016-06"'
    full = (f'<?xml version="1.0"?><OME {ns}><Image ID="Image:0"><Pixels ID="Pixels:0" DimensionOrder="XYZCT" '
            'Type="uint8" SizeX="4" SizeY="6" SizeZ="2" SizeC="1" SizeT="1" PhysicalSizeX="0.5" PhysicalSizeY="0.5">'
            '<Channel ID="Channel:0"/><TiffData/></Pixels></Image></OME>')
    stub = f'<?xml version="1.0"?><OME {ns}><BinaryOnly MetadataFile="m-Z1.ome.tiff" UUID="urn:uuid:0"/></OME>'
    tifffile.imwrite(tmp_path / "m-Z1.ome.tiff", np.zeros((6, 4), "uint8"), description=full, metadata=None)
    tifffile.imwrite(tmp_path / "m-Z2.ome.tiff", np.zeros((6, 4), "uint8"), description=stub, metadata=None)
    info = read_info(tmp_path / "m-Z2.ome.tiff", "m-Z2.ome.tiff")
    assert info.readable and info.pixel_size_um["x"] == 0.5, info


def test_tiff_codec_missing_is_not_unreadable(tmp_path, monkeypatch):
    """BIA submissions hold LZW TIFFs; without imagecodecs tifffile can't decode them, but the file isn't bad."""
    import tifffile

    from micro_validate.imageinfo import read_info

    write_ome_tiff(tmp_path / "a.tif", ome=False)

    def no_codec(self, *a, **k):
        raise ValueError("<COMPRESSION.LZW: 5> requires the 'imagecodecs' package")

    monkeypatch.setattr(tifffile.TiffPage, "asarray", no_codec)
    info = read_info(tmp_path / "a.tif", "a.tif")
    assert info.readable is None and "imagecodecs" in info.notes[-1]


def test_mrc_map_is_an_image(tmp_path):
    """EMDB maps (EMD-2225.map) are MRC2014 volumes: read the header; a '.map' that isn't MRC stays 'other'."""
    import struct

    from micro_validate.imageinfo import classify, read_info

    h = bytearray(1024)
    h[0:16] = struct.pack("<4i", 8, 8, 4, 2)
    h[28:40] = struct.pack("<3i", 8, 8, 4)
    h[40:52] = struct.pack("<3f", 28.0, 28.0, 14.0)
    h[208:216] = b"MAP DA\0\0"
    (tmp_path / "emd.map").write_bytes(bytes(h) + b"\0" * (8 * 8 * 4 * 4))
    info = read_info(tmp_path / "emd.map", "emd.map")
    assert classify(tmp_path / "emd.map") == "mrc"
    assert info.readable and info.sizes["Z"] == 4 and abs(info.pixel_size_um["x"] - 3.5e-4) < 1e-9
    (tmp_path / "short.mrc").write_bytes(bytes(h) + b"\0" * 10)
    assert read_info(tmp_path / "short.mrc", "short.mrc").readable is False
    (tmp_path / "route.map").write_text("not an image")
    assert classify(tmp_path / "route.map") == "other"


def test_series_consistent_ignores_png_jpeg(tmp_path):
    """S-BIAD4056: photos of different leaves differ in size by design; not an acquisition series."""
    root = tmp_path / "ds"
    (root / "photos").mkdir(parents=True)
    for n, (w, h) in {"a.png": (10, 20), "b.png": (30, 40)}.items():
        _write_png(root / "photos" / n, w, h)
    res = run(root, "rembi")["REMBI-IMG-004"]
    assert res.status == "skip", res.messages


def _write_png(path: Path, w: int, h: int) -> None:
    import struct
    import zlib

    raw = b"".join(b"\0" + b"\0" * w for _ in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">2I5B", w, h, 8, 0, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


# ------------------------------------------------------------- regressions from ship-bar round 4


def test_ome_tiff_in_older_schema_is_readable(tmp_path):
    """Micro-Manager 1.4 writes OME 2015-01, Olympus exports 2016-DEV0; ome-types refuses both, the files are fine."""
    import numpy as np
    import tifffile

    from micro_validate.imageinfo import read_info

    for schema in ("2015-01", "2016-DEV0"):
        xml = (f'<?xml version="1.0"?><OME xmlns="http://www.openmicroscopy.org/Schemas/OME/{schema}">'
               '<Image ID="Image:0"><Pixels ID="Pixels:0" DimensionOrder="XYCZT" Type="uint16" SizeX="4" SizeY="6" '
               'SizeZ="1" SizeC="2" SizeT="1" PhysicalSizeX="0.2" PhysicalSizeY="0.2"><Channel ID="Channel:0:0" '
               'Name="FITC"/><Channel ID="Channel:0:1" Name="Rhodamine"/><TiffData/></Pixels></Image></OME>')
        f = tmp_path / f"mm_{schema}.ome.tif"
        tifffile.imwrite(f, np.zeros((2, 6, 4), "uint16"), description=xml, metadata=None)
        info = read_info(f, f.name)
        assert info.readable and info.is_ome, info.error
        assert info.sizes["C"] == 2 and info.pixel_size_um["x"] == 0.2 and info.channel_names == ["FITC", "Rhodamine"]
        assert schema in info.notes[-1]


def test_klb_and_fits_are_images(tmp_path):
    from micro_validate.imageinfo import classify

    for n in ("img.klb", "frame.fits"):
        (tmp_path / n).write_bytes(b"\0" * 64)
        assert classify(tmp_path / n) == "vendor"


def test_only_zipped_images_is_a_warning_not_no_images(tmp_path):
    """S-BIAD3450 submits every image inside .zip archives."""
    (tmp_path / "CTX_DIFF2_GCASE.zip").write_bytes(b"PK\x05\x06" + b"\0" * 18)
    res = run(tmp_path, "bia")["BIA-FMT-001"]
    assert res.status == "warn" and "1 archive(s) not inspected" in res.messages[0], res.messages


def test_series_consistent_compares_one_format(tmp_path):
    """Olympus folder: a 1920x1080 screen capture (.tif) beside the OME-TIFF stack is not part of the series."""
    root = tmp_path / "ds"
    write_ome_tiff(root / "stack.ome.tif", shape=(2, 16, 16))
    write_ome_tiff(root / "capture.tif", shape=(2, 40, 60), dtype="uint8", ome=False)
    assert run(root, "rembi")["REMBI-IMG-004"].status == "skip"
    write_ome_tiff(root / "stack2.ome.tif", shape=(2, 16, 16), dtype="uint8")
    assert run(root, "rembi")["REMBI-IMG-004"].status == "warn"
