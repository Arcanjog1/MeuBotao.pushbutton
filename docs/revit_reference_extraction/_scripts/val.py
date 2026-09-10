# -*- coding: utf-8 -*-
exec(open("gen3.py",encoding="utf-8").read())
print("\n"+"="*70+"\n=== VALIDACAO CRUZADA (secao 14) ===")
ids=[r["id"] for r in blocks]
print("1. duplicatas de ElementId:", len(ids)-len(set(ids)))
print("2. pecas sem parametro Parede:", sum(1 for r in blocks if not r["parede"]))
print("3. pecas sem nivel associado no Revit:", sum(1 for r in blocks if r["level"] is None), "(todas VERGA/CONTRAVERGA)")
print("4. pecas sem LocationPoint:", sum(1 for r in blocks if r["x"] is None))
print("5. soma por nivel bate com o total:", sum(collections.Counter(r["_level"] for r in blocks).values())==len(blocks))
print("6. aberturas por nivel:", dict(sorted(collections.Counter(o["level"] for o in real_ops).items())))
print("7. furos de tubulacao por nivel:", dict(sorted(collections.Counter(o["level"] for o in ops if o["_furo"]).items())))
SOLVER6={("BLOCO INTEIRO - 14x19x39","BLOCO INTEIRO - 14x19x39"):"B39",("BLOCO 34 - 14x19x34","BLOCO 34 - 14x19x34"):"B34",
 ("BLOCO 54 - 14x19x54","BLOCO 54 - 14x19x54"):"B54",("MEIO BLOCO - 14x19x19","MEIO BLOCO - 14x19x19"):"B19",
 ("COMPENSADOR 14x19x9","COMPENSADOR 14x19x9"):"C09",("PASTILHA - 14x19X4","PASTILHA - 14x19X4"):"C04"}
sup=sum(1 for r in blocks if (r["family"],r["type"]) in SOLVER6)
print("8. COBERTURA DO CATALOGO DO SOLVER: %d/%d pecas (%.2f%%) | tipos: 6/57" % (sup,len(blocks),100.0*sup/len(blocks)))
nao=collections.Counter("%s | %s"%(r["family"],r["type"]) for r in blocks if (r["family"],r["type"]) not in SOLVER6)
print("   top nao suportados:")
for k,v in nao.most_common(10): print("      %6d  %s" % (v,k))
print("9. pecas com familia B39/B34/B54/B19/C09/C04 mas TIPO diferente (nao casam por nome exato):",
      sum(1 for r in blocks if r["family"] in [f for f,t in SOLVER6] and (r["family"],r["type"]) not in SOLVER6))
print("10. P01 excecoes (pecas de 19cm fora da grade):")
off=[r for r in blocks if r["_zrel"] is not None and r["_h"]>=18.5 and min((r["_zrel"]-1)%20,20-((r["_zrel"]-1)%20))>=0.02]
print("    n=%d  z_rel=%s  familias=%s" % (len(off),dict(collections.Counter(r["_zrel"] for r in off).most_common(6)),dict(collections.Counter(r["family"] for r in off).most_common(4))))
print("11. VERGAS sem abertura pareada:")
unp=[r for r in blocks if r["_k"]=="LINTEL"]
unp=[r for r in unp if not pair(r,"up")]
print("    n=%d  paredes=%s  z_rel=%s tipos=%s" % (len(unp),sorted(set(r["parede"] for r in unp)),dict(collections.Counter(r["_zrel"] for r in unp)),dict(collections.Counter(r["type"] for r in unp))))
for r in unp[:3]:
    cands=[o for o in real_ops if o["_ax"]==r["_ax"] and abs(o["_t"]-r["_t"])<=15 and o["level"]==r["_level"]]
    print("      verga %d parede=%s a=[%.1f,%.1f] z0=%.1f -> aberturas na mesma linha: %s" % (r["id"],r["parede"],r["_a0"],r["_a1"],r["_z0"],
        [(o["id"],o["titulo_abertura"],round(o["_a0"],1),round(o["_a1"],1),round(o["_head"],1)) for o in cands]))
print("12. ABERTURAS sem nenhuma peca especial associada:")
lm=collections.defaultdict(list)
for d in rel: lm[d["opening_element_id"]].append(d)
semtudo=[o for o in real_ops if not lm[o["id"]]]
print("    n=%d  por rotulo=%s  larguras=%s" % (len(semtudo),dict(collections.Counter(o["titulo_abertura"] for o in semtudo)),dict(collections.Counter(o["_w"] for o in semtudo).most_common(6))))
print("\n=== RECONSTRUCAO MANUAL DE 2 EXEMPLOS ===")
for oid in (5745651, None):
    if oid is None:
        o=[x for x in real_ops if x["titulo_abertura"]=="JANELA" and x["level"]=="04. TGD"][0]
    else:
        o=[x for x in real_ops if x["id"]==oid][0]
    print("\nABERTURA id=%d %s parede=%s nivel=%s" % (o["id"],o["titulo_abertura"],o["parede"],o["level"]))
    print("  eixo=%s jambas=[%.2f, %.2f] largura=%.2f  peitoril=%.2f  vao z=[%.2f, %.2f] (z rel %.2f-%.2f)" % (
        o["_ax"],o["_a0"],o["_a1"],o["_w"],o["peitoril_cm"],o["_sill"],o["_head"],o["_sill"]-LVBASE[o["level"]],o["_head"]-LVBASE[o["level"]]))
    for d in sorted(lm[o["id"]], key=lambda x:x["z_bottom_cm"]):
        print("  %-15s %-16s L=%6.1f  apoio esq=%5.1f dir=%5.1f  z=[%.1f,%.1f] offset=%.2f" % (
            d["classification"],d["type_name"],d["piece_length_cm"],d["left_bearing_cm"],d["right_bearing_cm"],d["z_bottom_cm"],d["z_top_cm"],d["vertical_offset_cm"]))
    viz=[r for r in blocks if r["_level"]==o["level"] and r["_ax"]==o["_ax"] and abs(r["_t"]-o["_t"])<=10
         and (abs(r["_a1"]-o["_a0"])<0.02 or abs(r["_a0"]-o["_a1"])<0.02)]
    print("  blocos encostando nas jambas: %d" % len(viz))
    for r in sorted(viz, key=lambda x:(x["_z0"],x["_a0"]))[:8]:
        lado="ESQ" if abs(r["_a1"]-o["_a0"])<0.02 else "DIR"
        print("     %-4s %-32s L=%5.1f h=%4.1f z=%7.1f (z rel %6.1f)" % (lado,r["type"],r["_len"],r["_h"],r["_z0"],r["_zrel"]))
