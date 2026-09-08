# CR-G12 — `PRISM_CONTINUOUS_JOINT` na fronteira de banda de abertura

> **CR PREPARADA, NÃO IMPLEMENTADA.** Nenhum patch no solver. Nada de
> produção tocado. Ver `docs/CR_G12_CROSS_BAND.md`.

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

## Estado do reproducer — declarado

**Não existe reproducer reduzido.** As três tentativas acima estão
versionadas justamente por terem falhado: elas delimitam o que **não** é
a causa isolada (nem o tipo do nó sozinho, nem a banda de abertura
sozinha, nem a vizinhança imediata da parede).

O reproducer válido hoje é o **projeto completo**, determinístico e
reprodutível pelos passos acima. Por isso **nenhum patch mínimo foi
proposto**: sem reprodução reduzida não há como demonstrar que uma
correção ataca a causa em vez do sintoma.
