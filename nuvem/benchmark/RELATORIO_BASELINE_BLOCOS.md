# RELATÓRIO FINAL — CONTA 2 / AUDITORIA GLOBAL DOS BLOCOS

> Auditoria independente da modulação de blocos, rodando em PARALELO à
> CONTA 1 (`CR-BLOCK-01`, sobre prisma/fiadas). Este relatório audita
> **exclusivamente a `main` original** — a branch da CONTA 1 nunca foi
> lida. Nenhuma correção de produção foi implementada.
>
> Análise completa (pipeline, catálogo, matriz regra×código, backlog
> detalhado): **`docs/BLOCK_MODULATION_AUDIT.md`**. Este documento é o
> relatório de dados/prestação de contas da missão, no formato pedido.

## Git

```
branch:      claude/block-audit-baseline-350nav
SHA inicial: 9f3bab41b35f0e2a5f9782583ead8e1ee7755f49  (main, confirmado
             idêntico ao pedido na missão)
SHA final:   eafec7a7dcd8a683aaa7cc926e25271008041599  (checkpoint A —
             ver histórico de commits desta branch para o final real)
```

`git fetch origin && git checkout main && git pull --ff-only` confirmou
fast-forward limpo (`c60b1f7..9f3bab4`) e `git status` limpo antes de
criar a branch. Nenhum merge, nenhum rebase, nenhum force push.

## Pipeline completo

Ver `docs/BLOCK_MODULATION_AUDIT.md` seção 1 — mapa arquivo/função/
entrada/saída/responsabilidade completo, com a fronteira motor puro ×
integração Revit marcada explicitamente. Resumo do fluxo:

```
PAREDES → GRAFO → CLASSIFICAÇÃO L/T/X → BLOCOS DE AMARRAÇÃO → ABERTURAS →
FIADA → (JAMB, legado) → TRECHO LIVRE → LAYOUT → COMPENSADORES →
REPARO DE ABERTURA → VALIDAÇÃO → CANDIDATOS FINAIS → MATERIALIZAÇÃO REVIT
```

Nota importante: o pipeline de produção hoje é `continuous_first`
(seção 23 das REGRAS) — `solve_opening_jamb` não roda nesse modo, embora
o censo tenha medido `jamb_exceptions=172` (achado a investigar, seção 12
do audit).

## Catálogo

6 peças (B39/B34/B54/B19/C09/C04), família "14x19". Ver
`docs/BLOCK_MODULATION_AUDIT.md` seção 2 para a tabela completa com
confiança por regra (OBRIGATÓRIA/PREFERENCIAL/EXCEÇÃO/OBSERVADO) e o
breakdown de `NODE_TRUE`/`NODE_DEGRADED`/`MID_WALL_FILL` medido por
código. Catálogo real do escritório tem 33 tipos; o solver só implementa
6 (escopo pendente já documentado, não erro).

## Prisma

Censo independente (junta = ponto médio entre peças vizinhas, coincidência
≤1cm entre fiadas físicas consecutivas):

| | valor |
|---|---|
| pares de fiadas medidos | 7.444 |
| juntas coincidentes suspeitas | **1.086** |
| isentas (encoste em abertura, §11.8) | 10 |
| ambíguas (`RULE_AMBIGUOUS`) | 157 |
| paredes com ≥1 suspeita | 47/167 (28,1%) |
| stagger mediano | 15,0cm |

Comparável em ordem de grandeza ao `PRISM_CONTINUOUS_JOINT=961` já medido
pelo benchmark oficial — duas medições independentes concordando.

## C09

1.185 peças. **201 sequências de 2+ consecutivos**, das quais **183 são
puramente de preenchimento comum** (violação direta da regra "proibido
2+ em sequência") e só 18 tocam uma peça de nó (adjacência legítima). 25
faixas verticais repetitivas.

## C04

584 peças. 17 sequências de 2+, das quais 11 puras de preenchimento
comum. Mais disciplinado que C09 na prática (mediana de distância até
abertura/ponta: 12cm contra 19,5cm do C09).

## B19

840 peças, 100% `MID_WALL_FILL` (nunca usado em nó — confirma a regra).
**100/840 (11,9%) ficam a mais de 60cm de qualquer borda de abertura/
ponta** — achado a confirmar (não é prova definitiva de violação, a
regra proíbe "meio de trecho", não define um raio; ver nota metodológica
no audit §6) antes de virar item de correção.

## B34

2.530 peças: 1.423 `NODE_TRUE` (56,2%), 443 `NODE_DEGRADED` (17,5%), 664
`MID_WALL_FILL` (26,2%). 424 sequências de 2+ no total, mas só **40 são
puramente de preenchimento comum** — as outras 384 são adjacência
legítima peça-de-nó + filler vizinho. Distinção que reduz o "problema
aparente" em ~10× frente à contagem bruta.

## B54

636 peças, **100% `NODE_TRUE`, 0% `MID_WALL_FILL`** — nunca usado como
enchimento, confirmando com dado real de projeto o que a seção 23.6 das
REGRAS já media em cenário sintético.

## L

63 nós L_CORNER. **62/63 (98,4%) resolvidos como TRUE** (2×B34, vão
menor sobreposto), validado diretamente com `validate_l_corner` numa
amostra. É o encontro mais bem resolvido dos três tipos.

## T

118 nós T_INTERSECTION. 80 TRUE (67,8%), 23 DEGRADED (19,5%, vira L),
15 sem solução (12,7%). Achado de metodologia: `validate_t_intersection`
reprova nós DEGRADED por natureza (exige B54+B34); o validador correto
para eles é `validate_l_corner` — usado corretamente neste censo depois
de identificar o problema.

## X

17 nós X_INTERSECTION. Só **8/17 (47,1%) resolvidos**; **9/17 (52,9%)
sem solução alguma** — a taxa de falha mais alta dos três tipos de nó, e
X não tem caminho de degradação (ao contrário de T). Maior contribuinte
individual para paredes não moduladas.

## Aberturas

82 no input (57 portas sem peitoril, 25 janelas). `non_modular`: 3.023
segmentos em 124 paredes. `alignment_conflicts`: 30. `door_void_
violations`: **290, em 41/167 paredes (24,6%)** — a zona de exclusão
absoluta (§3 das REGRAS) é cumprida como rede de segurança REATIVA
(bloqueia a criação), mas não é respeitada pela geração do layout por
construção nesses casos.

## Blocos em vãos

Censo independente por EXTENT real (nunca ponto central), com filtro de
banda vertical (a primeira versão sem esse filtro superestimou o achado
em ~10×, corrigido durante a missão):

| | contagem |
|---|---|
| FORA | 3.502 |
| DENTRO | 5 |
| PARCIAL | 108 |

Cross-check contra `classify_extent_against_openings` (produção): **60/60
concordam** — a fórmula de produção bate com a documentação nos casos
amostrados. Os 113 casos residuais (3,1% das peças perto de abertura) são
achado real, pequeno em proporção.

## Paredes não moduladas

**29/167 (17,4%) sem nenhuma peça** — bate EXATAMENTE com
`COVERAGE_WALL_NOT_MODULATED=29` já medido pelo benchmark oficial
(confirmação cruzada forte, metodologia 100% independente). Causa
dominante: `L_T_X_FAILURE` (13/29, 44,8%) — consistente com a taxa alta
de falha em X/T medida acima.

## Determinismo

**Achado principal desta auditoria.** 8 rodadas do solver de blocos
(baseline, ordem invertida, endpoints invertidos, 5 shuffles com seed
fixa) sobre o mesmo `input.json` → **8 fingerprints distintos**, variação
de até 130 peças (~1,2%). O solver de blocos **não é determinístico**
sob permutação de entrada — nunca medido/corrigido antes (o CR-2F-D
tratou só a camada de baixo, formação das paredes). Na maioria dos casos
testados, a primeira divergência aparece já no **grafo de nós**
(`build_wall_graph`/`extend_wall_ends_to_junctions`), antes do solver de
blocos propriamente dito.

## Performance

Solver de blocos: 3,47s para 167 paredes/17 fiadas/10.657 peças. Não é o
hotspot do pipeline (a Fase A — pareamento de paredes — já está
documentada como o gargalo real, ~25s, fora do escopo desta auditoria).

## Regras vs implementação

Matriz completa em `docs/BLOCK_MODULATION_AUDIT.md` seção 16. Destaque:
`PIER_LAYOUT_VARIANTS_PER_COURSE` — a seção 11.7 das REGRAS documenta
K=3 como escolha deliberada; a seção 18.4 (mais recente) já registra que
o usuário revogou isso de volta para K=1, **com o conflito anotado no
próprio documento**. Confirmado nesta auditoria que o código hoje usa
K=1 — não é uma divergência escondida, é um conflito já rotulado que
continua em aberto.

## Top 20 defeitos encontrados

Ordenados por severidade/frequência (P0 primeiro):

1. Compensador C09 em sequência pura (2+): 183 casos — viola regra
   obrigatória sem exceção.
2. Solver de blocos não determinístico sob permutação: 8/8 fingerprints
   distintos.
3. Junta corrida entre fiadas (regra #1) residual: 1.086 suspeitas —
   provavelmente já é o alvo do CR-BLOCK-01 em andamento.
4. X_INTERSECTION sem solução: 9/17 nós (52,9%).
5. `door_void_violations` só reativo: 290 candidatos, 41/167 paredes.
6. Paredes não moduladas por falha L/T/X: 13/29 (44,8% das não
   moduladas).
7. Bloco sobrevive dentro/parcial de vão real: 113 casos.
8. Compensador C04 em sequência pura (2+): 11 casos.
9. T_INTERSECTION sem solução: 15/118 nós (12,7%).
10. B19 a >60cm de qualquer borda: 100/840 (11,9%, achado a confirmar).
11. B34 em sequência pura de preenchimento comum: 40/2.530.
12. `jamb_exceptions=172` em modo `continuous_first` (esperado ser 0 —
    investigar antes de classificar).
13. Faixa vertical repetitiva de C09: 25 casos.
14. Faixa vertical repetitiva de C04: 13 casos.
15. Faixa vertical repetitiva de B34: 21 casos.
16. `L_CORNER` sem candidato: 1/63.
17. Divergência do grafo de nós (T_INTERSECTION 118→119/120) sob
    permutação — camada anterior ao solver de blocos, contribui para o
    item 2.
18. Faixa vertical repetitiva de B19: 4 casos.
19. 47/167 paredes (28,1%) têm pelo menos 1 junta corrida suspeita —
    granularidade "por parede" do item 3.
20. Ambiguidade de classificação de junta perto de borda: 157 casos
    marcados `RULE_AMBIGUOUS` (não são defeito confirmado, mas
    representam um ponto cego da definição atual da regra 11.8 que vale
    a pena fechar).

## Priorização P0/P1/P2/P3/P4

Tabela completa com frequência/severidade/evidência/função provável/CR
sugerido/risco de regressão: `docs/BLOCK_MODULATION_AUDIT.md` seção 17.
Resumo:

- **P0** (quebra de regra obrigatória, dado real): compensador em
  sequência (1); não-determinismo do solver de blocos (2); junta corrida
  residual (3, provável escopo do CR-BLOCK-01).
- **P1** (modulação tecnicamente errada, frequente): X sem degradação
  (4); bloco residual em vão (7); porta sem peitoril só reativo (5);
  paredes não moduladas por L/T/X (6).
- **P2** (uso ruim de peça especial): B19 longe de borda (10, a
  confirmar); B34 em sequência pura (11); `jamb_exceptions` inesperado
  (12).
- **P3** (qualidade/otimização): reavaliar `PIER_LAYOUT_VARIANTS_PER_
  COURSE` variando só nos trechos com compensador (pendência já nomeada
  nas REGRAS §18.4/23.7); performance da Fase A (fora do escopo de
  blocos).
- **P4** (UX/diagnóstico): distinguir "sequência tocando nó" de
  "sequência pura" nos validadores oficiais; documentar que
  `intersection_failures` conta por tentativa, não por nó único.

## CRs recomendados (sequência sugerida pelos dados, não assumida a priori)

1. **CR-BLOCK-01** (CONTA 1, em andamento) — prisma/fiadas, maior volume
   de achados.
2. **CR-BLOCK-DETERMINISM** — antes de comparar "antes/depois" de
   qualquer outro CR de blocos com confiança, o solver precisa produzir
   o mesmo resultado em toda rodada.
3. **CR-COMPENSADORES** — segunda maior classe de violação obrigatória,
   já isolada (mid-wall-puro vs tocando-nó).
4. **CR-X-DEGRADACAO** — taxa de falha de 52,9% em X.
5. **CR-DOOR-EXCLUSION-PREVENTIVA** — mover de reativo para preventivo.
6. **CR-OPENING-REPAIR** — os 113 casos residuais de bloco em vão.
7. P2/P3/P4 depois, por esforço vs impacto.

Fora do escopo desta priorização (sem dado de frequência medido, porque o
solver de hoje nem tenta usá-los): verga, contraverga, canaleta, blocos
cortados — 27 dos 33 tipos do catálogo real do escritório.

## Arquivos criados

```
docs/BLOCK_MODULATION_AUDIT.md
nuvem/benchmark/RELATORIO_BASELINE_BLOCOS.md   (este arquivo)
nuvem/benchmark/diagnostics_block_audit/README.md
nuvem/benchmark/diagnostics_block_audit/lib_audit.py
nuvem/benchmark/diagnostics_block_audit/run_course_bond_census.py
nuvem/benchmark/diagnostics_block_audit/run_special_block_census.py
nuvem/benchmark/diagnostics_block_audit/run_intersection_census.py
nuvem/benchmark/diagnostics_block_audit/run_opening_census.py
nuvem/benchmark/diagnostics_block_audit/run_coverage_census.py
nuvem/benchmark/diagnostics_block_audit/run_determinism_census.py
nuvem/benchmark/diagnostics_block_audit/run_full_census.py
nuvem/benchmark/diagnostics_block_audit/out_course_bond_census.json
nuvem/benchmark/diagnostics_block_audit/out_special_block_census.json
nuvem/benchmark/diagnostics_block_audit/out_intersection_census.json
nuvem/benchmark/diagnostics_block_audit/out_opening_census.json
nuvem/benchmark/diagnostics_block_audit/out_coverage_census.json
nuvem/benchmark/diagnostics_block_audit/out_determinism_census.json
nuvem/benchmark/diagnostics_block_audit/out_full_census.json
```

**ARQUIVOS DE PRODUÇÃO ALTERADOS: ZERO.**

---

**PARADO ANTES DO MERGE.**
**CONTA 2 CONCLUÍDA.**
**AUDITORIA INDEPENDENTE PRONTA PARA CRUZAR COM A CONTA 1.**
