# Escala do solver: onde o fluxo para de funcionar ao sair da bancada de 2 paredes

```json
{
  "date": "2026-09-10",
  "scope": "current",
  "branch": "claude/revit-scale-autofix",
  "base": "41086e43b6b56102ce736b816debad04749fa4bf",
  "main_observada": "21576ee3d0826f362bce1038131603bd2ccf5dc1",
  "pr": "not-created",
  "veredito": "PARTIAL SCALE PASS - LIMITE CONHECIDO E EXPLICADO (diagnostico fechado, correcao BLOQUEADA por decisao normativa e por permissao)",
  "objective": "Descobrir qual e' a PRIMEIRA diferenca, ao sair do cenario de 2 paredes/1 encontro em L/0 aberturas, que faz o fluxo falhar - e isolar a MENOR reproducao de cada causa, sem hardcodar nada deste RVT e sem criar norma de dominio nova.",
  "ambiente": [
    "Revit 2027, build 27.2.0.39, pt-BR, PID 33220.",
    "pyRevit 6.5.4.26228+1146. Botao roda no engine CPython 3 (shebang `#! python3`); o MCP roda IronPython 2.7 - distincao registrada, ver LIMITES.",
    "Documento UNICO aberto: 'TESTE MODULACAO' (C:\\Users\\twitc\\Desktop\\CIVIX). Sem ambiguidade de alvo, portanto sem HARD BLOCKER de identificacao.",
    "Pacote executado: teste-perf.pushbutton, head 712f2217f455694e10b110b3cd46543d7c0fbdce, os 13 arquivos de core/ + Script.py conferidos por sha256 contra o repo - IDENTICOS. O codigo Python de 712f221 e do HEAD desta missao e' o mesmo (a diferenca entre os dois commits e' documental)."
  ],
  "estado_inicial_do_rvt": [
    "As ~309 Walls de execucoes anteriores NAO existiam mais, como o usuario relatou. Mas o documento AINDA continha a bancada provada: 2 Walls 'Parede CAD - 14.0cm' (354cm + 69cm em L, nivel pb, altura 280cm) e 154 blocos do plugin (112 B39 + 28 B34 + 14 B19) em 14 fiadas de 11 pecas.",
    "154 = 14 fiadas x 11 pecas confere com a altura NATIVA de 280cm deste modelo; os 187/17 fiadas do historico vinham da bancada derivada de 340cm. Nao e' divergencia."
  ],
  "planta_deste_rvt": [
    "CAD 'TORRE' (ImportInstance), 1196 linhas em 10 layers, 0 degeneradas. Layer de parede: A-WALL, 937 linhas -> 630 apos merge_collinear_fragments.",
    "Espessura 14cm -> 179 eixos, 272 linhas sem par, 0 duplicatas removidas.",
    "251 nos: 85 T, 83 ponta livre, 57 L, 14 continuacao reta, 12 X.",
    "0 aberturas: o modelo nao tem NENHUMA familia de porta/janela (so' os blocos, itens de detalhe, anotacoes e carimbo). O modo 'auto' devolver 0 e' correto, nao falha de deteccao.",
    "Comprimentos: min 18,5cm, mediana 159,5cm, max 802cm; 42 eixos abaixo de 40cm (bonecas).",
    "EVIDENCIA DE TESTE LOCAL, nao regra: o historico citava 128 eixos / 309 paredes / 264 ignoradas. Este RVT da 179 eixos / 272 sem par com 0 aberturas. Numeros NAO foram forcados para o historico; a diferenca mais provavel e' que a execucao historica tinha aberturas (modo 'pick'), que religam fragmentos e mudam a contagem de eixos."
  ],
  "metodo": [
    "A escada de escala roda FORA do Revit, em CPython 3.14.7, com os dubles de tests/revit_stubs.py - a MESMA semantica de `/` do engine CPython que executa o botao. Motivo: nenhum modulo do motor tem `from __future__ import division`, entao rodar o solver no IronPython 2.7 do MCP mudaria silenciosamente divisoes inteiras.",
    "Os 179 eixos vem do PROPRIO pipeline do plugin dentro do Revit (extract_lines_by_layer -> collect_opening_instances -> merge_collinear_fragments -> find_wall_pairs) e foram exportados como fixture. Nenhum algoritmo de deteccao improvisado.",
    "Cada rodada executa o caminho real: extend_wall_ends_to_junctions -> build_wall_graph -> assign_openings_to_walls -> solve_building_blocks_all_courses -> controlled_beta_preflight, e le a auditoria de amarracao de dentro do proprio resultado do solver (`wall_bond_audits`), nunca uma segunda implementacao paralela.",
    "Subsets crescem por CONEXIDADE a partir da bancada e sao identificados por CHAVE FISICA (extremos arredondados e ordenados), nunca por indice, W0xx ou ElementId."
  ],
  "matriz_de_escala": [
    "K=2   PASS  (147 pecas, 0 colisao, preflight ok) - BASELINE REESTABELECIDO",
    "K=5   FAIL  bond: CONTINUOUS_VERTICAL_JOINT",
    "K=6   PASS  (742 pecas, 0 colisao, preflight ok)",
    "K=7   FAIL  preflight: 7 colisoes -> BETA BLOQUEADO (gate DURO, nada e' criado)",
    "K=10..K=179 FAIL, sempre pelo preflight",
    "PLANTA INTEIRA (179 eixos, 251 nos, ~10.500 pecas): solve em 2,0-3,6s, preflight com 49 colisoes."
  ],
  "desempenho": [
    "PERFORMANCE NAO E' O GARGALO. K=10 0,023s | K=50 0,086s | K=100 0,164s | K=150 1,06s | K=179 2,0s. Nenhum stall, nenhum congelamento, nenhuma chamada presa.",
    "O travamento historico ('planta de 306 eixos, ~55 min parado em 99%') NAO se reproduz - a otimizacao de _collision_candidate_pairs/_placed_index_near_wall ja' o resolveu.",
    "Ha' um joelho superlinear entre K=100 (0,16s) e K=150 (1,06s) que merece medicao futura, mas 2s absolutos na planta inteira nao bloqueiam nada."
  ],
  "causas_raiz": [
    "DEFEITO 1 - AMARRACAO (PHYSICAL SOLVER FAILURE, categoria H/encontro em T). Reproducao minima: 2 eixos. Um trecho curto entre a ponta livre e um no' T e' preenchido de forma IDENTICA nas duas paridades, produzindo junta corrida de altura total. Medido: parede 781cm com T em t=48cm; fiada 0 = B39[1,40]|B34[41,75], fiada 1 = B39[1,40]|B34[41,55] - junta em 40,5cm com gap 1,0cm nas 14 fiadas. O auditor esta' CORRETO; nao e' falso positivo (verificado reproduzindo passo a passo o proprio calculo do detector).",
    "DEFEITO 2 - COLISAO EM NOS T PROXIMOS (categoria H+P). Reproducao minima: 3 eixos. Dois nos T sobre a MESMA parede a 27cm um do outro, enquanto a peca de amarracao B54 mede 54cm. O solver emite um `T_INTERSECTION_MAIN` por no', independentemente: A centrado em t=338 ocupa [311,365], B centrado em t=365 ocupa [338,392]. Dois solidos no mesmo espaco. Alcance: 1 parede em 179 (2 pares de nos proximos: 48cm e 27cm).",
    "DEFEITO 3 - COLISAO BONECA x PAREDE (categoria F+P). DOMINANTE: 42 das 49 colisoes da planta inteira. Bonecas de 21-24cm que ATRAVESSAM o eixo de uma parede longa recebem `STANDARD_FILL` proprio, que ocupa o mesmo espaco do preenchimento da parede atravessada. Medido: parede 150 (21cm, 1765,7->1786,7) cruzando a parede 175 em X=1772,7 -> B19 invade B39 em 13,0cm; parede 123 (24cm) cruzando a parede 34 -> B19 invade B39 em 9,0cm e C04 em 4,0cm."
  ],
  "hipoteses_descartadas_com_evidencia": [
    "NAO e' quantidade. O primeiro FAIL de amarracao reproduz com 2 eixos e o primeiro FAIL de colisao com 3 - ambos do tamanho da bancada. Acrescentar uma parede chega a CORRIGIR o defeito de amarracao (K=5 FAIL -> K=6 PASS), o que confirma que a causa e' o contexto geometrico local, nao o tamanho do conjunto.",
    "NAO e' orcamento de busca. Subir PIER_LAYOUT_VARIANTS_PER_COURSE de 1 para 2/3/4 NAO resolve: as colisoes vao de 49 para 61/57/62 e as reprovacoes de amarracao de 22 para 45/46/51, com 5x o tempo. Knob descartado (e' orcamento, nao norma - por isso podia ser testado sem decisao do usuario).",
    "NAO e' proteccao de bancada. Varredura do motor por expected_wall/allowed_wall/allowlist/expected_count/fingerprint/187/17 fiadas: NADA. `controlled_beta_preflight` e' GENERAL SAFETY (geometria finita, colisao, invasao de vao), sem limite de contagem nem lista de IDs. A unica coisa calibrada na bancada e' a tolerancia do refresh - ver RISCOS.",
    "NAO e' desempenho/stall/thread. Ver secao desempenho."
  ],
  "correcoes_anteriores_verificadas_presentes": [
    "A - solve->create: `Execute()` consome a acao no inicio e despacha por copia local (linha ~10286); o `finally` so' registra `pendente`. PRESERVADA.",
    "B - auditor de faixa vertical: BOND_STRIP_MIN_ADJACENT_COURSES=2 e `_longest_adjacent_course_run` presentes; `alternating_strips` continua devolvido como DADO sem penalidade. PRESERVADA.",
    "C - `_pump_ui`: guarda de ManagedThreadId presente. PRESERVADA.",
    "D - analyze sincrono: nenhuma thread de fundo no caminho normal. PRESERVADA.",
    "E - Z pelo NIVEL: `base_z_abs = selected_level.Elevation` (linha 15612), nao Base Offset da Wall. PRESERVADA e NAO alterada."
  ],
  "property_tests": [
    "PERMUTACAO DA ENTRADA - as mesmas 179 paredes em 5 ordens diferentes (natural, invertida, 3 shuffles): as COLISOES sao ESTAVEIS em 49 e as intersection_failures em 4 (portanto os defeitos 2 e 3 sao geometricos e robustos, nao artefato de ordem). Mas as pecas variam 10514-10626 (+-112) e as reprovacoes de amarracao 19-24. O resultado fisico NAO e' invariante a ordem de coleta.",
    "Isso e' da MESMA familia do achado ja' registrado em 2026-09-10 ('a atribuicao das letras A/B depende do REFERENCIAL DE COORDENADAS'), agora medido tambem sob permutacao. Registrado como EVIDENCIA DE TESTE LOCAL, nao como regra."
  ],
  "limites_desta_missao": [
    "As Walls NAO foram recriadas no Revit: a limpeza dos 2 Walls + 154 blocos do lote anterior do plugin (propriedade PROVADA: WallType 'Parede CAD - 14.0cm' que o proprio plugin gera, e as 3 familias de bloco em 14 fiadas alinhadas a essas paredes) foi RECUSADA pelo gate de permissao. Sem essa limpeza, rodar main() criaria paredes coincidentes com as 2 existentes (medido: distancia 0,0cm dos eixos #21 e #178), e o auto-join do Revit contaminaria justamente o gate de refresh sob investigacao.",
    "Portanto NAO houve validacao fisica da Tela 2 (criacao real de blocos) nesta missao, nem exercicio do ExternalEvent/UI. O diagnostico e' do SOLVER e do PREFLIGHT, que sao o que decide se a criacao chega a comecar.",
    "O motor usa `math.isfinite` (Python >= 3.2) em controlled_beta_preflight - correto em producao (CPython 3), mas impede rodar o preflight sob o IronPython 2.7 do MCP. Nao e' defeito de producao; e' um limite do harness via MCP."
  ],
  "riscos_restantes": [
    "GATE DE REFRESH CALIBRADO NA BANCADA (nao alterado, conforme instrucao): `_refresh_geometry_from_document` levanta 'BETA BLOQUEADO: eixo deslocado/rotacionado' quando o desvio lateral de qualquer extremo passa de 1e-6 pe (~3e-5 cm). Em modo nao-beta o mesmo caminho degrada com `continue`. Com 251 nos e auto-join do Revit, essa tolerancia tem risco alto de disparar em escala. NAO foi desativada nem afrouxada - fica registrada para decisao.",
    "265 trechos nao modulares na planta inteira. E' o material de trabalho normal da Etapa 3B ('Ajustar Erros'), nao um defeito novo - mas em escala significa que o fluxo depende fortemente dessa etapa, que nao foi exercitada aqui."
  ],
  "decisoes_pendentes_do_usuario": [
    "1. Autorizar (ou nao) a limpeza dos 2 Walls + 154 blocos do lote anterior do plugin neste RVT de teste, para recriar as paredes pelo pipeline real e validar a Tela 2 fisicamente.",
    "2. DEFEITO 2 - qual e' a solucao FISICA correta quando dois nos T caem a menos de 54cm na mesma parede? Uma amarracao unica cobrindo os dois nos? Outra peca? Isso e' norma de dominio e nao pode ser inventado pelo agente (item 21 da missao).",
    "3. DEFEITO 3 - qual e' a solucao FISICA correta para uma boneca de 21-24cm que atravessa uma parede? Ela deve virar amarracao da parede atravessada, ser absorvida por ela, ou ser rejeitada na deteccao? Tambem e' norma de dominio.",
    "4. DEFEITO 1 - a junta corrida no trecho curto antes de um no' T exige escolher COMO escalonar (que peca usar no trecho de 48cm). Norma de dominio."
  ],
  "nao_feito_de_proposito": [
    "Nenhuma regra fisica, tolerancia, baseline, reference, threshold ou input oficial alterado.",
    "Nenhum skip/xfail. Nenhum detector silenciado. Nenhum gate desativado.",
    "Nenhum merge na main. Nenhum rebase, nenhum force-push.",
    "Nenhuma observacao deste RVT promovida a regra - tudo classificado como EVIDENCIA DE TESTE LOCAL.",
    "Nenhum arquivo de producao (nuvem/core/**, Script.py) modificado nesta entrega."
  ],
  "reproducao": [
    "py -3 tests/scale_bench.py --axes docs/checkpoints/evidence/2026-09-10-scale-autofix-axes.json --indices 21,178          # BASELINE 2 paredes = PASS",
    "py -3 tests/scale_bench.py --axes docs/checkpoints/evidence/2026-09-10-scale-autofix-axes.json --indices 19,64           # DEFEITO 1, minimo (2 eixos)",
    "py -3 tests/scale_bench.py --axes docs/checkpoints/evidence/2026-09-10-scale-autofix-axes.json --indices 21,19,44        # DEFEITO 2, minimo (3 eixos)",
    "py -3 tests/scale_bench.py --axes docs/checkpoints/evidence/2026-09-10-scale-autofix-axes.json --seed-key \"1910.7,-797.7->2250.7,-797.7@14.0cm\" --ladder 2,5,10,20,30,50,75,100,150,0 --no-stop   # matriz completa"
  ],
  "references": [
    {"path": "docs/checkpoints/evidence/2026-09-10-scale-autofix-prestate.json"},
    {"path": "docs/checkpoints/evidence/2026-09-10-scale-autofix-axes.json"},
    {"path": "tests/scale_bench.py"},
    {"path": "docs/checkpoints/2026-09-09-beta-revit-preparing-solver-performance.md"},
    {"path": "nuvem/core/wall_modeling.py"}
  ]
}
```

## A pergunta central da missao, respondida

> "Qual e' a primeira diferenca introduzida ao sair do cenario de duas paredes
> que faz o sistema falhar?"

**A introducao de um encontro em T.** A bancada provada tinha 1 encontro em L,
0 aberturas e 0 bonecas. Esta planta tem 85 nos T, 12 X e 42 bonecas. Os tres
defeitos isolados nascem todos de T ou de boneca; nenhum precisa de escala para
aparecer:

| Defeito | Reproducao minima | Categoria | Alcance na planta |
|---|---|---|---|
| Junta corrida antes de no' T | **2 eixos** | H (T) | 14-24 paredes (varia com a ordem) |
| Amarracao dupla em nos T proximos | **3 eixos** | H + P | 7 colisoes, 1 parede |
| Boneca atravessando parede | 2 eixos | F + P | 42 colisoes |

Nenhum deles e' "o limite e' N paredes". O tamanho do conjunto nunca foi a
causa - a prova mais direta e' que K=5 REPROVA e K=6 PASSA.

## Por que o gate duro e' o preflight, nao a auditoria

`_execute_create` (linha 10717) roda `controlled_beta_preflight` ANTES de abrir
qualquer Transaction e levanta `BETA BLOQUEADO: N invasoes de abertura, M
colisoes` sem criar nada. Uma parede reprovada na auditoria de amarracao remove
apenas as pecas daquela parede (`_bond_reproved_created_instance_ids`); uma
colisao no preflight bloqueia o LOTE INTEIRO. Por isso a ordem de ataque
recomendada e' DEFEITO 3 (42 colisoes) -> DEFEITO 2 (7 colisoes) -> DEFEITO 1.

## Proximo passo recomendado

Decidir os itens 1-4 de `decisoes_pendentes_do_usuario`. Com o item 1 liberado,
a bancada de escala ja' esta' pronta para: recriar as paredes pelo pipeline
real, refazer a matriz dentro do Revit e validar fisicamente a Tela 2 no maior
K que passar (hoje K=6).
