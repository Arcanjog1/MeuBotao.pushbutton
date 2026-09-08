# CHECKPOINT — sessão multifase CR-C2 / revisão C1 / reavaliação CR-B

**Data:** 2026-09-08 · **Branch:** `claude/multifase-cr-c2-c1-b-ikr8jc`

> **Nota sobre o checkpoint anterior — e por que este arquivo está em
> `docs/`:** o arquivo `.claude/checkpoints/sessao-multifase-s1-c1-b-d1.md`,
> citado como insumo desta sessão, **não existe em nenhuma branch do
> repositório** (conferido por `git ls-tree` nas 4 branches das CRs e na
> `main`). **Causa encontrada:** `.gitignore` linha 8 ignora `.claude/*`
> (só `.claude/skills/**` é versionado) — um checkpoint escrito ali
> **nunca chega a ser commitado** e morre com o contêiner. Por isso este
> checkpoint foi gravado em `docs/`, que é versionado.
>
> O contexto da sessão anterior foi reconstruído a partir dos relatórios
> reais:
> `CR_B_INTEGRATION_PREPARATION.md`,
> `CR_C1_COVERAGE_EXPECTED_ROWS_PHYSICAL.md`,
> `BENCH_OPENING_RECONSTRUCTION_B_INDEPENDENT_RECONCILIATION.md` e o
> `README.md` do candidato.

## Estado real

```
main real: 91258dd627af97fe437a56c0506eb096ca5aa267   (= base histórica informada; não avançou)
```

| PR | CR | branch | HEAD | estado |
|---|---|---|---|---|
| #25 | CR-S1 | `claude/corrigir-alternancia-no-l-76nnb3` | `33d035f` | draft |
| #26 | CR-C1 | `claude/cr-c1-expected-rows-fisico` | `34bf696` | draft |
| #27 | CR-D1 | `claude/cr-d1-recuperacao-documental` | `b852695` | draft |
| #28 | CR-B prep | `claude/cr-b-preparacao-identidade` | `0596e78` | draft |
| — | candidato CR-B | `claude/candidato-validacao-gabarito-q450yr` | `5640933` | gerador |

**Nada mesclado. Nenhum PR `ready`. Nenhum arquivo oficial regravado.
Nenhum monitoramento criado.**

## O que ficou provado (não repetir)

1. **CR-C1 = APPROVE.** `95/94 → 0` é geometria: **193 de 193 paredes com
   veredito** (0 sem `height_cm`), folga física **1,0cm** em todas contra
   limiar de **20cm**. Bateria independente de 14 casos: 7 falham na
   `main`, 14 passam na C1; **7a/7b/7c provam que a detecção de ausência
   real sobrevive** (7c é melhora: `expected_rows` baixo não esconde mais
   truncamento). Delta zero nos demais códigos. **2 falhas de baseline
   pré-existentes**, reproduzidas na `main` com os mesmos valores.

2. **CR-C2: os `+23` são 100% mudança de unidade.** Vazio físico
   **−14.409cm**; **58/58** vazios novos contidos em vazio já existente;
   **geometria nova = 0**; e a prova decisiva: mesmos blocos reavaliados
   na unidade de parede de `STATE_R` dão **−3**, não `+23`.

3. **Defeito pré-existente encontrado:** faixa de verga/peitoril contada
   como fiada de parede — **72% (TGD) e 57% (TP1)** dos
   `ROW_MOSTLY_EMPTY` do gabarito **humano**. Não é da CR-B.

4. **G12 reavaliado:** 28 identidades novas sem S1 (reproduz a CR-B),
   **12 com S1**. A S1 **não zera** o G12. **G12 continua reprovado.**

5. **G13 resolvido pela S1:** `+16 → 0` nos dois projetos.

6. **Método de identidade (regra §38.5):** nunca `W0xx`, nunca o eixo da
   parede, nunca o tipo do nó. A divisão de parede converte `T` em `L` e
   muda o eixo sem mover nada.

## Sessão de fechamento (2026-09-08, mesma branch)

7. **C2 — nenhum patch, e a recomendação mudou.** Busca em camadas pelo
   fundamento normativo: **A** não tem (o conceito de *banda* é do solver
   e 71% das fiadas fora do passo não têm abertura ativa); **B** não tem
   **e contradiz a tese física da CR-B** (os 19 casos são duas paredes que
   terminam no nó — se são paredes distintas, agregar é avaliar na unidade
   errada). **Recomendação revista: opção C isolada**, não "A+B".

8. **Duas correções da minha própria análise**, registradas em §38.2:
   (i) as fiadas fora do passo **não são majoritariamente vergas** — 71%
   não têm abertura ativa; são **peças cortadas** (`B39_C`, `B34_C`…);
   (ii) existe contrato real (`solver_supported_catalog`) para peças que o
   solver não implementa, mas ele governa solver×gabarito e **não** o G16 —
   e **10 dos 23** estão em fiadas 100% de peças suportadas.

9. **Contido ≠ falso.** Medido: correspondência **1:1 perfeita** entre
   vazio físico ≥5cm e `COVERAGE_GAP_IN_ROW` (648/648, 601/601, 637/637,
   590/590), **zero vazios sem achado**. Nenhuma mudança no
   `ROW_MOSTLY_EMPTY` perde detecção de vazio real.

10. **G12 — causa-raiz encontrada.** As 12 identidades (× 2 projetos) são
    **fronteira de banda de abertura**: cotas `141/161` relativas nos dois
    projetos, 2 paredes × 6 juntas de 40cm, desencontro **0,00cm**,
    **gabarito humano sem junta ali**. É instância do defeito já
    documentado na **§27.7** (*"as 33 são cross-band"*, correção proposta e
    não implementada). Numa parede de geometria **idêntica**, a única
    diferença é `B39`→`B19` na fiada acima da verga, disparada pela
    conversão `T→L`. **Classificação: A — defeito físico real, 12 de 12.**

11. **Reproducer reduzido do G12: NÃO obtido.** Três tentativas
    versionadas, todas negativas (sem abertura; com banda; subprojeto
    isolado — este último inválido, porque isolar muda o resultado). Por
    isso **nenhum patch** foi proposto. **CR-G12 preparada, não iniciada.**

12. **`JUNCTION_MISSING_BINDING` — motivo exato.** Peça mais próxima a
    **~8,0cm** nos 20 achados. O ponto do nó é onde o eixo de uma parede
    encontra a **face** da outra, e cai no **centro de um vazio de 16,0cm
    (`t=669..685`) que existe idêntico em `STATE_R`**. **10 de 10 = classe
    C**; nenhum nó pré-existente piorou.

## Decisões que ESPERAM o usuário

1. **Normativa da CR-C2** — `docs/CR_C2_DECISAO_FISICA.md`. **Bloqueia**
   a implementação da C2. **Recomendação revista: opção C isolada**
   (a de "A+B" da entrega anterior foi **retirada**, ver item 7).
2. **CR-G12** — autorizar ou não (`docs/CR_G12_CROSS_BAND.md`). Defeito
   físico real, causa conhecida, correção já proposta na §27.7. Exige
   escrever `nuvem/core/wall_modeling.py` e abre dívida de refresh de
   `baseline.json`. **Não iniciada.**
3. **Merge da CR-S1 (#25)** e **da CR-C1 (#26)**.
4. **`reference_score.json`** e **`baseline.json`** — escrita oficial.
5. **D1–D5** — nenhuma tomada nem presumida.

## Próximo passo

Nada a fazer sem decisão humana nos bloqueios (1) e (2). Trabalho
independente restante: nenhum dentro deste escopo.

**Não iniciar** C02/C10/Junction/ARM nem CRs antigas fora deste escopo.

## Como reproduzir tudo

```bash
cd nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b_candidate
export CR_B_OUT=/tmp/cr_b_candidate && python3 build_candidate.py
cd ../cr_c2_row_mostly_empty && cat README.md    # índice dos 18 diagnósticos
```
