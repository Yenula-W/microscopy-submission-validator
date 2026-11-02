"""Classify image files by format and read the metadata the checks need."""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VENDOR_EXTS = {
    ".czi", ".nd2", ".lif", ".lsm", ".oib", ".oif", ".ims", ".vsi", ".svs", ".ndpi", ".scn",
    ".dv", ".r3d", ".lei", ".zvi", ".ics", ".ids", ".sld", ".mrc", ".dm3", ".dm4", ".ser",
    ".stk", ".nd", ".lof", ".lifext", ".mvd2", ".obf", ".msr", ".ome", ".xdce", ".flex",
    ".mrxs", ".bif", ".tf2", ".tf8", ".btf", ".ets", ".spe", ".fli", ".oir", ".lsr",
}
RASTER_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".jp2"}
TABLE_EXTS = {".tsv", ".csv", ".txt", ".xlsx", ".xls", ".json", ".yaml", ".yml", ".md", ".pdf"}

TO_MICRON = {"pm": 1e-6, "nm": 1e-3, "µm": 1.0, "um": 1.0, "micron": 1.0, "micrometer": 1.0,
             "mm": 1e3, "millimeter": 1e3, "cm": 1e4, "m": 1e6, "meter": 1e6, "nanometer": 1e-3,
             "Å": 1e-4, "angstrom": 1e-4}


def classify(path: Path) -> str:
    """Return one of: ome-tiff, ome-zarr, ome-zarr-zip, tiff, vendor, raster, table, other."""
    name = path.name.lower()
    if path.is_dir():
        return "ome-zarr" if name.endswith(".zarr") else "other"
    if name.endswith((".ome.tif", ".ome.tiff", ".ome.tf2", ".ome.tf8", ".ome.btf")):
        return "ome-tiff"
    if name.endswith(".zarr.zip"):
        return "ome-zarr-zip"
    suffix = path.suffix.lower()
    if suffix in (".tif", ".tiff"):
        return "tiff"
    if suffix in VENDOR_EXTS:
        return "vendor"
    if suffix in RASTER_EXTS:
        return "raster"
    if suffix in TABLE_EXTS:
        return "table"
    return "other"


IMAGE_FORMATS = {"ome-tiff", "ome-zarr", "ome-zarr-zip", "tiff", "vendor", "raster"}


@dataclass
class ImageInfo:
    path: str
    format: str
    readable: bool | None = None  # None = not verified (no reader available)
    error: str = ""
    is_ome: bool = False
    sizes: dict[str, int] = field(default_factory=dict)  # X Y Z C T
    dtype: str = ""
    pixel_size_um: dict[str, float | None] = field(default_factory=dict)  # x y z
    channel_names: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _um(value: float | None, unit: Any) -> float | None:
    if value is None:
        return None
    u = getattr(unit, "value", unit) or "µm"
    factor = TO_MICRON.get(str(u))
    return value * factor if factor is not None else None


def read_info(path: Path, rel: str, verify_pixels: bool = True) -> ImageInfo:
    fmt = classify(path)
    info = ImageInfo(path=rel, format=fmt)
    try:
        if fmt in ("ome-tiff", "tiff"):
            _read_tiff(path, info, verify_pixels)
        elif fmt == "ome-zarr":
            _read_zarr_dir(path, info, verify_pixels)
        elif fmt == "ome-zarr-zip":
            _read_zarr_zip(path, info)
        elif fmt == "vendor":
            _read_bioio(path, info)
        else:
            info.readable = None
            info.notes.append("no reader for this format; readability not verified")
    except Exception as e:
        info.readable = False
        info.error = f"{type(e).__name__}: {e}"
    return info


def _read_tiff(path: Path, info: ImageInfo, verify_pixels: bool) -> None:
    import tifffile

    with tifffile.TiffFile(path) as tif:
        xml = tif.ome_metadata
        if xml:
            _apply_ome_xml(xml, info)
        else:
            s = tif.series[0]
            info.dtype = str(s.dtype)
            axes = s.axes.upper()
            for ax, n in zip(axes, s.shape):
                key = {"S": "C", "I": "Z", "Q": "Z"}.get(ax, ax)
                if key in "XYZCT":
                    info.sizes[key] = info.sizes.get(key, 1) * n
            for k in "XYZCT":
                info.sizes.setdefault(k, 1)
            info.pixel_size_um = _tiff_resolution(tif)
            if info.format == "ome-tiff":
                info.notes.append("file named .ome.tif but contains no OME-XML")
        if verify_pixels:
            tif.pages[0].asarray()
    info.readable = True


def _tiff_resolution(tif: Any) -> dict[str, float | None]:
    page = tif.pages[0]
    ij = tif.imagej_metadata or {}
    unit = ij.get("unit")
    out: dict[str, float | None] = {"x": None, "y": None, "z": None}
    try:
        xr = page.tags["XResolution"].value
        yr = page.tags["YResolution"].value
        runit = page.tags.get("ResolutionUnit")
        runit = int(runit.value) if runit is not None else 1
        # Inch-based resolution is almost always a screen DPI default, so only trust an
        # ImageJ unit or centimetre resolution.
        if unit:
            scale = TO_MICRON.get(str(unit).replace("\\u00B5", "µ"), None)
        else:
            scale = 10000.0 if runit == 3 else None
        if scale and xr[0] and yr[0]:
            out["x"] = xr[1] / xr[0] * scale
            out["y"] = yr[1] / yr[0] * scale
        if "spacing" in ij and scale:
            out["z"] = float(ij["spacing"]) * scale
    except (KeyError, ZeroDivisionError, TypeError):
        pass
    return out


def _apply_ome_xml(xml: str, info: ImageInfo) -> None:
    from ome_types import from_xml

    ome = from_xml(xml)
    if not ome.images:
        raise ValueError("OME-XML has no Image elements")
    info.is_ome = True
    px = ome.images[0].pixels
    info.sizes = {"X": px.size_x, "Y": px.size_y, "Z": px.size_z, "C": px.size_c, "T": px.size_t}
    info.dtype = getattr(px.type, "value", str(px.type))
    info.pixel_size_um = {
        "x": _um(px.physical_size_x, px.physical_size_x_unit),
        "y": _um(px.physical_size_y, px.physical_size_y_unit),
        "z": _um(px.physical_size_z, px.physical_size_z_unit),
    }
    info.channel_names = [c.name or "" for c in px.channels]
    if len(ome.images) > 1:
        info.notes.append(f"{len(ome.images)} images (series) in OME-XML; using the first")


def _ngff_attrs(attrs: dict[str, Any]) -> dict[str, Any]:
    return attrs.get("ome", attrs)  # NGFF 0.5 nests under "ome"


def _apply_ngff(attrs: dict[str, Any], array_meta: dict[str, Any], info: ImageInfo) -> None:
    ms = attrs["multiscales"][0]
    axes = [a["name"] if isinstance(a, dict) else a for a in ms.get("axes", ["t", "c", "z", "y", "x"])]
    shape = array_meta["shape"]
    info.sizes = {k: 1 for k in "XYZCT"}
    for name, n in zip(axes, shape):
        info.sizes[name.upper()] = n
    raw = array_meta.get("dtype") or array_meta.get("data_type")
    try:
        import numpy as np

        info.dtype = str(np.dtype(raw))  # '<u2' -> 'uint16'
    except TypeError:
        info.dtype = str(raw)
    info.is_ome = True
    scale = None
    for ct in ms["datasets"][0].get("coordinateTransformations", []):
        if ct.get("type") == "scale":
            scale = ct["scale"]
    units = {a["name"]: a.get("unit") for a in ms.get("axes", []) if isinstance(a, dict)}
    info.pixel_size_um = {"x": None, "y": None, "z": None}
    if scale:
        for name, v in zip(axes, scale):
            if name in ("x", "y", "z"):
                u = units.get(name)
                info.pixel_size_um[name] = _um(v, u) if u else None
                if not u:
                    info.notes.append(f"axis {name} has no unit; physical size not established")
    omero = attrs.get("omero", {})
    info.channel_names = [c.get("label", "") for c in omero.get("channels", [])]


def _read_json(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text())


def _read_zarr_dir(path: Path, info: ImageInfo, verify_pixels: bool) -> None:
    if (path / "zarr.json").exists():
        attrs = _read_json(path / "zarr.json").get("attributes", {})
    elif (path / ".zattrs").exists():
        attrs = _read_json(path / ".zattrs")
    else:
        raise ValueError("not a zarr group (no .zattrs or zarr.json)")
    attrs = _ngff_attrs(attrs)
    if "multiscales" not in attrs:
        if "plate" in attrs or "bioformats2raw.layout" in attrs:
            raise ValueError("HCS plate / bioformats2raw container: per-image checks not supported yet")
        raise ValueError("zarr group has no 'multiscales' (not an OME-Zarr image)")
    level0 = path / attrs["multiscales"][0]["datasets"][0]["path"]
    if (level0 / "zarr.json").exists():
        meta = _read_json(level0 / "zarr.json")
    else:
        meta = _read_json(level0 / ".zarray")
    _apply_ngff(attrs, meta, info)
    if verify_pixels:
        import zarr

        arr = zarr.open_array(str(level0), mode="r")
        arr[(0,) * arr.ndim]
    info.readable = True


def _read_zarr_zip(path: Path, info: ImageInfo) -> None:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        bad = zf.testzip()
        if bad:
            raise ValueError(f"corrupt member in zip: {bad}")
        meta_names = sorted((n for n in names if n.endswith((".zattrs", "zarr.json"))), key=len)
        for n in meta_names:
            raw = json.loads(zf.read(n))
            attrs = _ngff_attrs(raw.get("attributes", raw) if n.endswith("zarr.json") else raw)
            if "multiscales" in attrs:
                prefix = n.rsplit("/", 1)[0] + "/" if "/" in n else ""
                lvl = prefix + attrs["multiscales"][0]["datasets"][0]["path"]
                arr_meta_name = f"{lvl}/zarr.json" if f"{lvl}/zarr.json" in names else f"{lvl}/.zarray"
                _apply_ngff(attrs, json.loads(zf.read(arr_meta_name)), info)
                info.readable = True
                return
    raise ValueError("zip contains no OME-Zarr multiscales image")


def _read_bioio(path: Path, info: ImageInfo) -> None:
    try:
        from bioio import BioImage  # optional extra
    except ImportError:
        info.readable = None
        info.notes.append("vendor format: install 'micro-validate[vendor]' plus a bioio reader plugin to verify")
        return
    img = BioImage(path)
    d = img.dims
    info.sizes = {"X": d.X, "Y": d.Y, "Z": d.Z, "C": d.C, "T": d.T}
    info.dtype = str(img.dtype)
    ps = img.physical_pixel_sizes
    info.pixel_size_um = {"x": ps.X, "y": ps.Y, "z": ps.Z}
    info.channel_names = list(img.channel_names or [])
    info.readable = True
