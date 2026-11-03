"""Convert a BioStudies / BioImage Archive page-tab JSON study into the REMBI dict used by the rules.

Lets a facility validate a study exported from (or already in) the BioStudies submission tool,
e.g. https://www.ebi.ac.uk/biostudies/api/v1/studies/S-BIAD634
"""
from __future__ import annotations

import re
from typing import Any, Iterator


def is_pagetab(data: Any) -> bool:
    return isinstance(data, dict) and "section" in data and isinstance(data.get("attributes"), list)


def _attrs(sec: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for a in sec.get("attributes", []) or []:
        if isinstance(a, dict) and a.get("name") is not None:
            out.setdefault(str(a["name"]).strip().lower(), []).append("" if a.get("value") is None else str(a["value"]))
    return out


def _sections(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, list):
        for x in node:
            yield from _sections(x)
    elif isinstance(node, dict):
        yield node
        yield from _sections(node.get("subsections", []))


def _first(a: dict[str, list[str]], key: str) -> str | None:
    vals = a.get(key.lower())
    return vals[0] if vals else None


def _organism(text: str, qualifiers: str = "") -> dict[str, Any]:
    """'Homo sapiens (human)' -> scientific + common name; NCBI taxon from the text or its TermId qualifier."""
    m = re.match(r"^\s*([^()]+?)\s*(?:\(([^)]*)\))?\s*$", text)
    sci, common = (m.group(1), m.group(2)) if m else (text, None)
    taxon = re.search(r"NCBITaxon[_:]\s*(\d+)", text) or re.search(r"NCBITaxon[_:]\s*(\d+)", qualifiers)
    return {"scientific_name": sci, "common_name": common, "ncbi_taxon": f"NCBITaxon_{taxon.group(1)}" if taxon else None}


def to_rembi(data: dict[str, Any]) -> dict[str, Any]:
    top = _attrs(data)
    root = data["section"]
    secs = list(_sections(root))
    by_type: dict[str, list[dict[str, Any]]] = {}
    for s in secs:
        by_type.setdefault(str(s.get("type", "")).strip().lower(), []).append(s)
    orgs = {s.get("accno"): _first(_attrs(s), "Name") for s in by_type.get("organisation", []) + by_type.get("organization", [])}

    st = _attrs(root)
    study: dict[str, Any] = {
        "title": _first(st, "Title") or _first(top, "Title"),
        "description": _first(st, "Description"),
        "keywords": st.get("keywords", []),
        "private_until_date": _first(st, "ReleaseDate") or _first(top, "ReleaseDate"),
        "license": _first(st, "License"),
        "acknowledgements": _first(st, "Acknowledgements"),
    }
    authors = []
    for s in by_type.get("author", []):
        a = _attrs(s)
        aff = [orgs.get(v, v) for v in a.get("affiliation", [])]
        name = _first(a, "Name") or ""
        parts = name.split()
        authors.append({
            "name": name,
            "first_name": " ".join(parts[:-1]) or None,
            "last_name": parts[-1] if parts else None,
            "email": _first(a, "E-mail"),
            "orcid": _first(a, "ORCID"),
            "role": _first(a, "Role"),
            "affiliation": {"name": aff[0]} if aff and aff[0] else None,
        })
    study["authors"] = authors
    statements = st.get("funding statement", [])
    grants = [{"funder": _first(_attrs(s), "Agency"), "identifier": _first(_attrs(s), "grant_id")} for s in by_type.get("funding", [])]
    grants = [g for g in grants if any(g.values())]  # accepted studies contain empty Funding shells
    if statements or grants:
        study["funding"] = [{"funding_statement": statements[0] if statements else None, "grant_references": grants}]
    pubs = [{"title": _first(_attrs(s), "Title"), "doi": _first(_attrs(s), "DOI"), "pubmed_id": _first(_attrs(s), "Pubmed ID"),
             "year": _first(_attrs(s), "Year")} for s in by_type.get("publication", [])]
    pubs = [p for p in pubs if any(p.values())]
    if pubs:
        study["publications"] = pubs

    def items(kind: str, fields: dict[str, str]) -> list[dict[str, Any]]:
        out = []
        for s in by_type.get(kind, []):
            a = _attrs(s)
            out.append({k: _first(a, v) for k, v in fields.items()})
        return out

    meta: dict[str, Any] = {"study": study}
    meta["study_components"] = items("study component", {"name": "Name", "description": "Description"})
    bios = []
    for s in by_type.get("biosample", []):
        a = _attrs(s)
        bios.append({
            "organism": [_organism(str(o.get("value") or ""), " ".join(str(q.get("value") or "") for q in o.get("valqual") or []
                                                                     if isinstance(q, dict)))
                         for o in s.get("attributes", []) or []
                         if isinstance(o, dict) and str(o.get("name", "")).strip().lower() == "organism"],
            "biological_entity": _first(a, "Biological entity"),
            "description": _first(a, "Description"),
            "intrinsic_variables": _first(a, "Intrinsic variable"),
            "extrinsic_variables": _first(a, "Extrinsic variable"),
            "experimental_variables": _first(a, "Experimental variable"),
        })
    meta["biosample"] = bios
    meta["specimen"] = items("specimen", {"sample_preparation": "Sample preparation protocol", "growth_protocol": "Growth protocol"})
    meta["image_acquisition"] = items("image acquisition", {
        "imaging_method": "Imaging method", "imaging_instrument": "Imaging instrument",
        "image_acquisition_parameters": "Image acquisition parameters"})
    analysis = items("image analysis", {"analysis_overview": "Image analysis overview"})
    if analysis:
        meta["image_analysis"] = analysis
    corr = items("image correlation", {"spatial_and_temporal_alignment": "Spatial and temporal alignment",
                                       "fiducials_used": "Fiducials used", "transformation_matrix": "Transformation matrix"})
    if corr:
        meta["image_correlation"] = corr
    ann = items("annotations", {"annotation_overview": "Annotation Overview", "annotation_method": "Annotation Method"})
    ann += items("annotation", {"annotation_overview": "Annotation Overview", "annotation_method": "Annotation Method"})
    if ann:
        meta["annotations"] = ann
    meta["_source"] = {"format": "biostudies-pagetab", "accession": data.get("accno")}
    return meta
