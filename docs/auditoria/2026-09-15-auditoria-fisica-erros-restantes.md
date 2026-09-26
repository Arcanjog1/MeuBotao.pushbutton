# Auditoria física dos erros restantes — BUTANTÃ (2026-09-15)

STATUS: **AUDITORIA / EVIDÊNCIA — NÃO NORMATIVO.**
Nenhuma regra aqui vale como contrato aprovado antes de o usuário decidir e
de a seção correspondente entrar em `nuvem/REGRAS_MODULACAO_BLOCOS.md`.

| Campo | Valor |
|---|---|
| Missão | Auditoria paralela de apoio ao PR [#42](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/42) |
| Branch | `claude/tender-carson-0t631s` |
| Base | `55e990d962ed22ae1021f0d335db197607bddda1` (= `origin/main` no fetch de 2026-09-15) |
| Alvo auditado | `origin/claude/butanta-modulation-physical-fixes` @ `93dc0c2` (PR #42, draft) |
| Escopo | somente leitura + relatório. Sem MCP, sem Revit, sem código de motor. |
| Arquivos criados | só `docs/auditoria/**` (nenhum arquivo do PR #42 é tocado) |

## 0. O que esta auditoria NÃO fez

- Não alterou `nuvem/core/**`, `tests/**`, `benchmark/**`, `nuvem/benchmark/**`,
  `nuvem/REGRAS_MODULACAO_BLOCOS.md` nem `docs/PROJECT_STATUS.md`.
- **Não reconciliou `PROJECT_STATUS.md` nem criou checkpoint em
  `docs/checkpoints/`**, como o `CLAUDE.md` normalmente exige: esses dois
  arquivos estão sendo editados pela sessão principal no PR #42 e a instrução
  explícita desta missão é não criar conflito. A reconciliação documental cabe
  à sessão principal, junto do fechamento do #42.
- Não registrou nada em `nuvem/REGRAS_MODULACAO_BLOCOS.md`. As regras
  inferidas na seção 5 são **candidatas**, para a sessão principal levar à
  REGRAS depois da decisão do usuário. Elas não vêm de uma correção do
  usuário; vêm de medição.
- Não abriu monitoramento, check-in nem polling (proibido pelo `CLAUDE.md`).
- Não fez merge.

**Validador documental / CI `check-status-doc` — falha conhecida e assumida.**

O gate falha nesta branch com quatro erros. Dois são de natureza diferente e
vale separar:

1. `docs/PROJECT_STATUS.md: main changed; fetch and reconcile before publishing`
   — **pré-existente na `main`, não causado por esta branch.** O
   `PROJECT_STATUS.md` da `main` declara `"main": "61d4f6c"`, mas a `main` real
   é `55e990d` (o merge do #41 não reconciliou o próprio painel). Enquanto isso
   não for corrigido, **qualquer** PR aberto a partir da `main` atual reprova
   neste gate, independente do conteúdo. O PR #42 reconcilia
   (`observed_utc` 2026-09-15, `main` → `55e990d`, #41 para `official`).
2. `delivery must reconcile docs/PROJECT_STATUS.md` + os dois de checkpoint —
   consequência de `validate.py`: **se qualquer arquivo mudou em relação à
   base, o painel e um checkpoint passam a ser obrigatórios.** Não há isenção
   para entrega documental nem para anexo de auditoria.

**Os quatro ficam deliberadamente abertos.** Satisfazê-los exige editar
`docs/PROJECT_STATUS.md` exatamente no bloco JSON que o PR #42 também edita
(`observed_utc`, `main`, fim de `official`, `candidates`) — conflito textual
quase certo entre os dois PRs, que é precisamente o que esta missão mandou
evitar. A ordem natural resolve sem custo: **#42 mescla primeiro e reconcilia o
painel; esta branch rebaseia na nova `main` e só então recebe painel e
checkpoint**, sem conflito. Até lá o vermelho é esperado e não indica defeito no
relatório.

> Nota de método: rodando `validate.py` num clone **raso**, aparece também
> `official revision is not integrated: 8a93a27a`. É **artefato do clone**
> (o objeto existe, o histórico não), não uma falha da `main` — a CI, com
> `fetch-depth: 0`, não reporta esse erro. Registrado aqui porque induz ao erro.

## 1. Método, proveniência e o que é reproduzível

Três fontes, com pesos muito diferentes. **A diferença importa mais que os
números** e está declarada em cada tabela adiante.

| # | Fonte | Versionada? | Reproduzível a partir do Git? |
|---|---|---|---|
| F1 | `docs/revit_reference_extraction/butanta-r08-lt/08_piece_opening_wall_relations.json` (3.625 peças humanas, peça a peça, 142 vãos, todos os pavimentos) | **sim** | **sim** |
| F2 | `docs/checkpoints/evidence/2026-09-15-butanta-physical-fixes/*.json` do PR #42 (comparador por lado de vão, métricas, execuções no Revit) | sim (o resultado) | **não** (depende de `target_1pav.clean.json` / `human_1pav.clean.json`, que **não estão no Git**) |
| F3 | `nuvem/REGRAS_MODULACAO_BLOCOS.md` + seções novas do PR #42 | sim | — (normativo/documental) |

Para F1 escrevi um levantamento próprio, que roda só com o repositório:

```
python3 docs/auditoria/evidencia/human_pier_survey.py
```

**Correção metodológica que muda resultado.** Agrupar as peças humanas por
`(parede, fiada, vão)` junta os **dois lados** do vão numa sequência só e
produz padrões falsos — por exemplo `B39+C04+C04+B39` (18 ocorrências), que
parece um par de pastilhas encostadas e na verdade são duas pastilhas em
pilaretes **opostos**, com o vão inteiro entre elas. O levantamento acima
quebra as sequências em **corridas contíguas** (junta ≤ 1,6 cm) antes de
contar. Todos os números humanos deste relatório usam corrida contígua.

**Limites de F1, para não superinterpretar:** cobre só peças relacionadas a
abertura (3.625 de 65.747); não serve para meio de parede longe de vão nem
para amarração L/T/X; inclui pavimentos clonados; **não tem campo de
espelhamento**, então a orientação do vazado menor do B34 não é reconstruível
por ali com confiança (ver 2.1). Vale o `REVIEW_2026-09-10.md`.

## 2. Classificação das 10 categorias

Antes da tabela, o limite mais importante da auditoria:

> **Não existe dump peça a peça do solver versionado no repositório.** O PR #42
> publica agregados (`revit_runs_summary.json`, `metrics_summary.json`) e o
> comparador por lado de vão, mas não as peças. Por isso **cinco das dez
> categorias não têm contagem própria** — e dizer um número para elas seria
> inventar. Está marcado caso a caso.

| # | Categoria | Casos (solver) | Humano | Fonte | Situação |
|---|---|---|---|---|---|
| 1 | B34 desalinhado entre fiadas | **336** (lote final) | 41 | F2 | aberto, resíduo pede mudança de POSIÇÃO |
| 2 | B34+B19 onde B54 deveria dominar | **sem contagem** | — | — | **hipótese não confirmada** (ver 2.2) |
| 3 | B19 no meio de parede | **sem contagem direta**; proxy: 3 paredes `bond_reproved` | 0 acima/abaixo de vão | F1/F2 | aberto, sem medição |
| 4 | C09+C09 lado a lado | **22** (run1) | **0** em 1.866 corridas | F1/F2 | aberto, deliberadamente não fundido |
| 5 | C09+C04 / clusters de especiais | **161** (136+25, run1); C04+C04 7→0 | **0** em F1; 97 em F2 | F1/F2 | aberto + **baseline humano em conflito** (ver 2.5) |
| 6 | T com B54 mal resolvido | **sem contagem** | — | — | sem evidência nesta missão |
| 7 | B34 acima/abaixo de abertura | **sem contagem** | **0** na 1ª fiada (602/602 e 395/395) | F1 | regra humana clara, solver não medido |
| 8 | Canaleta desalinhada | **0** | — | F2 | **fechado** no lote final |
| 9 | Peças pequenas sem apoio | **0** | 7 a 9 | F2 | **fechado — e mais rígido que o humano** |
| 10 | Diferenças humano × solver | **51 de 88 lados** SOLVER_WORSE | — | F2 | aberto, é o guarda-chuva das outras |

### 2.1 — Categoria 1: vazado menor do B34

**Geometria física.** B34 tem células assimétricas: vazado menor em X local
`[-14,5; -3,75]` (10,75 cm), vazado maior `[-1,25; 14,5]`. B54 tem vazado
central `[-6,25; 6,25]`. B39 e B19 são simétricos — não têm vazado menor.
A regra 52 exige que a peça vazada da fiada vizinha ofereça, sobre o centro do
vazado menor do B34, outro vazado menor (B34) ou o central do B54.

**Padrão do solver.** Antes: orientação fixa por convenção → 2.460 violações.
Depois do passe individual + giro em par: 336 no lote real do Revit
(264 na bancada offline).

**Padrão humano e causa.** O humano resolve por **orientação** (giro de 180°),
não por posição; em corridas de B34 deslocadas 20 cm entre fiadas, o B34 de uma
fiada fica girado em relação ao da outra.

**Ressalva de auditoria — a evidência dos 2.500/2.541 não é reauditável.**
Ela vem de uma extração MCP não versionada. Tentei reproduzi-la sobre F1 e
**o resultado é inconclusivo, não contrário**: só 27 pares caem no escopo
(801 vizinhos ausentes, porque F1 só tem peças de vão), e sem campo de
espelhamento a reconstrução da orientação não é confiável. **Não use meu
número; use o do PR #42 sabendo que ele não é reauditável hoje.**

### 2.2 — Categoria 2: B54 × B34+B19 — hipótese NÃO confirmada

Esta era a hipótese mais forte da missão e a medição **não a sustenta como
defeito sistêmico**:

| Proporção de B54 | Humano | Solver (lote final) |
|---|---|---|
| B54 / total de peças | 1.614 / 65.747 = **2,45%** | 260 / 9.088 = **2,86%** |
| B54 / B39 | 0,051 | 0,052 |

O solver usa B54 em proporção **igual ou ligeiramente maior** que o humano.
Não há déficit de B54 a corrigir. Em vão de 54 cm o humano prefere B54
(90%) a B19+B34 (8%) — a preferência existe (ver 3.1) —, mas nada na
evidência disponível mostra que o solver a esteja violando em volume.
**Recomendação: não abrir frente de trabalho aqui sem antes medir**
(precisa do dump de peças, hoje inexistente).

### 2.3 — Categoria 3: B19 no meio de parede

Sem medição. F1 não cobre meio de parede longe de vão; o PR #42 não publica
contagem. O que existe: `HALF_BLOCK_NEAR_TIE` (rede de segurança da regra #2),
`repair_b19_residual_fill` com a exceção aprovada de 15–20 cm (seção 35), e
**3 paredes `bond_reproved`** no lote final — cuja causa não está detalhada na
evidência. Essas 3 paredes são o próximo passo barato e concreto: são poucas,
são nomeáveis, e o auditor já as reprova.

O que F1 mostra e é utilizável: dos 289 B19 relacionados a vão, **289 estão na
jamba** — zero acima do vão, zero abaixo do peitoril. E em vão de 59 cm o
humano prefere `B39+B19` (96%) a `B54+C04` (4%), ou seja, **na face do vão o
B19 não é "último recurso": é a segunda escolha depois do B39**. O rótulo
"último recurso" da tabela do catálogo (seção 1) é enganoso fora do contexto
de nó — a jamba é ponta aberta, e ali o B19 é regra, não exceção.

### 2.4 — Categoria 4: C09+C09

**Geometria.** C09 + junta + C09 = 9+1+9 = 19 cm, ocupando 20 cm de grade —
**exatamente um B19**. Substituição de contorno idêntico.

**Humano: zero.** Em 1.866 corridas contíguas de F1 não há **nenhum** par
especial+especial encostado (H2 do levantamento). Em vão de 19 cm o humano usa
B19 em 173 de 185 corridas (94%); o resto é meia-canaleta e bloco cortado.

**Solver: 22** (run1). O PR #42 **deliberadamente não fundiu**, e a decisão
está certa: a guarda de ponta aberta da REGRA CRÍTICA #2 impede fazer nascer um
B19 no meio de um trecho só porque a aritmética fecha. **O erro não é a falta
da fusão — é o trecho ter sido resolvido com dois compensadores.** Fundir
mascararia a causa. Ver 4.2.

### 2.5 — Categoria 5: clusters de especiais — o achado central

Este é o resultado mais forte da auditoria, e é um **invariante sem exceção**:

> **Em 1.426 corridas contíguas de pilarete do projeto humano, NENHUMA tem dois
> ou mais compensadores/pastilhas. 1.296 têm zero, 130 têm exatamente um.
> Em 1.866 corridas contíguas (todas as posições), há ZERO pares
> especial+especial encostados.**
>
> **E quando o pilarete tem mais de uma peça, o especial está SEMPRE na face
> que toca o vão: 107 de 107 casos. Nunca na ponta oposta, nunca no meio.**
> (As outras 23 corridas com especial são de peça única — `C09` sozinho 18×,
> `C04` sozinho 3×, `C04` cortado 2× — onde a posição não se aplica.)

Não é tendência, é invariante: 0 exceções em 1.426 e 0 em 107.

Do lado do solver (run1): 136 `C09+C04`, 25 `C04+C09`, 22 `C09+C09` — 183 pares
encostados. E o comparador mostra lados de vão com 21, 22 e 23 especiais em
12 fiadas, ou seja **quase dois por fiada**; o humano nunca passa de 14 em
12 fiadas (86 dos 88 lados ficam em ≤ 12 = no máximo um por fiada).

**Conflito de baseline humano que precisa ser resolvido.** O
`metrics_summary.json` registra `adjacent_specials_touching` humano
`{"C04+C09": 97}`. F1 dá **zero**. As duas medições não são do mesmo recorte
(F2 = 34 paredes do 1º pavimento, todas as peças; F1 = peças de vão, todos os
pavimentos), então **não se refutam** — mas o número 97 **não tem script
versionado** no `_scripts/` do checkpoint, e nenhum dos dois pode ser
reproduzido pelo outro. Enquanto isso não fechar, o alvo "reduzir especiais
adjacentes" está sem régua confiável. **Isto é uma pendência de evidência, não
de código.**

### 2.6 — Categoria 6: T com B54

Sem evidência nesta missão. O corpus F1 não carrega rótulo de nó L/T/X, e o
PR #42 não mede encontros. A seção 5 da REGRAS continua sendo a única fonte.
O `REVIEW_2026-09-10.md` é explícito: o acervo BUTANTÃ **não é prova de
amarração L/T/X**. Não inventar contagem aqui.

### 2.7 — Categoria 7: B34 acima/abaixo de abertura

Regra humana medida, limpa, com n alto:

| Posição | Canaleta | B39/B34/B54/B19 | C09/C04 | C09 deitado | n |
|---|---|---|---|---|---|
| 1ª fiada **acima** do vão | 572 (95,0%) | **0** | **0** | 30 | 602 |
| 1ª fiada **abaixo** do peitoril | 392 (99,2%) | **0** | **0** | 0 | 395 |
| 2ª fiada acima | 501 (88,4%) | 35 | 0 | 31 | 567 |
| 2ª fiada abaixo | 0 | 396 | 15 | 0 | 411 |

**A primeira fiada que fecha um vão nunca é alvenaria comum**: é canaleta
(verga/contraverga) ou, em vão pequeno, uma fiada de compensador deitado.
Nenhum B34, nenhum B19, nenhum especial. Isso casa com BP01 (47/47 portas) e
BP02 (89/89 peitoris). Da segunda fiada em diante a alvenaria comum volta, e
aí o B34 aparece normalmente (63 abaixo, 12 acima).

Sem contagem do solver — mas `CHANNEL_INVADES_OPENING = 0`,
`MISSING_REQUIRED_CHANNEL = 0` e 40/40 + 23/23 canaletas casadas sugerem que a
1ª fiada está correta no lote final. **O que falta medir é a 2ª fiada.**

### 2.8 — Categorias 8 e 9: fechadas (com uma ressalva)

Categoria 8 (canaleta desalinhada): **fechada**. No lote final,
`CHANNEL_WRONG_COURSE`, `EXTRA_CHANNEL`, `CHANNEL_ORPHAN_PIECE`,
`CHANNEL_COLLISION`, `CHANNEL_INVADES_OPENING`, `CHANNEL_OPENING_OVERCUT` e
`MISSING_REQUIRED_CHANNEL` são todos 0, com 40/40 superiores e 23/23
inferiores.

Categoria 9 (peças sem apoio): **fechada — e passou do humano.** Solver 0,
humano 7 a 9 na mesma régua. O humano tolera peça sem apoio em pilarete de
passagem e topo de vão. Ver risco de overfitting OV-1: **zero não é o alvo
correto**; transformar isso em gate bloqueante seria exigir do solver mais
rigor do que o projeto de referência tem.

### 2.9 — Categoria 10: humano × solver, o quadro geral

88 lados de vão, 12 fiadas, 60 cm a partir da jamba:

| Veredito | n |
|---|---|
| SOLVER_WORSE | 51 |
| PHYSICALLY_EQUIVALENT | 25 |
| SOLVER_BETTER | 10 |
| VALID_ALTERNATIVE | 2 |

O diagnóstico decisivo está **dentro** dos 51 SOLVER_WORSE:

- **40 dos 51 (78%) têm cobertura IGUAL OU MAIOR que a do humano.** Só 11 têm
  cobertura menor.
- Nesses 40, a diferença é exclusivamente o número de especiais.
- Mediana da diferença: **+6 especiais por lado**, com cobertura idêntica.
- Total: humano **354** especiais para 58.342 cm cobertos; solver **612** para
  57.982 cm. **+73% de especiais para 0,6% menos cobertura.**
- Humano usa **zero** especiais em 42 dos 88 lados (48%); o solver, em 16 (18%).

> **Conclusão: o problema restante não é geométrico nem de cobertura. É de
> COMPOSIÇÃO. O solver preenche o mesmo espaço físico com muito mais peças
> pequenas.**

## 3. Matriz de dominância de peças

Grade: peça + 1 cm de junta. B39→40, B34→35, B54→55, B19→20, C09→10, C04→5
(`PIER_MODULE_CM = 5`).

### 3.1 — Dominância medida por vão ocupado (projeto humano, corridas de pilarete)

Esta é a tabela pedida, construída a partir do que o humano **de fato** assenta
em cada comprimento, não de dedução:

| Vão | n | Escolha humana dominante | Alternativas usadas | Veredito |
|---|---|---|---|---|
| 9 cm | 18 | **C09** 100% | — | C09 domina C04+C04 (**zero** ocorrências) |
| 19 cm | 185 | **B19** 94% | K19 3%, B19 cortado 2% | B19 domina C09+C09 (**zero** ocorrências) |
| 34 cm | 395 | **B34** 91% | K34 9% | — |
| 39 cm | 603 | **B39** 84% | **B34+C04 6%**, B19+B19 0,5% | preferência, **não** proibição |
| 44 cm | 54 | C04+B39 / B39+C04 100% | — | não há solução sem especial |
| 49 cm | 12 | C09+B39 100% | — | não há solução sem especial |
| 54 cm | 39 | **B54** 90% | **B19+B34 8%** | preferência, **não** proibição |
| 59 cm | 111 | **B39+B19 / B19+B39 96%** | **C04+B54 4%** | preferência forte |

### 3.2 — Respostas diretas às perguntas da missão

**B54 domina B34+B19?** — **Sim, como preferência forte; não como proibição.**
55 de grade dos dois lados: contorno idêntico, cobertura idêntica. B54 é 1 peça
contra 2, não gasta o B19 (peça de fechamento) e **remove um B34, ou seja,
remove uma restrição da regra 52 de graça**. Evidência humana: 35 × 3 (90% × 8%)
em vão de 54 cm. As 3 exceções humanas provam que há contexto legítimo —
provavelmente junta exigida pela amarração, ou B54 reservado para nó. Logo:
**preferir B54 sempre que ele couber sem invadir vão, sem colidir, sem piorar
junta e sem consumir uma peça de nó reservada — mas permitir B34+B19 quando um
desses gates o exigir.** Nunca proibir.

**B19 × C09+C09** — **C09+C09 deve ser PROIBIDO.** 20 de grade nos dois casos,
zero ocorrências humanas em 1.866 corridas, e a regra #2 já proíbe dois
compensadores em sequência. **Mas a correção não é fundir em B19** (a guarda de
ponta aberta existe por um bug real de 2026-08-25). O par é sintoma: o trecho
foi mal resolvido. Ver 4.2.

**B34 × B39** — **não são substituíveis** (34 ≠ 39) e as proporções já batem
com o humano: B34/B39 = 0,50 no humano contra 0,45 no solver. **Não é defeito.
Não mexer.**

**B34+B34 × B39+especial** — **B34+B34 domina.** 70 de grade contra
B39+B19+C09 (3 peças, 1 especial, 1 B19). Já é a regra 5b da seção 2, com
evidência humana registrada (1.615 B34 contra 242 C09 no pavimento). Confirmado,
nada a fazer.

**C09 × C04+C04** — **C04+C04 deve ser PROIBIDO.** 10 de grade nos dois casos,
zero ocorrências humanas. Já implementado no PR #42
(`fuse_adjacent_equal_compensators`). Aqui a fusão é segura porque o alvo é um
compensador, não um B19 — não há guarda de ponta aberta em jogo.

### 3.3 — Princípio geral, com o contraexemplo que o limita

O princípio tentador é: *"se uma peça do catálogo cobre exatamente o mesmo vão
que duas peças, use a peça única — fundir só remove uma junta, e remover junta
nunca cria coincidência de junta, logo nunca piora o prisma."*

O raciocínio geométrico está certo. **Mas o humano o contraria em três lugares
medidos:** `B34+C04` onde `B39` cobre os mesmos 39,0 cm (37 casos), `B19+B19`
onde `B39` cobre os mesmos 39,0 cm (3 casos), e `B19+B34` onde `B54` cobre os
mesmos 54,0 cm (3 casos).

Ou seja: o humano às vezes **paga uma junta a mais de propósito** — quase certo
que para desencontrar junta com a fiada vizinha, ou porque a peça grande está
reservada a um nó. Portanto:

> **Fusão automática só é segura quando o alvo é um compensador
> (C04+C04 → C09). Em todo caso que produza bloco vazado (B39, B19, B54), a
> troca é PREFERÊNCIA sujeita aos gates de amarração e prisma, nunca
> substituição cega.**

## 4. Matriz de prioridade física — confirmação e correção

### 4.1 — Ordem proposta pela missão × ordem que a evidência sustenta

| Proposta | Auditada | Item | Por quê |
|---|---|---|---|
| 1 | **1** | abertura | confirmado — invariante geométrico |
| 2 | **2** | colisão | confirmado — invariante geométrico |
| 7 | **3 ⬆** | **CHANNEL** | **sobe 4 posições**: BP01 47/47, BP02 89/89, 1ª fiada acima 95% e abaixo 99,2% canaleta com **zero** alvenaria comum. É requisito estrutural do vão, não otimização. `MISSING_REQUIRED_CHANNEL` já é bloqueante. |
| 3 | **4 ⬇** | apoio | desce 1 e **muda de natureza**: o humano tem 7–9 peças sem apoio. Alvo é "≤ humano", não zero (ver OV-1). |
| 4 | **5** | amarração (L/T/X) | confirmado — mas degrada (11.10: amarração que não cabe fica sem modular), logo abaixo dos invariantes |
| 5 | **6** | prisma / junta a prumo | confirmado |
| 9 | **7 ⬆** | **densidade de especiais: ≤ 1 por trecho contíguo + sempre na face do vão** | **sobe 2 posições e vira regra dura**: 0 exceções em 1.426 corridas e 0 em 107 posições. Já é normativo (regra #2). |
| 6 | **8 ⬇** | vazado menor do B34 | **desce 2 posições**: o humano **viola** essa regra 41 vezes, e **nunca** viola a densidade de especiais. Exceção medida vence exceção zero. |
| 8 | **9** | fragmentação / contagem total de especiais | confirmado como **otimização** |

### 4.2 — A correção mais importante: "especiais" são duas coisas diferentes

A lista da missão tem um único item "especiais", em último lugar. A evidência
separa dois critérios com forças opostas:

- **Densidade e posição** (≤1 por trecho contíguo; sempre na face do vão) —
  **regra dura**, 0 exceções humanas. Tem de subir para o nível 7.
- **Total de especiais na parede** (500 humano × 808 solver) — **otimização**,
  fica no nível 9.

Isso muda o alvo de trabalho. Perseguir o **total** foi exatamente o que a
seção 55 do PR #42 tentou em cinco variantes, e **todas trocaram erro**
(especiais 835→550 ao custo de violações de B34 264→476). Perseguir
**densidade e posição** é outro problema, com alvo verificável (zero) e sem
troca conhecida.

### 4.3 — Por que a ordem de tiers não resolve o problema

O `_pier_ordered_layout` já tem a ordem certa (seção 2) e os rácios de peça já
batem com o humano (3.2). O defeito está **onde** essa ordem é aplicada. A
própria seção 55 do PR #42 mede a causa raiz:

> a modulação contínua põe peças no trecho inteiro entre dois nós, atravessando
> o vão; o recorte derruba o que invade o vão e o reparo refaz **só a sobra
> junto da jamba** — e *"o próprio solver de pilarete, chamado sobre o pilarete
> inteiro, devolve exatamente a solução humana"*.

E as cinco variantes medidas da seção 55 são **todas dominadas por Pareto pelo
humano** (humano: 500 especiais **e** 41 violações; melhor variante:
550 especiais **e** 476 violações). Quando toda a fronteira medida é dominada
pela referência, o problema não é escolher o ponto certo da fronteira — **é que
o espaço de busca está errado**. Nenhuma reordenação de prioridade alcança o
humano daqui.

## 5. Regras inferidas (candidatas, com rótulo de confiança)

Formato do `CLAUDE.md`. **Nenhuma está implementada; nenhuma está na REGRAS.**

| ID | Regra | Confiança | Como foi descoberta |
|---|---|---|---|
| **A-1** | Nunca dois compensadores/pastilhas encostados numa mesma corrida contígua | **REGRA OBRIGATÓRIA** (já é a regra #2; agora com n) | 0 em 1.426 corridas de pilarete; 0 pares em 1.866 corridas (F1) |
| **A-2** | Em pilarete de mais de uma peça, o especial fica **sempre** na face que toca o vão, nunca na ponta oposta nem no meio | **REGRA OBRIGATÓRIA** | 107 de 107 (F1) |
| **A-3** | A 1ª fiada acima do vão e a 1ª abaixo do peitoril não recebem alvenaria comum nem especial: são canaleta, ou fiada de compensador deitado em vão pequeno | **REGRA OBRIGATÓRIA** | 602/602 e 395/395 sem bloco comum (F1); BP01 47/47, BP02 89/89 |
| **A-4** | B19 nunca acima do vão nem abaixo do peitoril | **REGRA OBRIGATÓRIA** | 289/289 dos B19 de vão estão na jamba (F1) |
| **A-5** | Em vão de 54 cm, preferir B54 a B34+B19, salvo gate de amarração/prisma/reserva de nó | **PREFERENCIAL** | 35 × 3 (F1) |
| **A-6** | Em vão de 59 cm, preferir B39+B19 a B54+C04 | **PREFERENCIAL** | 107 × 4 (F1) |
| **A-7** | Em vão de 39 cm, preferir B39; B34+C04 é **exceção legítima**, não erro | **EXCEÇÃO PERMITIDA** | 509 × 37 (F1) |
| **A-8** | Fusão automática de duas peças numa só é segura quando o alvo é compensador; quando o alvo é bloco vazado é preferência sujeita a gate | **PREFERENCIAL** | dedução geométrica + 43 contraexemplos humanos (3.3) |
| **A-9** | Na jamba, o B19 não é último recurso: é a 2ª escolha depois do B39 (a face do vão é ponta aberta) | **PADRÃO OBSERVADO** | 289 B19 na jamba; domina 59 cm com 96% (F1) |
| **A-10** | Peça sem apoio não é zero no humano: o alvo é ≤ 9 em 34 paredes, não 0 | **PADRÃO OBSERVADO** | humano 7–9 na mesma régua (F2) |

## 6. Exemplos humanos representativos

- **Pilarete limpo (o caso normal, 91%):** uma peça só — `B39` (509×),
  `B34` (358×), `B19` (173×). O humano **não compõe** pilarete quando não
  precisa.
- **Pilarete com um especial (9%):** `B39+C04` / `C04+B39` (54× em 44 cm),
  `C09+B39` (12× em 49 cm) — sempre o especial contra a face do vão.
- **O caso que o solver erra (seção 55, medido):** porta com jamba a 75 cm de
  um nó B54. Solver: `B19+C04+B39+C09` numa fiada e `B39+C04+B39+C09` na outra
  — 2 especiais por fiada, ambos longe da face do vão. Humano: `B39+B34` e
  `B19+B39+B34` — **zero especiais**. Viola A-1 e A-2 simultaneamente.
- **Exceção legítima que não pode virar erro:** `B34+C04` em 39 cm (37×), onde
  `B39` cabe exato. O humano paga uma junta a mais de propósito.
- **Vão pequeno:** janela de 66 cm resolvida com 5 compensadores **deitados**
  sobre o vão (`C09D`), sem canaleta — mecanismo distinto, não confundir com
  compensador vertical em sequência.

## 7. Riscos de overfitting

| ID | Risco | Mitigação |
|---|---|---|
| **OV-1** | **Transformar apoio = 0 em gate bloqueante.** O humano tem 7–9. Zero é mais rígido que a referência. | manter `physical_support` como validador de leitura; alvo "≤ humano" |
| **OV-2** | **Ruído determinístico.** 39 peças mudam com ruído de 1,4e-14 ft; inversão de pontas e permutação de ordem mudam ~200 peças. **Diferenças abaixo de ~40 peças não são atribuíveis a uma mudança de regra.** Ex.: 264 × 261 violações de B34 (seção 55) está dentro dessa faixa. | não decidir regra por delta pequeno; fixar sentido/ordem antes de comparar |
| **OV-3** | **Uma régua só.** Tudo vem do 1º pavimento do BUTANTÃ (34 paredes, 44 vãos). Pavimentos clonados inflam n (REVIEW). TORRE EASY não pode ser transportado (REVIEW). | rotular toda regra como BUTANTÃ até uma 2ª obra confirmar |
| **OV-4** | **Números não reauditáveis.** Os 2.500/2.541 da regra 52 e os 97 `C04+C09` humanos não têm script versionado. A regra 52 **já está implementada** apoiada num deles. | versionar os dumps ou um resumo peça a peça |
| **OV-5** | **Regra do BUTANTÃ movendo benchmark legado.** A fusão C04+C04 mudou TP1 936→881 e TGD V2 472→464. | toda regra nova nascida do BUTANTÃ precisa do delta legado declarado |
| **OV-6** | **Otimizar o total de especiais.** É a métrica que a seção 55 provou trocar erro. | usar densidade+posição (A-1/A-2), não o total |
| **OV-7** | **Contagem de run1 usada como estado atual.** As adjacências (22 C09+C09, 136 C09+C04) são do run1 (`4823114`), não do lote final (`23dfcb7`). | remedir no lote final antes de dimensionar o trabalho |

## 8. Recomendações para a sessão principal

Em ordem de retorno sobre esforço.

**R1 — Não perseguir mais o total de especiais por ajuste de tier.** A seção 55
já provou que troca erro, e 4.3 mostra por quê: toda a fronteira medida é
dominada pelo humano. Fechar a seção 55 como **pendência de escopo de reparo**,
não como pendência de prioridade normativa.

**R2 — Trocar a régua antes de trocar o motor.** Adotar A-1 e A-2
(corridas com ≥2 especiais; especiais fora da face do vão) como métrica de
acompanhamento. As duas valem **zero** no humano, são verificáveis sem
julgamento e não têm troca de erro conhecida. O par 500 × 808 não é régua: é
sintoma.

**R3 — Remedir as adjacências no lote final.** Os números de cluster são do
run1. Sem isso não dá para dimensionar as categorias 4 e 5 (OV-7).

**R4 — Não fundir C09+C09 em B19.** A guarda de ponta aberta está certa.
Instrumentar como contador de sintoma apontando para o trecho mal resolvido.

**R5 — Fechar o conflito de baseline dos especiais adjacentes** (97 × 0,
seção 2.5) antes de abrir frente de trabalho na categoria 5.

**R6 — Versionar o dump de peças** (`target_*.clean.json` / `human_*.clean.json`,
ou um resumo peça a peça). Hoje a bancada do PR #42 não roda a partir do Git, e
cinco das dez categorias não têm contagem por causa disso. É o maior bloqueio
estrutural da missão.

**R7 — Investigar as 3 paredes `bond_reproved`.** São poucas, nomeáveis, e o
auditor já as reprova. É a única pista concreta da categoria 3.

**R8 — Não mexer na ordem de tiers nem nos rácios de peça.** B34/B39 e B54/B39
já batem com o humano (2.2, 3.2). Mudar ali é risco sem retorno demonstrado.

**R9 — Medir a 2ª fiada acima/abaixo do vão** (categoria 7). A 1ª está
comprovadamente correta; a 2ª nunca foi medida no solver.

**R10 — Se a regra 52 for revista, ela é que cede** — não a densidade de
especiais (4.1). O humano viola a 52 quarenta e uma vezes e a A-1 nenhuma.

## 9. Conflitos entre regras (registrados, não resolvidos)

| ID | Conflito | Leitura da auditoria |
|---|---|---|
| **CF-1** | Regra 52 (vazado menor) × redução de especiais (seção 55) | 52 cede: 41 exceções humanas × 0 exceções de A-1. **Decisão do usuário.** |
| **CF-2** | Guarda de ponta aberta da regra #2 × fusão C09+C09→B19 | não fundir; corrigir a montante (R4) |
| **CF-3** | Seção 51.3 (CHANNEL ≡ legado fora das corridas) × 30.9 (tolerâncias com tentativa) | já rompido onde a tolerância atua; o PR #42 registra. A "seleção global" romperia mais — mais uma razão para não integrá-la |
| **CF-4** | Catálogo chama B19 de "último recurso" × B19 domina 59 cm na jamba (96%) | não há contradição real (a jamba é ponta aberta), mas o rótulo induz erro — vale nota na seção 1 da REGRAS |
| **CF-5** | Apoio físico = 0 × humano 7–9 | o solver está mais rígido que a referência (OV-1) |
| **CF-6** | A-3 (1ª fiada do vão é canaleta) × decisão F (cinta de topo) e 51.8, ambas pendentes | A-3 é sobre o vão, não sobre o topo da parede; não confundir |

## 10. Regras que podem virar teste permanente

Ordenadas por confiança. Todas são verificáveis sobre o resultado do solver,
sem Revit.

| # | Teste | Regra | Alvo | Confiança |
|---|---|---|---|---|
| **T1** | nenhuma corrida contígua tem ≥2 compensadores/pastilhas | A-1 | 0 | **alta** — 0/1.426 |
| **T2** | todo especial de pilarete encosta na face do vão ou numa ponta aberta | A-2 | 0 violações | **alta** — 107/107 |
| **T3** | não existe `C09+C09` encostado | A-1 | 0 | **alta** — 0 humano |
| **T4** | não existe `C04+C04` encostado (já coberto pela fusão da seção 54) | A-1 | 0 | **alta** — já implementado |
| **T5** | 1ª fiada acima do vão e 1ª abaixo do peitoril sem B39/B34/B54/B19/C09/C04 | A-3 | 0 | **alta** — 997/997 |
| **T6** | nenhum B19 acima do vão nem abaixo do peitoril | A-4 | 0 | **alta** — 289/289 |
| **T7** | varredura: em trecho livre de 54 cm sem reserva de nó, a solução é B54 e não B34+B19 | A-5 | preferência | média |
| **T8** | varredura: em trecho livre de 59 cm, a solução é B39+B19 e não B54+C04 | A-6 | preferência | média |
| **T9** | régua de regressão: corridas com ≥2 especiais ≤ 0 e especiais fora da face ≤ 0 | A-1+A-2 | 0 | **alta** |
| **T10** | `B34+C04` em 39 cm **não** é reportado como erro | A-7 | proteção contra falso positivo | média |

T1 a T6 e T9 são hard gates candidatos. T7, T8 e T10 são testes de varredura
de preferência, no mesmo estilo do
`test_regra_geral_fileira_de_b34_so_quando_nem_um_b34_nem_um_compensador_fecham`.

**T10 merece atenção**: é o teste que impede uma regra nova de criar falso
positivo em cima de um padrão humano legítimo. Sem ele, A-7 vira erro.

## 11. Resumo em uma página

1. O lote final do PR #42 **resolveu** buracos (215→10), apoio (116→0),
   sub-preenchimento de janela (11→0), canaleta (0 erros) e C04+C04 (7→0).
2. O que sobrou **não é geometria: é composição.** Em 78% dos lados de vão
   piores que o humano, a cobertura é igual ou melhor — só o número de peças
   pequenas é maior. +73% de especiais para 0,6% menos cobertura.
3. O invariante humano mais forte da auditoria: **nunca dois especiais na mesma
   corrida (0/1.426) e o especial sempre na face do vão (107/107)**.
4. A prioridade proposta na missão precisa de **três correções**: CHANNEL sobe
   de 7 para 3; densidade de especiais sobe de 9 para 7 e vira regra dura;
   vazado menor do B34 desce de 6 para 8 (o humano o viola 41 vezes e nunca
   viola a densidade).
5. Dominância confirmada com evidência: **C09 sobre C04+C04** e **B19 sobre
   C09+C09** (proibições); **B54 sobre B34+B19** e **B39+B19 sobre B54+C04**
   (preferências). **B34 × B39 não é defeito** — as proporções já batem.
   **B54 não está em déficit** — o solver usa mais que o humano.
6. Reordenar prioridade **não alcança o humano**: as cinco variantes da seção 55
   são todas dominadas por Pareto pela referência. O espaço de busca é que está
   errado — o reparo refaz a sobra junto da jamba, não o pilarete inteiro.
7. Maior bloqueio estrutural: **não há dump de peças do solver versionado.**
   Cinco das dez categorias ficaram sem contagem por causa disso.

---

**Evidência reproduzível:** [`evidencia/human_pier_survey.py`](evidencia/human_pier_survey.py)
(roda só com o repositório).
**Fontes:** `docs/revit_reference_extraction/butanta-r08-lt/` (F1),
`docs/checkpoints/evidence/2026-09-15-butanta-physical-fixes/` no PR #42 (F2),
`nuvem/REGRAS_MODULACAO_BLOCOS.md` (F3).
