# UI premium — preparação pós-PR #42

## Escopo e estado

Missão de 2026-09-17, sobre `ca301c34da730b8fea7ef5bd7256a36f81a51e42`.
Somente apresentação. Nenhuma alteração em `wall_modeling.py`, solver ou regras
nesta missão. Nenhum merge, rebase, instalação no botão real ou edição do #42.
O PR #46 já continha alterações de UI no host antes desta missão; elas não foram
ampliadas aqui. A integração dos novos dados permanece **pendente do pós-#42**.

## Fluxo revisado

| Etapa lógica | Apresentação / critério de conferência |
|---|---|
| Configuração | Origem exclusiva; abas Projeto/CAD e Aberturas/reforço; NONE/CHANNEL; ação principal no rodapé. |
| Análise | Selecionadas e detectadas não equivalem a analisadas. Novo contador de analisadas exige informação explícita; ausência = —. |
| Microajuste | Subetapa contextual entre análise e modulação; proposto, aplicando, confirmado, desnecessário, falhou ou interrompido. O stepper compacto continua com seis etapas. |
| Modulação | Console existente, progresso por eventos reais; nenhum timer de percentuais. Na reanálise, resumo anterior invalidado e abas bloqueadas durante execução. |
| Revisão | Quantidade de todas as fiadas; paredes analisadas; movimentos confirmados; avisos e bloqueios críticos. Gate existente continua sendo autoridade para habilitar criação. |
| Criação | Console existente mostra done/total da operação; total desconhecido permanece indeterminado. Não permite navegação concorrente. |
| Resultado | Título de sucesso/parcial/falha, blocos criados, falhas, confirmação de microajuste, relatório e revisão humana. |

Avisos e bloqueios do novo resumo são contagens fornecidas pelo adaptador futuro.
Não somar categorias do solver que possam representar o mesmo incidente.
Enquanto não houver adaptador, aparecem como —; o banner e o botão continuam
respeitando os gates já implementados. Zero só pode ser publicado após avaliação.
Nenhuma mensagem de sucesso deste componente libera uma criação bloqueada.

## Contrato de apresentação (implementado, ligação futura)

`report['ui_execution']` inicializa o resumo. Para atualizações na thread de UI:

```python
form._ux.present_execution(form, {
    'run_id': 'identidade-unica-da-execucao',
    'revision': 0,
    'walls_analyzed': 34,
    'openings_moved': None,
    'warnings': 1,
    'hard_gates': 0,
    'adjustment_status': 'planned',
    'detail': 'Detalhes fornecidos pelo adaptador'
}, new_run=True)
```

Contrato: snapshots completos; revisão crescente por execução; contadores inteiros
naturais ou None; mensagens detalhadas já preparadas pelo adaptador. Eventos de outra
execução ou revisão antiga são descartados. `new_run=True` é reservado ao início real
de uma execução, nunca usado indiscriminadamente em callbacks. Iniciar reanálise
invalida a identidade anterior. Após `busy(form, 3)`, abrir nova identidade antes de
publicar seus resultados. Publicar snapshot antes de `solved`/`completed`, para o
relatório copiável refletir a mesma revisão do resumo.

Estados: `planned`, `applying`, `confirmed`, `not_required`, `failed`, `cancelled`.
Ausência/valor desconhecido = confirmação não recebida. `confirmed` com contador
válido >0 habilita a frase “Abertura foi ajustada automaticamente”. Com zero, informa
nenhuma movimentação. Não usar simples presença de lista `automatic_adjustments`.
O detalhe deve identificar abertura/parede, deslocamento e unidade, origem da
confirmação e pendências; a UI não calcula esses valores.

## Proposta separada para wall_modeling.py — NÃO APLICADA

1. Depois do #42, revisar o contrato consolidado e localizar o evento que realmente
   confirma a transação no Revit. No snapshot atual, `plan_opening_micro_adjustments`
   apenas planeja. No engine, `record['applied']` significa offset escolhido não zero;
   `confirmed` pertence à avaliação do plano. Nenhum dos dois certifica transação Revit.
2. Em `_WallReviewForm._on_analyze_done`, transportar quantidade efetivamente analisada
   e identidade da execução, sem substituir por quantidade selecionada.
3. Em `_PostCreationForm._on_solve_click`, criar identidade após invalidar a anterior;
   em `_on_fix_done` e `_on_solve_done`, preparar snapshots apenas com dados conhecidos.
   Verificar exatamente onde o fluxo final do #42 expõe esses resultados antes de editar.
4. Publicar `confirmed` somente no callback posterior à confirmação efetiva da aplicação;
   se rollback, cancelamento ou erro, não reportar movimentos confirmados sem evidência
   de persistência. Não implementar movimentação no adaptador de UI.
5. Em `_on_create_done`, publicar o snapshot final antes de `completed`. Conservar
   ExternalEvent, transações, watchdog, cancelamento, pausa e dispatcher existentes.
6. `_ProgressConsole.set_progress(done, total, detail)` permanece a fronteira de
   progresso real. Não inferir porcentagem a partir do tempo ou da etapa visual.
7. Reexecutar testes de criação/gates/progresso e smoke Revit antes de integrar.

Esta é uma proposta por símbolos, não um patch com linhas frágeis de uma branch
experimental. Nenhuma chamada adicional ao host foi aplicada.

## Mapa de conflitos (snapshot fixo)

Main observada: `55e990d962ed22ae1021f0d335db197607bddda1`.
[#42](https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/42) aberto no HEAD
`759bcd453dae3dabba4acee4b3bdaabca875237c`, consultado somente para leitura.
Comparação: alterações de cada branch contra a main; não houve ensaio de merge.

| Arquivo | Trechos afetados / risco | Reconciliação após autorização futura |
|---|---|---|
| `nuvem/core/wall_modeling.py` | #42: região física ~3681–4144 na base, wrapper de solve, microajuste e reforço. #46 anterior: UI ~9116 em diante, consoles/forms/revisão e chamadas de apresentação. Regiões textualmente distintas neste snapshot; risco semântico nos resultados entregues à UI. | Preservar integralmente física consolidada; reaplicar somente hooks de apresentação e revisar contratos de callbacks. Nunca aceitar um lado inteiro do arquivo. Esta missão tem zero diff no arquivo. |
| `nuvem/REGRAS_MODULACAO_BLOCOS.md` | #42 acrescenta conhecimento físico; #46 contém documentação UI de entregas anteriores. Mesmo arquivo, conteúdo normativo sensível. | Preservar novas regras do #42; reconciliar apenas documentação de UX sem duplicar/reescrever física. Zero diff nesta missão. |
| `docs/PROJECT_STATUS.md` | Ambas atualizam candidatos e evidências. Alto risco de sobrescrever estado recente. | Refazer fetch e reconciliar entradas por SHA/PR; conservar histórico e distinguir integrado/candidato. |
| `nuvem/core/ui_*.py` | Não constam nas mudanças do #42 observado. | Manter componentes; conectar novo adaptador só depois do contrato final. |
| `tests/test_script.py` | Modificado no #46 anterior; não consta no #42 deste snapshot. Risco futuro, não conflito atual observado. | Conservar testes físicos e adaptar somente expectativas de apresentação necessárias. |
| `docs/checkpoints/`, evidências | Arquivos de nomes distintos nas duas entregas. | Preservar ambos; checkpoint novo para reconciliação, nunca sobrescrever o de outra sessão. |

## Screenshots e revisão visual

[Capturas finais](ui-post42-preview/manifest.json): WinForms nativo em processo
isolado com dados sintéticos. Não são screenshots de execução no Revit.

- [Configuração](ui-post42-preview/02-configuracao.png)
- [Análise](ui-post42-preview/03-paredes.png)
- [Microajuste proposto](ui-post42-preview/microajuste-planned.png)
- [Microajuste confirmado — fixture](ui-post42-preview/microajuste-confirmed.png)
- [Plano e contadores](ui-post42-preview/microajuste-plano.png)
- [Gate crítico](ui-post42-preview/gate.png)
- [Erro](ui-post42-preview/error.png)
- [Progresso](ui-post42-preview/progress.png)
- [Criação](ui-post42-preview/06-criacao.png)
- [Resultado](ui-post42-preview/microajuste-resultado.png)

Revisados: contraste e símbolos além de cor; foco/Tab nas abas e seletores nativos;
preview explicitamente ilustrativo; relatório acessível por teclado; erro recuperável;
rodapé preservado em janela reduzida. Matriz: bounds e fontes em 100/125/150/175/200%,
1366×768, 1920×1080, 2560×1440. Não equivale a DPI nativo nem teste com leitor de tela.

## Checklist de smoke real no Revit — PENDENTE

Registrar versão Revit/pyRevit/Windows, SHA instalado, projeto de teste, DPI/monitor,
resultado esperado/observado e screenshot por cenário. Executar em cópia de teste.

- [ ] Abrir pelo botão real; configurar CAD e paredes existentes; cancelar e reabrir.
- [ ] Navegar por Tab/Shift+Tab, Enter/Esc, abas e seletor NONE/CHANNEL; foco visível.
- [ ] Em 100/125/150/175/200% reais, mover entre monitores, reduzir e maximizar;
      verificar texto, preview, scrolls e ação principal. Não mudar DPI global via plugin.
- [ ] Analisar paredes: comparar contador com resultado efetivo; pular análise mantém
      desconhecido; não apresentar selecionadas como analisadas.
- [ ] Após integração: proposta sem aplicar não mostra abertura movida; confirmação
      pós-transação mostra contagem correta; deslocamento e unidades conferidos no modelo.
- [ ] Após integração: microajuste dispensado, erro, cancelamento/rollback e resultado
      parcial preservam status correto; evento atrasado não substitui execução nova.
- [ ] Reanalisar: esconder plano anterior; bloquear ações concorrentes; atualizar quantidades
      de todas as fiadas somente após conclusão; não criar automaticamente.
- [ ] Família ausente e hard gate: criação desabilitada com motivo claro; warning isolado
      segue decisão do backend, sem novo bloqueio físico criado pela UI.
- [ ] Progresso com total conhecido confere done/total; desconhecido indeterminado;
      pausar/retomar/cancelar preserva comportamento do host e não congela a janela.
- [ ] Criar, falhar parcialmente e concluir: conferir instâncias/relatório; copiar relatório;
      revisão humana continua necessária antes de excluir referências.
- [ ] Repetir atualização de lote e fechamento/reabertura; testar nomes longos, lista vazia,
      muitas pendências e leitor de tela. Não declarar READY antes desses resultados.
