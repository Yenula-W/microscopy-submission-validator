"""Build the held-out evaluation inputs (small subsets of real public datasets).

Usage: python -I scripts/holdout/fetch.py <out-dir>
Creates <out-dir>/inputs/<id>/ for every entry in MANIFEST and <out-dir>/manifest.json.
Large originals are subset: OME-Zarr keeps all JSON metadata but only the first chunk of
level 0; BIA studies keep the study JSON, the submitted file-list TSVs and the 2 smallest images.
"""
from __future__ import annotations

import io
import itertools
import json
import math
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

OME = "https://downloads.openmicroscopy.org/images"
IJ = "https://imagej.net/ij/images"
IDR_S3 = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr"
GH_RAW = "https://raw.githubusercontent.com/IDR"

MANIFEST = [
    # id, kind, spec
    ("H01-ome-artificial", "files", [f"{OME}/OME-TIFF/2016-06/bioformats-artificial/{n}" for n in (
        "single-channel.ome.tif", "multi-channel.ome.tif", "z-series.ome.tif", "time-series.ome.tif",
        "multi-channel-z-series.ome.tif")]),
    ("H02-ome-companion", "files", [f"{OME}/OME-TIFF/2016-06/companion/{n}" for n in (
        [f"multifile-Z{i}.ome.tiff" for i in range(1, 6)] + ["multifile.companion.ome"])]),
    ("H03-ome-modulo", "files", [f"{OME}/OME-TIFF/2016-06/modulo/{n}" for n in (
        "FLIM-ModuloAlongC.ome.tiff", "LAMBDA-ModuloAlongZ-ModuloAlongT.ome.tiff")]),
    ("H04-imagej-confocal-series", "zip", f"{IJ}/confocal-series.zip"),
    ("H05-imagej-5d", "zip", f"{IJ}/5d.zip"),
    ("H06-imagej-composites", "files", [f"{IJ}/Composite.tif", f"{IJ}/3_channel_inverted_luts.tif"]),
    ("H07-fluoview-tiff", "files", [f"{IJ}/fluoview-multi.tif"]),
    ("H08-zeiss-lsm", "files", [f"{IJ}/Cntrl1.lsm"]),
    ("H09-nikon-nd2", "files", [f"{OME}/ND2/aryeh/MeOh_high_fluo_{n}.nd2" for n in ("003", "007")]),
    ("H10-olympus-oib", "files", [f"{OME}/Olympus-FluoView/imagesc-71616/20220824_4492_cord_dapi__iba568_60x.oib"]),
    ("H11-metamorph-timelapse", "files", [f"{OME}/Metamorph/zenodo-13642395/{n}" for n in (
        ["test_timelapse_20240816.nd"] + [f"test_timelapse_20240816_s1_t{i}.TIF" for i in (1, 2, 3)])]),
    ("H12-plain-tiff-screen", "files", [f"{OME}/TIFF/condensation/{n}" for n in ("A1.pattern1.tif", "A1.pattern2.tif")]),
    # IDR: one OME-Zarr image (subset) + the study's published study/assay files where they exist
    ("H13-idr0052", "idr", {"zarr": "v0.4/idr0052A/5514375.zarr", "repo": "idr0052-walther-condensinmap",
                            "meta": ["idr0052-study.txt", "experimentA/MitoSys_assay_file.txt"]}),
    ("H14-idr0054", "idr", {"zarr": "v0.4/idr0054A/5025551.zarr", "repo": "idr0054-segura-tonsilhyperion",
                            "meta": ["idr0054-study.txt", "experimentA/idr0054-experimentA-assays.txt"]}),
    ("H15-idr0066-v05", "idr", {"zarr": "v0.5/idr0066/ExpD_chicken_embryo_MIP.ome.zarr", "repo": "idr0066-voigt-mesospim",
                                "meta": ["idr0066-study.txt", "experimentD/idr0066-chicken-assays.txt"]}),
    ("H16-idr0101", "idr", {"zarr": "v0.4/idr0101A/13457537.zarr", "repo": "idr0101-payne-insitugenomeseq",
                            "meta": ["idr0101-study.txt"]}),
    ("H17-idr0076", "idr", {"zarr": "v0.4/idr0076A/10501752.zarr", "repo": "idr0076-ali-metabric",
                            "meta": ["idr0076-study.txt"]}),
    ("H18-idr0047", "idr", {"zarr": "v0.4/idr0047A/4496763.zarr", "repo": "idr0047-neuert-yeastmrna",
                            "meta": ["idr0047-study.txt"]}),
    ("H19-idr0138", "idr", {"zarr": "v0.4/idr0138A/TimEmbryos-120919/HybCycle_29/MMStack_Pos9.ome.zarr",
                            "repo": "idr0138-lohoff-seqfish", "meta": ["idr0138-study.txt"]}),
    ("H20-idr0001-plate", "idr", {"zarr": "v0.4/idr0001A/2551.zarr", "repo": None, "meta": []}),
    # BioImage Archive: accepted, released studies
    ("H21-S-BIAD634", "bia", "S-BIAD634"),
    ("H22-S-BIAD4325", "bia", "S-BIAD4325"),
    ("H23-S-BIAD2619", "bia", "S-BIAD2619"),
    ("H24-S-BIAD4214", "bia", "S-BIAD4214"),
    ("H25-S-BIAD3623", "bia", "S-BIAD3623"),
    ("H26-S-BIAD4285", "bia", "S-BIAD4285"),
]

IMAGE_EXT = re.compile(r"\.(ome\.tiff?|tiff?|czi|nd2|lif|lsm|oib|ims|png|jpe?g|dv|mrc|zarr\.zip)$", re.I)


def get(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(urllib.parse.quote(url, safe=":/?=&%"), headers={"User-Agent": "micro-validate-eval"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def save(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def fetch_zarr_subset(base: str, out: Path) -> None:
    """Copy NGFF metadata of an image (v2 or v3 zarr) plus the first chunk of level 0."""
    def meta(rel: str) -> dict | None:
        for name in ("zarr.json", ".zattrs", ".zgroup", ".zarray"):
            try:
                data = get(f"{base}/{rel}{name}")
            except Exception:
                continue
            save(out / rel / name, data)
            if name in ("zarr.json", ".zattrs", ".zarray"):
                yield_meta[(rel, name)] = json.loads(data)
        return None

    yield_meta: dict = {}
    meta("")
    root = yield_meta.get(("", "zarr.json"), {}).get("attributes") or yield_meta.get(("", ".zattrs"), {})
    root = root.get("ome", root)
    if "plate" in root:  # HCS: first well, first field only
        well = root["plate"]["wells"][0]["path"]
        meta(f"{well}/")
        w = yield_meta.get((f"{well}/", "zarr.json"), {}).get("attributes") or yield_meta.get((f"{well}/", ".zattrs"), {})
        w = w.get("ome", w)
        field = w["well"]["images"][0]["path"]
        fetch_zarr_subset(f"{base}/{well}/{field}", out / well / field)
        return
    ms = root["multiscales"][0]
    for i, ds in enumerate(ms["datasets"]):
        p = ds["path"]
        meta(f"{p}/")
        if i:
            continue
        if (f"{p}/", ".zarray") in yield_meta:
            za = yield_meta[(f"{p}/", ".zarray")]
            key = za.get("dimension_separator", ".").join("0" * len(za["shape"]))
        else:
            za = yield_meta[(f"{p}/", "zarr.json")]
            enc = za.get("chunk_key_encoding", {"name": "default"})
            sep = enc.get("configuration", {}).get("separator", "/")
            zeros = sep.join("0" * len(za["shape"]))
            key = ("c" + sep + zeros) if enc.get("name", "default") == "default" else zeros
        try:
            save(out / p / key, get(f"{base}/{p}/{key}"))
        except Exception as e:
            print("  first chunk missing:", e)


def fetch_bia(acc: str, out: Path) -> dict:
    info = json.loads(get(f"https://www.ebi.ac.uk/biostudies/api/v1/studies/{acc}/info"))
    http = info["httpLink"]
    save(out / f"{acc}.json", get(f"https://www.ebi.ac.uk/biostudies/api/v1/studies/{acc}"))
    study = json.loads((out / f"{acc}.json").read_text())
    lists = sorted({a["value"] for a in _iter_attrs(study) if a.get("name") == "File List"})
    for fl in lists:
        stem = fl.rsplit(".", 1)[0]
        try:
            data = get(f"{http}/Files/{stem}.tsv")
        except Exception:
            data = _json_list_to_tsv(get(f"{http}/Files/{fl}"))
        save(out / f"{stem}.tsv" if "file_list" in stem.lower() else out / f"{stem}_file_list.tsv", data)
    files = json.loads(get(f"https://www.ebi.ac.uk/biostudies/api/v1/files/{acc}?start=0&length=5000"))["data"]
    imgs = sorted({(f["Size"], f["path"]) for f in files if IMAGE_EXT.search(f["path"]) and f.get("isDirectory") != "true"})
    picked = [p for s, p in imgs if s < 60_000_000][:2]
    for p in picked:
        save(out / p, get(f"{http}/Files/{p}"))
    return {"http": http, "file_lists": lists, "picked": picked, "n_files": len(files)}


def _iter_attrs(node):
    if isinstance(node, list):
        for x in node:
            yield from _iter_attrs(x)
    elif isinstance(node, dict):
        yield from node.get("attributes", []) or []
        for k in ("section", "subsections"):
            if k in node:
                yield from _iter_attrs(node[k])


def _json_list_to_tsv(raw: bytes) -> bytes:
    rows = json.loads(raw)
    cols: list[str] = []
    for r in rows:
        for a in r.get("attributes", []):
            if a["name"] not in cols:
                cols.append(a["name"])
    lines = ["\t".join(["Files"] + cols)]
    for r in rows:
        av = {a["name"]: str(a.get("value", "")) for a in r.get("attributes", [])}
        lines.append("\t".join([r["path"]] + [av.get(c, "") for c in cols]))
    return ("\n".join(lines) + "\n").encode()


def main() -> None:
    out = Path(sys.argv[1])
    only = set(sys.argv[2:])
    record = {}
    for hid, kind, spec in MANIFEST:
        if only and hid not in only:
            continue
        d = out / "inputs" / hid
        if d.exists() and any(d.iterdir()):
            print("have", hid)
            continue
        print("fetch", hid)
        src: dict = {"kind": kind}
        try:
            if kind == "files":
                for url in spec:
                    save(d / url.rsplit("/", 1)[1], get(url, 600))
                src["urls"] = spec
            elif kind == "zip":
                with zipfile.ZipFile(io.BytesIO(get(spec))) as z:
                    for n in z.namelist():
                        if not n.endswith("/") and "__MACOSX" not in n:
                            save(d / Path(n).name, z.read(n))
                src["urls"] = [spec]
            elif kind == "idr":
                name = Path(spec["zarr"]).name
                img_id = name.split(".")[0]
                try:
                    real = json.loads(get(f"https://idr.openmicroscopy.org/api/v0/m/images/{img_id}/"))["data"]["Name"]
                    stem = re.sub(r"(\.ome)?\.(tiff?|companion\.ome|czi|nd2|lif|dv|zarr)$", "", real, flags=re.I)
                    name = f"{stem}.ome.zarr"
                except Exception:
                    pass
                fetch_zarr_subset(f"{IDR_S3}/{spec['zarr']}", d / name)
                for m in spec["meta"]:
                    save(d / Path(m).name, get(f"{GH_RAW}/{spec['repo']}/HEAD/{m}"))
                src.update(spec, image_name=name)
            elif kind == "bia":
                src.update(acc=spec, **fetch_bia(spec, d))
        except Exception as e:
            print("  FAILED", hid, e)
            src["fetch_error"] = str(e)
        record[hid] = src
    mf = out / "manifest.json"
    old = json.loads(mf.read_text()) if mf.exists() else {}
    old.update(record)
    mf.write_text(json.dumps(old, indent=2))


if __name__ == "__main__":
    main()
