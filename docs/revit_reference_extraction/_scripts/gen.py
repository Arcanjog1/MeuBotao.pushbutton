# -*- coding: utf-8 -*-
import json, os, collections, datetime, hashlib
from lib import *
OUT = r"C:\Users\CIVIX\OneDrive\Área de Trabalho\Scripts.extension\MinhaAba.tab\MeuPainel.panel\MeuBotao.pushbutton\docs\revit_reference_extraction"
os.makedirs(OUT, exist_ok=True)
NOW = datetime.datetime.now().isoformat(timespec="seconds")
META = {
 "extracted_at": NOW,
 "document_title": "TORRE EASY-LO-R00_desanexado_joaoC9CL7",
 "document_path": "C:/Users/CIVIX/OneDrive/Documentos/TORRE EASY-LO-R00_desanexado_joaoC9CL7.rvt",
 "project_name": "JARDIM DA COSTA BEACH CLUB",
 "revit_version": "2026 (build 26.3.0.37)",
 "units": "cm (todas as medidas). Origem: coordenadas internas do Revit convertidas de pes (x30.48).",
 "extraction_method": "pyRevit MCP (mcp__revit-pyrevit__execute_revit_code), somente leitura, nenhuma transacao aberta.",
 "coordinate_note": "Z interno do elemento = Level.ProjectElevation + Deslocamento_do_hospedeiro. Level.Elevation esta deslocado +1510cm em relacao ao Z interno neste documento.",
 "bbox_note": "get_BoundingBox(None) das familias de BLOCO tem folga de +1cm em cada ponta do comprimento (e ate +10cm em Z no BLOCO 54 CORTADO). As dimensoes REAIS vem do solido (campos solid_*_cm em 01_family_catalog.json).",
}
GEO={}
for g in load("family_geometry.ndjson"): GEO[(g["family"],g["type"])]=g

def real(r):
    g=GEO.get((r["family"],r["type"]))
    ax,a0,a1,t,z0,z1=geom(r)
    if not g or g.get("solid_len_cm") is None: return ax,a0,a1,t,z0,z1
    dl=(a1-a0)-g["bbox_len_cm"]
    L=g["solid_len_cm"]+(dl if abs(dl)>0.001 else 0.0)
    pad=((a1-a0)-L)/2.0
    dz=(z1-z0)-g["solid_hgt_cm"]
    return ax, round(a0+pad,3), round(a1-pad,3), t, z0, round(z1-dz,3)

blocks=list(all_blocks())
for r in blocks:
    ax,a0,a1,t,z0,z1=real(r)
    r["_ax"],r["_a0"],r["_a1"],r["_t"],r["_z0"],r["_z1"]=ax,a0,a1,t,z0,z1
    r["_k"]=klass(r); r["_len"]=round(a1-a0,3); r["_h"]=round(z1-z0,3)
    r["_ved"]="VEDA" in (r["type"] or "").upper()
ops=[]
for o in load("openings.ndjson"):
    ax,a0,a1,t,z0,z1=geom(o)
    b=o["z"]; p=o["peitoril_cm"] or 0.0; a=o["altura_abertura_cm"] or 0.0
    o["_ax"],o["_a0"],o["_a1"],o["_t"]=ax,a0,a1,t
    o["_sill"],o["_head"],o["_base"]=b+p,b+p+a,b
    o["_w"]=round(a1-a0,3); o["_furo"]=not o["family"].startswith("Abertura")
    ops.append(o)
real_ops=[o for o in ops if not o["_furo"]]

def pkey(level, ax, t, a0, a1, z0):
    """chave fisica estavel: nao usa ElementId nem PARxx"""
    s="%s|%s|%.1f|%.1f|%.1f|%.1f" % (level or "?", ax, t, a0, a1, z0)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]

# ---------------- 01 catalogo -------------------
cat=collections.defaultdict(lambda: {"count":0,"por_nivel":collections.Counter()})
for r in blocks:
    c=cat[(r["family"],r["type"])]
    c["count"]+=1; c["por_nivel"][r["level"] or "(sem nivel associado)"]+=1
SOLVER={"BLOCO INTEIRO - 14x19x39|BLOCO INTEIRO - 14x19x39":"B39",
        "BLOCO 34 - 14x19x34|BLOCO 34 - 14x19x34":"B34",
        "BLOCO 54 - 14x19x54|BLOCO 54 - 14x19x54":"B54",
        "MEIO BLOCO - 14x19x19|MEIO BLOCO - 14x19x19":"B19",
        "COMPENSADOR 14x19x9|COMPENSADOR 14x19x9":"C09",
        "PASTILHA - 14x19X4|PASTILHA - 14x19X4":"C04"}
def papel(f,t):
    fu=f.upper()
    if fu.startswith("VERGA"): return "VERGA"
    if fu.startswith("CONTRAVERGA"): return "CONTRAVERGA"
    if "CANALETA" in fu: return "CANALETA_CORTADA" if "CORTAD" in fu else "CANALETA"
    if "CORTAD" in fu: return "BLOCO_CORTADO"
    return "BLOCO_COMUM"
catalog=[]
for (f,t),c in sorted(cat.items(), key=lambda kv:-kv[1]["count"]):
    g=GEO.get((f,t),{})
    code=SOLVER.get("%s|%s"%(f,t))
    catalog.append({
      "family_name":f,"type_name":t,"type_id":g.get("type_id"),"sample_element_id":g.get("sample_id"),
      "instances":c["count"],"instances_por_nivel":dict(sorted(c["por_nivel"].items())),
      "papel_observado":papel(f,t),
      "vedacao_nao_estrutural":"VEDA" in (t or "").upper(),
      "solid_len_cm":g.get("solid_len_cm"),"solid_wid_cm":g.get("solid_wid_cm"),"solid_hgt_cm":g.get("solid_hgt_cm"),
      "bbox_len_cm":g.get("bbox_len_cm"),"bbox_wid_cm":g.get("bbox_wid_cm"),"bbox_hgt_cm":g.get("bbox_hgt_cm"),
      "volume_cm3":g.get("volume_cm3"),
      "param_tipo_Comprimento_bloco_cm":next((r["t_comp_cm"] for r in blocks if r["family"]==f and r["type"]==t),None),
      "param_tipo_Altura_bloco_cm":next((r["t_alt_cm"] for r in blocks if r["family"]==f and r["type"]==t),None),
      "param_tipo_Largura_bloco_cm":next((r["t_larg_cm"] for r in blocks if r["family"]==f and r["type"]==t),None),
      "solver_block_code":code,
      "solver_support":"SUPPORTED" if code else "NOT_SUPPORTED",
    })
json.dump({"_meta":dict(META, dataset="01_family_catalog", n=len(catalog),
   nota="param_tipo_* sao PARAMETRO_REAL lidos do FamilySymbol; solid_*/bbox_* sao MEDIDOS na geometria; papel_observado e' INFERIDO."),
   "families":catalog}, open(os.path.join(OUT,"01_family_catalog.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("01_family_catalog.json:", len(catalog))

# ---------------- 02 aberturas -------------------
orecs=[]
for o in ops:
    orecs.append({
     "element_id":o["id"],"unique_id":o["uid"],"family_name":o["family"],"type_name":o["type"],
     "category":"Mobiliario (OST_Furniture)",
     "opening_type": (None if o["_furo"] else o["titulo_abertura"]),
     "classe_geometrica": "FURO_TUBULACAO" if o["_furo"] else ("PORTA" if (o["peitoril_cm"] or 0)==0 else "JANELA"),
     "level":o["level"],"level_proj_elev_cm":o["level_proj_elev_cm"],"host_offset_cm":o["host_offset_cm"],
     "parede_param":o["parede"],"sublocal":o["sublocal"],
     "x_cm":o["x"],"y_cm":o["y"],"z_cm":o["z"],"rotation_deg":round((o["rot_rad"] or 0)*180/3.141592653589793,3),
     "axis":o["_ax"],"axis_start_cm":o["_a0"],"axis_end_cm":o["_a1"],"perp_center_cm":o["_t"],
     "opening_width_cm":o["largura_abertura_cm"],"opening_height_cm":o["altura_abertura_cm"],
     "sill_height_cm":o["peitoril_cm"],"sill_z_abs_cm":None if o["_furo"] else round(o["_sill"],3),
     "head_z_abs_cm":None if o["_furo"] else round(o["_head"],3),
     "bbox":o["bb"],
     "altura_furo_cm":o["altura_furo_cm"],
     "wall_physical_key":pkey(o["level"],o["_ax"],o["_t"],o["_a0"],o["_a1"],o["_base"]),
     "wall_thickness_cm":14.0,
     "wall_element_id":None,
    })
json.dump({"_meta":dict(META,dataset="02_openings",n=len(orecs),
  nota="NAO existem Portas/Janelas nativas nem Paredes no documento: aberturas sao familias de Mobiliario e a espessura 14cm e' INFERIDA da largura real dos blocos. bbox vai do piso ate a verga (altura da bbox == Peitoril + Altura_abertura, 484/484); o vao REAL e' [sill_z_abs_cm, head_z_abs_cm]."),
  "openings":orecs}, open(os.path.join(OUT,"02_openings.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("02_openings.json:", len(orecs))
