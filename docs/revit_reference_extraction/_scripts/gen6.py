# -*- coding: utf-8 -*-
exec(open("gen3.py",encoding="utf-8").read())
import statistics
P=[]
def pat(pid,desc,n,exc,mn=None,mx=None,med=None,conf=None,extra=None):
    tot=n+exc
    d={"id":pid,"padrao":desc,"ocorrencias":n,"excecoes":exc,
       "percentual":round(100.0*n/tot,2) if tot else None,"min":mn,"max":mx,"mediana":med,
       "confianca":conf or ("ALTA" if tot and n/float(tot)>=0.98 else ("MEDIA" if tot and n/float(tot)>=0.80 else "BAIXA"))}
    if extra: d.update(extra)
    P.append(d); print("  %-8s %-72s %5d/%-5d %6.2f%%  %s" % (pid,desc[:72],n,tot,d["percentual"] or 0,d["confianca"]))
    return d

print("=== PADROES ===")
# P01 grade de fiadas
zs=collections.Counter()
for r in blocks:
    if r["_zrel"] is None: continue
    zs[r["_zrel"]]+=1
z19=collections.Counter(); z9=collections.Counter()
for r in blocks:
    if r["_zrel"] is None: continue
    (z19 if r["_h"]>=18.5 else z9)[r["_zrel"]]+=1
def onmod(z,m): 
    d=(z-m)%20.0
    return min(d,20.0-d)<0.02
grade=sum(v for z,v in z19.items() if onmod(z,1))
fora=sum(v for z,v in z19.items() if not onmod(z,1))
pat("P01","Peca de 19cm de altura assenta na grade base_nivel+1cm + k*20cm (19 bloco + 1 junta)",grade,fora,
    extra={"z_relativos_pecas_19cm":dict(sorted(z19.items())),"z_relativos_pecas_9cm":dict(sorted(z9.items()))})
# P02/P03 portas
portas=[o for o in real_ops if o["titulo_abertura"]=="PORTA"]
jan=[o for o in real_ops if o["titulo_abertura"]=="JANELA"]
ab=[o for o in real_ops if o["titulo_abertura"]=="ABERTURA"]
lm=collections.defaultdict(list); cm=collections.defaultdict(list)
for d in rel:
    (lm if d["classification"]=="LINTEL" else cm)[d["opening_element_id"]].append(d)
pat("P02","Toda PORTA tem verga (familia VERGA JANELA)",sum(1 for o in portas if lm[o["id"]]),sum(1 for o in portas if not lm[o["id"]]))
pat("P03","Nenhuma PORTA tem contraverga",sum(1 for o in portas if not cm[o["id"]]),sum(1 for o in portas if cm[o["id"]]))
pat("P04","JANELA tem verga",sum(1 for o in jan if lm[o["id"]]),sum(1 for o in jan if not lm[o["id"]]))
pat("P05","JANELA tem contraverga",sum(1 for o in jan if cm[o["id"]]),sum(1 for o in jan if not cm[o["id"]]))
pat("P06","Vao rotulado ABERTURA nao tem verga nem contraverga",sum(1 for o in ab if not lm[o["id"]] and not cm[o["id"]]),sum(1 for o in ab if lm[o["id"]] or cm[o["id"]]))
# P07/P08 offsets
L=[d for d in rel if d["classification"]=="LINTEL"]; C=[d for d in rel if d["classification"]=="COUNTER_LINTEL"]
pat("P07","Base da verga coincide EXATAMENTE com o topo do vao (offset 0)",sum(1 for d in L if abs(d["vertical_offset_cm"])<0.02),sum(1 for d in L if abs(d["vertical_offset_cm"])>=0.02))
pat("P08","Topo da contraverga coincide EXATAMENTE com o peitoril (offset 0)",sum(1 for d in C if abs(d["vertical_offset_cm"])<0.02),sum(1 for d in C if abs(d["vertical_offset_cm"])>=0.02))
bl=[d["left_bearing_cm"] for d in L]+[d["right_bearing_cm"] for d in L]
bc=[d["left_bearing_cm"] for d in C]+[d["right_bearing_cm"] for d in C]
pat("P09","Verga apoia >= 9cm de cada lado da jamba",sum(1 for x in bl if x>=8.98),sum(1 for x in bl if x<8.98),min(bl),max(bl),statistics.median(bl),
    extra={"distribuicao_apoio":dict(sorted(collections.Counter(round(x,1) for x in bl).items(), key=lambda kv:-kv[1])[:12])})
pat("P10","Contraverga apoia >= 9cm de cada lado da jamba",sum(1 for x in bc if x>=8.98),sum(1 for x in bc if x<8.98),min(bc),max(bc),statistics.median(bc),
    extra={"distribuicao_apoio":dict(sorted(collections.Counter(round(x,1) for x in bc).items(), key=lambda kv:-kv[1])[:12])})
pat("P11","Verga simetrica (apoio esquerdo == direito)",sum(1 for d in L if abs(d["left_bearing_cm"]-d["right_bearing_cm"])<0.6),sum(1 for d in L if abs(d["left_bearing_cm"]-d["right_bearing_cm"])>=0.6))
pat("P12","Verga = largura do vao + 19 + 19 (apoio padrao de meio bloco)",sum(1 for d in L if abs(d["piece_length_cm"]-d["opening_width_cm"]-38)<0.6),sum(1 for d in L if abs(d["piece_length_cm"]-d["opening_width_cm"]-38)>=0.6),
    extra={"distribuicao_comprimento_menos_vao":dict(sorted(collections.Counter(round(d["piece_length_cm"]-d["opening_width_cm"],0) for d in L).items(), key=lambda kv:-kv[1])[:8])})
# P13 dimensoes
vc=[r for r in blocks if r["_k"] in ("LINTEL","COUNTER_LINTEL")]
pat("P13","Verga/contraverga tem 9cm de altura e 14cm de largura",sum(1 for r in vc if abs(r["_h"]-9)<0.02),sum(1 for r in vc if abs(r["_h"]-9)>=0.02))
pat("P14","Toda peca tem 14cm de largura (espessura unica de parede)",sum(1 for r in blocks if abs(GEO.get((r["family"],r["type"]),{}).get("solid_wid_cm",14)-14)<0.05),
    sum(1 for r in blocks if abs(GEO.get((r["family"],r["type"]),{}).get("solid_wid_cm",14)-14)>=0.05))
def ort(rr):
    d=(rr or 0.0)%(math.pi/2.0)
    return min(d, math.pi/2.0-d)<1e-4
pat("P15","Rotacao e' multiplo exato de 90 graus (modelo 100% ortogonal)",sum(1 for r in blocks if ort(r["rot_rad"])),sum(1 for r in blocks if not ort(r["rot_rad"])))
# P16 cortados
cu=[r for r in blocks if r["_k"] in ("CUT_BLOCK","CHANNEL_CUT")]
pat("P16","CORTADO = corte na ALTURA (19->9cm) com comprimento nominal preservado",
    sum(1 for r in cu if abs(r["_h"]-9)<0.02 and not r["i_comp_cm"]),sum(1 for r in cu if not(abs(r["_h"]-9)<0.02 and not r["i_comp_cm"])),
    extra={"alturas_medidas":dict(sorted(collections.Counter(r["_h"] for r in cu).items()))})
ctxall=collections.Counter(ctx_cut(r)["context"] for r in cu)
djs=[ctx_cut(r)["dist_jamba_mais_proxima_cm"] for r in cu]
djs=[d for d in djs if d is not None]
pat("P17","Bloco cortado fica a menos de 60cm de uma jamba de vao (REGRAS 10.5)",sum(1 for d in djs if d<60),sum(1 for d in djs if d>=60),
    extra={"sem_abertura_na_mesma_parede":len(cu)-len(djs),"por_contexto":dict(ctxall.most_common())})
# P18 fiada de topo
tops=collections.Counter(); nocan=[]
for k,rs in wl.items():
    if k[0] is None: continue
    top=max(x["_z1"] for x in rs); last=[x for x in rs if abs(x["_z1"]-top)<0.5]
    ks=collections.Counter(x["_k"] for x in last)
    frac=(ks.get("CHANNEL",0)+ks.get("CHANNEL_CUT",0))/float(len(last))
    tops["canaleta" if frac>0.999 else ("mista" if frac>0 else "sem_canaleta")]+=1
    if frac<=0.001: nocan.append((k, round(top-LVBASE[k[0]],2), len(rs)))
pat("P18","Ultima fiada da parede e' 100% canaleta (conflito REGRAS 10.7)",tops["canaleta"],tops["sem_canaleta"]+tops["mista"],
    extra={"detalhe":dict(tops),"topo_z_rel_das_paredes_sem_canaleta":dict(collections.Counter(x[1] for x in nocan))})
# P19 sequencia acima da porta
seq=collections.Counter()
for o in portas:
    zr=round(o["_head"]-LVBASE[o["level"]],2)
    seq[zr]+=1
pat("P19","Topo do vao de PORTA na cota 221cm (fiada 12 completa)",seq.get(221.0,0),sum(v for k,v in seq.items() if k!=221.0),
    extra={"cotas_de_topo_de_porta":dict(seq)})
# P20 duas fiadas de 9 == uma de 19
ok9=sum(v for z,v in z9.items() if onmod(z,1) or onmod(z,11))
bad9=sum(v for z,v in z9.items() if not (onmod(z,1) or onmod(z,11)))
pat("P20","Peca de 9cm ocupa metade de uma fiada: base da fiada (z=+1) ou meia-fiada (z=+11); 9+1+9=19",ok9,bad9,
    extra={"z_fora_do_par":dict(sorted((z,v) for z,v in z9.items() if not (onmod(z,1) or onmod(z,11))))})
json.dump({"_meta":dict(META,dataset="09_observed_patterns",n=len(P),
  nota="Confianca: ALTA >=98% sem excecao relevante; MEDIA >=80%; BAIXA abaixo disso. NENHUM destes padroes foi promovido a regra normativa - sao observacoes medidas."),
  "patterns":P}, open(os.path.join(OUT,"09_observed_patterns.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n09_observed_patterns.json:", len(P))
