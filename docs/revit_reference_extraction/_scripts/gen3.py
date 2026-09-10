# -*- coding: utf-8 -*-
exec(open("gen2.py",encoding="utf-8").read())
DETALHE="04. TGD"

def ctx_cut(r):
    k=(r["_level"],r["parede"]); we=wext.get(k)
    dj=None; rel_o=None; ov=None
    for o in ops_near(r):
        d=min(abs(r["_a0"]-o["_a0"]),abs(r["_a1"]-o["_a0"]),abs(r["_a0"]-o["_a1"]),abs(r["_a1"]-o["_a1"]))
        if dj is None or d<dj:
            dj=d; rel_o=o; ov=min(r["_a1"],o["_a1"])-max(r["_a0"],o["_a0"])
    dend=None
    if we and we[0]==r["_ax"]: dend=round(min(abs(r["_a0"]-we[1]), abs(we[2]-r["_a1"])),3)
    topo = bool(we and abs(r["_z1"]-we[3])<0.5)
    var = r["i_comp_cm"] not in (None,0)
    if var: lab="CUT_LENGTH_VAR"
    elif rel_o is not None and ov>0.5 and r["_z0"]>=rel_o["_head"]-1: lab="CUT_HEIGHT_ABOVE_OPENING"
    elif rel_o is not None and ov>0.5 and r["_z1"]<=rel_o["_sill"]+1: lab="CUT_HEIGHT_BELOW_SILL"
    elif topo: lab="CUT_HEIGHT_TOP_OF_WALL"
    elif dj is not None and dj<=25: lab="CUT_HEIGHT_NEAR_JAMB"
    elif dend is not None and dend<=25: lab="CUT_HEIGHT_WALL_END"
    else: lab="CUT_HEIGHT_OTHER"
    return {"context":lab,"dist_jamba_mais_proxima_cm":round(dj,3) if dj is not None else None,
            "dist_extremidade_parede_cm":dend,"na_ultima_fiada_da_parede":topo,
            "opening_element_id_mais_proximo":rel_o["id"] if rel_o else None,
            "opening_type_mais_proximo":rel_o["titulo_abertura"] if rel_o else None,
            "corte_em":"COMPRIMENTO" if var else ("ALTURA" if r["_h"]<18.5 else "NENHUM_MEDIDO")}

def agg(sel, extra=None):
    a={"n":len(sel),
       "por_nivel":dict(sorted(collections.Counter(x["_level"] for x in sel).items())),
       "por_familia_tipo":dict(sorted(collections.Counter("%s | %s"%(x["family"],x["type"]) for x in sel).items(), key=lambda kv:-kv[1])),
       "altura_real_cm":dict(sorted(collections.Counter(x["_h"] for x in sel).items())),
       "comprimento_real_cm":dict(sorted(collections.Counter(x["_len"] for x in sel).items())[:25]),
       "por_fiada_z_rel":dict(sorted(collections.Counter(x["_zrel"] for x in sel).items())),
       "vedacao":sum(1 for x in sel if x["_ved"])}
    if extra: a.update(extra)
    return a

# 05 canaletas
ch=[r for r in blocks if r["_k"] in ("CHANNEL","CHANNEL_CUT")]
chd=[dict(base_rec(r), classification="CHANNEL_CUT" if r["_k"]=="CHANNEL_CUT" else "CHANNEL",
          **{k:v for k,v in ctx_cut(r).items() if k in ("context","dist_jamba_mais_proxima_cm","na_ultima_fiada_da_parede","opening_element_id_mais_proximo","opening_type_mais_proximo")})
     for r in ch if r["_level"]==DETALHE]
json.dump({"_meta":dict(META,dataset="05_channels",n_total_modelo=len(ch),n_detalhado=len(chd),nivel_detalhado=DETALHE,
  nota="Instancias detalhadas so' do nivel gabarito; agregados cobrem o modelo inteiro."),
  "agregado_modelo_inteiro":agg(ch),"instances":chd},
  open(os.path.join(OUT,"05_channels.json"),"w",encoding="utf-8"), ensure_ascii=False)
print("05_channels.json: total=%d detalhadas=%d" % (len(ch),len(chd)))

# 06 cortados
cu=[r for r in blocks if r["_k"] in ("CUT_BLOCK","CHANNEL_CUT")]
cud=[dict(base_rec(r), classification="CUT_BLOCK", **ctx_cut(r)) for r in cu if r["_level"]==DETALHE]
ctxall=collections.Counter()
for r in cu: ctxall[ctx_cut(r)["context"]]+=1
json.dump({"_meta":dict(META,dataset="06_cut_blocks",n_total_modelo=len(cu),n_detalhado=len(cud),nivel_detalhado=DETALHE,
  nota="No projeto humano CORTADO significa corte na ALTURA (19->9cm) com o comprimento nominal preservado, feito por FAMILIA DEDICADA. O corte no COMPRIMENTO existe so' nas familias '...VAR', via parametro de INSTANCIA Comprimento_bloco."),
  "agregado_modelo_inteiro":agg(cu,{"por_contexto":dict(ctxall.most_common())}),"instances":cud},
  open(os.path.join(OUT,"06_cut_blocks.json"),"w",encoding="utf-8"), ensure_ascii=False)
print("06_cut_blocks.json: total=%d detalhadas=%d  contextos=%s" % (len(cu),len(cud),dict(ctxall.most_common())))

# 07 blocos especiais (amarracao B34/B54 + compensadores) 
sp=[r for r in blocks if r["_k"]=="BLOCK" and any(s in (r["family"] or "").upper() for s in ("BLOCO 34","BLOCO 54","COMPENSADOR","PASTILHA","MEIO BLOCO"))]
spd=[dict(base_rec(r), classification="SPECIAL_BLOCK") for r in sp if r["_level"]==DETALHE]
json.dump({"_meta":dict(META,dataset="07_special_blocks",n_total_modelo=len(sp),n_detalhado=len(spd),nivel_detalhado=DETALHE,
  nota="Pecas nao-B39 de alvenaria comum: B34/B54 (amarracao), B19 (meio bloco), C09/C04 (compensador/pastilha) e suas variantes deitadas/VEDACAO."),
  "agregado_modelo_inteiro":agg(sp),"instances":spd},
  open(os.path.join(OUT,"07_special_blocks.json"),"w",encoding="utf-8"), ensure_ascii=False)
print("07_special_blocks.json: total=%d detalhadas=%d" % (len(sp),len(spd)))
