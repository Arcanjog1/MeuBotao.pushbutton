"""Comparacao por identidade geometrica NORMALIZADA (sem rotulo sequencial de bloco)."""
import json, re, sys, collections

SP = sys.argv[2]
proj = sys.argv[1]
RE_BLOCKID = re.compile(r"\bW\d+-R\d+-B\d+\b")

def norm(idstr):
    d = json.loads(idstr)
    d["detail"] = RE_BLOCKID.sub("<BLK>", d.get("detail") or "")
    return json.dumps(d, sort_keys=True, ensure_ascii=False)

def load(tag):
    x = json.load(open(f"{SP}/{tag}_{proj}.json", encoding="utf-8"))
    x["norm"] = {c: collections.Counter(norm(i) for i in v)
                 for c, v in x["finding_identities"].items()}
    return x

A, B, C = load("A"), load("B"), load("C")
print("="*76); print(f"{proj.upper()} - identidade geometrica NORMALIZADA"); print("="*76)
allc = sorted(set(A["norm"]) | set(B["norm"]) | set(C["norm"]))
print(f"{'CODE':<40}{'A':>6}{'B':>6}{'C':>6} | {'novoB':>6}{'novoC':>6}{'sumiuC':>7}")
print("-"*76)
tot = collections.Counter()
for c in allc:
    a, b, k = A["norm"].get(c, collections.Counter()), B["norm"].get(c, collections.Counter()), C["norm"].get(c, collections.Counter())
    nb, nc, sc = sum((b-a).values()), sum((k-a).values()), sum((a-k).values())
    tot["novoB"] += nb; tot["novoC"] += nc; tot["sumiuC"] += sc
    mark = "  <<<" if nc else ""
    print(f"{c:<40}{sum(a.values()):>6}{sum(b.values()):>6}{sum(k.values()):>6} | {nb:>6}{nc:>6}{sc:>7}{mark}")
print("-"*76)
print(f"{'TOTAL':<40}{'':>18} | {tot['novoB']:>6}{tot['novoC']:>6}{tot['sumiuC']:>7}")

print("\n### achados NOVOS EM C (nao existiam em A), detalhados:")
for c in allc:
    a, k = A["norm"].get(c, collections.Counter()), C["norm"].get(c, collections.Counter())
    novos = list((k-a).elements())
    if not novos: continue
    walls = collections.Counter(json.loads(x)["wall"] for x in novos)
    print(f"\n  {c}  (+{len(novos)})  paredes: {dict(walls)}")
    for x in sorted(novos)[:6]:
        d = json.loads(x); print(f"      {d['wall']}: {d['detail'][:150]}")
    if len(novos) > 6: print(f"      ... (+{len(novos)-6})")

print("\n### achados que a GUARDA (B->C) eliminou:")
for c in allc:
    b, k = B["norm"].get(c, collections.Counter()), C["norm"].get(c, collections.Counter())
    el = sum((b-k).values()); ad = sum((k-b).values())
    if el or ad: print(f"  {c}: eliminados={el}  adicionados={ad}")
