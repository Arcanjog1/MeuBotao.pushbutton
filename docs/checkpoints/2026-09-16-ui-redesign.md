# Redesign da experiência — entrega candidata

```json
{
  "date": "2026-09-16",
  "branch": "codex/modulacao-automatica-ui-redesign",
  "head": "20d7e392e6aa9b9f98eeb9aafdaac6aa0d64c136",
  "base": "55e990d962ed22ae1021f0d335db197607bddda1",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/44",
  "objective": "Redesenhar UI/UX em WinForms, com revisão explícita do plano, sem alterar motor, backend de execução ou PR #42.",
  "changes": [
    "core/ui_state.py e core/ui_components.py: estado e componentes de apresentação reutilizáveis.",
    "core/wall_modeling.py: integração nas telas/callbacks de UI e escolha explícita de reforço no fluxo existente.",
    "Testes de UI, renderizador WinForms e prova de escopo; wireframes, antes/depois, checklist.",
    "Regras: registrar somente contrato UX, com substituição explícita da antiga criação automática; status reconciliado ao merge #41."
  ],
  "tests": [
    "301 passed / 1 warning em 61.63s, exit 0: evidence/2026-09-16-ui-redesign-delivery-focused.json e .txt; tests/test_ui_redesign.py, tests/test_channel_ui_and_family_gate.py, tests/test_script.py, nuvem/tests/test_progress.py; Windows CPython 3.14.6/pytest 9.1.1.",
    "39 passed na seleção de testes de UI, configuração, gates, docking e paredes existentes.",
    "Renderização WinForms real fora do Revit: Python 3.13/pythonnet 3.1.0; dez estados, comparação anterior, Scale 1/1.25/1.5/1.75/2 e janela 740x520. Não equivale a DPI nativo nem smoke Revit.",
    "check_ui_scope.py: 188 definições fora da UI intactas; handler completo e funções de threading/pump/timer intactos; engine/benchmark/loader sem diff.",
    "Suíte completa: 1228 passed / 3 failed / 1 warning, 1273.64s, exit 1; py -3 -m pytest tests -q -n 4 --dist loadfile -p no:cacheprovider em 76b758b; evidence/2026-09-16-ui-redesign-suite.json e .txt."
  ],
  "known_failures": [
    "test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]: JUNCTION_MISSING_BINDING 8→9; mesma asserção documentada na main.",
    "test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2]: compensators 61→62; mesma asserção documentada na main.",
    "test_retencao_nativa_de_gil_dispara_e_despeja_as_pilhas: UnboundLocalError ctypes, tests/test_perf_trace_stall_sampler.py:96, Windows; falha já documentada na main.",
    "Um DeprecationWarning herdado de codecs.open.",
    "Smoke no Revit e escala nativa Windows ainda não executados; limitações funcionais descritas abaixo."
  ],
  "physical_deltas": ["Não aplicável: solver, validadores físicos, catálogo, criação, transações e geometria não alterados."],
  "decisions_taken": [
    "Pedido do usuário autoriza branch própria sobre main, commits/push e PR draft; não autoriza merge.",
    "Novo pedido substitui criação automática após cálculo por revisão antes de Criar blocos no Revit.",
    "Manter WinForms e callbacks existentes; não alterar threading nem implementar lógica física na apresentação."
  ],
  "decisions_pending": ["Reconciliar com #42 após seu encerramento; executar smoke Revit/DPI antes de considerar pronto."],
  "next_steps": ["Revisar PR draft; reconciliar após #42, sem merge nesta missão.", "Executar checklist manual em checkout de teste isolado do #42."],
  "references": [
    {"path": "docs/PROJECT_STATUS.md"},
    {"path": "docs/UI_REDESIGN.md"},
    {"path": "nuvem/core/ui_state.py"},
    {"path": "nuvem/core/ui_components.py"},
    {"path": "tests/test_ui_redesign.py"},
    {"path": "docs/checkpoints/evidence/2026-09-16-ui-redesign-delivery-focused.json"},
    {"path": "docs/checkpoints/evidence/2026-09-16-ui-redesign-suite.json"},
    {"path": "docs/checkpoints/evidence/2026-09-16-ui-scope.json"}
  ]
}
```

## Veredito

PR draft: [#44](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/44).

**PARTIAL — LIMITATIONS EXPLAINED.** Candidato revisável; não declarar
smoke no Revit nem DPI nativo como aprovados. Não houve merge ou instalação
do candidato no botão em uso. A sessão do #42 permanece independente.

## Identidade, stack e fluxo

- `origin/main` inicial e última observada: `55e990d962ed22ae1021f0d335db197607bddda1`.
- Branch: `codex/modulacao-automatica-ui-redesign`.
- HEAD avaliado: `20d7e392e6aa9b9f98eeb9aafdaac6aa0d64c136`.
- Checkout: `C:\Users\CIVIX\modulacao-ui-redesign`; o diretório originalmente
  fornecido pertence a outro repositório e contém trabalho de outras sessões.
- Stack preservado: WinForms + CPython/pythonnet, pyRevit, ExternalEvent.
  Sem Qt, pacote web, novo loop, novo worker ou dependência no deployment.
- Fluxo: fonte/configuração → paredes → revisão → cálculo e plano →
  criação explícita → resultado/revisão humana. Paredes existentes usam
  seleção nativa, detecção automática de aberturas e escolha NONE/CHANNEL.

O [inventário completo e mapa ação → função → estado → tela](../UI_REDESIGN.md)
foi escrito antes da integração. Também contém os wireframes das seis etapas
e o checklist de smoke.

## Antes → depois

| Antes | Depois |
|---|---|
| Botões com nomes de solver, hierarquia semelhante | Uma ação dominante conforme o estado; termos de usuário |
| Cálculo criava automaticamente | Quantidades reais por fiada/peça, revisão e ação explícita |
| Criar habilitado mesmo com gate beta negativo | Gate já emitido pelo backend refletido na UI; aviso não vira regra nova |
| Log ocupa a tela | Detalhes recolhíveis e relatório organizado |
| Índice temporário na lista | ID já disponível como identidade, índice rotulado como temporário quando necessário |
| Cancelamento podia avançar à tela seguinte | Análise interrompida permanece na etapa; ajustes avisam que alterações aplicadas ficam |
| Família ausente abre popup | Instrução e lista na área de revisão; detalhes técnicos preservados |
| Paredes existentes sem escolha de reforço | Configuração explícita desta execução; cache de estratégia diferente não reaproveitado |
| Layout exige janela alta | Rodapé fixo, conteúdo rolável, DPI local ao Form e limite da área de trabalho |

## Telas e evidências visuais

Imagens são **WinForms reais com dados sintéticos**, renderizadas sem abrir
o Revit. Não representam resultado real de modulação.

| Estado | Antes | Depois |
|---|---|---|
| Fonte | [anterior](../ui-preview/before/01-fonte.png) | [atual](../ui-preview/01-fonte.png) |
| Configuração CAD | [anterior](../ui-preview/before/02-configuracao.png) | [atual](../ui-preview/02-configuracao.png) |
| Paredes | [anterior](../ui-preview/before/03-paredes.png) | [atual](../ui-preview/03-paredes.png) |
| Revisão | [anterior](../ui-preview/before/04-revisao.png) | [atual](../ui-preview/04-revisao.png) |
| Plano | Sem parada antes de criar | [quantidades e ação explícita](../ui-preview/05-plano.png) |
| Criação | Console/log | [atividade e contagem](../ui-preview/06-criacao.png) |
| Resultado | Popup e log | [relatório na janela](../ui-preview/07-resultado.png) |
| Família ausente | Popup | [instrução e lista abertas](../ui-preview/08-familia-ausente.png) |
| Gate crítico | Revisão técnica | [criação bloqueada](../ui-preview/09-gate-critico.png) |
| Cancelamento | Avanço para próxima tela | [análise interrompida na etapa](../ui-preview/10-cancelamento.png) |

[Janela mínima 740×520](../ui-preview/small-740x520.png),
[125%](../ui-preview/scale-1.25.png), [150%](../ui-preview/scale-1.5.png),
[175%](../ui-preview/scale-1.75.png), [200%](../ui-preview/scale-2.png).
Esses últimos são chamadas explícitas a `Scale`, não troca do DPI do Windows;
fontes/área do monitor e comportamento per-monitor dependem do host real.

## Arquivos de produção e motivo

| Arquivo | Motivo |
|---|---|
| `nuvem/core/ui_state.py` (novo) | Tokens, estado, apresentação dos resultados/gates existentes, relatório; sem imports Revit/engine |
| `nuvem/core/ui_components.py` (novo) | Cabeçalho/stepper, cards, seções, tabela, logs, seleção guiada, tamanho/scroll e estilo |
| `nuvem/core/wall_modeling.py` | Menor integração nos construtores/callbacks existentes; cálculo separado de criação, confirmação, estratégia em existentes |

`Script.py`, toda a pasta `engine/`, benchmark, baselines e golden permanecem
idênticos à base. O loader já sincroniza recursivamente `core/`, incluindo os
dois módulos novos. Não foi alterado ou instalado na extensão local.

Outros arquivos: testes de UI e seus dublês, `tools/ui_preview.py`,
`tools/documentation/check_ui_scope.py`, `tools/documentation/render_ui_states.py`,
documentação, imagens e evidências.
O arquivo de regras recebe apenas o contrato UX oficial, sem novo conhecimento
ou alteração de amarração. [Prova por AST e diff](evidence/2026-09-16-ui-scope.json).

## Testes e procedência

[Captura focada final](evidence/2026-09-16-ui-redesign-delivery-focused.json) e
[saída integral](evidence/2026-09-16-ui-redesign-delivery-focused.txt): **301 passed,
1 warning, 61.63s**, exit 0.
Windows, Python 3.14.6, pytest 9.1.1. Inclui teste_script inteiro, UI,
NONE/CHANNEL, catálogo ausente e progresso.
Os 4 FAIL iniciais eram expectativas anteriores da UI (sem abas, rótulo antigo,
seleção sem simular confirmação); foram atualizadas explicitamente, mantendo
as asserções de dados/dispatch. Não foram suprimidos testes físicos.

A captura focada final é de `20d7e39`; as anteriores registram 299 testes em
`8113143` e 300 em `5fff01b`. A suíte completa foi iniciada em `76b758b`, com
árvore limpa. Depois dela, os deltas de produção foram: abertura/instrução de
família ausente (`8113143`), bloqueio de ações concorrentes durante loading
(`5fff01b`) e preservação da referência Python do painel de famílias (`20d7e39`).
Todos são de apresentação e estão cobertos pela captura focada final.
Nenhum teste de domínio mudou entre esses HEADs. Engine/benchmark/loader têm
diff vazio; o handler de execução continua idêntico por AST.

A renderização nativa adicional encontrou um erro que os dublês não expunham:
recuperar o painel por `Controls[index]` devolvia um wrapper pythonnet sem o
método Python auxiliar. A correção conserva a referência original; as três
renderizações de erro/cancelamento passaram após o ajuste. Esse ensaio é do
pythonnet local, não prova de compatibilidade do runtime embutido do pyRevit.

[Suíte completa](evidence/2026-09-16-ui-redesign-suite.json),
[log integral](evidence/2026-09-16-ui-redesign-suite.txt): **1228 passed,
3 failed, 1 warning, 1273.64s**. Não é PASS. As três falhas coincidem por nome
e asserção com o [checkpoint oficial anterior](2026-09-14-channel-final-merge.md):

| Teste | Asserção observada |
|---|---|
| `test_projeto_nao_regrediu_contra_o_baseline[torre_easy_lo_r00_tp1]` | `JUNCTION_MISSING_BINDING`: 8 → 9 |
| `test_projeto_nao_regrediu_contra_o_baseline_versionado[torre_easy_lo_r00_tgd-v2]` | `compensators`: 61 → 62 |
| `test_retencao_nativa_de_gil_dispara_e_despeja_as_pilhas` | `UnboundLocalError: ctypes` no Windows, linha 96 |

Não foi feita nova execução completa da base nesta missão: a atribuição histórica
usa o checkpoint oficial e a identidade do código de domínio. Baselines e testes
dessas falhas não foram alterados. O warning é `codecs.open` obsoleto.

## Limitações restantes e riscos

1. **Smoke Revit pendente.** A renderização local não valida o pythonnet
   embutido do pyRevit, a seleção nativa, o ExternalEvent ou a criação real.
   O ambiente em uso não foi alterado enquanto o #42 está em desenvolvimento.
2. **DPI nativo pendente.** Definidos AutoScaleMode.Dpi, base 96 DPI, mínimo,
   limite de monitor e rolagem. Ensaios de Scale e tamanho mínimo passam
   visualmente; troca real 100/125/150/175/200% precisa do checklist.
3. **Fase inicial CAD ainda usa output pyRevit.** Extração/detecção/criação
   de paredes antes da Tela 1 mantém o caminho síncrono e seus diálogos.
   Não foi criado um novo mecanismo de bombeamento/thread para essa fase.
4. **Lote de sessão anterior:** quando o resultado anterior está em memória,
   a confirmação mostra o número. Em sessão nova, mostra explicitamente que
   eventual lote será substituído; descobrir sua quantidade continua no backend,
   no contexto de execução existente. Não consultar o modelo a cada redraw.
5. **Progresso:** contagem/percentual reais e tempo nos callbacks existentes.
   Trechos sem callback continuam sujeitos à responsividade do host/GIL;
   não se promete atualização por segundo independente do motor.
6. **Métricas:** contagem total apenas com plano de todas as fiadas disponível;
   aberturas detectadas não são apresentadas como aberturas tratadas. Não há
   novo resultado físico presumido ou novo validador na UI.
7. **Popups legados:** autenticação, fallbacks e fluxo de união conservam os
   diálogos atuais. Revisão final, famílias e logs das telas principais foram
   incorporados à janela; não se declara eliminação de todo popup do projeto.
8. **PR #42:** sobreposição textual em `wall_modeling.py`, regras e status.
   Reaplicar apenas os hooks de UI depois de preservar o solver do #42; nunca
   resolver por substituição integral de arquivo. Nenhum commit nesta branch
   usa o #42 como ancestral. Na observação `7724ab6` do #42, a comparação de
   funções por AST encontrou **zero funções alteradas em comum** em
   `wall_modeling.py`; [mapa de sobreposição](evidence/2026-09-16-ui-pr42-overlap.json).
   Isso reduz o risco textual, mas não substitui a reconciliação após o #42.

## Smoke e integração

| Critério de aceitação do pedido | Evidência / situação |
|---|---|
| 1. Fluxo inteiro mapeado | Inventário e mapa de callbacks, incluindo loader/fallbacks/união |
| 2. Wizard claro | Seis etapas lógicas, cabeçalho persistente, áreas de revisão/plano/resultado |
| 3. Estratégia clara | NONE/CHANNEL, família pendente/ausente/disponível, LINTEL não selecionável |
| 4. Paredes existentes | Instrução, confirmação da seleção, coleta automática e reforço explícito |
| 5. Progresso informativo | Contador, percentual, etapa e tempo nos callbacks; fase CAD permanece pendente |
| 6. Erros acionáveis | Gates/famílias/geometria desatualizada nas telas principais; fallbacks legados permanecem |
| 7. Logs secundários | Recolhidos por padrão |
| 8. Resultado final | Relatório em áreas de resultados, validação, avisos, retenções, famílias e desempenho |
| 9. DPI | Render e Scale ensaiados; Windows/Revit nativo pendente |
| 10. Nenhum solver alterado | Diff vazio de engine/benchmark, 188 definições e handler intactos |
| 11. Nenhuma regra física na UI | Adaptação dos resultados e gates emitidos; nenhum cálculo geométrico |
| 12. Loading/cancelamento | Testes de estados, ausência de auto-criação, cancelamento e concorrência; smoke Revit pendente |
| 13. Fluxo anterior | 301 testes focados, incluindo test_script completo; mudança intencional somente na interação documentada |
| 14. Smoke manual | **Não executado no Revit; não está PASS** |

Consulta de API usada apenas para apresentação do nome do documento:
[Document.Title — Revit API Docs 2027](https://www.revitapidocs.com/2027/6cbb045c-a145-04f2-0a26-1ac9285c4d17.htm).
As ações de seleção/zoom continuam usando os callbacks já existentes.

Checklist em [UI_REDESIGN](../UI_REDESIGN.md#smoke-manual-obrigatório-registrar-evidência-não-presumir-pass),
todo pendente no Revit. Revisar o draft, reconciliar após #42 e executar esse
checklist antes de promoção. **Nenhum merge autorizado ou realizado.**
