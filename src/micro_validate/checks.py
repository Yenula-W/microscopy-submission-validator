"""Check implementations referenced by name from the rules YAML files."""
from __future__ import annotations

import math
import re
from collections import defaultdict
from pathlib import PurePosixPath
from typing import Any, Iterator

from .dataset import Dataset
from .engine import Issue, SkipCheck, check
from .imageinfo import IMAGE_FORMATS, classify

PLACEHOLDERS = {"", "todo", "tbd", "fill in", "xxx", "n/a", "na", "none", "null", "unknown", "?", "-"}


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, dict)):
        return len(value) == 0
    s = str(value).strip()
    return s.lower() in PLACEHOLDERS or s.startswith("#")


def resolve(obj: Any, path: str) -> Iterator[tuple[str, Any]]:
    """Yield (concrete_path, value) for a dotted path; 'a[*].b' fans out over list a."""

    def walk(o: Any, toks: list[str], prefix: str) -> Iterator[tuple[str, Any]]:
        if not toks:
            yield prefix, o
            return
        t = toks[0]
        star = t.endswith("[*]")
        key = t[:-3] if star else t
        v = o.get(key) if isinstance(o, dict) else None
        p = f"{prefix}.{key}" if prefix else key
        if star:
            if isinstance(v, dict):
                v = [v]  # a single object where a list is expected is fine
            if not isinstance(v, list) or not v:
                yield p, None
                return
            for i, item in enumerate(v):
                yield from walk(item, toks[1:], f"{p}[{i}]")
        else:
            yield from walk(v, toks[1:], p)

    yield from walk(obj, path.split("."), "")


def _need_metadata(ds: Dataset) -> dict[str, Any]:
    if ds.metadata is None:
        raise SkipCheck("no readable submission metadata file (see metadata rule)")
    return ds.metadata


# ---------------------------------------------------------------- metadata


@check("metadata_present")
def metadata_present(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    if ds.metadata_error:
        return [Issue("problem", f"{ds.metadata_path}: cannot parse: {ds.metadata_error}")]
    if ds.metadata is None:
        return [Issue("problem", "no metadata file found in the dataset root (submission.yaml, submission.json "
                                 "or a BioStudies S-BIAD*.json export)")]
    return []


@check("field_present")
def field_present(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    """params: path | any_of: [paths]; optional if_present: path; pattern: regex; allowed: [values]."""
    meta = _need_metadata(ds)
    if "if_present" in params:
        if all(is_missing(v) for _, v in resolve(meta, params["if_present"])):
            return []
    paths = params.get("any_of") or [params["path"]]
    issues: list[Issue] = []
    found_any = False
    for path in paths:
        missing = [p for p, v in resolve(meta, path) if is_missing(v)]
        if not missing:
            found_any = True
            break
        issues.extend(Issue("problem", f"missing or empty: {p}") for p in missing)
    if not found_any:
        if len(paths) > 1:
            first_missing = [i.message.split(": ", 1)[1] for i in issues][:5]
            return [Issue("problem", f"none of these is filled in: {', '.join(paths)} (missing: {', '.join(first_missing)})")]
        return issues
    pattern = params.get("pattern")
    allowed = params.get("allowed")
    out: list[Issue] = []
    for p, v in resolve(meta, path):
        if pattern and not re.search(pattern, str(v)):
            out.append(Issue("problem", f"{p} = {v!r} does not match expected form /{pattern}/"))
        if allowed and str(v) not in [str(a) for a in allowed]:
            out.append(Issue("problem", f"{p} = {v!r}; expected one of {allowed}"))
    return out


# ---------------------------------------------------------------- formats and image content


@check("formats_accepted")
def formats_accepted(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    """params.levels: {format: pass|warn|fail}; params.messages: {format: text}."""
    levels = params.get("levels", {})
    msgs = params.get("messages", {})
    images = ds.image_files
    if not images:
        archives = [f for f in ds.data_files if f.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".7z", ".rar"))]
        if archives:  # S-BIAD3450 submits every image zipped
            sample = ", ".join(archives[:3]) + (f" (+{len(archives) - 3} more)" if len(archives) > 3 else "")
            return [Issue("warning", f"no image files outside archives; {len(archives)} archive(s) not inspected "
                                     f"(images inside them can't be checked or viewed): {sample}")]
        return [Issue("problem", "no image files found in dataset")]
    issues = []
    by_fmt: dict[str, list[str]] = defaultdict(list)
    for f in images:
        by_fmt[classify(ds.root / f)].append(f)
    for fmt, files in sorted(by_fmt.items()):
        level = levels.get(fmt, params.get("default", "warn"))
        if level == "pass":
            continue
        sample = ", ".join(files[:3]) + (f" (+{len(files) - 3} more)" if len(files) > 3 else "")
        note = msgs.get(fmt, f"format '{fmt}' not in the preferred list")
        issues.append(Issue("problem" if level == "fail" else "warning", f"{len(files)} {fmt} file(s): {note}: {sample}"))
    return issues


@check("images_readable")
def images_readable(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    infos = ds.all_image_info()
    if not infos:
        raise SkipCheck("no image files")
    unverified = params.get("unverified", "warn")
    issues = []
    for i in infos:
        if i.readable is False:
            issues.append(Issue("problem", f"{i.path}: unreadable: {i.error}"))
        elif i.readable is None and unverified != "pass":
            issues.append(Issue("warning", f"{i.path}: readability not checked ({'; '.join(i.notes)})"))
    return issues


@check("ome_metadata")
def ome_metadata(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    """Images should carry OME metadata with physical pixel sizes (REMBI image acquisition parameters)."""
    axes = params.get("pixel_size_axes", ["x", "y"])
    # PNG/JPEG never carry calibration; they are usually masks or figures, so don't nag about them here
    infos = [i for i in ds.all_image_info() if i.readable and i.format != "raster"]
    if not infos:
        raise SkipCheck("no readable microscopy images")
    issues = []
    for i in infos:
        if i.format in ("tiff", "ome-tiff") and not i.is_ome:
            issues.append(Issue("problem", f"{i.path}: no OME-XML header (plain TIFF)"))
        missing = [a for a in axes if i.pixel_size_um.get(a) is None]
        unitless = [n.split()[1] for n in i.notes if n.startswith("axis ") and "no unit" in n]
        if missing and set(missing) <= set(unitless):
            issues.append(Issue("warning", f"{i.path}: axes {', '.join(sorted(unitless))} have a scale but no unit, "
                                           "so the physical pixel size is not established"))
        elif missing and i.sizes.get(missing[0].upper(), 2) > 1:
            issues.append(Issue("warning", f"{i.path}: physical pixel size missing for axis {', '.join(missing)}"))
        issues += [Issue("warning", f"{i.path}: {n}") for n in i.notes if "non-standard key" in n]
    return issues


def _group_key(ds: Dataset, rel: str, group_by: str) -> str:
    if group_by == "all":
        return "(all images)"
    if group_by.startswith("column:"):
        col = group_by.split(":", 1)[1]
        for t in ds.file_lists:
            files = t.column("Files")
            if rel in files and col in t.header:
                return f"{col}={t.column(col)[files.index(rel)]}"
        # fall back to directory when no column value is available
    parent = str(PurePosixPath(rel).parent)
    return parent if parent != "." else "(dataset root)"


def _close(a: float | None, b: float | None, rtol: float) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(a, b, rel_tol=rtol)


@check("series_consistent")
def series_consistent(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    """Images in one series (group) should share channels, pixel size, dtype and XY size."""
    group_by = params.get("group_by", "directory")
    fields = params.get("fields", {"channels": "problem", "pixel_size": "problem", "dtype": "warning", "xy": "warning"})
    rtol = float(params.get("rtol", 1e-3))
    groups: dict[str, list] = defaultdict(list)
    for i in ds.all_image_info():
        if i.readable and i.sizes and i.format != "raster":  # figures/photos (S-BIAD4056 leaf scans) vary by design
            # one series comes from one writer: a screen-capture TIFF next to an OME-TIFF stack isn't part of it
            groups[(_group_key(ds, i.path, group_by), i.format)].append(i)
    groups = {k: v for k, v in groups.items() if len(v) > 1}
    if not groups:
        raise SkipCheck("no series with 2+ readable images to compare")
    issues = []
    for (key, _fmt), infos in sorted(groups.items()):
        ref = infos[0]
        for i in infos[1:]:
            diffs: list[tuple[str, str]] = []
            if "channels" in fields and i.sizes.get("C") != ref.sizes.get("C"):
                diffs.append(("channels", f"C={i.sizes.get('C')} vs {ref.sizes.get('C')}"))
            if "pixel_size" in fields:
                for ax in ("x", "y", "z"):
                    a, b = i.pixel_size_um.get(ax), ref.pixel_size_um.get(ax)
                    if not _close(a, b, rtol):
                        diffs.append(("pixel_size", f"pixel size {ax}={a} vs {b} µm"))
            if "dtype" in fields and i.dtype != ref.dtype:
                diffs.append(("dtype", f"dtype {i.dtype} vs {ref.dtype}"))
            if "xy" in fields and (i.sizes.get("X"), i.sizes.get("Y")) != (ref.sizes.get("X"), ref.sizes.get("Y")):
                diffs.append(("xy", f"XY {i.sizes.get('X')}x{i.sizes.get('Y')} vs {ref.sizes.get('X')}x{ref.sizes.get('Y')}"))
            if "z" in fields and i.sizes.get("Z") != ref.sizes.get("Z"):
                diffs.append(("z", f"Z={i.sizes.get('Z')} vs {ref.sizes.get('Z')}"))
            for fld, text in diffs:
                issues.append(Issue(fields[fld], f"folder '{key}': {i.path} differs from {ref.path}: {text}"))
    return issues


@check("file_size")
def file_size(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    hard = params.get("max_bytes")
    soft = params.get("warn_bytes")
    issues = []
    for rel, n in ds.sizes.items():
        if hard and n > hard:
            issues.append(Issue("problem", f"{rel}: {n / 1e9:.1f} GB exceeds hard limit {hard / 1e12:.1f} TB"))
        elif soft and n > soft:
            issues.append(Issue("warning", f"{rel}: {n / 1e9:.1f} GB exceeds recommended {soft / 1e9:.0f} GB per file"))
    return issues


@check("filename_chars")
def filename_chars(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    pattern = re.compile(params.get("pattern", r"^[A-Za-z0-9!\-_.*'() /]+$"))
    issues = []
    for rel in ds.data_files:
        bad = sorted({c for c in rel if not pattern.match(c)}) if not pattern.match(rel) else []
        if bad:
            issues.append(Issue("problem", f"{rel}: disallowed character(s) {''.join(bad)!r}"))
        elif any(part != part.strip() for part in rel.split("/")):
            issues.append(Issue("problem", f"{rel!r}: leading/trailing space in a path component"))
    return issues


# ---------------------------------------------------------------- BIA file lists


def _need_file_lists(ds: Dataset):
    if not ds.file_lists:
        raise SkipCheck("no file list found (see file list rule)")
    return ds.file_lists


@check("file_list_present")
def file_list_present(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    if not ds.file_lists:
        return [Issue("problem", "no file list found (a .tsv whose first column is 'Files', or a file named *file_list*.tsv)")]
    return [Issue("problem", f"{t.path}: {t.error}") for t in ds.file_lists if t.error]


@check("file_list_header")
def file_list_header(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    first = params.get("first_column", "Files")
    issues = []
    for t in _need_file_lists(ds):
        if t.error:
            continue
        if not t.header or t.header[0] != first:
            got = t.header[0] if t.header else "(empty)"
            issues.append(Issue("problem", f"{t.path}: first column header is {got!r}, must be {first!r}"))
        empties = [i + 1 for i, h in enumerate(t.header) if not h]
        if empties:
            issues.append(Issue("warning", f"{t.path}: unnamed column(s) at position {empties}"))
    return issues


@check("file_list_format")
def file_list_format(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    issues = []
    for t in _need_file_lists(ds):
        if t.error or not t.header:
            continue
        for n, row in enumerate(t.rows, start=2):
            if not any(c.strip() for c in row):
                issues.append(Issue("problem", f"{t.path}:{n}: blank line"))
                continue
            path = row[0]
            if "\\" in path:
                issues.append(Issue("problem", f"{t.path}:{n}: backslash in path {path!r}; use '/'"))
            if path.startswith(("./", "../", "/")) or "/../" in path:
                issues.append(Issue("problem", f"{t.path}:{n}: relative/absolute prefix in {path!r}"))
            if path.endswith("/"):
                issues.append(Issue("problem", f"{t.path}:{n}: trailing slash in {path!r}"))
            if path != path.strip():
                issues.append(Issue("problem", f"{t.path}:{n}: leading/trailing space in {path!r}"))
            empty_cols = [t.header[i] for i in range(1, len(t.header)) if i >= len(row) or not row[i].strip()]
            if empty_cols:
                issues.append(Issue("warning", f"{t.path}:{n}: empty attribute(s) {empty_cols} for {path}"))
    return issues


@check("file_list_matches")
def file_list_matches(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    """Every listed file exists (exact, case-sensitive) and every data file is listed."""
    lists = _need_file_lists(ds)
    # a submitter may list the file-list TSV itself (S-BIAD4206); it is on disk even though it isn't a data file
    present = set(ds.data_files) | {t.path for t in ds.file_lists}
    lower = {f.lower(): f for f in present}
    listed: set[str] = set()
    issues = []
    for t in lists:
        for n, f in enumerate(t.column(t.header[0] if t.header else "Files"), start=2):
            f = f.strip()
            listed.add(f)
            if f not in present and not ds.partial and not any(p.startswith(f.rstrip("/") + "/") for p in present):
                hint = f" (case differs: on disk as {lower[f.lower()]})" if f.lower() in lower else ""
                issues.append(Issue("problem", f"{t.path}: listed but not found: {f}{hint}"))
    dupes = [f for t in lists for f in set(t.column("Files")) if t.column("Files").count(f) > 1]
    issues += [Issue("warning", f"listed more than once: {f}") for f in sorted(set(dupes))]
    if params.get("check_orphans", True):
        scope = ds.image_files if params.get("orphans_images_only") else ds.data_files
        # BIA allows a directory path in Files ("the file path may refer to a directory"), e.g. S-BIAD3835
        dirs = tuple(d.rstrip("/") + "/" for d in listed if d and d not in present)
        for f in scope:
            if f not in listed and not f.startswith(dirs):
                issues.append(Issue("problem", f"on disk but not in any file list: {f}"))
    return issues


def _norm_col(name: str) -> str:
    return re.sub(r"[\s_-]+", "_", name.strip().lower())


@check("annotation_source_image")
def annotation_source_image(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    want = params.get("column", "source_image")
    ann = [t for t in ds.file_lists if "annotation" in t.path.lower()]
    if not ann:
        raise SkipCheck("no annotation file list (file name containing 'annotation')")
    issues = []
    present = set(ds.data_files)
    for t in ann:
        col = next((h for h in t.header if _norm_col(h) == _norm_col(want)), None)
        if col is None:
            issues.append(Issue("problem", f"{t.path}: missing required column {want!r}"))
            continue
        for v in t.column(col):
            # S-BIAD3632 points into a container: 'PLA4_realigned.zarr.zip/images/B05067G5_HE_regist'
            inside = any(v.strip().startswith(f + "/") for f in present)
            if v.strip() and v.strip() not in present and not inside and not ds.partial:
                issues.append(Issue("problem", f"{t.path}: {col} {v!r} not found in dataset"))
            elif not v.strip():
                issues.append(Issue("problem", f"{t.path}: empty {col} value"))
    return issues


# ---------------------------------------------------------------- IDR tables


def _study_value(ds: Dataset, key: str) -> list[str]:
    assert ds.idr_study is not None
    return [v for v in ds.idr_study.get(key, []) if not is_missing(v)]


@check("idr_study_present")
def idr_study_present(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    if ds.idr_study_error:
        return [Issue("problem", f"{ds.idr_study_path}: {ds.idr_study_error}")]
    if ds.idr_study is None:
        return [Issue("problem", "no IDR study file (*study*.txt) in dataset root")]
    return []


@check("idr_study_fields")
def idr_study_fields(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    if ds.idr_study is None:
        raise SkipCheck("no IDR study file")
    issues = []
    for key in params.get("fields", []):
        alts = key if isinstance(key, list) else [key]
        if not any(_study_value(ds, k) for k in alts):
            issues.append(Issue("problem", f"{ds.idr_study_path}: '{' / '.join(alts)}' missing or still a template hint"))
    return issues


def _table_stem(name: str) -> str:
    return re.sub(r"\.(txt|tsv|csv)$", "", PurePosixPath(name.strip()).name, flags=re.I)


@check("idr_assay_present")
def idr_assay_present(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    issues = []
    if not ds.idr_assays:
        issues.append(Issue("problem", "no IDR assay, library or annotation table (*assay*.txt, *library*.txt, *annotation*.csv)"))
    if ds.idr_study is not None:
        cells = _study_value(ds, "Experiment Assay File") + _study_value(ds, "Screen Library File")
        # accepted studies write "a.txt, b.txt", "a.txt and b.txt", or omit the extension
        named = [n.strip() for c in cells for n in re.split(r",|;|\s+and\s+", c) if n.strip()]
        have = {_table_stem(t.path) for t in ds.idr_assays} | {_table_stem(f) for f in ds.data_files}
        tables = [PurePosixPath(t.path).name for t in ds.idr_assays]
        unresolved = [n for n in named if _table_stem(n) not in have]
        unreferenced = [t for t in tables if _table_stem(t) not in {_table_stem(n) for n in named}]
        for n in unresolved if not ds.partial else []:
            same = [t for t in tables if _experiment_key(t) and _experiment_key(t) == _experiment_key(n)]
            keys = {_experiment_key(n), _experiment_key(unreferenced[0]) if unreferenced else None}
            if not same and len(unresolved) == 1 and len(unreferenced) == 1 and None in keys:
                # one dangling name, one unnamed table (idr0091, idr0109); never pair experiment B with A (idr0083)
                same = unreferenced
            if same:
                # accepted IDR repos: study names the submitted '...-assays.txt', table published as '...-annotation.csv'
                issues.append(Issue("warning", f"study file names assay file {n!r}, which is not in the dataset; "
                                               f"{same[0]!r} looks like the table it means, so update "
                                               "'Experiment Assay File' to the name of the file you submit"))
            else:
                issues.append(Issue("problem", f"study file names assay file {n!r} but it is not in the dataset"))
    return issues


def _experiment_key(name: str) -> str | None:
    """'idr0086-experimentB-assays.txt', 'ExperimentB_Assays', 'screenA-library' -> 'experiment b' / 'screen a'."""
    m = re.search(r"(experiment|screen)[\s_-]*([A-Z0-9]+)(?![a-z])", PurePosixPath(name).name, flags=re.I)
    return f"{m.group(1).lower()} {m.group(2).lower()}" if m else None


@check("idr_assay_columns")
def idr_assay_columns(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    if not ds.idr_assays:
        raise SkipCheck("no IDR assay file")
    issues = []
    for t in ds.idr_assays:
        if t.delimiter == "," and not t.path.lower().endswith(".csv") and params.get("note_delimiter", True):
            issues.append(Issue("warning", f"{t.path}: comma-separated, while the IDR template is tab-delimited (read anyway)"))
        for col in params.get("columns", []):
            alts = col if isinstance(col, list) else [col]
            hit = next((c for c in alts if c in t.header), None)
            if hit is None:
                issues.append(Issue("problem", f"{t.path}: missing column '{' / '.join(alts)}'"))
                continue
            if params.get("require_values", True):
                empty = sum(1 for v in t.column(hit) if is_missing(v))
                if empty:
                    issues.append(Issue("warning", f"{t.path}: column '{hit}' empty in {empty} row(s)"))
    return issues


COMPOUND_EXTS = (".ome.zarr.zip", ".zarr.zip", ".ome.zarr", ".zarr", ".ome.tiff", ".ome.tif", ".ome.btf", ".companion.ome")


def stem(name: str) -> str:
    """File name without image extensions, so 'B1_C1.tif' and 'B1_C1.ome.zarr' compare equal."""
    base = PurePosixPath(name).name
    for ext in COMPOUND_EXTS:
        if base.lower().endswith(ext):
            return base[: -len(ext)]
    return PurePosixPath(base).stem


class _ImageIndex:
    """Resolve assay 'Image File' (+ optional path) values to dataset images."""

    def __init__(self, images: list[str]):
        self.images = set(images)
        self.by_name: dict[str, list[str]] = defaultdict(list)
        self.by_stem: dict[str, list[str]] = defaultdict(list)
        for f in images:
            self.by_name[PurePosixPath(f).name].append(f)
            self.by_stem[stem(f)].append(f)

    def match(self, name: str, rel_dir: str = "", use_stem: bool = True) -> tuple[str | None, bool]:
        """Return (image, matched_by_stem_only)."""
        rel_dir = rel_dir.strip().strip("/")
        for f in (f"{rel_dir}/{name}" if rel_dir else name, name):
            if f in self.images:
                return f, False
        hits = self.by_name.get(PurePosixPath(name).name, [])
        if len(hits) == 1:
            return hits[0], False
        hits = self.by_stem.get(stem(name), []) if use_stem and name else []
        if len(hits) == 1:
            return hits[0], True  # e.g. original .tif listed, converted .ome.zarr on disk
        return None, False


@check("idr_assay_matches_files")
def idr_assay_matches_files(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    """Every 'Image File' row resolves to a dataset image; every image is described by a row."""
    if not ds.idr_assays:
        raise SkipCheck("no IDR assay file")
    file_cols = params.get("file_columns", ["Image File", "Image Name"])
    path_col = params.get("path_column", "Comment [Image File Path]")
    index = _ImageIndex(ds.image_files)
    by_stem = 0
    referenced: set[str] = set()
    missing: list[Issue] = []
    for t in ds.idr_assays:
        file_col = next((c for c in file_cols if c in t.header), None)
        if file_col is None:
            continue  # reported by idr_assay_columns
        for rec in t.records():
            name = rec.get(file_col, "").strip()
            if is_missing(name):
                continue
            hit, stem_only = index.match(name, rec.get(path_col, ""), params.get("match_stem", True))
            if hit is None and rec.get(path_col, "").strip().strip("/"):
                # multi-file fileset converted to one image named after one of its folders
                # (idr0052: .../cell0015_R0002/rawtif/TR1_..._T0001.tif -> cell0015_R0002.ome.zarr)
                for part in reversed(PurePosixPath(rec[path_col].strip().strip("/")).parts):
                    hit, _ = index.match(part)
                    if hit:
                        stem_only = True
                        break
            if hit:
                referenced.add(hit)
                by_stem += stem_only
            elif not ds.partial:
                missing.append(Issue("problem", f"{t.path}: Image File {name!r} not found in dataset"))
    plates = {v.strip() for t in ds.idr_assays for v in t.column("Plate") if v.strip()}
    for f in ds.image_files:  # HCS: a library/annotation table describes plates, one row per well
        if f not in referenced and (stem(f) in plates or PurePosixPath(f).name in plates):
            referenced.add(f)
    issues = [Issue("problem", f"image not described in any assay file: {f}") for f in ds.image_files if f not in referenced]
    if by_stem:
        issues.append(Issue("warning", f"{by_stem} row(s) matched an image only by file-name stem or containing folder, "
                                       "not by exact name; update 'Image File' to the names of the files you submit"))
    return issues + missing


@check("idr_processed_data")
def idr_processed_data(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    if ds.idr_study is None:
        raise SkipCheck("no IDR study file")
    names = _study_value(ds, "Processed Data File Name")
    if not names:
        return [Issue("problem", "study file declares no 'Processed Data File Name'")]
    have = {PurePosixPath(f).name for f in ds.data_files} | {PurePosixPath(t.path).name for t in ds.idr_assays}
    if ds.partial:
        return []
    return [Issue("warning", f"processed data file {n!r} is declared but not in the dataset") for n in names
            if PurePosixPath(n).name not in have]


@check("idr_channels_match")
def idr_channels_match(ds: Dataset, params: dict[str, Any]) -> list[Issue]:
    """'Channels' column (label:target;...) should list as many channels as the image has."""
    if not ds.idr_assays:
        raise SkipCheck("no IDR assay file")
    index = _ImageIndex(ds.image_files)
    issues = []
    compared = 0
    for t in ds.idr_assays:
        name_col = next((c for c in ("Image File", "Image Name") if c in t.header), None)
        if "Channels" not in t.header or name_col is None:
            continue
        for rec in t.records():
            ch, name = rec.get("Channels", ""), rec.get(name_col, "").strip()
            hit, _ = index.match(name, rec.get("Comment [Image File Path]", ""))
            if is_missing(ch) or hit is None:
                continue
            info = ds.image_info(hit)
            if not info.readable or "C" not in info.sizes:
                continue
            compared += 1
            n = len([c for c in ch.split(";") if c.strip()])
            if n != info.sizes["C"]:
                issues.append(Issue("problem", f"{name}: Channels lists {n} channel(s) but image has C={info.sizes['C']}"))
    if not compared:
        raise SkipCheck("no assay rows with Channels and a readable matching image")
    return issues


__all__ = ["IMAGE_FORMATS", "is_missing", "resolve"]
