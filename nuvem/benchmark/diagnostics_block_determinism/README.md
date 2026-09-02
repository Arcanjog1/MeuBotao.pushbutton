# `diagnostics_block_determinism/` — laboratório do CR-BLOCK-DETERMINISM (CONTA 1)

Baseline: `24ada98f5a8d4e7aa4cf0b30621d7818e4bb4fdc`.

## Contrato desta pasta

- Só **lê** o motor (`nuvem/core/**`), via `benchmark/solver_bridge.py`.
- Nenhum script daqui escreve fora desta pasta.
- 100% headless (`tests/revit_stubs.py`), sobre os projetos versionados em
  `nuvem/benchmark/projects/`.
- **Nenhum fingerprint definido aqui pode depender de `wall_idx`, da ordem
  da lista de paredes, do sentido de desenho de um eixo, de `id()` ou da
  ordem de iteração de um `dict`.**

Não confundir com `diagnostics_block_audit/` (CONTA 2, auditoria
independente — **não alterar**). Lá o fingerprint é do **resultado** final;
aqui há fingerprint **por camada** do pipeline, que é o que este CR pede.

## Scripts

| script | o que faz | saída |
|---|---|---|
| `lib_det.py` | chaves canônicas, fingerprints por camada, as 8 variantes | — |
| `run_baseline.py` | roda as 8 variantes, fingerprint por camada, acha a 1ª camada divergente | `out_baseline.json` |
| `run_rootcause.py` | desce dentro de `build_wall_graph` (junction_map → arms → clusters → classificação) | `out_rootcause.json` |
| `run_examples.py` | exemplos geométricos **com números** de cada causa-raiz | `out_examples.json` |
| `run_roles.py` | dependências de ordem **latentes**: papéis (main/incoming/neighbor/crossing) e ordem de `arms` | `out_roles.json` |
| `run_ablation.py` | teste de ablação: só ordenar a entrada × correção estrutural | `out_ablation.json` |
| `run_benchmark.py` | benchmark completo antes/depois nos 3 projetos + gates do CR-BLOCK-01 | `out_benchmark.json` |

Rodar (a partir desta pasta):

```
python3 run_baseline.py            # projeto primário torre_easy_lo_r00_tgd
python3 run_baseline.py piloto_sintetico_2x2
```
