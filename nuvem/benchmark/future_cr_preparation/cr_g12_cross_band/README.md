# CR-G12 — `PRISM_CONTINUOUS_JOINT` na fronteira de banda de abertura

> **CR IMPLEMENTADA (2026-09-08)**, aguardando revisão humana e merge.
> Diagnóstico: `docs/CR_G12_CROSS_BAND.md`. **Implementação, medições e
> vereditos: `docs/CR_G12_CROSS_BAND_IMPLEMENTATION.md`.** Regras:
> `nuvem/REGRAS_MODULACAO_BLOCOS.md` §27.7 e §39.
>
> O cabeçalho anterior dizia *"CR PREPARADA, NÃO IMPLEMENTADA"* — e a §6
> abaixo dizia que **não existia reproducer reduzido**. **As duas coisas
> mudaram**; o texto original foi mantido como registro e está corrigido
> in loco (ver "Estado do reproducer" no fim).

## Como reproduzir

```bash
# 1. candidato CR-B
cd nuvem/benchmark/future_cr_preparation/bench_opening_reconstruction_b_candidate
export CR_B_OUT=/tmp/cr_b_candidate && python3 build_candidate.py

# 2. projeção isolada S1+C1 (worktree; NENHUM merge)
git worktree add /tmp/proj origin/main --detach
cd /tmp/proj
git checkout origin/claude/corrigir-alternancia-no-l-76nnb3 -- nuvem/core/engine/wall_stepper.py
git checkout origin/claude/cr-c1-expected-rows-fisico  -- nuvem/benchmark/validators/validate_wall_coverage.py

# 3. resolver e salvar (~25 min)
python3 <este dir>/g12_detalhe.py /tmp/proj $CR_B_OUT /tmp/solved_s1c1

# 4. classificar as identidades
SCR=<raiz do scratch> python3 <este dir>/g12_classif.py torre_easy_lo_r00_tgd torre_easy_lo_r00_tp1
```

## Índice

| script | o que faz |
|---|---|
| `g12_detalhe.py` | roda o solver sobre `IN_R` e `IN_C` e **salva** os projetos resolvidos com os achados |
| `g12_classif.py` | tabela física das identidades novas: ponto global, cotas, parede, desencontro, e se o **gabarito humano** tem junta ali |
| `jmb10.py` | as 10 identidades novas de `JUNCTION_MISSING_BINDING` (gabarito) |
| `jmb_motivo.py` | **motivo exato** do `MISSING_BINDING`: distância da peça mais próxima ao ponto do nó |
| `repro_g12.py` | tentativa de reprodução mínima — **nó T × L sem abertura**. **NEGATIVA** (0 × 0) |
| `repro_g12b.py` | tentativa com **banda de abertura** (porta t=314..405, head=160). **NEGATIVA** (0 × 0) |
| `repro_g12c.py` | tentativa com **subprojeto real isolado**. **NEGATIVA e inválida** — isolar a parede muda o resultado (o solver resolve em função do contexto global), então o subprojeto não é o mesmo problema |

## Estado do reproducer — CORRIGIDO (2026-09-08)

> **A afirmação anterior desta seção — *"não existe reproducer
> reduzido"* — está superada.** Ela continuava certa quanto às
> tentativas SINTÉTICAS (nenhuma planta inventada reproduz: as três
> acima mais ~4.900 combinações de `sweep2_janela.py` e
> `sweep3_no_de_meio.py`). O que estava errado era a **generalização**
> de que só o projeto inteiro serviria.

**Existe reproducer reduzido: `repro_g12d_minimo.py`, 3 paredes REAIS**
do `input.json` oficial (índices 55/82/124 do TGD), obtidas por
*delta-debugging* com `reduzir.py` — não por proximidade, que foi
justamente o erro do `repro_g12c.py`. Roda em segundos, falha no código
anterior pelo **mesmo mecanismo físico** (junta em `t=39,5` presa à
borda de um `B54` de `T_INTERSECTION_MIDSPAN`, desencontro 0,00cm) e some
com a correção ligada.

## Novos scripts desta CR

| script | o que faz |
|---|---|
| `repro_g12d_minimo.py` | **reproducer mínimo** — 3 paredes reais, pré-fix × pós-fix |
| `reduzir.py` | delta-debugging: reduz a planta oficial mantendo a identidade física alvo |
| `medir_crossband.py` | mede `PRISM_CONTINUOUS_JOINT` no corpus e separa **cross-band** de intra-banda (`G12_OFF=1` desliga a correção) |
| `g12_ident.py` | as identidades novas do G12 no delta `IN_R → IN_C` do candidato CR-B |
| `sweep2_janela.py` | 1.952 cenários sintéticos porta+janela — **negativo** |
| `sweep3_no_de_meio.py` | 430 cenários sintéticos com T de meio de parede — **negativo** |
