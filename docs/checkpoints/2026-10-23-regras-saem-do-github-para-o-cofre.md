# Regras de modulação saem do GitHub e passam ao cofre T:\CIVIX IA\MODULAÇÃO

Branch `claude/civix-ia-modulacao-acesso-ff42dc`, sem PR. Pedido do usuário em 2026-10-23: "A PARTIR DE
AGORA AS REGRAS Q ESTAVAM NO GITHUB DEVEM SER ATUALZIADA NESSA PASTA, PODE ARQUIVAR OU DELETAR TODOS OS
ARQUIVOS DE REGRA Q ESTAO NO GITHUB". Escolhas do usuário na mesma conversa: tirar **tudo de regra e
decisão**; **deletar + tag de recuperação**; no cofre, **arquivo único + gerador local**; **merge na main
autorizado** para esta entrega, depois dos testes.

```json
{
  "date": "2026-10-23",
  "scope": "current",
  "branch": "claude/civix-ia-modulacao-acesso-ff42dc",
  "head": "08dbec9cdcf02dba150736dcbd01fab44561d892",
  "base": "c855397f20a7b78e65bc2537f1a555ec4031d051",
  "pr": "not-created",
  "objective": "Mudar a casa oficial das regras de modulacao do GitHub para o cofre T:\\CIVIX IA\\MODULAÇÃO: copiar os originais para o cofre, fazer o gerador do cofre ler de la', remover os arquivos de regra e decisao do repositorio e apontar as instrucoes de agentes para o cofre.",
  "changes": [
    "Removidos do repo: nuvem/REGRAS_MODULACAO_BLOCOS.md, nuvem/PADRAO_MODULACAO.md, rules/ (5 READMEs), docs/decisions/ (8 arquivos), .claude/skills/revit-block-modulation e .agents/skills/revit-block-modulation (BLOCKS, BONDING, ERROR_HISTORY, EXAMPLES, OPENINGS, RULES, VALIDATION).",
    ".claude/skills/revit-block-modulation/SKILL.md e a copia .agents: so' ponteiro para a skill completa no cofre, para o gatilho da skill continuar existindo.",
    "CLAUDE.md e AGENTS.md: secao nova 'Regras de modulacao moram no cofre (2026-10-23)'; toda mencao a nuvem/REGRAS_MODULACAO_BLOCOS.md virou 'REGRAS_MODULACAO_BLOCOS.md do cofre'. README, START_HERE e DEVELOPMENT_PROCESS idem.",
    "tests/test_junta_no_toco_86_15.py: o teste que lia a 86.15 no REGRAS foi dividido - chave+codigo continuam no repo; a leitura da regra vai ao cofre (MODULACAO_COFRE ou T:) e pula se o cofre nao estiver acessivel (CI).",
    "tools/documentation/verify_reference_inventory.py: a checagem de preservacao do REGRAS so' roda enquanto o arquivo estiver versionado.",
    "Fora do repo (cofre): originais copiados para T:\\CIVIX IA\\MODULAÇÃO\\Original (editar aqui)\\ (23 arquivos, git hash-object igual ao blob de c855397); _Sistema/gerar_cofre.py versao 2 le as regras dessa pasta (LOCAL_MAP), marca as fontes com origem cofre/git, avisa quando um original muda depois da geracao, e os textos (LEIA-ME PARA IA, CLAUDE.md/AGENTS.md do cofre, caixa de entrada, mapa, llms.txt) dizem que o original e' editado no cofre."
  ],
  "tests": [
    "HEAD 08dbec9 (arvore de trabalho igual ao commit): py -3 -m pytest tests/test_script.py tests/test_junta_no_toco_86_15.py tools/documentation/test_validate.py -q -> 297 passed, 1 warning (DeprecationWarning de codecs.open em nuvem/core/wall_modeling.py:12082, pre-existente), 130 s. O teste novo do cofre rodou (T: acessivel), nao pulou.",
    "Gerador do cofre (versao 2) num rascunho fora do repositorio, originais do cofre + documentos de c855397: relatorio OK - 460 arquivos gerados, 188 fontes conferidas, 23 originais editaveis, documento oficial reconstruido byte a byte das 89 notas (826 847 bytes), 88 secoes, 301 subsecoes, 3 212 links sem quebra.",
    "py -3 tools/documentation/validate.py --base c855397f20a7b78e65bc2537f1a555ec4031d051 --main origin/main --require-current-main -> ver o commit documental."
  ],
  "known_failures": [
    "Nenhuma no escopo. Sessoes na nuvem e o CI do GitHub nao enxergam T:; para elas as regras ficam indisponiveis (o teste do cofre pula e o SKILL.md ponteiro manda avisar o usuario)."
  ],
  "physical_deltas": [
    "Nao aplicavel: nenhuma peca, chave ou texto de regra muda. Os originais no cofre sao byte a byte os de c855397."
  ],
  "decisions_taken": [
    "Escopo: regra + decisao (REGRAS, PADRAO_MODULACAO, rules/, docs/decisions/) e a skill revit-block-modulation; checkpoints, evidencias e relatorios continuam no repo.",
    "Deletar em vez de mover para pasta de arquivo, com a tag regras-github-final em c855397 para recuperar.",
    "O original editavel no cofre e' um arquivo unico (Original (editar aqui)/REGRAS_MODULACAO_BLOCOS.md); o gerador continua refazendo notas e indices a partir dele.",
    "Merge na main autorizado pelo usuario para esta entrega (resposta 'Sim, mesclar na main' em 2026-10-23), depois de tests/test_script.py e do validador."
  ],
  "decisions_pending": [
    "Comentarios e docstrings do codigo e dos testes continuam citando 'REGRAS_MODULACAO_BLOCOS.md secao N'; os numeros de secao seguem validos, mas o arquivo agora esta' no cofre. Nao foram reescritos.",
    "Checkpoints e relatorios antigos em docs/ continuam com links para nuvem/REGRAS_MODULACAO_BLOCOS.md, rules/ e docs/decisions/ (historico, nao reescrito); para ler, usar a tag regras-github-final."
  ],
  "next_steps": [
    "Regenerar o cofre com o gerador versao 2 pela main nova: py -3 \"T:\\CIVIX IA\\MODULAÇÃO\\_Sistema\\gerar_cofre.py\" --repo <clone> --cofre \"T:\\CIVIX IA\\MODULAÇÃO\".",
    "Proxima correcao de modulacao: editar T:\\CIVIX IA\\MODULAÇÃO\\Original (editar aqui)\\REGRAS_MODULACAO_BLOCOS.md e regenerar o cofre."
  ],
  "references": [
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md", "commit": "c855397f20a7b78e65bc2537f1a555ec4031d051"},
    {"path": ".claude/skills/revit-block-modulation/SKILL.md"},
    {"path": ".agents/skills/revit-block-modulation/SKILL.md"},
    {"path": "CLAUDE.md"},
    {"path": "AGENTS.md"},
    {"path": "tests/test_junta_no_toco_86_15.py"},
    {"path": "tools/documentation/verify_reference_inventory.py"},
    {"path": "docs/checkpoints/2026-10-20-s87-7-docs-skill-ate-87.md"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## O que mudou

1. **Onde se edita uma regra agora.** `T:\CIVIX IA\MODULAÇÃO\Original (editar aqui)\REGRAS_MODULACAO_BLOCOS.md`.
   Ao lado ficam `PADRAO_MODULACAO.md`, `rules\`, `decisions\` e `skill revit-block-modulation\`. São
   cópias byte a byte do commit `c855397`.
2. **O cofre continua sendo gerado.** O `_Sistema\gerar_cofre.py` (versão 2) lê as regras desses
   originais e os documentos de apoio (checkpoints, relatórios, medições) do GitHub, como antes. As
   notas de `Regras\` e os índices continuam sendo gerados; editar essas notas não adianta.
3. **O repositório não guarda mais regra.** Quem procurar `nuvem/REGRAS_MODULACAO_BLOCOS.md` encontra
   as instruções em `CLAUDE.md`/`AGENTS.md` e o `SKILL.md` ponteiro. A versão final no GitHub fica na tag
   `regras-github-final`.

## Limites

- Sessões na nuvem e o CI do GitHub não acessam `T:`.
- Referências antigas em comentários de código e documentos históricos não foram reescritas (ver
  `decisions_pending`).
