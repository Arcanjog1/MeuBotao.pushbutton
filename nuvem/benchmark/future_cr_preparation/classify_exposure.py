import json, re, sys, collections
SP="/tmp/claude-0/-home-user-MeuBotao-pushbutton/5ced94a0-db34-5820-b277-429cee84dcb1/scratchpad"
proj=sys.argv[1]; CODE=sys.argv[2]
RE_BLK=re.compile(r"\bW\d+-R\d+-B\d+\b"); RE_T=re.compile(r"t=([\d.]+)cm"); RE_ROWS=re.compile(r"fiadas (\d+) e (\d+)")
def load(t):
    return (json.load(open(f"{SP}/out2/{t}_{proj}.json",encoding="utf-8")),
            json.load(open(f"{SP}/out2/{t}_{proj}.blocks.json",encoding="utf-8")))
A,bA=load("A"); C,bC=load("C")
def index(rows):
    ix=collections.defaultdict(list)
    for wid,ri,code,t0,t1,cx,cy,z,role in rows: ix[(wid,ri)].append((t0,t1))
    return {k:sorted(v) for k,v in ix.items()}
IA,IC=index(bA),index(bC)
def state(ix,w,r,t,tol=0.35):
    segs=ix.get((w,r),[])
    if not segs: return "FIADA_VAZIA"
    for t0,t1 in segs:
        if t0+tol < t < t1-tol: return "INTERIOR_DE_PECA"
    for t0,t1 in segs:
        if abs(t-t0)<=tol or abs(t-t1)<=tol: return "JUNTA_JA_EXISTIA"
    lo=min(s[0] for s in segs); hi=max(s[1] for s in segs)
    return "VAZIO_LOCAL" if lo<=t<=hi else "FORA_DO_PREENCHIDO"
def norm(i):
    d=json.loads(i); d["detail"]=RE_BLK.sub("<BLK>",d.get("detail") or ""); return json.dumps(d,sort_keys=True,ensure_ascii=False)
a=collections.Counter(norm(i) for i in A["finding_identities"].get(CODE,[]))
c=collections.Counter(norm(i) for i in C["finding_identities"].get(CODE,[]))
novos=sorted((c-a).elements())
print(f"### {proj.upper()} / {CODE}: {len(novos)} novos")
tab=collections.Counter(); rowsdet=[]
for x in novos:
    d=json.loads(x); det=d["detail"]; w=d["wall"]
    mt=RE_T.search(det); mr=RE_ROWS.search(det)
    if not mt or not mr: tab["sem_geometria"]+=1; continue
    t=float(mt.group(1)); ra,rb=int(mr.group(1)),int(mr.group(2))
    sa,sb=state(IA,w,ra,t),state(IA,w,rb,t)
    key=tuple(sorted([sa,sb]))
    tab[key]+=1; rowsdet.append((w,t,ra,rb,sa,sb))
for k,v in tab.most_common(): print(f"   {v:>4}x  estado em STATE_A das duas fiadas: {k}")
print("   amostras:")
seen=set()
for w,t,ra,rb,sa,sb in rowsdet:
    k=tuple(sorted([sa,sb]))
    if k in seen: continue
    seen.add(k); print(f"      {w} t={t} fiadas {ra}/{rb} -> A:{sa} | A:{sb}")
