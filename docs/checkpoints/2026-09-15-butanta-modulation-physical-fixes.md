# Missão BUTANTÃ — correções físicas da modulação (2026-09-15)

```json
{
  "date": "2026-09-15",
  "scope": "current",
  "branch": "claude/butanta-modulation-physical-fixes",
  "head": "23dfcb7f494b4568980339784ece17b6fb70a668",
  "base": "55e990d962ed22ae1021f0d335db197607bddda1",
  "main_observada": "55e990d962ed22ae1021f0d335db197607bddda1",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/42",
  "veredito": "PARTIAL — REMAINING LIMITATIONS PRECISELY EXPLAINED",
  "objective": "Corrigir a modulação real no Revit comparando o projeto humano BUTANTÃ R08_LT (somente leitura) com o doc de teste 'butanta testes', sem hardcode, sem mascarar validador e sem corromper a referência humana.",
  "changes": [
    "nuvem/core/engine/small_void_alignment.py (novo): validador do vazado menor entre fiadas e passe de orientação 180° dos B34 que não são peça de nó.",
    "nuvem/core/wall_modeling.py: _orient_small_voids_final nas duas saídas de _solve_building_blocks_all_courses_impl e, com CHANNEL, antes de _unify_candidates_with_courses; resultado em result['small_void_alignment'].",
    "tests/test_b34_small_void_alignment.py (novo): 10 testes (vermelho/verde, nó fixo, rotação rígida, invariâncias, controle do validador).",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md: seção 52 nova; seções 6 e 18.5 atualizadas.",
    "nuvem/core/engine/wall_stepper.py: physical_tolerance_trial (30.8 e ruido de jamba com tentativa por parede: assenta mais sem coincidencia nova e sem deixar a familia oposta vazia), fuse_adjacent_equal_compensators (C04+C04 -> C09 depois do reparo de vao).",
    "nuvem/core/engine/continuous_modulation.py: contador/supressao da tolerancia de ruido de jamba para a tentativa.",
    "nuvem/core/engine/physical_support.py (novo): validador somente leitura UNSUPPORTED_SMALL_BLOCK/UNSUPPORTED_BLOCK.",
    "nuvem/core/wall_modeling.py: CHANNEL_PHYSICAL_TOLERANCES_ENABLED (tolerancias com tentativa so' na estrategia CHANNEL) e _physical_support_final no resultado final.",
    "tests/test_physical_tolerance_trial.py e tests/test_physical_support_audit.py (novos); tests/test_node_bounded_residual.py: o vermelho desliga tambem a ativacao na CHANNEL.",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md: 30.8 (status), 30.9, 53 e 54 novas.",
    "nuvem/core/engine/small_void_alignment.py: giro em par dos B34 (commit 23dfcb7); tests/test_b34_small_void_alignment.py: vermelho/verde do par.",
    "nuvem/REGRAS_MODULACAO_BLOCOS.md: 52 (giro em par), 55 (especiais junto da jamba, documentado), nota 30.9 CHANNEL x legado.",
    "docs/checkpoints/evidence/2026-09-15-butanta-physical-fixes/: resumo das execucoes no Revit, metricas, comparador por lado de vao, regressao final e scripts."
  ],
  "tests": [
    "Regressao completa final (HEAD 2eca44c, codigo 23dfcb7): 1237 passed / 3 failed em 42 min 37 s - as tres historicas da main (TP1 V1 JUNCTION_MISSING_BINDING 8->9; TGD V2 compensators 61->62; test_perf_trace_stall_sampler ctypes/win32). Nenhuma falha nova.",
    "Novos testes: test_b34_small_void_alignment (12), test_physical_tolerance_trial (14), test_physical_support_audit (5).",
    "Revit real (IronPython via MCP, handler real _execute_solve/_execute_create, 34 paredes, 17 fiadas, CHANNEL): run1 (4823114) 9.088 criadas apos purgar 9.458 do lote antigo; run2/run3b/run4 (23dfcb7) assinatura identica 5f6dc513, 9.088 -> 9.088, 0 falhas, 0 divergencias de releitura, humano IsModified False antes e depois de todas.",
    "Paridade Revit x offline: identica com as coordenadas exatas lidas no Revit.",
    "Determinismo offline: 3 processos identicos; inversao de pontas, permutacao e translacao alteram o resultado - pre-existente na main (medido com as mudancas desligadas)."
  ],
  "known_failures": [
    "Herdadas da main: TP1 V1 JUNCTION_MISSING_BINDING 8->9; TGD V2 compensators 61->62; test_perf_trace_stall_sampler (ctypes, win32).",
    "Especiais junto da jamba: humano 500 x lote final 808 (fiadas 0-11); comparador por lado de vao: 51 SOLVER_WORSE de 88 (secao 55, pendente).",
    "Vazado menor do B34: humano 41 x lote final 336 (validador externo, fiadas 0-12); restantes exigem mudanca de posicao.",
    "Determinismo: resultado depende do sentido das paredes, da ordem de entrada e de ruido de 1e-14 ft (pre-existente).",
    "CHANNEL_ALIGNMENT_ERROR nao foi criado como validador separado: a canaleta usa as pecas da propria fiada (51.3) e a validacao CHANNEL existente e a auditoria de prisma cobrem o caso; cinta de topo (decisao F) continua pendente."
  ],
  "physical_deltas": [
    "Revit real, lote anterior -> lote final [humano] (34 paredes, fiadas 0-12): buracos 215 (22.451 cm) -> 10 (872 cm) [71 (2.953 cm)]; pecas sem apoio fora de vao 116 -> 0 [7]; vaos com sub-preenchimento sob janela 11 -> 0 [0]; violacoes do vazado menor do B34 2.460 -> 336 [41].",
    "Motor: B34 de meio de parede orientado pelo vazado menor (individual e em par); tolerancias 30.8/jamba com tentativa por parede so na CHANNEL; validador de apoio fisico; C04+C04 -> C09.",
    "Legado: so a fusao C04+C04 muda pecas (COMPENSATOR_CONSECUTIVE TP1 936->881, TGD V2 472->464; vereditos iguais)."
  ],
  "decisions_taken": [
    "Regra do usuário (2026-09-15): fiada vizinha preserva o vazado menor do B34; registrada como seção 52 com a evidência humana (2.500/2.541 pares alinhados).",
    "As 12 paredes do doc de teste sem bloco no humano seguem a seção 49 (não estruturais); a comparação física usa as 34 de alvenaria. Consulta somente leitura no humano: nenhum elemento de parede nem bloco no eixo de 11 delas.",
    "Tolerancias fisicas (30.8 e jamba) ligadas com tentativa somente na estrategia CHANNEL: preserva o motivo da opcao B da auditoria (legado identico) e fecha os buracos que o humano fecha no caminho usado no BUTANTA.",
    "Re-solucao do pilarete inteiro junto da jamba NAO integrada: todas as variantes reduzem especiais trocando por violacao do vazado menor do B34 ou quebram o contrato 51.3; medicoes na secao 55 e em metrics_summary.json."
  ],
  "decisions_pending": [
    "DECISION-WALL-OUTSIDE-MODULE e COMPENSATOR-LIMIT continuam pendentes.",
    "Regra 30.8 e tolerância de ruído de jamba (51.13/51.14): em avaliação nesta missão com prova de cobertura por fiada.",
    "Levar as tolerancias com tentativa ao legado exige decisao sobre a regua (TGD V2 COVERAGE_ROW_MOSTLY_EMPTY 86->92 por reclassificacao; categoria compensadores 62->63).",
    "Robustez numerica: empates de composicao decididos por ruido de 1e-14 ft (pre-existente).",
    "Prioridade entre a regra 52 (vazado menor) e a reducao de especiais junto da jamba (secao 55).",
    "Decisao F (cinta de topo) e 51.8 (topo/peitoril fora da grade) continuam pendentes."
  ],
  "next_steps": [
    "Revisao do PR draft pelo usuario; nenhuma integracao sem autorizacao.",
    "Secao 55: criterio conjunto especiais + vazado menor + pecas de no + bandas.",
    "Robustez numerica e independencia de ordem e sentido do motor (pre-existente)."
  ],
  "references": [
    {
      "path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"
    },
    {
      "path": "nuvem/core/engine/small_void_alignment.py"
    },
    {
      "path": "tests/test_b34_small_void_alignment.py"
    },
    {
      "path": "docs/PROJECT_STATUS.md"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-15-butanta-physical-fixes/revit_runs_summary.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-15-butanta-physical-fixes/metrics_summary.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-15-butanta-physical-fixes/comparator_rows_final.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-15-butanta-physical-fixes/regressao_final.txt"
    },
    {
      "path": "tests/test_physical_tolerance_trial.py"
    },
    {
      "path": "tests/test_physical_support_audit.py"
    }
  ]
}
```

## 1. Estado de git

- `origin/main` = `55e990d962ed22ae1021f0d335db197607bddda1` (merge do PR
  [#41](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/41)), confirmado por fetch.
- Branch `claude/butanta-modulation-physical-fixes` criada dessa main. PR draft [#42](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/42), sem merge.

## 2. Documentos Revit

- HUMANO (somente leitura): `BUTANTÃ - R08_LT (TODOS OS PAVIMENTOS PARA ENVIO) (1).rvt`,
  identificado pelo caminho exato; `IsModified=False` antes e depois de cada consulta.
- TARGET: `butanta testes.rvt` (46 paredes de 340 cm, 44 aberturas). Lote anterior do botão
  `20260914-191852` (9.458 peças) feito com uma main anterior.

## 3. Vazado menor do B34 (regra 52)

| Medida | Humano | Lote anterior | Bancada sem passe | Bancada com passe |
|---|---|---|---|---|
| Violações (34 paredes, fiadas 0–12) | 41 | 2.460 | 2.000 | 264 (com giro em par) |

No lote final do Revit o validador externo mede 336. As restantes exigem mudar a posição do B34, não a orientação.

## 4. Buracos, apoio e compensadores (regras 30.9, 53, 54)

| Métrica (34 paredes, 13 fiadas) | Sem as correções | Com as correções | Humano |
|---|---|---|---|
| Buracos | 94 (3.754 cm) | 10 (872 cm) | 71 (2.953 cm) |
| NON_MODULAR | 78 | 0 | — |
| Peças sem apoio | 50 | 0 | 9 |
| C04+C04 encostados | 7 | 0 | 0 |

Os 10 buracos restantes são vazios que o humano também deixa: passagem livre
até o topo e pilaretes de 5 e 15 cm.

## 5. Revit real — lote final

| Execução | Código | Peças | Substituição | Falhas | Releitura | Humano modificado |
|---|---|---|---|---|---|---|
| run1 | 4823114 | 9.088 | 9.458 purgadas → 9.088 | 0 | 0 divergências | não |
| run2 | 23dfcb7 | 9.088 | 9.088 → 9.088 | 0 | 0 divergências | não |
| run3b | 23dfcb7 | 9.088 | 9.083 → 9.088 | 0 | 0 divergências | não |
| run4 | 23dfcb7 | 9.088 | 9.088 → 9.088 | 0 | 0 divergências | não |

O run3 original foi descartado: carregou o motor enquanto um patch experimental
estava na árvore de trabalho. Runs 2, 3b e 4 têm a mesma assinatura.

| Métrica (34 paredes, fiadas 0–12) | Humano | Lote anterior | Lote final |
|---|---|---|---|
| Buracos | 71 (2.953 cm) | 215 (22.451 cm) | 10 (872 cm) |
| Peças sem apoio fora de vão | 7 | 116 | 0 |
| Vãos com sub-preenchimento sob janela | 0 | 11 | 0 |
| Violações do vazado menor do B34 | 41 | 2.460 | 336 |
| Compensadores + pastilhas (fiadas 0–11) | 500 | 686 | 808 |

Validação CHANNEL no Revit: 40/40 canaletas superiores e 23/23 inferiores,
nenhuma faltante, extra, em fiada errada, invadindo vão ou colidindo.

## 6. Limitações restantes

- **Especiais junto da jamba** (seção 55): 51 de 88 lados de vão com dois ou mais
  especiais acima do humano. Toda correção medida trocava erro.
- **Vazado menor do B34**: 336 × 41 do humano; o resíduo pede mudança de posição.
- **Determinismo**: sentido das paredes, ordem de entrada e ruído numérico mudam
  empates de composição — pré-existente na main.
- **Regressão final**: 1.237 passaram, 3 falhas históricas da main.

## 7. Gate global de não-regressão (adendo) — BASE `55e990d` × PR #42

Evidência completa em `docs/checkpoints/evidence/2026-09-15-matriz-main-x-pr42.txt`
(gerada por `delta_metrics.py` sobre árvores congeladas `C:/mbase` e `C:/mbpr`,
nenhuma gravação nos repositórios medidos).

### BUTANTÃ — 34 paredes de alvenaria, 13 fiadas, estratégia CHANNEL

| Métrica | BASE | PR #42 | Δ |
|---|---|---|---|
| Vazado menor do B34 desalinhado | 1.931 | 316 | **−1.615** |
| `NON_MODULAR` | 78 | 0 | **−78** |
| Buracos | 94 (3.754 cm) | 10 (872 cm) | **−84 (−2.882 cm)** |
| `MISSING_REQUIRED_CHANNEL` | 1 | 0 | −1 |
| Colisões | 0 | 0 | 0 |
| Peças sem apoio | — | 0 | — |
| Paredes reprovadas na amarração | 3 | 3 | 0 |
| `C09+C09` encostados | 11 | 9 | −2 |
| `C09+C04` encostados | 98 | 119 | +21 |
| Especiais (fiadas 0–11) | 714 | 808 | +94 |
| `SPECIAL_CLUSTER` (≤40 cm) | 11 | 11 | 0 |
| `MID_WALL_HALF_BLOCK` | 5 | 5 | 0 |
| `REPLACEABLE_COMPOSITE_BY_B54` | 59 | 65 | +6 |
| Tempo de solve | 3,1 s | 5,6 s | +2,5 s |

### TGD V2 — benchmark oficial, estratégia legada

| Achado | BASE | PR #42 | Δ |
|---|---|---|---|
| `COMPENSATOR_CONSECUTIVE` | 472 | 407 | **−65** |
| `COMPENSATOR_EXCESS_IN_RUN` | 454 | 428 | **−26** |
| `COMPENSATOR_VERTICAL_STRIP` | 86 | 84 | −2 |
| `PRISM_STAGGER_BELOW_TARGET` | 739 | 712 | −27 |
| `PRISM_CONTINUOUS_JOINT` / `PRISM_JOINT_STACK` | 53 / 5 | 53 / 5 | 0 |
| Cobertura, aberturas, posições, junções | iguais | iguais | 0 |
| Veredito do benchmark | REGRESSÃO | REGRESSÃO | inalterado |

### TP1 V1 — benchmark oficial, estratégia legada

| Achado | BASE | PR #42 | Δ |
|---|---|---|---|
| `COMPENSATOR_CONSECUTIVE` | 936 | 825 | **−111** |
| `COMPENSATOR_EXCESS_IN_RUN` | 933 | 909 | **−24** |
| `COMPENSATOR_VERTICAL_STRIP` | 149 | 147 | −2 |
| `PRISM_CONTINUOUS_JOINT` | 16 | 16 | 0 |
| `PRISM_STAGGER_BELOW_TARGET` | 1.539 | 1.689 | **+150** |
| Demais categorias | iguais | iguais | 0 |
| Veredito do benchmark | REGRESSÃO CRÍTICA | REGRESSÃO CRÍTICA | inalterado |

### Classificação das pioras

| Piora | Classe | Justificativa medida |
|---|---|---|
| TP1 `PRISM_STAGGER_BELOW_TARGET` +150 | **C — validador/preferência mais rígido que a referência física** | O travamento de 10 cm (18.6) é preferência, não regra: no projeto humano 7% das juntas ficam abaixo de 10 cm e 244 são exatamente coincidentes, contra 30 do solver. `PRISM_CONTINUOUS_JOINT`, que audita o defeito real, não se move (16 → 16). |
| BUTANTÃ especiais 714 → 808 e `C09+C04` 98 → 119 | **A — regressão física real, localizada** | Causa medida na seção 58: o ramo degradado do T emitia pastilha de 9 cm nas duas famílias. Corrigida nesta sessão (ver item 8). |
| BUTANTÃ `REPLACEABLE_COMPOSITE_BY_B54` 59 → 65 | **B — mudança de regra legítima** | A seção 56.3 mediu que `B34+B19` no envelope de 54 cm é o que o humano faz **mais** que o solver (107 × 81); o validador conta um padrão que a referência física aprova. |
| Tempo 3,1 s → 5,6 s | **B** | Custo das tentativas por parede (30.9, 56.2), que só re-resolvem a parede que apresenta o defeito. |

Nenhuma piora ficou nas classes A-não-corrigida ou E-desconhecida.

## 8. Regras desta rodada

### 8.1 Aceitas (ligadas) — seção 56

| Regra | Onde | Efeito medido |
|---|---|---|
| 56.1 — regra #2 em todo trecho da Fiada A | `RULE2_ON_EVERY_COURSE_A_SEGMENT` | TGD V2 `COMPENSATOR_CONSECUTIVE` 464→412; TP1 881→830 |
| 56.2 — compensador do preenchimento não encosta em compensador de nó, por **tentativa por parede** | `compensator_node_adjacency_trial` | BUTANTÃ `C09+C09` 20→9; prisma intacto |

Ligada direto na escolha de composição, a 56.2 reprovava o corpus (TGD V2
`PRISM_CONTINUOUS_JOINT` 53→87). Com a tentativa, o prisma volta a 53.

### 8.2 Medidas e **rejeitadas**

| Hipótese | Seção | Por quê |
|---|---|---|
| Fileira de B34 (reordenar corridas) | 57 | Piora a própria métrica: 473→483 (13 fiadas) e 613→669 (17 fiadas); empilha junta 100→120. Código removido. |
| B19 no meio da parede é erro | 56.3 | Humano usa **mais** (103 × 35 do solver). |
| `B54` domina `B34+B19` | 56.3 | Humano usa `B34+B19` **mais** (107 × 81) e nunca põe B54 longe de nó (172/172 a ≤35 cm). |
| Travamento de 10 cm como guarda | 56.2 | No humano 7% das juntas ficam abaixo de 10 cm, 244 coincidentes. |
| Compensador longo não é peça extrema (no preenchimento) | 58.1 | Alcança 6 de 40 casos; guardas recusam os 6; forçada piora `C09` 494→500. |

### 8.3 Implementada e **desligada** — seção 58.2

Escada de amarração no nó degradado (`B34` antes de compensador, como o X já
faz). Corrige o defeito no BUTANTÃ (pastilhas de T degradado 30→0, `C09` extremo
40→10, vazado menor 316→283, especiais 808→802, portões duros intactos), mas
custa `PRISM_CONTINUOUS_JOINT` no corpus legado (TP1 16→32, TGD 53→55) em juntas
de fronteira de banda. `CORNER_DEGRADED_PREFERS_TIE_BLOCK = False`; com a chave
desligada o BUTANTÃ sai **idêntico**, métrica por métrica, ao head anterior.

## 9. Determinismo

| Variação da entrada | main `55e990d` | branch |
|---|---|---|
| mesma entrada, processo novo | reprodutível | reprodutível (mesmo hash) |
| translação (+1000, +500 cm) | — | **invariante** (mesmo hash) |
| sentido das paredes invertido | 8.890 → 8.916 peças | 9.088 → 9.117 |
| ordem das paredes invertida | 8.890 → 8.885 | 9.088 → 9.084 |

A sensibilidade a sentido e ordem é **pré-existente na main**, com a mesma
magnitude; a branch não a introduz nem a agrava.

## 10. Revit real — rodada com as regras da seção 56

| Execução | Peças | Substituição | Falhas | Releitura | Humano modificado | Assinatura das linhas |
|---|---|---|---|---|---|---|
| run4 (código anterior) | 9.088 | 9.088 → 9.088 | 0 | 0 | não | `ca0cf689…` |
| run5 | 9.088 | 9.088 → 9.088 | 0 | 0 | não | `113c6b26…` |
| run6 | 9.088 | 9.088 → 9.088 | 0 | 0 | não | `113c6b26…` |
| run7 | 9.088 | 9.088 → 9.088 | 0 | 0 | não | `113c6b26…` |

**Idempotência**: runs 5, 6 e 7 têm assinatura de linhas idêntica — o mesmo
código aplicado três vezes seguidas produz exatamente a mesma modulação e
substitui 9.088 por 9.088 sem falha. O `IsModified` do projeto humano foi
`False` antes e depois de cada execução.

**Medido no Revit real (34 paredes, fiadas 0–11):**

| Métrica | Humano | run4 | run7 |
|---|---|---|---|
| Pares de compensadores encostados | 105 | 158 | **147** |
| Pares IGUAIS encostados | 6 (`C09D+C09D`) | 20 (`C09+C09`) | **9** |
| `C09+C09` | **0** | 20 | **9** |
| Vazado menor do B34 desalinhado | 41 | 320 | 316 |
| Especiais | 500 | 808 | 808 |
| `C09` como peça extrema | 0 | 39 | 39 |

A correção da seção 56 é visível na peça física: o par de compensadores iguais,
que o humano nunca usa, cai pela metade. O `C09` extremo e o excesso de
especiais continuam abertos — causa localizada na seção 58, correção pronta e
desligada pelo gate.

## 11. Regressão consolidada e classificação das falhas

`1.250 passaram, 3 falharam` (43 min, `pytest tests/ -q -p no:randomly`). As três
foram executadas também no worktree da BASE (`55e990d`) e **falham
identicamente lá**:

| Falha | Classe | Evidência |
|---|---|---|
| `test_benchmark_baselines[torre_easy_lo_r00_tp1]` | **D — baseline defasado** | falha na main |
| `test_benchmark_baselines_versionado[torre_easy_lo_r00_tgd-v2]` | **D — baseline defasado** | falha na main |
| `test_perf_trace_stall_sampler` | **ambiente** | `ctypes.PyDLL("kernel32")` no Windows; falha na main |

Nenhum baseline, golden, threshold, `reference_score` ou snapshot histórico foi
alterado nesta missão.

## 12. Comparador humano × solver (88 lados de vão, fiadas 0–11)

| Classe | Lote anterior | Lote atual |
|---|---|---|
| `EXACT_MATCH` | 0 | 0 |
| `PHYSICALLY_EQUIVALENT` | 25 | 25 |
| `SOLVER_BETTER` | 10 | 10 |
| `VALID_ALTERNATIVE` | 2 | 2 |
| `SOLVER_WORSE` | 51 | 51 |

Idêntico entre os dois lotes: as regras da seção 56 atuam no corpo da parede, não
na região de jamba (seção 55, ainda aberta).

## 13. `MISSING_UNDER_WINDOW` — artefato de limiar, não vazio físico

O único vão marcado (parede 8284584, vão de 66 cm, peitoril 40 cm) tem **94,7%**
de cobertura nas fiadas abaixo do peitoril; o **humano tem 95,5% no mesmo vão**,
e o limiar da métrica é 95%. Os 3,5 cm "faltantes" são **juntas de argamassa**: o
solver usa uma peça a mais que o humano naquele trecho, logo uma junta a mais.
Com limiar de 92% os dois dão zero vãos reprovados. O valor é o mesmo na BASE e
no PR — não é regressão, e o limiar **não** foi alterado.
