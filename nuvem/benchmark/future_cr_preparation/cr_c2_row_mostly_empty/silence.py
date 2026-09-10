import json, sys, os, collections
root = sys.argv[1]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_wall_coverage as V
from nuvem.benchmark import analysis
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    data = json.load(open(os.path.join(root,"nuvem/benchmark/projects",proj,"reference.json")))
    bh = analysis.block_height_of(data); step = analysis.course_step_cm(data)
    no_h = no_blocks = decided = 0; folgas=[]
    for w in data.get("walls") or []:
        top = V.wall_top_z_cm(w)
        if top is None: no_h += 1; continue
        el=[float(b.get("z_cm") or 0) for r in (w.get("rows") or []) for b in (r.get("blocks") or [])]
        if not el: no_blocks += 1; continue
        decided += 1
        folgas.append(round(top - max(el) - bh, 2))   # folga fisica acima do corpo da fiada mais alta
    folgas.sort()
    print(f"{proj}: paredes={len(data['walls'])} sem_height={no_h} sem_blocos={no_blocks} COM_VEREDITO={decided}")
    print(f"   block_h={bh} step={step} | folga(top - z_max - block_h): min={folgas[0]} max={folgas[-1]} limiar_para_acusar={step}")
    print("   distribuicao folgas:", collections.Counter(folgas).most_common(12))
