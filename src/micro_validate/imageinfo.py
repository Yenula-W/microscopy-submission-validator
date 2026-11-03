"""Classify image files by format and read the metadata the checks need."""
from __future__ import annotations

import html
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VENDOR_EXTS = {
    ".czi", ".nd2", ".lif", ".lsm", ".oib", ".oif", ".ims", ".vsi", ".svs", ".ndpi", ".scn",
    ".dv", ".r3d", ".lei", ".zvi", ".ics", ".ids", ".sld", ".mrc", ".dm3", ".dm4", ".ser",
    ".stk", ".nd", ".lof", ".lifext", ".mvd2", ".obf", ".msr", ".ome", ".xdce", ".flex",
    ".mrxs", ".bif", ".tf2", ".tf8", ".btf", ".ets", ".spe", ".fli", ".oir", ".lsr", ".klb", ".fits", ".fit",
}
TIFF_BASED_VENDOR = {".lsm", ".stk"}
# MRC2014 (EM maps, tomograms, particle stacks); ".map" is only MRC when the header says so
MRC_EXTS = {".mrc", ".mrcs", ".map", ".rec"}
# metadata files that accompany images but hold no pixels: OME companion XML, MetaMorph .nd index
SIDECAR_SUFFIXES = (".companion.ome", ".ome.xml", ".nd")
RASTER_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".jp2"}
TABLE_EXTS = {".tsv", ".csv", ".txt", ".xlsx", ".xls", ".json", ".yaml", ".yml", ".md", ".pdf"}

TO_MICRON = {"pm": 1e-6, "nm": 1e-3, "µm": 1.0, "um": 1.0, "micron": 1.0, "micrometer": 1.0,
             "mm": 1e3, "millimeter": 1e3, "cm": 1e4, "m": 1e6, "meter": 1e6, "nanometer": 1e-3,
             "Å": 1e-4, "angstrom": 1e-4}


def classify(path: Path) -> str:
    """Return one of: ome-tiff, ome-zarr, ome-zarr-zip, ome-xml, tiff, mrc, vendor, raster, sidecar, table, other."""
    name = path.name.lower()
    if path.is_dir():
        return "ome-zarr" if name.endswith(".zarr") else "other"
    if name.endswith((".ome.tif", ".ome.tiff", ".ome.tf2", ".ome.tf8", ".ome.btf")):
        return "ome-tiff"
    if name.endswith(".zarr.zip"):
        return "ome-zarr-zip"
    if name.endswith(".ome.xml") and b"BinData" in _head(path, 1 << 20):
        return "ome-xml"  # OME-XML carrying its own pixels (OME sample data 2012-06)
    if name.endswith(SIDECAR_SUFFIXES):
        return "sidecar"
    suffix = path.suffix.lower()
    if suffix in (".tif", ".tiff"):
        return "tiff"
    if suffix in MRC_EXTS and (suffix in (".mrc", ".mrcs") or _is_mrc(path)):
        return "mrc"
    if suffix in VENDOR_EXTS or (suffix == ".am" and _head(path).startswith((b"# AmiraMesh", b"# Avizo"))):
        return "vendor"
    if suffix in RASTER_EXTS:
        return "raster"
    if suffix in TABLE_EXTS:
        return "table"
    return "other"


IMAGE_FORMATS = {"ome-tiff", "ome-zarr", "ome-zarr-zip", "ome-xml", "tiff", "mrc", "vendor", "raster"}


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
        elif fmt == "ome-xml":
            # pattern read: ome-types rejects some BinData layouts, and the pixels aren't decoded anyway
            _apply_ome_xml_lenient(path.read_text(encoding="utf-8", errors="replace"), info)
            info.notes.append("pixels embedded as BinData (not decoded)")
            info.readable = True
        elif fmt == "mrc":
            _read_mrc_header(path, info)
        elif fmt == "vendor" and path.suffix.lower() in TIFF_BASED_VENDOR:
            _read_tiff(path, info, verify_pixels)  # Zeiss LSM, MetaMorph STK, Olympus FluoView TIFFs
        elif fmt == "vendor":
            _read_bioio(path, info)
        elif fmt == "raster" and path.suffix.lower() in (".png", ".jpg", ".jpeg"):
            _read_raster_header(path, info)
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
        binary_only = re.search(r'<(?:\w+:)?BinaryOnly[^>]*MetadataFile="([^"]+)"', xml or "")
        if binary_only:
            # valid OME-TIFF whose metadata lives in a companion file (OME-TIFF spec, "BinaryOnly")
            companion = path.parent / binary_only.group(1)
            if companion.is_file() and companion.suffix.lower() in (".tif", ".tiff", ".tf2", ".tf8", ".btf"):
                # the metadata file may itself be an OME-TIFF of the set (OME sample data "binaryonly")
                with tifffile.TiffFile(companion) as master:
                    _apply_ome_xml(master.ome_metadata or "", info)
                info.notes.append(f"metadata read from {companion.name}")
            elif companion.is_file():
                _apply_ome_xml(companion.read_text(encoding="utf-8", errors="replace"), info)
                info.notes.append(f"metadata read from companion file {companion.name}")
            else:
                _apply_tiff_series(tif, info)
                info.is_ome = True
                info.notes.append(f"binary-only OME-TIFF; companion metadata file {binary_only.group(1)!r} not found")
        elif xml:
            try:
                _apply_ome_xml(xml, info)
            except ValueError as e:
                if "Could not parse XML" not in str(e) and "not well-formed" not in str(e):
                    raise
                # S-BIAD3778 writes literal "\n" between attributes; the TIFF itself is fine
                _apply_tiff_series(tif, info)
                info.pixel_size_um = _tiff_resolution(tif)
                try:  # the calibration is usually still legible in the broken XML
                    lenient = ImageInfo(path=info.path, format=info.format)
                    _apply_ome_xml_lenient(xml.replace("\\n", " "), lenient)
                    info.pixel_size_um = {k: v for k, v in lenient.pixel_size_um.items() if v} or info.pixel_size_um
                except (ValueError, KeyError):
                    pass
                info.notes.append("OME-XML header is not valid XML (re-save with Bio-Formats/bfconvert to repair it); "
                                  "read as plain TIFF")
        else:
            _apply_tiff_series(tif, info)
            info.pixel_size_um = _tiff_resolution(tif)
            _vendor_tiff_calibration(tif, info)
            if info.format == "ome-tiff":
                info.notes.append("file named .ome.tif but contains no OME-XML")
        if verify_pixels:
            try:
                tif.pages[0].asarray()
            except ValueError as e:
                if "imagecodecs" not in str(e):
                    raise
                # e.g. LZW: a valid TIFF this install can't decode; not evidence the file is bad
                info.readable = None
                info.notes.append(f"header read, pixels not decoded ({e}); pip install imagecodecs to check them")
                return
    info.readable = True


def _apply_tiff_series(tif: Any, info: ImageInfo) -> None:
    s = tif.series[0]
    info.dtype = str(s.dtype)
    for ax, n in zip(s.axes.upper(), s.shape):
        key = {"S": "C", "I": "Z", "Q": "Z"}.get(ax, ax)
        if key in "XYZCT":
            info.sizes[key] = info.sizes.get(key, 1) * n
    for k in "XYZCT":
        info.sizes.setdefault(k, 1)


def _vendor_tiff_calibration(tif: Any, info: ImageInfo) -> None:
    """Vendor TIFF flavours keep calibration outside the TIFF resolution tags."""
    ps = info.pixel_size_um
    if tif.is_lsm and tif.lsm_metadata:
        for ax in "xyz":  # Zeiss LSM: voxel sizes in metres
            v = tif.lsm_metadata.get(f"VoxelSize{ax.upper()}")
            if v:
                ps[ax] = float(v) * 1e6
    elif tif.is_fluoview and tif.fluoview_metadata:
        for dim in tif.fluoview_metadata.get("Dimensions", []):  # (name, size, origin, step, unit)
            name, _, _, step, unit = dim[:5]
            if str(name).lower() in ("x", "y", "z") and step:
                ps[str(name).lower()] = _um(float(step), unit or "µm")
    elif (tif.pages[0].description or "").lstrip().startswith("<MetaData>"):  # MetaMorph / MetaSeries XML
        desc = tif.pages[0].description

        def prop(key: str) -> str | None:
            m = re.search(rf'id="{key}" type="\w+" value="([^"]*)"', desc)
            return m.group(1) if m else None

        unit = prop("spatial-calibration-units")
        for ax in "xy":
            v = prop(f"spatial-calibration-{ax}")
            if v and unit and unit.lower() not in ("pixel", "pixels"):
                ps[ax] = _um(float(v), unit)


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
        px_per_unit = xr[0] / xr[1] if xr[1] else 0
        if not unit and runit == 3 and round(px_per_unit, 2) in (72.0, 96.0, 300.0, 28.35, 37.8, 118.11):
            scale = None  # dpi default (e.g. Olympus FluoView writes 72/cm), not a microscope calibration
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

    try:
        ome = from_xml(xml)
    except (ValueError, ImportError) as e:
        ns = re.search(r'xmlns(?::\w+)?="(http://www\.openmicroscopy\.org/Schemas/OME/[^"]+)"', xml)
        if not ns or "/2016-06" in ns.group(1):
            raise
        # older or pre-release schema (Micro-Manager 1.4: 2015-01, Olympus exports: 2016-DEV0); ome-types reads only 2016-06
        _apply_ome_xml_lenient(xml, info)
        info.notes.append(f"OME-XML uses schema {ns.group(1).rsplit('/', 1)[1]}; read leniently "
                          "(re-saving with current Bio-Formats updates it to 2016-06)")
        return
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


def _apply_ome_xml_lenient(xml: str, info: ImageInfo) -> None:
    """Pixels/Channel attributes by pattern, for OME-XML in schemas ome-types refuses."""
    m = re.search(r"<(?:\w+:)?Pixels\b([^>]*)>", xml)
    if not m:
        raise ValueError("OME-XML has no Pixels element")
    attrs = {k: html.unescape(v) for k, v in re.findall(r'(\w+)="([^"]*)"', m.group(1))}  # PhysicalSizeXUnit="&#181;m"
    info.is_ome = True
    info.sizes = {k: int(attrs.get(f"Size{k}", 1)) for k in "XYZCT"}
    info.dtype = attrs.get("Type", "")

    def size(ax: str) -> float | None:
        try:
            return _um(float(attrs[f"PhysicalSize{ax}"]), attrs.get(f"PhysicalSize{ax}Unit", "µm"))
        except (KeyError, ValueError):
            return None

    info.pixel_size_um = {ax.lower(): size(ax) for ax in "XYZ"}
    info.channel_names = re.findall(r'<(?:\w+:)?Channel\b[^>]*\bName="([^"]*)"', xml)


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
    units = {}
    for a in ms.get("axes", []):
        if isinstance(a, dict):
            units[a["name"]] = a.get("unit") or a.get("units")
            if a.get("units") and not a.get("unit"):  # seen in IDR idr0047
                info.notes.append(f"axis {a['name']} uses non-standard key 'units' instead of 'unit'")
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
            kind = "HCS plate" if "plate" in attrs else "bioformats2raw container"
            info.readable = None  # valid OME-Zarr, just not something we inspect per image yet
            info.is_ome = True
            info.notes.append(f"OME-Zarr {kind}: per-image checks are not supported yet")
            return
        raise ValueError("zarr group has no 'multiscales' (not an OME-Zarr image)")
    level0 = path / attrs["multiscales"][0]["datasets"][0]["path"]
    if (level0 / "zarr.json").exists():
        meta = _read_json(level0 / "zarr.json")
    else:
        meta = _read_json(level0 / ".zarray")
    _apply_ngff(attrs, meta, info)
    if verify_pixels:
        import zarr

        if (level0 / "zarr.json").exists() and int(zarr.__version__.split(".")[0]) < 3:
            info.notes.append("zarr v3 array: pixel decode needs zarr>=3 (Python>=3.11); metadata checked only")
        else:
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


def _read_raster_header(path: Path, info: ImageInfo) -> None:
    """Check PNG/JPEG headers (no pixel decode): enough to catch truncated or mislabelled files."""
    import struct

    with open(path, "rb") as fh:
        head = fh.read(65536)
    if path.suffix.lower() == ".png":
        if not head.startswith(b"\x89PNG\r\n\x1a\n") or head[12:16] != b"IHDR":
            raise ValueError("not a valid PNG (bad signature or missing IHDR)")
        w, h, depth, ctype = struct.unpack(">IIBB", head[16:26])
        channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype, 1)
        info.dtype = "uint16" if depth == 16 else "uint8"
    else:
        if not head.startswith(b"\xff\xd8"):
            raise ValueError("not a valid JPEG (missing SOI marker)")
        i, w, h, channels = 2, 0, 0, 0
        while i + 9 < len(head):
            if head[i] != 0xFF:
                i += 1
                continue
            marker, seglen = head[i + 1], struct.unpack(">H", head[i + 2:i + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", head[i + 5:i + 9])
                channels = head[i + 9] if i + 9 < len(head) else 1
                break
            i += 2 + seglen
        if not w:
            raise ValueError("JPEG frame header not found")
        info.dtype = "uint8"
    info.sizes = {"X": w, "Y": h, "Z": 1, "C": channels, "T": 1}
    info.pixel_size_um = {"x": None, "y": None, "z": None}
    info.readable = True
    info.notes.append("header checked only (PNG/JPEG carry no microscopy calibration)")


def _head(path: Path, n: int = 64) -> bytes:
    try:
        with open(path, "rb") as fh:
            return fh.read(n)
    except OSError:
        return b""


def _is_mrc(path: Path) -> bool:
    try:
        with open(path, "rb") as fh:
            return fh.read(212)[208:212] == b"MAP "
    except OSError:
        return False


def _read_mrc_header(path: Path, info: ImageInfo) -> None:
    """MRC2014 header: NX NY NZ MODE (int32), MX MY MZ (int32 at 28), cell lengths in Å (float32 at 40)."""
    import struct

    with open(path, "rb") as fh:
        h = fh.read(1024)
    if len(h) < 1024 or h[208:212] != b"MAP ":
        raise ValueError("not an MRC2014 file (no 'MAP ' tag in the header)")
    endian = "<" if h[212] in (0x44, 0x41) else ">"
    nx, ny, nz, mode = struct.unpack(endian + "4i", h[0:16])
    mx, my, mz = struct.unpack(endian + "3i", h[28:40])
    cx, cy, cz = struct.unpack(endian + "3f", h[40:52])
    dtypes = {0: "int8", 1: "int16", 2: "float32", 4: "complex64", 6: "uint16", 12: "float16"}
    info.sizes = {"X": nx, "Y": ny, "Z": nz, "C": 1, "T": 1}
    info.dtype = dtypes.get(mode, f"mode {mode}")
    info.pixel_size_um = {ax: c / m * 1e-4 for ax, c, m in (("x", cx, mx), ("y", cy, my), ("z", cz, mz)) if m > 0 and c > 0}
    expected = 1024 + struct.unpack(endian + "i", h[92:96])[0] + nx * ny * nz * {0: 1, 1: 2, 2: 4, 4: 8, 6: 2, 12: 2}.get(mode, 0)
    if path.stat().st_size < expected:
        raise ValueError(f"MRC file truncated: {path.stat().st_size} bytes, header implies {expected}")
    info.notes.append("MRC header checked (pixel data not decoded)")
    info.readable = True


def _read_bioio(path: Path, info: ImageInfo) -> None:
    try:
        from bioio import BioImage  # optional extra
    except ImportError:
        info.readable = None
        info.notes.append("no reader installed for this vendor format; install micro-validate[vendor] and a bioio plugin to check it")
        return
    try:
        img = BioImage(path)
    except Exception as e:
        if type(e).__name__ != "UnsupportedFileFormatError":
            raise
        # bioio is installed but none of its plugins handles this format: not evidence the file is bad
        info.readable = None
        info.notes.append(f"no bioio plugin installed for {path.suffix} files; install one (see bioio's plugin list) to check it")
        return
    d = img.dims
    info.sizes = {"X": d.X, "Y": d.Y, "Z": d.Z, "C": d.C, "T": d.T}
    info.dtype = str(img.dtype)
    ps = img.physical_pixel_sizes
    info.pixel_size_um = {"x": ps.X, "y": ps.Y, "z": ps.Z}
    info.channel_names = list(img.channel_names or [])
    info.readable = True
