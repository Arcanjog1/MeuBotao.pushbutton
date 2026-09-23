# Modulação Automática — redesign compacto escuro

```json
{
  "date": "2026-09-16",
  "scope": "historical",
  "branch": "codex/modulacao-automatica-ui-redesign",
  "head": "ec5142402577520496fe144e08d02749338b695f",
  "base": "55e990d962ed22ae1021f0d335db197607bddda1",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/44",
  "objective": "Aplicar a referência visual real do vídeo ao fluxo WinForms: compacto, grafite, preview contextual e linguagem de produto, sem modificar solver.",
  "changes": [
    "Tokens de cor/tipografia, abas nativas discretas, campos agrupados e preview 2D local.",
    "Configuração em duas áreas; resumos em linha; diagnósticos separados; relatório recolhido e resultado curto.",
    "Exclusividade real dos rádios CAD/existentes/união; grupos de aberturas e modo de parede independentes.",
    "Mensagens, revisão explícita, estados de execução e bloqueios de UI preservam decisões do backend."
  ],
  "tests": [
    "307 passed / 1 warning em 69.61s, exit 0; Windows Python 3.14.6/pytest 9.1.1, HEAD ec51424; evidence/2026-09-16-dark-ui-focused.json e .txt; UI, CHANNEL/gates, test_script completo e progresso.",
    "Ensaio nativo WinForms/pythonnet: sete verificações de interação PASS, docs/ui-dark-preview/interaction-checks.json; sem Revit.",
    "Renderização nativa com dados sintéticos: telas principais, CHANNEL, existentes, família ausente, gate crítico, cancelamento, janela mínima e Scale 100/125/150/175/200.",
    "Prova AST/diff: 188 definições fora da UI intactas, handler e mecanismos de threading/pump/timer intactos, engine/benchmark/loader sem diff."
  ],
  "known_failures": [
    "DPI nativo e smoke no Revit/pyRevit ainda não executados.",
    "Suíte completa anterior em 76b758b: 1228 passed / 3 failed; TP1 V1 JUNCTION_MISSING_BINDING 8→9, TGD V2 compensators 61→62, UnboundLocalError ctypes no Windows. Não reexecutada integralmente nesta rodada visual; escopo físico permanece idêntico."
  ],
  "physical_deltas": ["Nenhum: solver, CHANNEL físico, B34/B54/B19, prism, junction, ETAPA 3B, benchmark e baselines não alterados."],
  "decisions_taken": [
    "Evoluir a branch própria e o mesmo draft #44, baseados na main observada; nenhum commit do #42 utilizado.",
    "Priorizar dark theme local; preservar chrome e controles de progresso do Windows, sem mudar tema/DPI do processo Revit.",
    "Preview esquemático explicitamente ilustrativo; nunca representar contagem ou validação física calculada."
  ],
  "decisions_pending": ["Smoke no botão real, DPI nativo e integração futura após encerramento do #42."],
  "next_steps": ["Revisar estética e executar checklist no Revit antes de promover; manter draft sem merge."],
  "references": [
    {"path": "docs/UI_VISUAL_REFERENCE.md"},
    {"path": "docs/UI_REDESIGN.md"},
    {"path": "docs/PROJECT_STATUS.md"},
    {"path": "docs/checkpoints/evidence/2026-09-16-dark-ui-focused.json"},
    {"path": "docs/checkpoints/evidence/2026-09-16-dark-ui-scope.json"},
    {"path": "docs/ui-dark-preview/interaction-checks.json"}
  ]
}
```

> Entrega anterior do #44. Nesta branch, sucedida pelo [redesign premium](2026-09-16-premium-ui-redesign.md). O registro original de evidência permanece preservado.

## Veredito

**PARTIAL — limitações.** Implementação e prévias disponíveis no
[PR #44 draft](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/44).
Não houve merge, alteração da branch do #42 ou instalação no botão em uso.
Não declarar READY sem smoke real e DPI nativo.

Base inicial e última main buscada: `55e990d962ed22ae1021f0d335db197607bddda1`.
HEAD de código avaliado: `ec5142402577520496fe144e08d02749338b695f`.
Branch própria: `codex/modulacao-automatica-ui-redesign`, continuação do
trabalho anterior; a main não avançou entre as duas rodadas.
Checkout: `C:\Users\CIVIX\modulacao-ui-redesign`.

## LIÇÕES EXTRAÍDAS DO VÍDEO

Estudado no navegador: [BIM Coder — Cotas e Detalhamento automático de
Arquitetura no Revit](https://www.youtube.com/watch?v=XRQ8CZEwTCE).
Amostras visuais observadas: 4:10, 5:51 e 7:20, além dos trechos de seleção.
Não se afirma reprodução integral do vídeo.

- 4:10: configuração à esquerda, preview à direita, abas curtas, rodapé fixo.
- 5:51: diálogo compacto, lista agrupada e uma ação principal.
- 7:20: campos alinhados, ajuda subordinada e estrutura estável entre abas.
- Superfícies escuras próximas, bordas sutis e azul reservado a destaques.

Aplicação, medidas próprias, análise anterior e seis wireframes estão em
[UI_VISUAL_REFERENCE](../UI_VISUAL_REFERENCE.md), commit `ae88544`, anterior
à implementação. Nenhuma marca, imagem ou logo do autor foi reutilizada.

## Stack e arquitetura visual

**WinForms + CPython/pythonnet + pyRevit**, preservando ExternalEvent e
callbacks existentes. Não foi introduzido WPF, Electron, web ou dependência
nova no deployment. O loader já sincroniza os módulos de `core/`.

Janela principal 940 × 680 px lógicos; origem 860 × 570; paredes 940 × 620;
mínimo 740 × 520. Preview é ocultado no plano quando o espaço fica reduzido,
para preservar resumo, lista e ação. Conteúdo avançado rola; rodapé é fixo.

Sistema visual: grafite `Background`, `Surface`, `SurfaceAlt`, `Border`,
`TextPrimary`, `TextSecondary`, `Primary`, `Success`, `Warning`, `Danger`;
Segoe UI com papéis de título/seção/campo/corpo/ajuda/status e escala de
espaçamento 4/8/12/16/24/32. Valores estão centralizados em `ui_state.py`.

Componentes: cabeçalho, TabDeck com botões nativos, field row, resumo em linha,
banner de estado, progresso existente, lista de problemas, preview pintado
localmente, botões e detalhes expansíveis. ComboBox/header de lista e botão
desabilitado recebem pintura local; foco/teclado e seletores nativos continuam.

## Antes / depois e screenshots

Todas as imagens abaixo são **controles WinForms reais com dados sintéticos**,
sem criação de elementos Revit. 34 paredes, 44 aberturas e 58 blocos são fixtures.

| Tela | Candidato anterior | Atual |
|---|---|---|
| Origem | [claro](../ui-preview/01-fonte.png) | [escuro e preview](../ui-dark-preview/01-fonte.png) |
| Configuração | [pilha de campos](../ui-preview/02-configuracao.png) | [abas, projeto/CAD e preview](../ui-dark-preview/02-configuracao.png) |
| CHANNEL | Sem preview contextual | [esquema com canaletas](../ui-dark-preview/08-channel.png) |
| Existentes | Instruções textuais | [seleção e contexto](../ui-dark-preview/09-paredes-existentes.png) |
| Paredes | [cards e espaço vazio](../ui-preview/03-paredes.png) | [resumo e atividade](../ui-dark-preview/03-paredes.png) |
| Pendências | [IDs e tabela](../ui-preview/04-revisao.png) | [linguagem de produto](../ui-dark-preview/04-revisao.png) |
| Plano | [cards e tabela ampla](../ui-preview/05-plano.png) | [quantidades compactas](../ui-dark-preview/05-plano.png) |
| Criação | [console expandido](../ui-preview/06-criacao.png) | [estado e progresso](../ui-dark-preview/06-criacao.png) |
| Resultado | [relatório extenso](../ui-preview/07-resultado.png) | [resumo e relatório recolhido](../ui-dark-preview/07-resultado.png) |
| Erros/cancelamento | Estados da primeira versão | [família](../ui-dark-preview/10-familia-ausente.png), [gate](../ui-dark-preview/11-gate-critico.png), [cancelamento](../ui-dark-preview/12-cancelamento.png) |

O antes da main, anterior a ambos os candidatos, está em
[ui-preview/before](../ui-preview/before/02-configuracao.png).

## Fluxo e comportamento

Configuração → Paredes → Modulação → Revisão do plano → Criação → Resultado.
São etapas lógicas: o fluxo conserva formulários próprios para fonte,
configuração/seleção e análise, respeitando as transições do host. **Ainda não
é uma única janela com navegação retroativa entre todas as seis etapas.**

CAD mostra projeto, nível, altura, layers e espessuras; aberturas/reforço ficam
em outra aba e modos avançados recolhidos. Valores lembrados e validações
existentes são preservados. Existentes continua usando seleção nativa e
detecção de aberturas; não há seleção modeless simulada.

Modulação calcula; Revisão mostra quantidades do plano de todas as fiadas.
Gates críticos continuam vindo do backend. Avisos não se tornam novas regras.
Atualizar modulação informa a substituição e mostra a quantidade quando o lote
anterior está em memória. Em nova sessão, a descoberta continua no backend.

Durante execução, ações concorrentes e abas ficam indisponíveis; estado
visível substitui a mensagem de plano pronto. Contagens/tempo vêm dos mesmos
callbacks. Sem total: indeterminado. Não inventar percentuais ou cancelamento
transacional. Resultado mostra conclusão, pendências ou falha, com relatório
amigável recolhido e diagnóstico técnico separado.

IDs permanecem nos dados usados pelo zoom e nos detalhes técnicos. Números
"Parede 1" da lista são identificadores locais de ocorrência, não ElementIds.
As mensagens traduzem diagnósticos existentes; não classificam a validade
física do modelo. Preview não consulta o documento, não gera planos e não
valida amarração. Nenhuma lógica futura de mover aberturas foi implementada.

## Arquivos de produção tocados nesta rodada e motivo

| Arquivo | Motivo |
|---|---|
| `nuvem/core/ui_state.py` | Tokens escuros, ordem das etapas, mensagens e relatório amigável |
| `nuvem/core/ui_components.py` | Layout, campos, abas, preview, resumos, estados e exclusividade dos rádios de fonte |
| `nuvem/core/ui_preview_panel.py` (novo) | Desenhos esquemáticos locais, sem API/modelo/solver |
| `nuvem/core/ui_native_style.py` (novo) | Pintura local de controles nativos para consistência e legibilidade |
| `nuvem/core/wall_modeling.py` | Somente imports/tokens e integração de apresentação em status, linhas de problemas e etapas |

Outros arquivos: testes de UI, stub do evento SizeChanged, renderer de
estados nativos, documentos, regras UX, screenshots e evidências. O registro
UX foi atualizado em `nuvem/REGRAS_MODULACAO_BLOCOS.md`; nenhuma regra física.

## Prova de escopo e testes

[Prova AST e diff](evidence/2026-09-16-dark-ui-scope.json): engine, benchmark,
baseline e loader sem alterações, inclusive desde o código avaliado anterior
`20d7e39`; 188 definições fora da UI e handler completo intactos. Métodos
protegidos de threading, dispatch, pump e timer permanecem idênticos.

[Captura focada](evidence/2026-09-16-dark-ui-focused.json) e
[log](evidence/2026-09-16-dark-ui-focused.txt) registram comando, SHA/tree,
ambiente, duração, exit code e hash do log. Inclui `tests/test_script.py`
inteiro, UI, CHANNEL/gates e progresso: **307 passed, 1 warning, 69,61 s**,
exit 0. Warning herdado de `codecs.open` obsoleto. Dois testes antigos foram adaptados
à nova navegação e ao texto amigável; dispatch e dados continuam verificados.
Foram adicionados seis testes sobre IDs/detalhes, análise pulada, execução,
lote existente, preview e falhas no resumo final.

[Ensaio nativo](../ui-dark-preview/interaction-checks.json): Python 3.13 e
pythonnet 3.1.0, sete verificações PASS. Encontrou a exclusividade ausente dos
rádios separados em painéis — `GroupName` não é API de agrupamento WinForms.
A correção está somente no comportamento de escolha de fonte. O teste
verifica também que aberturas e modo de paredes permanecem independentes.

A suíte completa anterior foi executada em `76b758b`: **1228 passed / 3 failed**,
1273,64 s; [captura preservada](evidence/2026-09-16-ui-redesign-suite.json).
Não foi repetida integralmente nesta rodada visual. Falhas históricas, ainda
abertas: TP1 V1 `JUNCTION_MISSING_BINDING` 8→9; TGD V2 `compensators` 61→62;
`UnboundLocalError: ctypes` no teste de retenção nativa de GIL em Windows.
O código físico e esses testes não mudaram; não houve regravação de baseline.

## DPI, compatibilidade e limitações

- [100%](../ui-dark-preview/scale-1.png), [125%](../ui-dark-preview/scale-1.25.png),
  [150%](../ui-dark-preview/scale-1.5.png), [175%](../ui-dark-preview/scale-1.75.png),
  [200%](../ui-dark-preview/scale-2.png), [740 × 520](../ui-dark-preview/small-740x520.png).
  São chamadas a Scale, **não** troca de DPI Windows. Em escalas altas, o
  monitor limita a altura; conteúdo rola. Não declarar DPI nativo aprovado.
  Fontes mantêm os pontos originais nesse ensaio; ele não simula a métrica
  real de texto de um monitor com outro DPI.
- Smoke no Revit/pyRevit pendente. Renderer local não comprova runtime embutido,
  seleção real, callbacks de ExternalEvent, criação ou comportamento do loader.
- Tema escuro é local e prioritário; não há sincronização com tema do Revit
  nem tema claro. Barra de título, rolagem, seletores e progresso conservam
  partes nativas do Windows. Não se promete skin integral do sistema.
- Fase inicial CAD ainda usa saída pyRevit e execução síncrona existente.
  Autenticação, fallbacks, união e confirmações destrutivas mantêm diálogos.
- Trechos sem callback podem continuar bloqueando pintura; sem alteração de
  threading/DoEvents não há garantia de animação contínua durante retenção de GIL.
- Preview é ilustrativo e rotulado; não é visualização do plano calculado.

## Smoke manual e integração futura

Checklist funcional em [UI_REDESIGN](../UI_REDESIGN.md#smoke-manual-obrigatório-registrar-evidência-não-presumir-pass),
todo pendente no Revit. Acrescentar:

- [ ] Alternar CAD/existentes/união, conferir seleção exclusiva e retorno do picker.
- [ ] Alterar reforço e confirmar preview, sem alterar grupo de aberturas.
- [ ] Teclado/foco nas abas, lista, campos e confirmações.
- [ ] Expandir relatório/detalhes em janela mínima e DPI nativo 100–200%.
- [ ] Conferir tema, seleção e contraste no Windows usado pelo pyRevit.

#42 não foi modificado nem usado como base. A
[comparação anterior](evidence/2026-09-16-ui-pr42-overlap.json) é um snapshot
datado em `7724ab6`, sem funções alteradas em comum naquele momento — não uma
garantia sobre o HEAD futuro do #42. Reconciliar `wall_modeling.py`, regras e
status depois que o #42 fechar, preservando a física e reaplicando os hooks
de UI. **PR permanece draft; nenhum merge.**
