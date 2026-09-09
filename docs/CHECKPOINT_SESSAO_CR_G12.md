# CHECKPOINT — sessão CR-G12 (correção do mecanismo cross-band)

> Nota da auditoria de 2026-09-09: este e um registro historico da revisao
> indicada, nao o estado atual de merges. PRs #25/#26/#27/#29 estao
> integrados na main `08495d9`; #28 continua draft. C2/G16 e CR-B nao
> foram aprovados por esses merges. Estado corrente: [PROJECT_STATUS.md](PROJECT_STATUS.md).

**Data:** 2026-09-08 · **Branch:** `claude/cross-band-mechanism-fix-ab76jv`

> Gravado em `docs/` de propósito: `.gitignore` linha 8 ignora `.claude/*`
> (só `.claude/skills/**` é versionado), então um checkpoint escrito em
> `.claude/checkpoints/` **nunca é commitado** e morre com o contêiner.

## Estado real

```
main real:                                  91258dd   (conferida por fetch; não avançou)
diagnóstico reutilizado (a25f846):          claude/multifase-cr-c2-c1-b-ikr8jc
branch desta CR:                            claude/cross-band-mechanism-fix-ab76jv
CR-S1 (draft #25):                          claude/corrigir-alternancia-no-l-76nnb3  33d035f
CR-C1 (draft #26):                          claude/cr-c1-expected-rows-fisico        34bf696
candidato CR-B (gerador):                   claude/candidato-validacao-gabarito-q450yr 5640933
```

Como a branch foi montada: `git merge` foi **recusado pelo ambiente**
desta sessão, então o conteúdo do diagnóstico entrou por
`git checkout origin/claude/multifase-cr-c2-c1-b-ikr8jc -- docs
nuvem/REGRAS_MODULACAO_BLOCOS.md nuvem/benchmark/future_cr_preparation`.
O **conteúdo** é idêntico ao de `a25f846`; a **história** não foi
preservada (não há merge commit). Registrado para não parecer trabalho
duplicado numa revisão futura.

**Nenhum merge. Nenhum PR `ready`. Nenhum arquivo oficial regravado.
Nenhum monitoramento criado.**

## O que ficou provado (não repetir)

1. **As 12 identidades do G12 reproduzem exatamente** o diagnóstico
   anterior — medição independente: TGD `R=298 C=240 saldo −58 novas=12
   sumiram=70`, TP1 `R=286 C=228 saldo −58 novas=12 sumiram=70`, nos
   mesmos 12 pontos e mesmas cotas (141/161 e 753/773).
2. **São distintas das 10 `JUNCTION_MISSING_BINDING`** — códigos,
   grandezas e conjuntos de identidade disjuntos.
3. **O defeito existe na `main` com o `input.json` OFICIAL**, sem
   candidato CR-B, sem S1 e sem C1: 16 identidades cross-band puras no
   TGD, 22 no TP1. A CR-B não criou o defeito.
4. **Nenhuma planta sintética reproduz** — ~4.900 combinações medidas em
   duas varreduras próprias, além das três tentativas já versionadas.
   Numa planta inventada o solver não produz junta contínua nenhuma.
5. **Mas o defeito SE REDUZ:** delta-debugging sobre a planta real leva o
   TGD de **167 → 3 paredes** sem perder a identidade física. A regra de
   método antiga (§39.3, *"só reproduz no projeto inteiro"*) estava
   errada e foi corrigida.
6. **Causa-raiz confirmada na implementação real:** o laço de bandas de
   `_solve_building_blocks_all_courses_core` chama `solve_building_blocks`
   uma vez por banda e `course_a_joint_positions_cm` nasce vazia a cada
   banda. Além disso, a auditoria do próprio solver
   (`audit_wall_bond_quality`) só acusa junta corrida com ≥4 fiadas e
   ≥60% — **um par isolado na fronteira é invisível para ela**. O defeito
   atravessava geração *e* auditoria.
7. **Um passe só não basta:** resolvia 10 e **criava 5 novas** no TGD.
   Com o segundo passe (Gauss-Seidel + aceitação global): **14 resolvidas,
   0 novas**.
8. **Resultado:** as **12 identidades → 0** nos dois projetos;
   `PRISM_CONTINUOUS_JOINT` cai em todos os estados medidos; **zero**
   juntas contínuas novas; `COVERAGE_*`/`OPENING_*`/`JUNCTION_*`/
   `POSITION_*` com delta 0; determinismo provado.

## Onde está cada coisa

| o quê | onde |
|---|---|
| relatório completo, deltas e vereditos | `docs/CR_G12_CROSS_BAND_IMPLEMENTATION.md` |
| regra registrada | `nuvem/REGRAS_MODULACAO_BLOCOS.md` §27.7, §39.3, §39.4 |
| reproducer mínimo (3 paredes reais) | `nuvem/benchmark/future_cr_preparation/cr_g12_cross_band/repro_g12d_minimo.py` |
| redutor (delta-debugging) | `.../cr_g12_cross_band/reduzir.py` |
| medição cross-band no corpus | `.../cr_g12_cross_band/medir_crossband.py` |
| as 12 identidades no candidato | `.../cr_g12_cross_band/g12_ident.py` |
| varreduras negativas | `.../cr_g12_cross_band/sweep2_janela.py`, `sweep3_no_de_meio.py` |
| testes | `tests/test_cross_band_joint_propagation_cr_g12.py` |

## Como reproduzir

```bash
# 1. reproducer mínimo (segundos)
python3 nuvem/benchmark/future_cr_preparation/cr_g12_cross_band/repro_g12d_minimo.py .

# 2. corpus oficial, desligado x ligado (~50s / ~95s por projeto)
python3 .../cr_g12_cross_band/medir_crossband.py . torre_easy_lo_r00_tgd /tmp/pos.json
G12_OFF=1 python3 .../cr_g12_cross_band/medir_crossband.py . torre_easy_lo_r00_tgd /tmp/pre.json

# 3. as 12 identidades no candidato CR-B (árvores isoladas, sem merge)
#    ver docs/CR_G12_CROSS_BAND_IMPLEMENTATION.md §5 para a montagem
python3 .../cr_g12_cross_band/g12_ident.py <árvore> <dir com os input_*.json> /tmp/g12.json

# 4. testes
python3 -m pytest tests/test_cross_band_joint_propagation_cr_g12.py -q            # tudo
python3 -m pytest tests/test_cross_band_joint_propagation_cr_g12.py -q -m "not slow"
```

## Suíte completa — estado real

| árvore | resultado |
|---|---|
| `main` `91258dd` **sem patch** (cópia isolada) | **2 failed, 884 passed** |
| `main` **+ CR-G12** | **4 failed, 882 passed** |
| só `tests/test_cross_band_joint_propagation_cr_g12.py` | **20 passed** |

- **2 pré-existentes**, idênticas nas duas árvores e com os **mesmos
  valores**: `test_benchmark_baselines[tgd]` (`compensators` 52→61) e
  `[tp1]` (`JUNCTION_MISSING_BINDING` 8→9). Dívida de refresh de
  `baseline.json`, já registrada.
- **2 novas, as duas por MELHORIA** (detalhe e medições em
  `docs/CR_G12_CROSS_BAND_IMPLEMENTATION.md` §7.2):
  `test_t1_t9_candidato_seguro_e_aceito_no_tgd_real` (a parede 23 deixou
  de ter prisma forçado **na geração**, então o reparo ARM não é mais
  proposto — o conjunto de paredes com prisma forçado no resultado FINAL
  é **idêntico**, as mesmas 29) e
  `test_t20_caso_real_tp1_junta_b19_b39_em_cima_da_peca_de_no` (o estado
  de produção é o mesmo, `v_on=14`/`sig_on=4`; o contrafactual "sem a
  metade simétrica" melhorou de 31 para 16, e a asserção travava uma
  redução de 2×). **Nenhuma das duas asserções foi alterada** — é decisão
  do usuário.

## Decisões que ESPERAM o usuário

1. **Revisão e merge da CR-G12** — trade-offs em
   `docs/CR_G12_CROSS_BAND_IMPLEMENTATION.md` §6.3 (nível 2 subindo,
   `COMPENSATOR_EXCESS_IN_RUN` +2 no TGD do candidato, solver ~2× mais
   lento).
2. **As duas asserções do §7.2** — autorizar (ou não) trocar asserção de
   *mecanismo* por *resultado físico*, no mesmo precedente da §27.9.
3. **Normativa da CR-C2** — continua pendente. **G16 continua reprovado.**
4. **Merge da CR-S1 (#25) e da CR-C1 (#26)**.
5. **`baseline.json` / `reference_score.json`** — escrita oficial, CR própria.
6. **§27.8 item 2** (`UNCLASSIFIED_RULE_CONFLICT`) — sem decisão normativa.
7. **D1–D5** — nenhuma tomada nem presumida.

## Não fazer

Não iniciar C2, C02, C10, Junction, ARM nem outras CRs. Não marcar
`ready`, não mesclar, não criar monitoramento, não regravar baseline nem
gabarito.
