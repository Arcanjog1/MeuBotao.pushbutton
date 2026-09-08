"""CR-C2 - SIMULACAO diagnostica das opcoes de correcao (NAO e' patch).
Mede, para cada opcao: efeito no gabarito humano (piso de ruido), efeito no
delta R->C (o G16), e se a deteccao de trecho REALMENTE vazio sobrevive."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_wall_coverage as VC
from nuvem.benchmark import analysis

def achados(d, filtro):
    """recontagem de ROW_MOSTLY_EMPTY sob um filtro de elegibilidade de fiada."""
    step=analysis.course_step_cm(d); off=analysis.FIRST_COURSE_Z_OFFSET_CM
    idx={w["id"]:w for w in d["walls"]}; n=0
    for f in VC.validate(d):
        if f["code"]!="COVERAGE_ROW_MOSTLY_EMPTY": continue
        w=idx[f["wall"]]; r=[x for x in w["rows"] if x["row"]==f["row"]][0]
        if filtro(w,r,f,step,off): n+=1
    return n

def no_grid(w,r,f,step,off):
    rel=r["elevation_cm"]-float(w.get("base_z_cm") or 0.0)
    return (abs(rel%step)<1e-6 or abs(rel%step-step)<1e-6
            or abs((rel-off)%step)<1e-6 or abs((rel-off)%step-step)<1e-6)

OPTS=[("HOJE (sem filtro)", lambda *a: True),
      ("A: so' fiada no passo do grid", no_grid),
      ("B: so' fiada com >=50% do n. de blocos da melhor fiada da parede", None)]
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    A=json.load(open(os.path.join(root,"nuvem/benchmark/projects",proj,"reference.json")))
    R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
    C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
    print(f"===== {proj}")
    for nome,fl in OPTS[:2]:
        a,r,c = achados(A,fl), achados(R,fl), achados(C,fl)
        print(f"   {nome:38s} gabarito_A={a:4d}  R={r:4d} C={c:4d}  delta_G16={c-r:+d}")
