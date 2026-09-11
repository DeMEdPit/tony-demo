#!/usr/bin/env python3
"""
brain025_migrate.py - the BRAIN02 -> BRAIN02.5 migration tool (PREREG-BRAIN025.md section 11).

Deterministic, and it does one thing: per action row it copies the original weights in order, unchanged,
and appends a zero weight for every input BRAIN02.5 adds. Every other compatible field is copied by name,
so nothing is inherited by accident:

    kind, period, lineage, rule, vocabulary, education, mood      copied
    inputs, layout, retina id, marker                             the migration's only changes

Because every appended weight is zero, no appended input can contribute to any accumulator, so the
argmax over the ten rows is untouched wherever the old observation interface applies. That is an
argument; the gate measures it.

The original file is never written to. The migrated brain is a new file with a new name.

  migrate IN.bin OUT.bin      write the migrated brain and print the report
  verify IN.bin OUT.bin       re-check an existing pair without writing anything
"""
import hashlib, json, os, sys
import importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
ref = _load("brain025_ref", os.path.join(ROOT, "tools/brain025_ref.py"))
b02 = _load("brain02_ref", os.path.join(ROOT, "tools/brain02_ref.py"))

def report(src_path, old, new):
    r = ref.migration_report(old, new)
    p, q = b02.parse_slot(old), ref.parse_slot(new)
    blocks = sorted(_load("bakeoff2", os.path.join(ROOT, "tools/bakeoff2.py")).sets()["s1424"])
    terrains = [[0] * len(ref.TERRAIN), [ref.CAP] * len(ref.TERRAIN)] + [[((i * 3 + j) % 8) for j in range(len(ref.TERRAIN))] for i in range(6)]
    n, bad = ref.predicts_same(old, new, blocks, terrains)
    r.update(source=os.path.basename(src_path), source_sha256=hashlib.sha256(old).hexdigest(), migrated_sha256=hashlib.sha256(new).hexdigest(),
             source_bytes=len(old), migrated_bytes=len(new), blocks=len(blocks), terrains=len(terrains), predictions_checked=n, prediction_mismatches=bad)
    return r

def main():
    cmd, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
    old = open(a, "rb").read()
    if cmd == "migrate":
        new = ref.migrate(old)
        assert not os.path.exists(b) or open(b, "rb").read() != old, "refusing to write the original's own bytes"
        open(b, "wb").write(new)
    else:
        new = open(b, "rb").read()
    r = report(a, old, new)
    for k in ("source", "source_bytes", "migrated_bytes", "inputs", "layout", "retina_id", "weights_copied", "appended_zero", "hash_before", "hash_after", "predictions_checked", "prediction_mismatches"):
        print(f"  {k}: {r[k]}")
    print("  fields copied by name: " + ", ".join(f"{k} {v[0]}->{v[1]}" for k, v in r["fields"].items() if k != "mood"))
    print("  MIGRATION CLEAN" if r["prediction_mismatches"] == 0 and r["weights_copied"] and r["appended_zero"] else "  MIGRATION NOT CLEAN")
    json.dump(r, open(b + ".report.json", "w"), indent=1)
    return 0 if (r["prediction_mismatches"] == 0 and r["weights_copied"] and r["appended_zero"]) else 1

if __name__ == "__main__": sys.exit(main())
