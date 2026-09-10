"""Casos discriminantes INDEPENDENTES da revisao da C1 (nao reutiliza os
testes da propria CR). Roda contra qualquer arvore passada em argv[1]."""
import sys, os, json
root = sys.argv[1]; sys.path.insert(0, root)
from nuvem.benchmark import model
from nuvem.benchmark.validators import validate_wall_coverage as VC

STEP, BH = 20.0, 19.0

def row(i, z, length, pieces=None, wid="W001"):
    pieces = pieces or [(0.0, length)]
    bl = [model.make_block("B39", e-s, ((s+e)/2.0, 0.0), z, 0.0, s, e,
                           role=model.ROLE_STANDARD, width_cm=14.0,
                           height_cm=BH, wall_id=wid, row=i) for s, e in pieces]
    return model.make_row(i, z, bl)

def wall(h, zs, base_z=0.0, length=300.0, wid="W001", openings=None, y=0.0, pieces=None):
    rows = [row(i, z, length, pieces, wid) for i, z in enumerate(zs)]
    return model.make_wall(wid, (0, y), (length, y), 14.0, base_z_cm=base_z,
                           height_cm=h, openings=list(openings or []),
                           junctions=[], rows=rows)

def proj(walls, expected_rows=17):
    return model.assign_ids(model.make_project(
        "indep", "solver", walls=list(walls),
        settings={"base_z_cm": 0.0, "course_step_cm": STEP, "block_height_cm": BH,
                  "num_courses": expected_rows, "expected_rows": expected_rows},
        catalog={"B39": {"length_cm": 39.0, "height_cm": BH, "width_cm": 14.0}}))

def mr(p):  # findings MISSING_ROW, por eixo fisico (nao por rotulo W0xx)
    idx = {w["id"]: (w["key"], w.get("base_z_cm"))
           for w in p["walls"]}
    return sorted(str(idx[f["wall"]]) for f in VC.validate(p)
                  if f["code"] == "COVERAGE_MISSING_ROW")

R = {}
# 1. parede COMPLETA ate' z=340 (h=340, ultima fiada z=321: 321+19=340)
R["1_completa_z340_esperado_SEM_achado"] = len(mr(proj([wall(340.0, [1+i*STEP for i in range(17)])])))
# 2. parede que para em z=301 e ainda admite fiada em z=321
R["2_para_z301_esperado_COM_achado"] = len(mr(proj([wall(340.0, [1+i*STEP for i in range(16)])])))
# 3. bases Z diferentes (base 612, caso real do TP1): completa e truncada
R["3a_baseZ612_completa_SEM"] = len(mr(proj([wall(260.0, [613+i*STEP for i in range(13)], base_z=612.0)])))
R["3b_baseZ612_truncada_COM"] = len(mr(proj([wall(260.0, [613+i*STEP for i in range(10)], base_z=612.0)])))
# 4. meia-fiada (ultima fiada cobre so' metade do comprimento) - nao e' MISSING_ROW
R["4_meia_fiada_topo_SEM_missing"] = len(mr(proj([wall(260.0, [1+i*STEP for i in range(13)])] )))
p4 = proj([wall(260.0, [1+i*STEP for i in range(12)], length=300.0)])
p4["walls"][0]["rows"].append(row(12, 241.0, 300.0, pieces=[(0.0, 150.0)]))
R["4b_topo_meia_fiada_SEM_missing"] = len(mr(p4))
# 5. parede com abertura + faixas intercaladas de verga
op = [model.make_opening("window", 100.0, 190.0, 100.0, 210.0)]
w5 = wall(260.0, [1+i*STEP for i in range(13)], openings=op)
w5["rows"].append(row(13, 150.0, 300.0, pieces=[(0.0, 39.0)]))
R["5_abertura_e_verga_SEM_missing"] = len(mr(proj([w5])))
# 6. parede DIVIDIDA: dois segmentos curtos, ambos completos
R["6_dividida_dois_segmentos_completos_SEM"] = len(mr(proj([
    wall(260.0, [1+i*STEP for i in range(13)], length=120.0, wid="A"),
    wall(260.0, [1+i*STEP for i in range(13)], length=169.0, wid="B", y=50.0)])))
# 7. AUSENCIA REAL: parede parou na metade
R["7a_parou_na_metade_COM"] = len(mr(proj([wall(260.0, [1+i*STEP for i in range(7)])])))
R["7b_falta_exatamente_a_ultima_COM"] = len(mr(proj([wall(260.0, [1+i*STEP for i in range(12)])])))
# 7c. expected_rows BAIXO nao pode mais esconder truncamento real
R["7c_expected_rows_1_nao_esconde_COM"] = len(mr(proj([wall(260.0, [1+i*STEP for i in range(7)])], expected_rows=1)))
# 7d. expected_rows ALTO nao pode inventar achado em parede completa
R["7d_expected_rows_999_nao_inventa_SEM"] = len(mr(proj([wall(260.0, [1+i*STEP for i in range(13)])], expected_rows=999)))
# 8. ordem de entrada + determinismo (por identidade fisica)
ws = [wall(260.0, [1+i*STEP for i in range(7)], length=300.0, wid="X", y=0.0),
      wall(340.0, [1+i*STEP for i in range(17)], length=250.0, wid="Y", y=80.0)]
a = mr(proj(ws)); b = mr(proj(list(reversed(ws))))
R["8a_ordem_entrada_invariante"] = (a == b)
R["8b_determinismo_3x"] = (mr(proj(ws)) == mr(proj(ws)) == mr(proj(ws)))
print(json.dumps(R, indent=1, sort_keys=True))
