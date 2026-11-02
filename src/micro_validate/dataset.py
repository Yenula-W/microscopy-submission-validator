"""Discover what a submission folder contains: metadata, file lists, IDR tables, data files."""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .imageinfo import IMAGE_FORMATS, ImageInfo, classify, read_info

METADATA_NAMES = ("submission.yaml", "submission.yml", "submission.json", "rembi.yaml", "rembi.json")
IGNORED_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}


@dataclass
class Table:
    path: str
    header: list[str]
    rows: list[list[str]]  # raw rows, may include blank ones
    error: str = ""

    def records(self) -> list[dict[str, str]]:
        return [dict(zip(self.header, r)) for r in self.rows if any(c.strip() for c in r)]

    def column(self, name: str) -> list[str]:
        if name not in self.header:
            return []
        i = self.header.index(name)
        return [r[i] if i < len(r) else "" for r in self.rows if any(c.strip() for c in r)]


@dataclass
class Dataset:
    root: Path
    metadata: dict[str, Any] | None = None
    metadata_path: str = ""
    metadata_error: str = ""
    file_lists: list[Table] = field(default_factory=list)
    idr_study: dict[str, list[str]] | None = None
    idr_study_path: str = ""
    idr_assays: list[Table] = field(default_factory=list)
    data_files: list[str] = field(default_factory=list)  # relative posix paths, zarr dirs as one entry
    sizes: dict[str, int] = field(default_factory=dict)
    read_pixels: bool = True
    _images: dict[str, ImageInfo] = field(default_factory=dict)

    @property
    def image_files(self) -> list[str]:
        return [f for f in self.data_files if classify(self.root / f) in IMAGE_FORMATS]

    def image_info(self, rel: str) -> ImageInfo:
        if rel not in self._images:
            self._images[rel] = read_info(self.root / rel, rel, self.read_pixels)
        return self._images[rel]

    def all_image_info(self) -> list[ImageInfo]:
        return [self.image_info(f) for f in self.image_files]

    def file_list_for(self, rel: str) -> Table | None:
        """Return the file list row's table that mentions rel, if any."""
        for t in self.file_lists:
            if rel in t.column("Files"):
                return t
        return None


def read_table(path: Path, root: Path) -> Table:
    rel = path.relative_to(root).as_posix()
    if path.suffix.lower() in (".xlsx", ".xls"):
        return Table(rel, [], [], error="Excel file lists are not parsed yet; export as TSV to validate")
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    rows = list(csv.reader(text.splitlines(), delimiter="\t"))
    while rows and not any(c.strip() for c in rows[-1]):
        rows.pop()  # trailing newline(s) are harmless
    header = [h.strip() for h in rows[0]] if rows else []
    return Table(rel, header, rows[1:])


def read_idr_study(path: Path) -> dict[str, list[str]]:
    """IDR study files are key<TAB>value[<TAB>value...] lines; '#' lines and hint cells are comments."""
    out: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, *vals = line.split("\t")
        key = key.strip()
        out.setdefault(key, []).extend(v.strip() for v in vals)
    return out


def _is_file_list(name: str) -> bool:
    n = name.lower()
    return ("file_list" in n or "filelist" in n or "file-list" in n) and n.endswith((".tsv", ".xlsx", ".xls"))


def _is_idr_study(name: str) -> bool:
    n = name.lower()
    return "study" in n and n.endswith(".txt")


def _is_idr_assay(name: str) -> bool:
    n = name.lower()
    return ("assays" in n or "library" in n) and n.endswith((".txt", ".tsv"))


def load_dataset(root: str | Path, metadata: str | Path | None = None, read_pixels: bool = True) -> Dataset:
    root = Path(root).resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    ds = Dataset(root=root, read_pixels=read_pixels)
    meta_path = Path(metadata).resolve() if metadata else None
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        # treat *.zarr directories as single data objects
        for dn in list(dirnames):
            if dn.lower().endswith(".zarr"):
                rel = (d / dn).relative_to(root).as_posix()
                ds.data_files.append(rel)
                dirnames.remove(dn)
            elif dn.startswith("."):
                dirnames.remove(dn)
        for fn in filenames:
            p = d / fn
            rel = p.relative_to(root).as_posix()
            if fn in IGNORED_NAMES or fn.startswith("."):
                continue
            if meta_path is None and d == root and fn in METADATA_NAMES:
                meta_path = p
                continue
            if meta_path is not None and p == meta_path:
                continue
            if _is_file_list(fn):
                ds.file_lists.append(read_table(p, root))
                continue
            if _is_idr_study(fn) and d == root:
                ds.idr_study = read_idr_study(p)
                ds.idr_study_path = rel
                continue
            if _is_idr_assay(fn):
                ds.idr_assays.append(read_table(p, root))
                continue
            ds.data_files.append(rel)
            try:
                ds.sizes[rel] = p.stat().st_size
            except OSError:
                pass
    ds.data_files.sort()
    if meta_path is not None:
        ds.metadata_path = str(meta_path)
        try:
            text = meta_path.read_text()
            ds.metadata = json.loads(text) if meta_path.suffix == ".json" else yaml.safe_load(text)
            if not isinstance(ds.metadata, dict):
                raise ValueError("top level must be a mapping")
        except Exception as e:
            ds.metadata, ds.metadata_error = None, f"{type(e).__name__}: {e}"
    return ds
