# C02 — `CR-BLOCK-ROOM-CHECK-ROBUSTNESS` — PREPARAÇÃO (MODO A)

> **Status: `READY_FOR_IMPLEMENTATION_PENDING_BASE` — com ressalva de
> domínio.** O gate de base falhou (PR #20 / C04 não mergeado), então só o
> MODO A foi executado. Mas a preparação encontrou evidência que **coloca em
> dúvida a premissa da própria CR**, e isso precisa de decisão humana antes
> do MODO B — ver §9 e §11.

Base medida: `origin/main` @ `3ebcd9b63875f9114a3d6223aa648e5075e2d35b`.
Zero alteração de produção. Artefatos: `nuvem/benchmark/diagnostics_c02/`.

---

## 1. Precondições — por que MODO A

| item | verificado | resultado |
|---|---|---|
| `origin/main` | `git rev-parse` | `3ebcd9b6…` (pós-PR #19), inalterada |
| PR #20 (C04) | API do GitHub | `state=open`, **`draft=true`, `merged=false`** |
| C04 `dde0261e…` ancestral de `main`? | `git merge-base --is-ancestor` | **NÃO** |

`<BASE_POS_C04>` **não existe** — não foi inventado nenhum SHA. Nada da
branch da Conta 2 foi tocado; nenhum merge; nenhum monitoramento criado.

---

## 2. O teto, confirmado no código atual

Localização confirmada (não presumida) em `nuvem/core/engine/wall_stepper.py`:

| encontro | função / gate | folga exigida | inclui junta? |
|---|---|---|---|
| **X** | `solve_x_intersection` + `_x_intersection_centered_candidate` | **28,00cm** | sim (27 + `BLOCK_JOINT_CM`) |
| **T** | `_t_intersection_room_ok` | **27,00cm** | **não** |
| **L** | `solve_l_corner` (`CORNER_B34_ROOM_FT`) | **34,00cm** | não |

Os três usam a mesma medição (`_room_at_t_on_wall`) e a mesma folga de
comparação `1e-6 ft` — **0,00003cm**, pequena demais para absorver qualquer
déficit real observado. Valores medidos, não lidos da documentação
(`room_distribution.json → contrato_medido_cm`).

**T e X não compartilham o contrato**, ao contrário do que a preparação
anterior sugeria: o X desconta a junta de 1cm, o T não.

---

## 3. Reprodução da evidência histórica — bate exatamente

`tools_c02_instrument.py` instrumentou a função real e reproduziu os números
da preparação anterior, sem divergência:

| projeto | avaliações de `_x_intersection_centered_candidate` | `room_cm` distintos |
|---|---|---|
| TGD | **2024** | `{0,0 ; 27,997}` |
| TP1 | **1350** | `{17,0 ; 27,9 ; 27,98 ; 27,99}` |
| Piloto | **4** | `{7,0}` |

---

## 4. Mas “≈1234 recuperações” é contagem de avaliações, não de peças

O solver refaz a resolução dos nós a cada rebuild/banda (SAFE REPAIR do ARM,
B19 residual fill, variantes por fiada). Separando avaliação de identidade
física (§ armadilhas, `README.md`):

| | TGD | TP1 | Piloto |
|---|---|---|---|
| avaliações do gate X | 6256 | 9100 | 4 |
| **nós X únicos** | **17** | **26** | **1** |
| identidades (nó, parede) com déficit ≤ 0,05cm | **1** | **5** | 0 |
| identidades com déficit 0,05–0,30cm | 0 | **1** | 0 |

**As 184 avaliações a 27,997cm do TGD são UMA identidade física.** As ~1050
do TP1 são **cinco**.

### As 7 identidades, uma a uma (`first_divergence.json`)

| projeto | nó (cm) | parede | `room` | déficit | escolha hoje |
|---|---|---|---|---|---|
| TGD | (1263,518; −507,951) | 1263,518;−569,948 → 1263,518;24,049 | 27,997 | **0,003** | B34 |
| TP1 | (6607,25; 594,93) | 6545,26 → 6669,24 | 27,990 | 0,010 | B34 |
| TP1 | (6607,25; 1814,95) | 6545,26 → 6669,24 | 27,990 | 0,010 | B34 |
| TP1 | (6607,25; 594,93) | 6607,25;532,95 → 6607,25;1876,95 | 27,980 | 0,020 | B34 |
| TP1 | (8942,24; 594,93) | 8880,25 → 9004,22 | 27,980 | 0,020 | B34 |
| TP1 | (8942,24; 594,93) | 8942,24;532,95 → 8942,24;1876,95 | 27,980 | 0,020 | B34 |
| TP1 | (8942,24; 1814,95) | 8880,34 → 9004,32 | 27,900 | **0,100** | B34 |

---

## 5. Efeito real, medido em PEÇA FINAL

`tools_c02_strategy.py`, uma variante por processo, comparando
`course_candidates` por identidade geométrica
(`candidate_strategy_comparison.json`):

| variante | TGD | TP1 | Piloto |
|---|---|---|---|
| **X @ 0,05cm** | **+9 B54** (1 nó, 9 fiadas) | **+42 B54** (3 nós, 17 fiadas) | **delta zero** |
| X @ 0,30cm | idem (+9) | +50 B54 (o 27,9 entra: +8) | delta zero |
| X + T @ 0,05cm | +21 B54 (+12 vindos do T) | +42 (T não muda nada) | delta zero |

**B54 recuperados como peça final, X @ 0,05cm: 51 — não 1234.**
São **4 nós físicos**. A estimativa histórica superava o efeito real em ~24×.

O Piloto tem **fingerprint físico idêntico** em todas as variantes.

### Efeito colateral já visível (a medir como hard gate no MODO B)

A troca B34→B54 recompõe o resto do trecho. No TP1, `x005` traz **+34 B19
`STANDARD_FILL` novos** e −126/+36 C09. B19 tem política restrita (só vão de
abertura ou ponta sem amarração) — no MODO B isso **precisa** passar pelo
gate de B19/`JUNCTION_*`, não pode entrar de carona.

---

## 6. Causa-raiz: **não é ruído numérico**

`tools_c02_origin.py` rastreou, para cada medição borderline, qual limite
venceu. Resultado em **100% dos casos**, nos dois projetos:

```
boundary_source = RESERVA_OU_PONTA      (nunca ABERTURA, nunca PONTA_FISICA)
boundary_cm     = 34,0  (CORNER_B34_ROOM_FT — a reserva do nó da outra ponta)
```

E o déficit vem da **coordenada de entrada**, não de conversão:

| caso | geometria real no `input.json` |
|---|---|
| TGD 27,997 | parede de **593,997cm** (y de −569,**948** a 24,049); as irmãs colineares medem 594,000 exatos (y de −569,**951**) |
| TP1 27,99 / 27,98 | paredes de **123,98 / 123,97cm** (x de 6545,26 a 6669,24) |
| TP1 27,90 | parede de 123,98cm com o cruzamento **0,09cm fora do centro** (t=61,90 onde o centro é 61,99) |

Os `input.json` vêm da extração do projeto Revit entregue
(`walls_already_extended: true`), com coordenadas de 3 casas em cm. O
déficit de 0,003cm é **imprecisão de desenho (0,03mm)**, não erro de
ponto flutuante — float64 erraria na 13ª casa.

> **Consequência de nomenclatura:** `ROOM_CHECK_NOISE_TOLERANCE_CM` seria um
> nome **enganoso**. Não existe ruído a absorver: existe uma decisão sobre
> **quanta imprecisão de desenho** o solver aceita ceder da junta de
> argamassa. O nome deve dizer isso (ex.: `ROOM_CHECK_DRAFTING_TOLERANCE_CM`).

### O que a tolerância cede, exatamente

No caso do TGD: o B54 centrado em t=61,997 ocuparia 34,997 → 88,997. A
fronteira está em 34,000. Folga resultante: **0,997cm em vez de 1,000cm de
junta**. A reserva de 34cm **não é invadida** — ela é a fronteira, e o B54
para antes dela.

Logo o argumento físico de `FUTURE_BLOCK_CR_PREPARATION.md` §18.4 **se
sustenta** (cede-se junta, não peça), mas por um caminho diferente do
descrito: a fronteira não é “a borda do próximo obstáculo físico”, é uma
**reserva conservadora** de 34cm que o próprio código documenta como pior
caso superestimado (`_wall_reserved_range_ft`). Ceder 0,003cm de junta
contra uma reserva superestimada é ainda mais seguro do que contra uma peça
real.

**Porém** — e isto é uma condição de implementação, não um detalhe: essa
segurança vale **só porque a fronteira tem junta**. Se a fronteira fosse uma
jamba, ponta livre ou reserva sem argamassa, ceder junta seria **invadir** —
exatamente o defeito que o C04 corrigiu com `_layout_fitted_to_physical_span`.
Hoje, empiricamente, nenhum caso afetado toca abertura; nada garante que
continue assim.

> **Requisito para o MODO B:** a tolerância deve ser aplicada **só quando a
> fronteira que fechou o `room` for uma fronteira COM junta**. A estratégia
> mínima de §18.5 da preparação anterior (somar epsilon incondicionalmente)
> é **insuficiente** — precisa da mesma distinção de fronteira do C04.

---

## 7. Classificação física — o 27,9 é diferente em espécie, não só em grau

| `room` | déficit | origem medida | classificação |
|---|---|---|---|
| 27,997 | 0,003 | parede 0,003cm mais curta | imprecisão de desenho |
| 27,99 / 27,98 | 0,01 / 0,02 | parede 123,98 em vez de 124,00 | imprecisão de desenho |
| **27,90** | **0,10** | **cruzamento 0,09cm fora do centro da parede** | **descentralização real do nó** |
| 17,0 / 7,0 / 0,0 | 11 – 28 | geometria de fato apertada | insuficiência real — degradar está certo |

O 27,9 é o único caso em que a folga é **assimétrica** (`+28,08 / −27,90`):
o B54 centrado ficaria descentrado em relação à parede. Isso justifica
mantê-lo fora — **não** por ultrapassar um número, mas porque a natureza
geométrica é outra. Registrar assim é mais defensável do que “0,10 > 0,05”.

### Instabilidade do limite exato

No reproducer, `room = 27,95cm` (déficit nominal **exatamente** 0,05) é
**rejeitado**: em float, `28.0 - 27.95 = 0.05000000000000071`. Um teste “no
limite exato” tem de fixar o lado (`<` ou `<=`) e o modo de comparação, ou
falha de forma não determinística. **Requisito de teste do MODO B.**

---

## 8. Invariância da medição — a medição está correta

`minimal_reproducers.py`, planta sintética independente do corpus, mesma
geometria sob cinco transformações:

| transformação | `room` medido | peça |
|---|---|---|
| identidade | 28,000 | B54/B54 |
| translação (+1234,567; −987,654) | 28,000 | B54/B54 |
| **rotação 90° exata** (troca de eixos) | **28,000** | B54/B54 |
| rotação 180° exata | 28,000 | B54/B54 |
| espelho em X / em Y | 28,000 | B54/B54 |
| reversão de extremidades | 28,000 | B54/B54 |
| permutação das paredes | 28,000 | B54/B54 |

**A medição do room check é invariante.** O mesmo vale para 27,997 / 27,98 /
27,90 / 17,0 — a parte fracionária se preserva em todas.

### Dívida encontrada de passagem (fora do escopo do C02)

Rotação por **trigonometria** (37°, ou 90° via `cos/sin`, que deixa resíduo
~1e-14 nas coordenadas) faz o `room` cair de 28,00 para 21,00cm — exatos
**7,0cm = espessura/2 por ponta**. A causa é `extend_wall_ends_to_junctions`
(`nuvem/core/wall_modeling.py`), que deixa de reconhecer a junção e **não
estende** as pontas. Rotação *exata* não tem o problema, o que confirma que
é sensibilidade a resíduo de coordenada, não dependência de orientação.

Isto é **pré-existente, upstream, em outro arquivo, e 140× maior que a
tolerância discutida aqui**. Não é a causa do déficit de 0,003–0,02cm. Fica
registrado como dívida separada — **não** deve ser corrigido dentro do C02.

---

## 9. Validação humana — o gabarito **não confirma** a hipótese

`human_reference_check.json`. As quatro paredes do TP1 que contêm os nós
afetados existem no gabarito com a **mesma geometria** (W021, W022, W092,
W093 — 123,98 / 123,97cm), então a comparação é confiável:

```
W021 (123,98cm), junctions registradas pelo humano:  L em t=0,0  e  L em t=123,98
                                     nenhuma junction em t≈61,99  ← onde o solver vê o X

fiada 0:  B39 [14,99–53,99]                       B39 [69,99–108,99]
fiada 1:  B34 [0–34]  B19 [34,99–53,99]           B19 [69,99–88,99]  B34 [89,98–123,98]
                              └──── vão livre de 16,0cm no eixo do cruzamento ────┘
```

O humano, nessas paredes:

- **não usa B54** (nenhum, em nenhuma fiada);
- **não registra encontro** no meio da parede — para ele o ponto não é um X;
- deixa um **vão livre de 16cm** exatamente no eixo do cruzamento (a passagem
  da parede transversal) e amarra **só nas duas pontas**, em L.

Ou seja: nos nós que a tolerância recuperaria, o humano **não coloca peça de
amarração centrada** — nem B54 nem B34. Recuperar o B54 (54cm, contra os
34cm de hoje) **ocuparia ainda mais** o vão que o humano deixa livre:
afastaria do gabarito em vez de aproximar.

**Classificação: `QUALITY_REGRESSION_RISK`** para as 4 identidades do TP1.

Calibração, para não superinterpretar:

| projeto | B54 humanos | nós X que hoje aceitam B54 | destes, com B54 humano a ≤5cm |
|---|---|---|---|
| TGD | 516 | 16 | **4** |
| TP1 | 519 | 26 (150 B54 humanos a ≤5cm de algum nó X) | — |

No TGD a parede do nó afetado **não existe** no gabarito com essa geometria
(fragmentação diferente — `BENCH-WALLMODEL-FRAGMENTS`), e mesmo onde o
solver já aceita B54 o gabarito só concorda em 4/16 nós.
**Classificação TGD: `INCONCLUSIVE`.**

---

## 10. Auditoria T / L — decisão de escopo

| | mesmo cálculo? | mesmo contrato? | identidades com déficit ≤0,05 | efeito em peça final @0,05 |
|---|---|---|---|---|
| **X** | — | 28cm (27 + junta) | TGD 1, TP1 5 | +9 / +42 B54 |
| **T** | sim (`_room_at_t_on_wall`) | **27cm, SEM junta** | TGD 6, TP1 4 | **+12 B54 no TGD**, TP1 zero |
| **L** | sim | **34cm, SEM junta** | TGD 1, TP1 0, Piloto 0 | não medido (fora da variante) |

**Recomendação: NÃO tratar T e L na mesma CR.**

- O X desconta a junta de 1cm; T e L **não**. São contratos físicos
  diferentes — o mesmo epsilon significa coisas diferentes em cada um
  (no X cede junta; no T/L cede **reserva estrutural**, que é o contrato
  que o C04 recusou ceder no W087).
- O L tem **uma única** identidade no corpus inteiro: impacto irrelevante,
  risco desproporcional.
- Ampliar “porque os nomes são parecidos” é exatamente o que o CR proíbe.

---

## 11. Estratégias comparadas — e por que nenhuma está pronta

| | estratégia | veredito da preparação |
|---|---|---|
| **A** | epsilon dedicado somado ao `room` | **funciona, mas incompleto** — recupera 51 peças; precisa da guarda de fronteira-com-junta (§6) e do nome correto (não é “noise”) |
| **B** | snap/normalização da folga | **rejeitada** — mascararia a imprecisão de desenho real sem torná-la visível |
| **C** | corrigir a medição geométrica | **não se aplica** — a medição está provada invariante (§8); a imprecisão está no **desenho de entrada**, não na medição |
| **D** | manter a rejeição | **é a opção defendida pelo gabarito humano** nos únicos casos comparáveis (§9) |

Reusar `PIER_FIT_TOLERANCE_CM = 0,30cm` continua **proibido** e agora
também medido: 0,30 recuperaria +8 B54 adicionais no TP1 — justamente o nó
**descentralizado**, o caso que a análise física manda rejeitar.

---

## 12. Perguntas que precisam de decisão humana antes do MODO B

1. **A CR ainda faz sentido?** O gabarito humano, nos únicos casos
   comparáveis, **não** coloca B54 nesses nós (§9). Antes de recuperar 51
   B54, vale confirmar: nesse tipo de cruzamento, o correto é peça de
   amarração centrada ou vão livre para a transversal passar?
2. **Quanta imprecisão de desenho o solver deve absorver?** 0,003cm e 0,02cm
   são a mesma coisa fisicamente; 0,05cm é um número herdado do
   `PIER_LAYOUT_TOLERANCE_CM`, não uma medida deste problema.
3. **O 27,9 (nó descentralizado 0,09cm) fica fora?** A preparação recomenda
   que sim, por natureza geométrica e não por magnitude (§7).
4. **Confirma-se o requisito de fronteira-com-junta** (§6) como parte
   obrigatória da implementação mínima?

Nenhuma regra de `nuvem/REGRAS_MODULACAO_BLOCOS.md` foi alterada: o
conhecimento de amarração aqui ainda é **hipótese em investigação**, e a
evidência humana **contradiz** a hipótese original. Registrar como regra
agora violaria “nunca apagar uma regra anterior em silêncio”. O registro
obrigatório será feito quando a decisão de §12.1 existir.

---

## 13. Entregáveis e higiene

- `nuvem/benchmark/diagnostics_c02/` — 5 JSON consolidados + 5 scripts
  reprodutíveis + `README.md`.
- Produção: **zero arquivos alterados** (`nuvem/core/**` intocado).
- `baseline.json` / `reference.json` / `reference_score.json` /
  `input.json`: **zero alterações**.
- Branch da Conta 2, worktree do C04, branch do PR #20: **não tocados**.
- Nenhum merge, nenhum PR aberto, nenhum monitoramento/check-in criado.

## 14. Veredito

**`READY_FOR_IMPLEMENTATION_PENDING_BASE`** — a base pós-C04 não existe
ainda (PR #20 draft).

Quando ela existir, o MODO B **não deve começar direto**: as perguntas de
§12 (em especial a evidência humana de §9) precisam de resposta primeiro,
porque mudam o que a CR deve fazer — não só como fazer.
