"""Mirror a small OME-Zarr v0.4 (zarr v2) image from HTTP to a local dir."""
import itertools, json, math, os, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
base, out = sys.argv[1].rstrip("/"), sys.argv[2]
def get(rel):
    with urllib.request.urlopen(f"{base}/{rel}") as r: return r.read()
def save(rel, data):
    p = os.path.join(out, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(data)
jobs = []
for meta in [".zattrs", ".zgroup"]:
    save(meta, get(meta))
attrs = json.loads(open(os.path.join(out, ".zattrs")).read())
for ds in attrs["multiscales"][0]["datasets"]:
    p = ds["path"]; za = json.loads(get(f"{p}/.zarray")); save(f"{p}/.zarray", json.dumps(za).encode())
    sep = za.get("dimension_separator", ".")
    grid = [range(math.ceil(s / c)) for s, c in zip(za["shape"], za["chunks"])]
    for idx in itertools.product(*grid):
        jobs.append(f"{p}/" + sep.join(map(str, idx)))
def fetch(rel):
    try: save(rel, get(rel))
    except Exception as e: print("skip", rel, e)
with ThreadPoolExecutor(16) as ex: list(ex.map(fetch, jobs))
print("done", len(jobs), "chunks")
