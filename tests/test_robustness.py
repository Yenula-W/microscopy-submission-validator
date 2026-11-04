"""Messy-input tests: the validator must report problems, never crash."""
from __future__ import annotations

import json
import os
import sys
import zipfile
from pathlib import Path

import pytest

from conftest import write_file_list, write_ome_tiff, write_ome_zarr
from micro_validate.cli import main

TARGETS = ["bia", "idr", "rembi"]


def run_all(root: Path, capsys) -> dict:
    out = {}
    for t in TARGETS:
        code = main([str(root), "-t", t, "--json"])
        assert code in (0, 1), f"{t}: exit {code}"
        out[t] = json.loads(capsys.readouterr().out)
        crashed = [r for r in out[t]["results"] if any("check crashed" in m for m in r["messages"])]
        assert not crashed, crashed
    return out


def test_empty_dataset(tmp_path, capsys):
    rep = run_all(tmp_path, capsys)
    assert rep["bia"]["overall"] == "fail"
    fmt = next(r for r in rep["bia"]["results"] if r["rule_id"] == "BIA-FMT-001")
    assert fmt["messages"] == ["no image files found in dataset"]


def test_dataset_is_a_file(tmp_path):
    f = tmp_path / "x.tif"
    f.write_bytes(b"")
    assert main([str(f), "-t", "bia"]) == 2


def test_binary_and_non_utf8_tables(tmp_path, capsys):
    write_ome_tiff(tmp_path / "a.ome.tif")
    (tmp_path / "file_list.tsv").write_bytes(b"Files\tc\n\xff\xfe\x00bad\tx\na.ome.tif\t\x80\n")
    (tmp_path / "x-study.txt").write_bytes(os.urandom(512))
    (tmp_path / "x-assays.txt").write_bytes(b"\x00\x01\x02")
    (tmp_path / "submission.yaml").write_bytes(b"\xff\xfe study: [")
    rep = run_all(tmp_path, capsys)
    meta = next(r for r in rep["bia"]["results"] if r["rule_id"] == "BIA-META-001")
    assert meta["status"] == "fail" and "cannot parse" in meta["messages"][0]


@pytest.mark.parametrize("content", ["study: [unclosed", "- just\n- a list\n", "", "{}", "study: 5\nbiosample: [1, 2]"])
def test_malformed_metadata(tmp_path, capsys, content):
    write_ome_tiff(tmp_path / "a.ome.tif")
    (tmp_path / "submission.yaml").write_text(content, encoding="utf-8")
    run_all(tmp_path, capsys)


def test_malformed_json_metadata(tmp_path, capsys):
    write_ome_tiff(tmp_path / "a.ome.tif")
    (tmp_path / "submission.json").write_text('{"study": {"title": ', encoding="utf-8")
    run_all(tmp_path, capsys)


def test_corrupt_images(tmp_path, capsys):
    (tmp_path / "zero.ome.tif").write_bytes(b"")
    (tmp_path / "junk.tif").write_bytes(os.urandom(2048))
    (tmp_path / "bad.ome.zarr.zip").write_bytes(b"PK\x03\x04 not really a zip")
    with zipfile.ZipFile(tmp_path / "empty.ome.zarr.zip", "w"):
        pass
    z = tmp_path / "badjson.ome.zarr"
    z.mkdir()
    (z / ".zattrs").write_text("{not json", encoding="utf-8")
    z2 = tmp_path / "nolevel.ome.zarr"
    z2.mkdir()
    (z2 / ".zattrs").write_text(json.dumps({"multiscales": [{"datasets": [{"path": "0"}]}]}), encoding="utf-8")
    z3 = tmp_path / "noattrs.zarr"
    z3.mkdir()
    (tmp_path / "x.czi").write_bytes(b"ZISRAWFILE" + os.urandom(100))
    (tmp_path / "p.png").write_bytes(b"\x89PNG\r\n")
    rep = run_all(tmp_path, capsys)
    readable = {i["path"]: i["readable"] for i in rep["bia"]["images"]}
    for bad in ["zero.ome.tif", "junk.tif", "bad.ome.zarr.zip", "empty.ome.zarr.zip", "badjson.ome.zarr",
                "nolevel.ome.zarr", "noattrs.zarr"]:
        assert readable[bad] is False, bad


def test_xml_garbage_in_ome_tiff(tmp_path, capsys):
    import numpy as np
    import tifffile

    tifffile.imwrite(tmp_path / "a.ome.tif", np.zeros((4, 4), "uint8"), description="<OME><Image>broken", metadata=None)
    rep = run_all(tmp_path, capsys)
    info = rep["bia"]["images"][0]
    assert info["readable"] in (True, False)  # either fallback-read or clean failure, never a crash


def test_huge_sparse_file_size_rule(tmp_path, capsys):
    f = tmp_path / "big.ome.tif"
    with open(f, "wb") as fh:
        fh.truncate(2_100_000_000_000)  # sparse: 2.1 TB apparent size, no disk use
    write_file_list(tmp_path, ["big.ome.tif"])
    rep = run_all(tmp_path, capsys)
    size = next(r for r in rep["bia"]["results"] if r["rule_id"] == "BIA-SIZE-001")
    assert size["status"] == "fail" and "2100.0 GB" in size["messages"][0]


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks")
def test_symlink_loop_and_broken_links(tmp_path, capsys):
    write_ome_tiff(tmp_path / "d" / "a.ome.tif")
    (tmp_path / "d" / "loop").symlink_to(tmp_path / "d", target_is_directory=True)
    (tmp_path / "self").symlink_to(tmp_path / "self")
    (tmp_path / "dangling.ome.tif").symlink_to(tmp_path / "nowhere.ome.tif")
    rep = run_all(tmp_path, capsys)
    paths = {i["path"] for i in rep["bia"]["images"]}
    assert "d/a.ome.tif" in paths


def test_unicode_paths(tmp_path, capsys):
    write_ome_tiff(tmp_path / "données" / "细胞 1.ome.tif")
    write_file_list(tmp_path, ["données/细胞 1.ome.tif"])
    rep = run_all(tmp_path, capsys)
    names = next(r for r in rep["bia"]["results"] if r["rule_id"] == "BIA-NAME-001")
    assert names["status"] == "fail"
    fl = next(r for r in rep["bia"]["results"] if r["rule_id"] == "BIA-FL-004")
    assert fl["status"] == "pass"


@pytest.mark.skipif(sys.platform == "win32" or os.geteuid() == 0, reason="needs POSIX non-root")
def test_unreadable_files_and_dirs(tmp_path, capsys):
    write_ome_tiff(tmp_path / "a.ome.tif")
    locked = write_ome_tiff(tmp_path / "locked.ome.tif")
    (tmp_path / "file_list.tsv").write_text("Files\na.ome.tif\nlocked.ome.tif\n", encoding="utf-8")
    (tmp_path / "x-study.txt").write_text("Study Title\tT\n", encoding="utf-8")
    sub = tmp_path / "private"
    sub.mkdir()
    write_ome_tiff(sub / "b.ome.tif")
    for p in (locked, tmp_path / "file_list.tsv", tmp_path / "x-study.txt"):
        p.chmod(0)
    sub.chmod(0)
    try:
        rep = run_all(tmp_path, capsys)
        readable = {i["path"]: i["readable"] for i in rep["bia"]["images"]}
        assert readable["locked.ome.tif"] is False
        fl = next(r for r in rep["bia"]["results"] if r["rule_id"] == "BIA-FL-001")
        assert fl["status"] == "fail" and "cannot read" in " ".join(fl["messages"])
    finally:
        for p in (locked, tmp_path / "file_list.tsv", tmp_path / "x-study.txt", sub):
            p.chmod(0o755)


def test_ragged_and_odd_tables(tmp_path, capsys):
    write_ome_zarr(tmp_path / "a.ome.zarr")
    (tmp_path / "file_list.tsv").write_text("\n\n", encoding="utf-8")
    (tmp_path / "s-study.txt").write_text("\t\t\n#only comments\n\tvalue without key\n", encoding="utf-8")
    (tmp_path / "s-assays.txt").write_text("Image File\tChannels\na.ome.zarr\nb\tx\ty\tz\n", encoding="utf-8")
    run_all(tmp_path, capsys)


def test_metadata_with_wrong_types(tmp_path, capsys):
    write_ome_tiff(tmp_path / "a.ome.tif")
    (tmp_path / "submission.yaml").write_text(
        "study:\n  title: 42\n  authors: 'Ada'\n  keywords: {a: 1}\n  private_until_date: 2026-01-01\n"
        "biosample:\n  organism: [null, 3]\n")
    rep = run_all(tmp_path, capsys)
    date = next(r for r in rep["bia"]["results"] if r["rule_id"] == "BIA-STUDY-004")
    assert date["status"] == "pass"  # YAML parses the date as datetime.date; still a valid date


def _has_bioio() -> bool:
    try:
        import bioio  # noqa: F401
    except ImportError:
        return False
    return True


@pytest.mark.skipif(_has_bioio(), reason="checks the behaviour without the [vendor] extra")
def test_vendor_file_without_extra_is_not_called_unreadable(tmp_path):
    from micro_validate.imageinfo import read_info

    (tmp_path / "scan.czi").write_bytes(b"ZISRAWFILE" + b"\0" * 100)
    info = read_info(tmp_path / "scan.czi", "scan.czi")
    assert info.readable is None
    assert any("micro-validate[vendor]" in n for n in info.notes)


def test_vendor_file_with_extra_but_no_plugin_is_not_called_unreadable(tmp_path):
    pytest.importorskip("bioio")
    from micro_validate.imageinfo import read_info

    # no bioio plugin reads Slidebook files; the [vendor] extra installs bioio alone
    (tmp_path / "scan.sld").write_bytes(b"\0" * 200)
    info = read_info(tmp_path / "scan.sld", "scan.sld")
    assert info.readable is None, info.error
    assert any("no bioio plugin" in n for n in info.notes)
