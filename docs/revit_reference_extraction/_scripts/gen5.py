# -*- coding: utf-8 -*-
exec(open("gen3.py",encoding="utf-8").read())
sp=[r for r in blocks if r["_k"]=="BLOCK" and any(s in (r["family"] or "").upper() for s in ("BLOCO 34","BLOCO 54","COMPENSADOR","PASTILHA","MEIO BLOCO"))]
amar=[r for r in sp if any(s in (r["family"] or "").upper() for s in ("BLOCO 34","BLOCO 54"))]
def lean(r):
    return {"id":r["id"],"family_name":r["family"],"type_name":r["type"],"parede_param":r["parede"],
      "axis":r["_ax"],"a0":r["_a0"],"a1":r["_a1"],"t":r["_t"],"z0":r["_z0"],"z_rel":r["_zrel"],
      "len_cm":r["_len"],"h_cm":r["_h"],"rot_deg":round((r["rot_rad"] or 0)*180/math.pi,1),
      "mirrored":r["mirrored"],"hand":[r["hx"],r["hy"]],"facing":[r["fx"],r["fy"]],
      "wall_physical_key":pkey(r["_level"],r["_ax"],r["_t"],wext[(r["_level"],r["parede"])][1],wext[(r["_level"],r["parede"])][2],wext[(r["_level"],r["parede"])][4])}
spd=[lean(r) for r in amar if r["_level"]==DETALHE]
json.dump({"_meta":dict(META,dataset="07_special_blocks",n_total_modelo=len(sp),
  n_amarracao_modelo=len(amar),n_detalhado=len(spd),nivel_detalhado=DETALHE,
  nota="Agregado cobre todas as pecas nao-B39 de alvenaria comum. Instancias detalhadas (registro enxuto) sao so' as pecas de AMARRACAO (BLOCO 34 / BLOCO 54) do nivel gabarito. As pecas B34/B54 sao ASSIMETRICAS: 'hand'/'facing'/'mirrored' definem a orientacao do vao menor."),
  "agregado_modelo_inteiro":agg(sp),"agregado_amarracao":agg(amar),"instances":spd},
  open(os.path.join(OUT,"07_special_blocks.json"),"w",encoding="utf-8"), ensure_ascii=False)
print("07 enxuto: detalhadas=%d" % len(spd))
