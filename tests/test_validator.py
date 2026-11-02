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


def test_bia_inconsistent_series(bia_dataset):
    write_ome_tiff(bia_dataset / "series1" / "img_02.ome.tif", shape=(3, 16, 16), px=0.2)
    res = run(bia_dataset, "bia")
    msgs = " ".join(res["BIA-IMG-003"].messages)
    assert res["BIA-IMG-003"].status == "fail"
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
    assert "matched only by name stem" in res["IDR-ASSAY-003"].messages[0]
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
