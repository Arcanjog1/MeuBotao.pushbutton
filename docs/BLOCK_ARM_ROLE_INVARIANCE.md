# RELATÓRIO FINAL — ARM-ROLE RESIDUALS

## Estado inicial

Continuação de `CR-BLOCK-ARM-ROLE-PRISM-STAGGER`. Estado recebido:
coordenação A/B resolvida e preservada; ganho de cobertura preservado;
workaround inward-reserve removido; junta de contorno nó↔preenchimento
agora rastreada; `PRISM_CONTINUOUS_JOINT` melhorou fortemente (2 de 11
paredes resolvidas por completo); 9 paredes com coincidência descrita
como "geometricamente forçada"; regressão real `OPENING_BLOCK_INSIDE_DOOR`
+3 no TGD, não diagnosticada.

## Branch / HEAD

```
branch de trabalho    claude/cr-block-arm-role-invariance-7tezx4
HEAD inicial (sessão)  77bda141df0038c973971075b09f3320e274adb2 (confere)
HEAD final              mesmo commit — NENHUMA alteração de produção
                        nesta continuação (ver veredito)
```

Working tree preservado sem `reset`/`checkout`/`pull`/`rebase`. NODE-FILL,
BENCH-Z, `wall_pairing.py`, baseline/reference não tocados.

## OPENING_BLOCK_INSIDE_DOOR +3

### Casos

Os 3 achados adicionais (TGD, contra o estado `d813f45`/pré-fix de
prisma) estão TODOS na fiada 11, em 3 paredes que JÁ apareciam neste
código antes de qualquer CR desta série:

| parede | opening | tipo | course_index | overlap medido | achados antes (`d813f45`) | achados depois (`77bda14`) |
|---|---|---|---|---|---|---|
| W045 | W045-O01 | door (sill=0, head=221cm) | 11 | 19,0cm + 4,0cm (2 blocos) | 1 (`B39`, overlap 39,0cm) | 2 (`B19` 19,0cm + `C04` 4,0cm) |
| W051 | W051-O02 | door (sill=0, head=221cm) | 11 | 4,0 + 19,0 + 34,0cm (3 blocos) | 2 (`B19` 19,0 + `B39` 39,0) | 3 (`C04` 4,0 + `B19` 19,0 + `B34` 34,0) |
| W112 | W112-O02 | door (sill=0, head=221cm) | 11 | 34,0 + 19,0 + 4,0cm (3 blocos) | 2 (`B19` 19,0 + `B39` 39,0) | 3 (`B34` 34,0 + `B19` 19,0 + `C04` 4,0) |

Nas 3 paredes, o intervalo TOTAL coberto pelos blocos "dentro do vão" é
praticamente o MESMO antes e depois (só a composição — quantos blocos e
quais códigos — mudou); nenhuma parede nova apareceu.

### Primeira divergência

Rastreada a cadeia completa (boundary joint → avoid_positions → escolha
do layout → recorte de abertura → repair → peça final →
`OPENING_BLOCK_INSIDE_DOOR`):

1. `_pier_boundary_joint_positions_cm`/as listas separadas (fix do CR
   anterior) alteram QUAL composição a busca escolhe em segmentos
   ANTERIORES da mesma parede (efeito colateral esperado e já medido —
   ver o relatório anterior).
2. Essa composição diferente, ainda em FASE 1 (antes do recorte de
   abertura), muda o conteúdo de `candidates[variant_candidates_start:]`
   que `_recut_openings_and_repair` recebe como entrada.
3. **A divergência real não está no recorte em si** (o parâmetro
   `avoid_joint_positions_cm` do recut permanece INALTERADO — ver o
   fix anterior, que deliberadamente manteve essas duas listas
   separadas): é que o recut, ao remover os blocos que cruzam o vão e
   reconstituir a região, o faz a partir de uma composição de ENTRADA
   já diferente — e o resultado final (quantos blocos "cabem" na fiada
   11) muda de composição, mas cobre PRATICAMENTE O MESMO intervalo
   físico.
4. **A causa raiz não está em nenhuma decisão de composição em si**:
   está em `analysis.opening_active_in_row`/`opening_active_in_row`
   (mesma função usada pelo validador `validate_openings.py`), que
   trata a fiada 11 (elevação 220–239cm) como "ativa" para a porta
   inteira (`head_cm=221`) porque a faixa vertical da fiada 11
   INTERCEPTA o intervalo [0, 221] em 1cm — quando na realidade **apenas
   1 dos 19cm de altura da fiada 11 (5,3%) está de fato dentro do vão**;
   os outros 94,7% da fiada já são a verga/travamento acima da porta,
   onde blocos SÃO fisicamente corretos. O modelo de "fiada ativa"
   binário (tudo ou nada) do validador — e do próprio motor, que usa a
   MESMA regra para decidir se essa fiada precisa de vão — não tem
   graduação por fração de altura.

### H1–H6

| # | hipótese | veredito | evidência |
|---|---|---|---|
| H1 | novo boundary joint altera composição antes do recorte | **PROVADA (como mecanismo, não como causa raiz)** | confirmado nos 3 casos — mas a composição diferente cobre o MESMO intervalo físico, então não é em si o defeito |
| H2 | recut remove peça e repair recoloca outra dentro do vão | **PARCIALMENTE PROVADA** | é exatamente o que acontece — mas o "vão" em si só é vão por 1 dos 19cm da fiada (ver H4) |
| H3 | informação de NODE-FILL vazando apesar da separação | **REFUTADA** | NODE-FILL não foi tocado nem incorporado nesta linha de CRs; a separação de listas do fix anterior é auto-contida em `solve_wall_free_fill`, sem qualquer acoplamento com NODE-FILL |
| H4 | regressão é consequência de medição vertical antiga | **PROVADA — causa raiz** | fiada 11 (elevação 220–239cm) contra porta com `head_cm=221`: a fiada é marcada "ativa" pela função binária `opening_active_in_row`, mas só 1cm dos 19cm (5,3%) está de fato dentro do vão — as MESMAS 3 paredes, na MESMA fiada 11, já tinham este código no estado A (pré-CR, `origin/main` limpo, `SHA 7c9a681`) com a MESMA lista de 3 paredes, ANTES de qualquer alteração desta série de CRs |
| H5 | regressão é física real mesmo com convenção vertical correta | **REFUTADA** | fisicamente, colocar bloco na fiada 11 é CORRETO em 94,7% da sua altura (é a região da verga) — o achado é uma leitura binária de um caso de fronteira pré-existente, não uma invasão real de vão |
| H6 | layout mudou só de fase, peça que cruzava a jamba passou a ficar majoritariamente dentro do vão | **PROVADA (efeito colateral, não causa)** | confirma H1/H2 — é o MECANISMO da amplificação de contagem (1-2 blocos → 2-3 blocos cobrindo a mesma área), não uma causa nova |

### Causa raiz

**PROVADA — é um artefato de medição/benchmark pré-existente, não uma
regressão física introduzida por esta série de CRs.** Confirmado
decisivamente: as MESMAS 3 paredes (`W045`, `W051`, `W112`), na MESMA
fiada 11, já tinham `OPENING_BLOCK_INSIDE_DOOR` no estado A
(`origin/main` limpo, `SHA 7c9a681`, ANTES de `CR-BLOCK-ARM-ROLE-*`
inteiro) — 43 achados totais nas mesmas 18 paredes, incluindo estas 3.
O fix de prisma do CR anterior não criou o defeito: mudou a composição
de blocos usada nessa fiada de fronteira (efeito colateral de segmentos
anteriores na mesma parede), o que fez o MESMO intervalo físico
"dentro do vão" (que já era um falso positivo do validador antes)
aparecer fatiado em mais blocos — de 1-2 achados para 2-3 achados por
parede, sem nenhuma parede nova.

### Fix

**Nenhum.** É um problema de medição do benchmark (H4 provada), não uma
regressão física do motor — conforme a instrução explícita desta
continuação ("Se for problema de benchmark: NÃO tocar produção"), a
produção NÃO foi alterada para isto. O gate mecânico "OPENING_BLOCK_
INSIDE_DOOR não pode ser pior que o estado anterior à regressão" **não
passa em contagem bruta** (43→46) mas **passa em paredes afetadas**
(mesmas 3, 0 novas) — documentado explicitamente, não escondido.

## Prisma residual

### 9 paredes

Nenhuma nova investigação de causa nesta fase — a causa (junta de
contorno geometricamente forçada quando as duas pontas usam a mesma
peça, `B34`) já estava provada no relatório anterior. Esta fase usa o
Reference Corpus para responder: **o humano acha isso inevitável?**

### Solver × Humano

Casamento geométrico correto feito via `nuvem/benchmark/comparator/match.py`
(`match_walls`) — **NÃO por `id`**: confirmado que IDs não são
estáveis entre `input.json`/resultado e `reference.json` (ex.: "W003"
do resultado do TGD é uma parede de 69cm; "W003" da referência do TGD é
uma parede de 1344cm completamente diferente — casadas corretamente
via geometria, resultando no par real W003→W014). Para as 8 paredes do
TP1 o casamento por geometria confirmou o mesmo `id` (coincidência,
não presunção).

**Resultado, decisivo e unânime**: nas 9 paredes, a fiada par e a fiada
ímpar da parede humana **NUNCA têm junta coincidente** — 8 de 9 têm
correspondente na referência (W137/TGD não tem, fora do escopo do
gabarito). Dois mecanismos distintos, medidos:

**Mecanismo 1 (paredes curtas — `W003`, `W076`, `W021`, `W092`, `W061`,
`W062`, e provavelmente `W137`)**: o humano NÃO ancora as duas famílias
em nós opostos como a coordenação determinística faz — em vez disso,
as DUAS peças de canto (dos dois nós) vão para a MESMA fiada física
(par OU ímpar), e a fiada OPOSTA fica sem nenhuma peça de nó, com um
preenchimento solto (às vezes nem tocando nenhuma das duas pontas).
Como a fiada "sem nó" não tem NENHUMA junta de contorno, não há nada
para coincidir com a fiada que tem as duas.

Exemplo medido, `W076`↔`W077` (par mínimo, ver "Caso 69cm" abaixo).

**Mecanismo 2 (paredes longas — `W010`, `W037`)**: aqui o humano AINDA
ancora as duas famílias em nós opostos (mesma direção da coordenação
atual do solver) — mas usa `B34` também como peça de preenchimento
COMUM ao longo da parede (não só como peça de canto), numa sequência
que nunca se repete de forma sincronizada entre as duas fiadas.
Resultado: nenhuma junta interna cai na mesma posição em toda a
extensão da parede, mesmo com as duas ancoragens presentes.

`W041` (já resolvida pelo fix do CR anterior, fora dos 9 residuais):
confirmado que a referência humana TAMBÉM não tem coincidência —
validação independente de que a direção do fix está correta.

### Classificação A/B/C/D/E

| parede | mecanismo | classificação |
|---|---|---|
| W003/TGD (↔W014) | ancoragem assimétrica (1 fiada com nó, outra sem) | **B — HUMAN_RESOLVE_COM_OUTRA_PECA/CONVENÇÃO** |
| W137/TGD (↔W077) | mesmo padrão de W076 (par mínimo) | **B** |
| W076/TP1 (↔W077, mesma referência de W137 — par simétrico) | ancoragem assimétrica, ver "Caso 69cm" | **B** |
| W021/TP1 | ancoragem assimétrica (uma fiada com B34+B19 nas duas pontas, outra sem nenhuma) | **B** |
| W092/TP1 | idêntico a W021 (mesma geometria, mesma referência) | **B** |
| W061/TP1 | ancoragem assimétrica + compensador C09 | **B** |
| W062/TP1 | idêntico a W061 (mirror) | **B** |
| W010/TP1 | ancoragem simétrica preservada, composição rica evita coincidência | **C — HUMAN_RESOLVE_COM_OUTRO_LAYOUT** |
| W037/TP1 | idêntico mecanismo de W010 | **C** |

Nenhuma parede classificada A (humano também alinha), D (geometria do
solver difere da humana) ou E (referência insuficiente) — as 8 com
referência têm evidência clara e concorde.

## Caso 69cm

### Solver (estado atual, commit `77bda14`)

```
fiada A: B34[0,34]  B19[35,54]   -> junta interna em t=34.5
fiada B: B19[15,34] B34[35,69]   -> junta interna em t=34.5  (COINCIDE)
```

### Humano (W076↔W077, referência)

```
fiada par:  B34[0,34]  B34[35,69]   -> junta interna em t=34.5 (só nesta fiada)
fiada ímpar: B39[15,54]             -> NENHUMA junta interna (peça única,
                                        nem toca t=0 nem toca t=69)
```

### Diferença

O humano **não alterna qual nó ancora qual família** — as DUAS peças
de canto (`B34` de cada ponta) vão para a MESMA fiada; a fiada oposta
fica com um único bloco de preenchimento comum (`B39`), sem amarração
de nó em NENHUMA das duas pontas, e sem sequer tocar as extremidades da
parede. Isso elimina a coincidência por construção: uma fiada sem
nenhuma junta interna nunca pode coincidir com a outra. Não é "outra
peça" nem "outro layout" no preenchimento — é uma CONVENÇÃO DIFERENTE
de qual nó amarra qual fiada, incompatível com a premissa central da
coordenação determinística (`_coordinate_arm_role_nodes`) de que as
duas famílias devem, sempre que possível, receber uma peça de nó real
em cada ponta.

## Regra de domínio

### Regra existente

Nenhuma regra em `REGRAS_MODULACAO_BLOCOS.md` documenta ou permite
"as duas peças de canto do mesmo nó par indo para a mesma fiada,
deixando a fiada oposta sem amarração de nó" — pesquisado (termos
"mesma familia", "duas pontas", "flutuante", sinônimos) sem resultado.
A seção 29.5 (`REGRA OBRIGATÓRIA`) documenta a coordenação
determinística atual, mas não proíbe nem prescreve qual dos dois
resultados válidos (mesma fiada vs. fiadas alternadas) a coordenação
deve preferir quando ambos evitariam o defeito original
(`COVERAGE_MISSING_ROW`) — a implementação atual resolve isso por um
critério de desempate geométrico determinístico (`_canonical_node_
sort_key`), não por uma regra de amarração explícita.

### Nova regra necessária?

**Possivelmente, mas NÃO confirmada com evidência suficiente para virar
regra obrigatória agora.** A hipótese, sustentada pelos 9 casos (100%
de concordância, mas mesma topologia — 2 nós L_CORNER de 2 braços,
mesma peça B34 nas duas pontas): o processo humano de amarração pode
não trabalhar com a abstração "família A/família B fixada globalmente
por parede" que a arquitetura atual do solver usa (`course_a` sempre
resolvida primeiro, `course_b` sempre evitando `course_a`) — pode
decidir fiada a fiada, evitando coincidência com a fiada JÁ COLOCADA
(seja ela par ou ímpar), o que naturalmente permite (e talvez prefira)
concentrar as duas amarrações de nó na mesma fiada quando isso evita
melhor a junta corrida.

### Confiança

**PADRÃO OBSERVADO AINDA NÃO CONFIRMADO.** Evidência forte mas estreita
(9 casos, 1 topologia, 2 projetos). Registrado em
`REGRAS_MODULACAO_BLOCOS.md` seção 29.7 com este rótulo — não promovido
a `REGRA OBRIGATÓRIA` nem usado para justificar mudança de código nesta
sessão. **CONFLITA** com a leitura de que a seção 29.5 (coordenação
determinística atual) representa "a" solução correta — na prática,
29.5 resolve o defeito ORIGINAL (família inteira ausente) mas o critério
de desempate específico que ela usa hoje (geométrico, por
`_canonical_node_sort_key`) não necessariamente reproduz a escolha
humana nestes 9 casos.

## Implementação

**Nenhuma.** As 4 condições da Fase 4 não estão simultaneamente
satisfeitas: (1) causa provada — sim; (2) referência humana mostra
padrão inequívoco — sim, mas (3) a regra existente NÃO sustenta a
mudança (29.5 é `REGRA OBRIGATÓRIA` vigente, e mudar o critério de
desempate da coordenação para "permitir/preferir ambas as peças de nó
na mesma fiada" é, em espírito, alterar a POLÍTICA da coordenação
determinística — não apenas a peça ou o layout do preenchimento) — e a
instrução explícita desta continuação proíbe exatamente isso ("NÃO
desfaça a coordenação A/B só para recuperar prisma"). Tecnicamente a
mudança ficaria dentro de `wall_stepper.py` (condição 4 satisfeita),
mas o ESCOPO AUTORIZADO desta continuação — não o arquivo — é o que
bloqueia: mudar a política de desempate da coordenação é uma decisão
de produto/engenharia que precisa de autorização explícita e de uma
verificação MUITO mais ampla (confirmar que "permitir ambas as
ancoragens na mesma fiada" não reintroduz o defeito original em algum
outro caso da topologia geral) do que esta sessão pode fazer com
segurança.

**Veredito da Fase 4: BLOQUEADO POR ESCOPO** para os 9 casos residuais
— não por faltar informação (a causa e a evidência humana estão
provadas), mas porque a correção plausível exige revisar uma decisão
de política já tomada e explicitamente protegida nesta continuação.

## Testes

Nenhum teste novo nesta fase (nenhuma mudança de código). Os 5 testes
de `tests/test_block_arm_role_prism_stagger.py` (CR anterior) continuam
válidos e passando — incluem exatamente o caso W076 (prova da
coincidência geometricamente forçada) e W041 (prova do caso resolvido).
Suíte rápida completa: `518 passed` (inalterada).

## Coverage A/B/C/D

A = `origin/main` limpo | B = `d813f45` (ARM-ROLE-CONSISTENCY) | C =
`77bda14` (PRISM-STAGGER) | D = este candidato (idêntico a C, nenhuma
mudança de código).

| métrica | TGD | TP1 | Piloto |
|---|---|---|---|
| COVERAGE_MISSING_ROW (A→C→D) | 265→258→**258** | 16→0→**0** | 0→0→0 |
| COVERAGE_ROW_MOSTLY_EMPTY (A→C→D) | 171→153→**153** | 27→18→**18** | 8→8→8 |
| TOTAL_COVERAGE_CRITICAL (A→C→D) | 436→411→**411** | 43→18→**18** | 8→8→8 |
| COVERAGE_GAP_IN_ROW (A→C→D) | 1934→1958→**1958** | 293→327→**327** | 16→16→16 |

**G9 confirmado: nenhuma mudança entre C e D — o ganho de cobertura
está 100% preservado.**

## Prisma A/B/C/D

| métrica | TGD | TP1 |
|---|---|---|
| PRISM_CONTINUOUS_JOINT (A→C→D) | 702→476→**476** | 837→576→**576** |
| PRISM_JOINT_STACK (A→C→D) | 46→29→**29** | 49→33→**33** |
| NEW_PRISM_WALLS (vs A) | 3→2→**2** (W003,W137) | 8→7→**7** | 
| alignment_conflicts (diagnóstico interno) | não medido isolado por projeto nesta fase | ver total abaixo |

Diagnóstico independente (`nuvem/benchmark/diagnostics_block_prisma/`,
ferramenta de outra CR, usada aqui só como CROSS-CHECK, classificação
própria e mais estrita — não substitui `PRISM_CONTINUOUS_JOINT` como
gate): `same_band=0`, `cross_band=24`, `FORBIDDEN_JOINT_ALIGNMENT=24`
no total dos 3 projetos no estado atual — ordem de grandeza compatível
com as 9 paredes residuais (algumas com mais de uma posição de
coincidência, ex. `W061`/`W062`), confirmando de forma independente que
o que resta é uma quantidade pequena e localizada, não um problema
difuso.

## Openings

`OPENING_BLOCK_CROSSES_JAMB`: inalterado (147 TGD, 168 TP1).
`OPENING_BLOCK_INSIDE_DOOR`: 43(A)=43(C)=**46(D, inalterado nesta
fase)** — regressão JÁ EXISTENTE desde o commit anterior, agora
explicada (ver acima), não corrigida por decisão explícita (H4/benchmark).

## Compensadores

Não investigados nesta fase (nenhuma mudança de código desde o estado
já reportado no relatório anterior — TGD `COMPENSATOR_CONSECUTIVE` -8,
`COMPENSATOR_AVOIDABLE` +2; TP1 `COMPENSATOR_EXCESS_IN_RUN` +44,
`COMPENSATOR_VERTICAL_STRIP` -4, nenhum crítico).

## Collisions

`POSITION_OVERLAP`: idêntico nos três estados (TGD 29, TP1 18, piloto
0) — sem mudança nesta fase.

## Determinismo

Preservado por construção (nenhuma mudança de código nesta fase); os
testes de determinismo do CR anterior continuam passando.

## Performance

Não medida separadamente (nenhuma mudança de código). Suíte rápida
completa roda em ~17s (518 testes), mesma ordem de grandeza reportada
antes.

## Production diff

**Nenhum.** `git diff --stat -- nuvem/` vazio para código de produção
nesta continuação — só documentação foi alterada
(`docs/BLOCK_ARM_ROLE_INVARIANCE.md`, `docs/PROJECT_STATUS.md`,
`nuvem/REGRAS_MODULACAO_BLOCOS.md`).

## Baselines

Não regravados. `tests/regression/test_benchmark_baselines.py -m slow`
continua com as mesmas 2 falhas já documentadas no relatório anterior
(TP1 `JUNCTION_MISSING_BINDING` +1, mirror de paridade benigno; TGD
`OPENING_BLOCK_INSIDE_DOOR` +1 contra o baseline.json armazenado — H4
provada nesta sessão, artefato pré-existente de medição, não regressão
física nova).

## Gates G1–G16

| gate | descrição | status |
|---|---|---|
| G1 | OPENING +3 reproduzido exatamente | ✅ (3 casos, tabela completa) |
| G2 | primeira divergência da regressão OPENING localizada | ✅ (composição de FASE 1 mudando antes do recut) |
| G3 | causa de OPENING provada | ✅ (H4 — artefato de medição pré-existente, mesmas 3 paredes desde o estado A) |
| G4 | nenhuma regressão física nova dentro de porta | ✅ (mesmo intervalo físico coberto, mesmas 3 paredes, 0 novas) |
| G5 | as 9 paredes de prisma comparadas contra o humano | ✅ (8/9 com referência, casamento geométrico correto) |
| G6 | todas as 9 classificadas A/B/C/D/E | ✅ (7×B, 2×C, 0×A/D/E) |
| G7 | caso de 69cm explicado | ✅ (W076↔W077, mecanismo exato identificado) |
| G8 | nenhuma regra inventada | ✅ (padrão registrado como "AINDA NÃO CONFIRMADO", não promovido) |
| G9 | coverage do 77bda141 preservada | ✅ (idêntica, C=D) |
| G10 | prisma não piora | ✅ (idêntico, C=D — nenhuma mudança de código) |
| G11 | nenhuma nova parede de prisma criada | ✅ (mesmas 9, nenhuma nova) |
| G12 | determinismo preservado | ✅ (nenhuma mudança de código) |
| G13 | baseline/reference intactos | ✅ |
| G14 | production diff restrito ao escopo autorizado | ✅ (diff de produção vazio) |
| G15 | testes focados passam | ✅ (os 5 do CR anterior, inalterados) |
| G16 | suíte final passa, caso exista candidato de fix | N/A — nenhum candidato de fix de código nesta continuação |

## Riscos

**OPENING_BLOCK_INSIDE_DOOR** continuará aparecendo como "REGRESSAO
CRITICA" no teste mecânico de regressão contra `baseline.json` enquanto
o baseline não for atualizado (decisão que exige merge/aprovação
humana, fora desta sessão) — o risco REAL (invasão física de porta) foi
refutado (H4/H5), mas o GATE MECÂNICO continua vermelho até alguém
decidir regravar o baseline ou ajustar a granularidade de
`opening_active_in_row` (mudança de escopo maior, não avaliada aqui).

**As 9 paredes de prisma residual** continuarão sinalizando
`PRISM_CONTINUOUS_JOINT` até uma futura CR, com autorização explícita,
revisar a política de desempate da coordenação (`_coordinate_arm_role_
nodes`) à luz da evidência humana levantada aqui — risco de regressão
SE essa mudança for feita sem verificação ampla (o critério atual
resolve corretamente o defeito original; mudar o desempate podia
reabri-lo em algum caso não testado).

## Próximo passo recomendado

1. Decisão humana explícita: regravar `baseline.json` do TGD (ou
   refinar `opening_active_in_row` para graduar por fração de altura em
   vez de binário) para eliminar o falso positivo mecânico de
   `OPENING_BLOCK_INSIDE_DOOR` — mudança de benchmark, não de produção.
2. Nova CR, com autorização explícita para revisar o critério de
   desempate de `_coordinate_arm_role_nodes` (não a coordenação em si,
   que deve continuar), usando a evidência humana desta sessão (seção
   29.7 de `REGRAS_MODULACAO_BLOCOS.md`) como ponto de partida — testar
   amplamente antes de mudar, para não reabrir o defeito original de
   `COVERAGE_MISSING_ROW`.

## Veredito

**BLOQUEADO POR ESCOPO**

Ambas as investigações desta continuação chegaram a causas PROVADAS,
com evidência concreta (medição direta e comparação sistemática com o
Reference Corpus humano, 8 de 9 paredes com correspondência
geométrica correta). Nenhuma das duas admite um "fix mínimo" seguro
dentro do escopo autorizado:

- `OPENING_BLOCK_INSIDE_DOOR`: é um artefato de medição do benchmark,
  não uma regressão física — corrigi-lo corretamente significa mudar o
  benchmark (`baseline.json` ou `opening_active_in_row`), não a
  produção. Instrução explícita: não tocar produção neste caso.
- As 9 paredes de prisma residual: a evidência humana é clara e
  unânime, mas a correção implícita (permitir/preferir que as duas
  peças de canto de um nó vão para a mesma fiada, em vez de sempre
  alternar) significa revisar a POLÍTICA de desempate da coordenação
  determinística — algo que esta continuação foi explicitamente
  instruída a NÃO fazer ("não desfazer a coordenação A/B").

O estado técnico em `77bda141` — coordenação A/B correta, cobertura
preservada, prisma reduzido a 9 casos residuais bem compreendidos, e
agora também `OPENING_BLOCK_INSIDE_DOOR` totalmente explicado como
artefato pré-existente — permanece o melhor estado íntegro disponível.
Nenhum código de produção foi alterado nesta continuação; nada foi
commitado além de documentação.

**Pare antes de qualquer merge.**
