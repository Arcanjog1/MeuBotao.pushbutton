# Redesign da experiência — entrega candidata

```json
{
  "date": "2026-09-16",
  "branch": "codex/modulacao-automatica-ui-redesign",
  "head": "5fff01b1b2b7614036f0ec363797a3b598613453",
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
    "300 passed: tests/test_ui_redesign.py, tests/test_channel_ui_and_family_gate.py, tests/test_script.py, nuvem/tests/test_progress.py; Windows CPython 3.14.6/pytest 9.1.1, 84.40s; evidence/2026-09-16-ui-redesign-final-focused.json e .txt.",
    "39 passed na seleção de testes de UI, configuração, gates, docking e paredes existentes.",
    "Renderização WinForms real fora do Revit: Python 3.13/pythonnet 3.1.0; sete estados, comparação anterior, Scale 1/1.25/1.5/1.75/2 e janela 740x520. Não equivale a DPI nativo nem smoke Revit.",
    "check_ui_scope.py: 188 definições fora da UI intactas; handler completo e funções de threading/pump/timer intactos; engine/benchmark/loader sem diff.",
    "Suíte completa em andamento na captura 2026-09-16-ui-redesign-suite; não declarada PASS neste checkpoint provisório."
  ],
  "known_failures": [
    "Nenhuma falha nos 300 testes focados finais; um DeprecationWarning herdado de codecs.open.",
    "Smoke no Revit e escala nativa Windows ainda não executados; limitações funcionais descritas abaixo."
  ],
  "physical_deltas": ["Não aplicável: solver, validadores físicos, catálogo, criação, transações e geometria não alterados."],
  "decisions_taken": [
    "Pedido do usuário autoriza branch própria sobre main, commits/push e PR draft; não autoriza merge.",
    "Novo pedido substitui criação automática após cálculo por revisão antes de Criar blocos no Revit.",
    "Manter WinForms e callbacks existentes; não alterar threading nem implementar lógica física na apresentação."
  ],
  "decisions_pending": ["Reconciliar com #42 após seu encerramento; executar smoke Revit/DPI antes de considerar pronto."],
  "next_steps": ["Concluir captura da suíte e publicar PR draft; nenhum merge.", "Executar checklist manual em checkout de teste isolado do #42."],
  "references": [
    {"path": "docs/PROJECT_STATUS.md"},
    {"path": "docs/UI_REDESIGN.md"},
    {"path": "nuvem/core/ui_state.py"},
    {"path": "nuvem/core/ui_components.py"},
    {"path": "tests/test_ui_redesign.py"},
    {"path": "docs/checkpoints/evidence/2026-09-16-ui-redesign-final-focused.json"},
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
- HEAD avaliado: `5fff01b1b2b7614036f0ec363797a3b598613453`.
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
`tools/documentation/check_ui_scope.py`, documentação, imagens e evidências.
O arquivo de regras recebe apenas o contrato UX oficial, sem novo conhecimento
ou alteração de amarração. [Prova por AST e diff](evidence/2026-09-16-ui-scope.json).

## Testes e procedência

[Captura focada final](evidence/2026-09-16-ui-redesign-final-focused.json) e
[saída integral](evidence/2026-09-16-ui-redesign-final-focused.txt): **300 passed**,
Windows, Python 3.14.6, pytest 9.1.1. Inclui teste_script inteiro, UI,
NONE/CHANNEL, catálogo ausente e progresso.
Os 4 FAIL iniciais eram expectativas anteriores da UI (sem abas, rótulo antigo,
seleção sem simular confirmação); foram atualizadas explicitamente, mantendo
as asserções de dados/dispatch. Não foram suprimidos testes físicos.

A captura focada final é de `5fff01b`; a anterior (299 passed) é de `8113143`. `8113143..c7db0fe` muda somente renderizador,
imagens e verificador documental, comprovável por diff. A suíte completa foi
iniciada em `76b758b`; o único delta de produção posterior é abrir a seção de
famílias ausentes e mostrar a instrução no cabeçalho (3 linhas), coberto pela
execução focada final. Nenhum teste de domínio mudou entre esses HEADs. A revisão `5fff01b` acrescenta somente desabilitação de ações concorrentes durante loading e um teste de UI; captura focada final concluída: 300 passed. A equivalência dos arquivos de domínio entre a suíte completa e o HEAD final é literal (nenhum diff em engine/benchmark nem no handler de execução).

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
   usa o #42 como ancestral.

## Smoke e integração

Checklist em [UI_REDESIGN](../UI_REDESIGN.md#smoke-manual-obrigatório-registrar-evidência-não-presumir-pass),
todo pendente no Revit. Revisar o draft, reconciliar após #42 e executar esse
checklist antes de promoção. **Nenhum merge autorizado ou realizado.**
