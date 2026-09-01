# Status do projeto - Modulacao Automatica

## 2026-09-01 - Primeiro teste visual no Revit

- Primeiro teste visual real no Revit foi **iniciado** (fora do pipeline
  headless via MCP - ver `pipeline-headless-modulacao-mcp` na memoria do
  projeto).
- **Bloqueio encontrado** antes da criacao de qualquer parede, durante a
  etapa "Extraindo linhas do CAD...":

  ```
  Autodesk.Revit.Exceptions.ArgumentsInconsistentException:
  Curve length is too small for Revit's tolerance
  (as identified by Application.ShortCurveTolerance).
  Parameter name: endpoints
  ```

  Stack: `extract_lines_by_layer` (`nuvem/core/wall_modeling.py`), na
  chamada `DB.Line.CreateBound(p0, p1)` ao explodir uma `PolyLine` do CAD
  em segmentos.

- **Causa confirmada:** o CAD real contem segmentos (vertices de
  `PolyLine` quase duplicados, e possivelmente `Line` degeneradas) com
  comprimento **abaixo de `Application.ShortCurveTolerance`** (a
  tolerancia oficial do Revit). O filtro antigo do script descartava so'
  segmentos com comprimento `< 1e-6` pe - um valor muito menor que a
  tolerancia real do Revit (~0,0026 pe = 1/32 polegada) - entao esses
  segmentos passavam pelo filtro e derrubavam `Line.CreateBound`.
- **Correcao aplicada:** `extract_lines_by_layer` agora le
  `Application.ShortCurveTolerance` (via `doc.Application`, cacheado em
  `_get_short_curve_tolerance()`) e usa a decisao pura
  `_segment_too_short_for_revit(distance, tolerance)` para IGNORAR (nao
  enviar a `Line.CreateBound`) qualquer segmento com
  `distance <= ShortCurveTolerance`, tanto no ramo `Line` quanto no ramo
  `PolyLine`. Segmentos normais continuam extraidos exatamente como
  antes. Um resumo (total analisado, quantos foram ignorados, menor
  comprimento visto, layers afetados) e' logado uma unica vez apos a
  extracao.
- Classificado como **BLOQUEIO DE INTEGRACAO REVIT / EXTRACAO CAD** - nao
  e' regressao do CR-2F-D (que trata pairing/merge/deduplicacao de
  paredes, nao extracao de geometria do CAD). CR-2F-D permanece encerrado
  e nao foi reaberto; `create_centerline`, `find_wall_pairs` e
  `core/engine/{geometry,wall_pairing,tolerances}.py` nao foram tocados.
- **Teste visual no Revit ainda PENDENTE de continuacao** - esta correcao
  so' desbloqueia a extracao do CAD; a analise/validacao das paredes
  geradas no Revit real ainda nao foi feita.
