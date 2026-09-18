# Checkpoint — auditoria independente do patch real da §74 (`2c55211`)

Terceira entrega desta sessão. **Produção intocada**:
`git diff origin/main..HEAD -- nuvem/` vazio. PR #42 não tocado (auditado
em worktree isolado, somente leitura). Nenhum apply no Revit.

```json
{
  "date": "2026-09-17",
  "scope": "historical",
  "branch": "claude/jolly-ritchie-0bq5f6",
  "head": "d6cbec4d74bc52173a37602bccee2637a1cd49cd",
  "base": "55e990d962ed22ae1021f0d335db197607bddda1",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/48",
  "objective": "Auditar o patch REAL da secao 74 (commit 2c55211, contido em origin/claude/butanta-modulation-physical-fixes e origin/pr42-audit), depois de a sessao principal apontar que a conclusao anterior desta auditoria usava referencia desatualizada (759bcd4).",
  "changes": [
    "docs/AUDITORIA_SECAO_74_PATCH_2c55211.md: NOVO. Diff exato, itens A-E, semantica antes/depois, prova de escala do ruido, saturacao, o que nao foi reproduzivel e as 10 respostas diretas.",
    "tests/audit_secao74_patch_2c55211.py: NOVO. Bateria adversarial OFF/ON contra oraculo fisico recalculado do zero; roda contra qualquer worktree via WT74.",
    "NENHUM arquivo sob nuvem/ alterado; PR #42 nao tocado."
  ],
  "tests": [
    "python3 tests/audit_secao74_patch_2c55211.py (WT74=worktree em 2c55211) -> 0 falhas",
    "python3 -m pytest tests/test_t_room_physical_tolerance.py -q (em 2c55211) -> 10 passed",
    "python3 -m pytest tests/ -q -m 'not slow' (em 2c55211) -> 1313 passed, 0 failed, 31 deselected, exit 0, 760.94s",
    "ponta a ponta no corpus versionado (46 paredes, 48 T, 6 fiadas): 1161 pecas, sha d63ce811c8b381c8 IDENTICO com a secao 74 OFF e ON, hard gates (0,28,0,0) iguais"
  ],
  "known_failures": [
    "Nenhuma falha observada no escopo auditavel."
  ],
  "physical_deltas": [
    "Nenhum: auditoria somente de leitura.",
    "MEDICAO - ruido da PLANTA REAL (corpus versionado 2026-09-10-butanta-test-walls.json, 144 medicoes de espaco em 48 encontros T): 107 das 144 com desvio nao-nulo ao meio-centimetro; MAIOR 0,013251 cm (0,1325 mm); mediana dos nao-nulos 0,001054 cm (0,0105 mm). Os casos citados pela §74 (0,035 mm e 0,12 mm) caem dentro desta faixa, medidos em geometria que a §74 NAO usou.",
    "MEDICAO - ruido de CALCULO apos extend_wall_ends_to_junctions com entrada limpa: 9,4147e-13 cm. A extensao de encontro NAO amplifica ruido; o ruido relevante e' da planta, nao do calculo.",
    "MEDICAO - faixa segura: ruido 0,0133 cm < tolerancia 0,05 cm (3,8x acima) < menor falta real do corpus 4,001054 cm (80x abaixo). A tolerancia OFF (3,048e-05 cm) cobre 0,002x do ruido - nao cobria.",
    "MEDICAO - saturacao: no corpus, 0,05 = 0,10 = 0,30 = 1,00 = 2,00 = 4,00 cm dao vereditos identicos e a igualdade quebra em 4,01 cm. No nivel da guarda ISOLADA nao satura: fronteiras 0,0495 / 0,1000 / 0,2995 cm. Logo a saturacao mostra ausencia de precipicio, mas nao seleciona 0,05."
  ],
  "decisions_taken": [
    "RETRATAR a conclusao anterior: 'a §74 nao existe' valia para o snapshot 759bcd4 buscado por fetch; a branch avancou para 6b04475 e 2c55211 existe. Conclusao retirada.",
    "CORRIGIR um argumento proprio: 'nao ha' ruido a absorver' estava errado - a medicao usava cenas sinteticas de coordenadas exatas. Na planta real ha' ruido, na escala que a §74 cita.",
    "Auditar em worktree isolado no SHA exato, sem checkout da branch do PR #42 e sem qualquer escrita nela."
  ],
  "decisions_pending": [
    "VERSIONAR a geometria das 34 paredes do corpus da §74 (eixos 8284xxx, p0/p1 em pes, no formato do JSON de 2026-09-10). Sem isso os numeros de corpus da §74 - 37 T, nos 24/44/46, sha256 bc261fe485de635a, 8284580 204,7->3,3, hard gates 0/0/0/0, legado 8939/0a2704e4faaf - permanecem NAO VERIFICADOS por esta auditoria. E' ausencia de dado, nao refutacao.",
    "REDIGIR a §74 declarando que a faixa (0 ; 0,05) cm e' ruido de MODELAGEM e que aceita-la e' decisao fisica declarada, e nao apresentar a saturacao como se ela selecionasse 0,05 (4,00 cm satura igual neste corpus).",
    "Integrar tools/preflight/purge_guard.py no harness: pendente de autorizacao (o _harness e' registro versionado de entrega passada).",
    "capture_export.py:57: PR separado, fora do #42. Nao corrigido.",
    "REGRAS_MODULACAO_BLOCOS.md: a §74 ja' esta' documentada na branch do PR #42; nada a fazer nesta branch."
  ],
  "next_steps": [
    "Versionar os eixos das 34 paredes para fechar os itens 7 e 8 (saturacao por assinatura e o caso 8284580).",
    "Decidir sobre a redacao da §74 quanto a saturacao e a natureza da faixa submilimetrica."
  ],
  "references": [
    {"path": "docs/AUDITORIA_SECAO_74_PATCH_2c55211.md"},
    {"path": "docs/RECONCILIACAO_74_2026-09-17.md"},
    {"path": "docs/AUDITORIA_INDEPENDENTE_GUARDA_ESPACO_T.md"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## Veredito

**`SUPPORTED WITH LIMITATIONS`** — o diagnóstico da §74 está correto e
medido, a mecânica é conservadora e o legado é idêntico; as limitações são
a não reprodutibilidade dos números de corpus (geometria não versionada) e
o argumento de saturação, que é mais fraco do que aparenta.
