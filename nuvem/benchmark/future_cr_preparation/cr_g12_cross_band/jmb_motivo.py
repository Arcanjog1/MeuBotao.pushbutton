"""MOTIVO EXATO do JUNCTION_MISSING_BINDING nas 10 identidades novas.
Criterio real do validador: nenhuma peca COBRE o ponto do no' naquela banda
de cota (block_covers_point), com >=2 paredes participantes."""
import json, sys, os, math, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_junctions as VJ
from nuvem.benchmark import model
def folga(block, pt):
    """quanto FALTA para a peca alcancar o ponto (cm); <=0 = cobre."""
    a=math.radians(block.get("rotation_deg") or 0.0)
    ux,uy=math.cos(a),math.sin(a)
    dx=pt[0]-block["center_cm"][0]; dy=pt[1]-block["center_cm"][1]
    along=dx*ux+dy*uy; across=-dx*uy+dy*ux
    return max(abs(along)-(block.get("length_cm") or 0)/2.0,
               abs(across)-(block.get("width_cm") or 14.0)/2.0)
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
    C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
    def ach(d):
        s={}
        for f in VJ.validate(d):
            if f["code"]=="JUNCTION_MISSING_BINDING":
                s.setdefault((tuple(round(v,1) for v in f["point_cm"]), round(f["elevation_cm"],1)),[]).append(f)
        return s
    aR,aC=ach(R),ach(C); novas=sorted(k for k in aC if k not in aR)
    print(f"\n===== {proj}: {len(novas)} identidades novas")
    print(f"  {'#':>2} {'ponto':>22} {'z':>7} {'tipo':>4} {'paredes':>28} {'peca+proxima':>14} {'codigo':>8}")
    for i,(pt,z) in enumerate(novas,1):
        f=aC[(pt,z)][0]
        best=(1e9,None)
        for w in C["walls"]:
            for r in w.get("rows") or []:
                if abs(r["elevation_cm"]-z)>0.6: continue
                for b in r.get("blocks") or []:
                    g=folga(b,pt)
                    if g<best[0]: best=(g,b)
        nb=f.get("neighbors") or []
        print(f"  {i:2d} {str(pt):>22} {z:7.1f} {str(f.get('junction_type')):>4} {str(nb):>28} {best[0]:11.1f}cm {str(best[1].get('code') if best[1] else '-'):>8}")
