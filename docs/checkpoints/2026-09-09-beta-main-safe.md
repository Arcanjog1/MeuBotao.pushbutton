# Beta main-safe: protecoes independentes de N1

```json
{
  "date": "2026-09-09",
  "scope": "current",
  "branch": "codex/beta-main-safe-20260909",
  "head": "8cdd33f974f41a9bf41010a32f82762740b31ed3",
  "base": "aa58d70d84c6134216f8f15a131edf060c4dce81",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/34",
  "objective": "Preparar primeiro ensaio de criacao/recriacao de um L em bancada isolada, sem transportar as regressoes N1 e sem abrir Revit.",
  "changes": ["Branch diretamente da main; tres arquivos de protecao identicos ao09b6ea0: Script.py, beta_package.py, wall_modeling.py. Nenhuma alteracao no motor geometrico, benchmark ou testes originais da main.", "Transportados testes beta e ferramentas de empacotamento/governanca; novo teste permanente do recorte75/81. Regras registram somente contencoes e limites do ensaio."],
  "tests": ["331 controles iniciais passaram em112.95s, arquivos transportados iguais aos do SHA final; teste do recorte passou em0.61s.", "Consolidada8cdd33f concluida:1027 passed/2 failed em3021.98s (wrapper3025.078s), exit1. PID25596, inicio17:32:04 UTC, timeout5400s. Falhas antigas: TGD compensators52->61; TP1 JUNCTION_MISSING_BINDING8->9.", "16 testes de governanca passaram em25.589s. Pacote build/verify passaram. Execute_solve real do handler, com dubles, gerou187 blocos e geometria/catalogo exatamente iguais ao probe, assinatura valida e zero achados com referencia. Eixos Z612cm tambem equivalentes."],
  "known_failures": ["Main conserva defeitos fisicos nos projetos completos; N1/#31 continua NO-GO. Nao liberar outros recortes nem tratar contencao como correcao.", "Alturas nativas TP1 de260/280cm nao equivalem ao setup global17 fiadas. Bancada derivada uniforme340cm explicitamente separada; nao substituir Walls nativas nem finalizar referencias.", "Revit/API/familias nao executados; exportacao universal de falhas nao implementada, captura manual numerica obrigatoria no runbook."],
  "physical_deltas": ["Motor geometrico igual a main, SEM N1. Recorte75/81:187 blocos,1L,2FREE,zero aberturas,zero nao-modulares,zero achados/preflight e auditorias brutas aprovadas.", "Caminho de extensao das Walls existentes tambem passa em13/14/17 fiadas com143/154/187 blocos. As alturas sao cenarios de engenharia distintos, nao invariancia vertical certificada."],
  "decisions_taken": ["Nao mesclar31 nem modificar sua cadeia para produzir esta candidata.32 ja integrado; novo draft nao tem autorizacao de merge.", "Ensaio inicial limitado a criacao/recriacao em copia descartavel uniforme75/81; sem aberturas,T/X,ajuste automatico,uniao ou Finalizar. Nenhum Revit iniciado."],
  "decisions_pending": ["Familias/API/rollback real sao verificacoes do beta, com parada e backup definidos. Nao iniciar Revit nesta missao.", "Eixos TGD, fases T, tetos/modulo e CR-B continuam decisoes de dominio para ampliar escopo; nao sao aprovadas nesta branch. Merge do novo draft exige autorizacao especifica."],
  "next_steps": ["Proxima etapa: executar o runbook somente na bancada descartavel definida, com conferencias de familias/API e captura de evidencias. Publicacao34 e CI inicial confirmados; codigo/testes continuam8cdd33f.", "GO tecnico restrito ao ensaio de criacao/recriacao de187 blocos da bancada uniforme75/81. Revit fica para a proxima etapa; nao finalizar referencias, ampliar escopo, integrar31 ou declarar aceite construtivo."],
  "references": [
    {"path": "docs/BETA_MAIN_SAFE_2026-09-09.md"},
    {"path": "docs/BETA_MAIN_SAFE_RUNBOOK.md"},
    {"path": "tests/test_beta_tp1_region.py"},
    {"path": "tests/test_controlled_beta_preflight.py"},
    {"path": "tests/test_beta_atomic_creation.py"},
    {"path": "tests/test_unmodulated_wall_retention.py"},
    {"path": "docs/checkpoints/evidence/main-safe-region-final.json"},
    {"path": "docs/checkpoints/evidence/main-safe-region-final-scored.json"},
    {"path": "docs/checkpoints/evidence/main-safe-ui-boundary-run.json"},
    {"path": "docs/checkpoints/evidence/main-safe-engineering-input.json"},
    {"path": "docs/checkpoints/evidence/main-safe-handler-bench.json"},
    {"path": "docs/checkpoints/evidence/main-safe-native-z.json"},
    {"path": "docs/checkpoints/evidence/main-safe-provenance.json"},
    {"path": "docs/checkpoints/evidence/main-safe-governance-tests.json"},
    {"path": "docs/checkpoints/evidence/main-safe-github-publication.json"},
    {"path": "docs/checkpoints/evidence/main-safe-documentation-validation.json"},
    {"path": "docs/checkpoints/evidence/main-safe-package-verify.json"},
    {"path": "docs/checkpoints/evidence/main-safe-consolidated.json"}
  ]
}
```

O SHA acima ficou congelado durante a consolidada. Apenas documentacao
e evidencias foram acrescentadas. O probe inicial foi executado antes
do commit com protecoes locais e nao e prova de checkout limpo da main.
O probe final e o replay do handler identificam o8cdd33f exato.

O input de engenharia deriva coordenadas de75/81, explicita altura340cm
uniforme e remove metadados de nos antigos; o grafo e reconstruido. Nao
reescreve input oficial e nao representa a substituicao construtiva das
Walls nativas260/280cm. A passagem nesse recorte nao libera a cadeia31.

Publicacao inicialee2250a no PR34 draft: checks push/PR verdes
34389067319/34389092291. Este complemento apenas registra links e o
snapshot; codigo/testes permanecem8cdd33f. CI e do GitHub; timestamps de
comandos sao do host. Nao inferir ordenacao fina entre relogios distintos.
