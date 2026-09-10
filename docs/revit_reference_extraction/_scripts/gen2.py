# -*- coding: utf-8 -*-
exec(open("pre.py",encoding="utf-8").read())
import math
LVBASE={"04. TGD":340.0,"05. TP1":611.0,"08. TP1":1424.0,"10. TP1":1966.0,"20. TP1":4676.0,"21. COB":4947.0,
        "01. TER":-760.0,"02. G02":-445.0,"03. G03":-80.0}
bases=sorted(set(LVBASE.values()))
def lvl_by_z(z):
    c=[b for b in bases if z>=b-5]
    if not c: return None,None
    b=max(c)
    nm=[k for k,v in LVBASE.items() if v==b][0]
    return nm, round(z-b,3)
for r in blocks:
    if r["level"] is None:
        nm,zr=lvl_by_z(r["_z0"]); r["_level"]=nm; r["_zrel"]=zr; r["_level_inferido"]=True
    else:
        r["_level"]=r["level"]; r["_zrel"]=round(r["_z0"]-LVBASE[r["level"]],3); r["_level_inferido"]=False
for o in real_ops:
    o["_zrel_sill"]=round(o["_sill"]-LVBASE[o["level"]],3); o["_zrel_head"]=round(o["_head"]-LVBASE[o["level"]],3)

# extensao das paredes por (nivel, parede)
wl=collections.defaultdict(list)
for r in blocks: wl[(r["_level"], r["parede"])].append(r)
wext={}
for k,rs in wl.items():
    axc=collections.Counter(x["_ax"] for x in rs); ax=axc.most_common(1)[0][0]
    sel=[x for x in rs if x["_ax"]==ax]
    wext[k]=(ax, min(x["_a0"] for x in sel), max(x["_a1"] for x in sel), max(x["_z1"] for x in rs), min(x["_z0"] for x in rs))

idx=collections.defaultdict(list)
for o in real_ops: idx[(o["_ax"], round(o["_t"]/25.0))].append(o)
def ops_near(r, tol=10.0):
    out=[]
    for d in (-1,0,1): out.extend(idx.get((r["_ax"], round(r["_t"]/25.0)+d),[]))
    return [o for o in out if abs(o["_t"]-r["_t"])<=tol and o["level"]==r["_level"]]

def base_rec(r):
    k=(r["_level"], r["parede"])
    we=wext.get(k)
    return {"piece_element_id":r["id"],"piece_unique_id":r["uid"],
      "family_name":r["family"],"type_name":r["type"],"sigla":r["sigla"],
      "level":r["_level"],"level_inferido_pelo_z":r["_level_inferido"],
      "parede_param":r["parede"],"local":r["local"],"sublocal":r["sublocal"],
      "piece_length_cm":r["_len"],"piece_width_cm":14.0,"piece_height_cm":r["_h"],
      "x_cm":r["x"],"y_cm":r["y"],"z_cm":r["z"],"rotation_deg":round((r["rot_rad"] or 0)*180/math.pi,3),
      "axis":r["_ax"],"axis_start_cm":r["_a0"],"axis_end_cm":r["_a1"],"perp_center_cm":r["_t"],
      "z_bottom_cm":r["_z0"],"z_top_cm":r["_z1"],"z_rel_nivel_cm":r["_zrel"],
      "course_or_z_band":("FIADA_%d"%(int(round((r["_zrel"]-1)/20.0))+1)) if (r["_zrel"] is not None and abs(((r["_zrel"]-1)%20))<0.01) else ("BANDA_9CM_z%s"%r["_zrel"]),
      "vedacao_nao_estrutural":r["_ved"],
      "wall_physical_key":pkey(r["_level"], r["_ax"], r["_t"], we[1] if we else 0, we[2] if we else 0, we[4] if we else 0),
      "instance_Comprimento_bloco_cm":r["i_comp_cm"] if r["i_comp_cm"] else None,
      "bbox":r["bb"]}

def pair(r, side):
    best=None
    for o in ops_near(r):
        ov=min(r["_a1"],o["_a1"])-max(r["_a0"],o["_a0"])
        if ov<=0.5: continue
        if side=="up" and not (o["_head"]-1.0 <= r["_z0"] <= o["_head"]+1.0): continue
        if side=="dn" and not (o["_sill"]-1.0 <= r["_z1"] <= o["_sill"]+1.0): continue
        if best is None or ov>best[1]: best=(o,ov)
    return best[0] if best else None

rel=[]; lint=[]; cvs=[]
for r in blocks:
    if r["_k"] not in ("LINTEL","COUNTER_LINTEL"): continue
    side = "up" if r["_k"]=="LINTEL" else "dn"
    o = pair(r, side)
    usado_como = r["_k"]
    if o is None:
        alt = pair(r, "dn" if side=="up" else "up")
        if alt is not None:
            o = alt
            usado_como = "COUNTER_LINTEL" if side=="up" else "LINTEL"
            side = "dn" if side=="up" else "up"
    d=base_rec(r)
    d["classification"]=usado_como
    d["classification_pela_familia"]=r["_k"]
    d["familia_usada_fora_do_papel_do_nome"]= usado_como!=r["_k"]
    r["_k"]=usado_como
    d["confidence"]="ALTA" if o else "BAIXA"
    if o:
        d.update({"opening_element_id":o["id"],"opening_unique_id":o["uid"],"opening_type":o["titulo_abertura"],
          "opening_width_cm":o["_w"],"opening_height_cm":o["altura_abertura_cm"],"sill_height_cm":o["peitoril_cm"],
          "left_bearing_cm":round(o["_a0"]-r["_a0"],3),"right_bearing_cm":round(r["_a1"]-o["_a1"],3),
          "vertical_offset_cm":round(r["_z0"]-o["_head"],3) if usado_como=="LINTEL" else round(o["_sill"]-r["_z1"],3),
          "parede_abertura":o["parede"],"parede_bate":o["parede"]==r["parede"]})
        rel.append(d)
    else:
        d.update({"opening_element_id":None,"opening_unique_id":None,"opening_type":None,
          "opening_width_cm":None,"opening_height_cm":None,"sill_height_cm":None,
          "left_bearing_cm":None,"right_bearing_cm":None,"vertical_offset_cm":None,
          "parede_abertura":None,"parede_bate":None})
    (lint if usado_como=="LINTEL" else cvs).append(d)
json.dump({"_meta":dict(META,dataset="03_lintels",n=len(lint),
  nota="Classificacao POR USO (posicao geometrica), nao pelo nome da familia. VERGAS = pecas assentadas com a base no topo do vao. NAO tem nivel associado no Revit (FAMILY_LEVEL_PARAM=-1): o campo level e' INFERIDO pelo Z. Comprimento so' existe no NOME do tipo; confirmado pelo solido."),
  "lintels":lint}, open(os.path.join(OUT,"03_lintels.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"_meta":dict(META,dataset="04_counter_lintels",n=len(cvs),
  nota="Classificacao POR USO: pecas com o topo exatamente no peitoril. Inclui 25 instancias da familia VERGA JANELA usadas como contraverga (ver familia_usada_fora_do_papel_do_nome). Mesma limitacao de nivel das vergas."),
  "counter_lintels":cvs}, open(os.path.join(OUT,"04_counter_lintels.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("03_lintels.json: %d (pareadas %d)" % (len(lint), sum(1 for d in lint if d["opening_element_id"])))
print("04_counter_lintels.json: %d (pareadas %d)" % (len(cvs), sum(1 for d in cvs if d["opening_element_id"])))
json.dump({"_meta":dict(META,dataset="08_piece_opening_wall_relations",n=len(rel),
  nota="Uma linha por par (peca especial, abertura) confirmado geometricamente. wall_element_id e' sempre null: NAO existem Walls neste documento."),
  "relations":rel}, open(os.path.join(OUT,"08_piece_opening_wall_relations.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("08_piece_opening_wall_relations.json:", len(rel))
