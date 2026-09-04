# START HERE

Ponto de entrada para qualquer nova sessão neste repositório. Leitura
progressiva: leia o mínimo do nível abaixo antes de subir para o
próximo — nunca "ler o repositório inteiro para entender".

---

## SOLVER DE BLOCOS (modulação / amarração)

Leia, nesta ordem:

1. `CLAUDE.md` (raiz)
2. `docs/PROJECT_STATUS.md`
3. `nuvem/REGRAS_MODULACAO_BLOCOS.md` — localize a seção pelo
   heading/ID/termo antes de ler o arquivo inteiro
4. `docs/CURRENT_REFERENCE_SNAPSHOT.md`

Depois: busque só o símbolo/erro específico (`git grep`/`rg`). NÃO leia
todos os `docs/diagnostics_*` ou relatórios de CR antigos por padrão —
só se uma busca específica apontar para eles.

---

## WALL PAIRING / GEOMETRIA (paredes a partir do CAD)

Leia, nesta ordem:

1. `CLAUDE.md` (raiz)
2. `docs/PROJECT_STATUS.md`
3. `docs/DEVELOPMENT_PROCESS.md`
4. o módulo específico (`nuvem/core/engine/geometry.py`,
   `wall_pairing.py`, `tolerances.py`, conforme o caso)

Não carregar o benchmark inteiro automaticamente.

---

## BENCHMARK / REFERENCE CORPUS

Leia, nesta ordem:

1. `CLAUDE.md` (raiz)
2. `docs/PROJECT_STATUS.md`
3. `docs/REFERENCE_CORPUS.md`
4. `docs/CURRENT_REFERENCE_SNAPSHOT.md`
5. o README do benchmark relevante (`nuvem/benchmark/`)

---

## UI / REVIT (integração pyRevit)

Não leia o benchmark de blocos inteiro por padrão. Abra só a
documentação da integração necessária (ex.: seção "REVIT — SHORT
CURVES" em `docs/PROJECT_STATUS_LOG.md` para o histórico da extração do
CAD).

---

## BUG / DEBUG

Fluxo:

```
reproduzir -> primeira divergência -> causa -> fix mínimo -> testes
```

Ver `docs/DEVELOPMENT_PROCESS.md` para o fluxo completo de CR. Para
diagnóstico sistemático de causa-raiz, use a skill `systematic-debugging`
quando disponível.

---

## REGRA DE OURO

NÃO: "ler o repositório inteiro para entender".

SIM:

```
START_HERE (este arquivo)
  -> PROJECT_STATUS.md
  -> documento do domínio
  -> busca exata (termo -> sinônimo -> heading -> símbolo de código)
  -> arquivo de produção específico
  -> expandir só se a busca em camadas ficou inconclusiva
```

Histórico completo de CRs: `docs/PROJECT_STATUS_LOG.md` — só abrir
quando o assunto for uma continuação de CR anterior ou a busca em
`PROJECT_STATUS.md` ficar inconclusiva.
