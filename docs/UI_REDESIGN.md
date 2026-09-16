# Redesign da experiência de modulação

Base inicial: `55e990d962ed22ae1021f0d335db197607bddda1` (`origin/main`).
Branch: `codex/modulacao-automatica-ui-redesign`. O PR #42 não é base.

## Inventário antes da implementação

Stack: WinForms, CPython/pythonnet e pyRevit; configuração modal e revisão
modeless. `Script.py` autentica, sincroniza recursivamente `core/` e instala
compatibilidade de `forms.*`. Sem Qt, WPF ou navegador no produto.

| Ação do usuário | Função/classe em core/wall_modeling.py | Estado → próxima interface |
|---|---|---|
| Abrir botão | `run`, `main`, `_ask_wall_source_mode` | Fonte CAD / existentes / união |
| Escolher CAD e selecionar desenho | `main`, `ask_setup`, `_SetupForm` | Layer, referência estrutural, espessuras, nível, altura, aberturas, modo de paredes, reforço → criação |
| Trocar layer | `_SetupForm._reload_thicknesses` | Sugestões em cache, validação inline |
| Usar seleção / selecionar paredes | `_select_existing_walls_for_modulation`, `_build_existing_walls_selection` | Confirmação modal + instrução modal + seleção nativa → coleta automática de aberturas |
| Unir paredes | `run_merge_existing_walls` | Seleção, resumo/confirmar reconstrução, relatório, oferecer modulação |
| Criar paredes | `main` | Progresso no output pyRevit; resumo → `_WallReviewForm` (Tela 1) |
| Analisar paredes | `_WallReviewForm._on_start_click` → handler `analyze` | Console, pausa/cancelamento → Tela 2 |
| Continuar sem ajustar | `_on_skip_click` | Confirmar omissão de análise → Tela 2 |
| Revisar problemas | `_PostCreationForm._populate_error_rows` | Tabela; seleção/duplo clique → ação `zoom` já existente |
| Aplicar ajustes | `_on_fix_click` → `fix_errors` | Progresso, pausa/cancelamento, linhas corrigidas → cálculo liberado |
| Calcular | `_on_solve_click` → `solve` | Catálogo, famílias CHANNEL, cálculo, callbacks por parede/faixa/etapa |
| Terminar cálculo (antes) | `_on_solve_done` | Criação disparada automaticamente; usuário não revisava quantidades |
| Criar/recriar | `_on_create_click` → `create` | Validações do backend, remoção de lote anterior, criação, realces → resumo modal |
| Revisar e excluir referências | `_on_delete_click` → `delete` | Checkbox de revisão humana + confirmação destrutiva |
| Detalhes | `_ProgressConsole`, `_append_log`, `_on_copy`, `_save_log_to_file` | Logs ocupam grande parte das telas; output pyRevit também recebe relatório |
| Erro | `forms.alert`, status das telas, callbacks `kind=error` | Mistura erros técnicos e instruções; catálogo ausente abre popup |
| Cancelar/fechar | `_on_cancel_click`, `_on_fix_cancel_click`, `FormClosed` | Cancelamento cooperativo da análise/ajustes; criação não oferece cancelamento seguro |
| Fallback | `_ask_setup_legacy`, `forms.SelectFromList/ask_for_string` | Sequência antiga preservada se formulário falhar |

Autenticação, senha, cache offline e seleção de arquivos pertencem ao loader,
e continuam com os diálogos de compatibilidade existentes. União mantém suas
confirmações e regras próprias. Não há API nova de navegação no Revit.

## Problemas de UX

- Nomes internos no caminho principal; botões de cálculo/criação semelhantes.
- Criação automática impede revisar o plano antes de escrever no modelo.
- Telas altas, regiões com altura fixa e logs ocupando o espaço útil.
- A interface habilita criação por existência de candidatos, embora o backend
  beta possa recusá-la; o usuário descobre tarde a condição crítica.
- Identidade de parede é índice temporário; usar IDs já fornecidos como identidade.
- Fonte de paredes existentes não passa pelo setup CAD; reforço precisa de escolha
  explícita também nesse caminho, sem inferir preferências de outra execução.

## Especificação visual (antes da implementação)

Seis etapas lógicas; não são seis novas janelas modais. Cabeçalho persistente,
conteúdo rolável e ações fora da rolagem. Uma ação principal por estado.
Paleta centralizada: Primary, Success, Warning, Danger, Surface, Border,
TextPrimary, TextSecondary. Texto + símbolo + cor para estados.

```text
MODULAÇÃO AUTOMÁTICA                  Etapa N de 6
1 Configuração · 2 Paredes · 3 Revisão · 4 Modulação · 5 Criação · 6 Resultado
O que fazer agora: instrução específica da etapa
┌──────────────────── conteúdo adaptável/rolável ──────────────────────┐
│ Configuração: fonte; projeto/nível/altura; CAD/layers/espessuras;     │
│ aberturas; reforço Sem reforço / Canaletas.                          │
│ [Continuar / Criar paredes]                                         │
│                                                                    │
│ Paredes: cards do relatório real, ocorrências, análise e progresso. │
│ [Analisar paredes] [Usar paredes atuais e continuar]                 │
│                                                                    │
│ Revisão: Parede | Problema | Situação; selecionar mostra no Revit.  │
│ [Aplicar ajustes disponíveis] → [Analisar modulação]                 │
│                                                                    │
│ Modulação: quantidade real por peça e por todas as fiadas,          │
│ famílias, erros críticos do backend, avisos separados.              │
│ [CRIAR BLOCOS NO REVIT] (desabilitado quando gate recusa)             │
│                                                                    │
│ Criação: atividade + contador + percentual real + tempo decorrido. │
│ Lote existente: confirmação explícita da substituição.              │
│                                                                    │
│ Resultado: criados, falhas, paredes, avisos, famílias, desempenho.   │
│ [Fechar] [Ver relatório]  revisão humana/exclusão como ação separada.│
└────────────────────────────────────────────────────────────────────┘
Detalhes da execução ▸ (fechado)            ação principal / Fechar
```

## Contratos de implementação

`ui_state.py` transforma resultados existentes em apresentação, sem geometria
ou validadores físicos. `ui_components.py` contém componentes WinForms.
Integração mínima nas classes de tela; nenhum algoritmo, thread, temporizador,
`DoEvents`, transação ou gate de backend é reimplementado.
Progresso só atualiza tempo nos callbacks existentes; não promete animação
durante trechos que monopolizam a thread/GIL. Ausência de total é indeterminada.
Contagem de blocos usa `course_candidates` quando disponível, nunca multiplica
indevidamente o par representativo de fiadas. Dados ausentes são desconhecidos.

## Smoke manual obrigatório (registrar evidência, não presumir PASS)

- [ ] Abrir pelo loader instalado; conferir documento e fonte.
- [ ] CAD: escolher layers, espessuras, nível e altura; criar paredes.
- [ ] Existentes: seleção prévia e nova seleção; Esc; detecção automática.
- [ ] NONE e CHANNEL; famílias completas e família ausente.
- [ ] Analisar, pausar, continuar, cancelar; reabrir janela sem travar.
- [ ] Revisar problemas e mostrar parede no Revit.
- [ ] Calcular sem criar; conferir quantidades de todas as fiadas.
- [ ] Gate crítico mantém criação desabilitada; aviso mantém política do backend.
- [ ] Criar e recriar; cancelar confirmação preserva lote anterior.
- [ ] Falha de criação não aparece como sucesso; relatório e logs acessíveis.
- [ ] Revisão humana e confirmação antes de excluir referências.
- [ ] Windows 100/125/150/175/200%; redimensionar; teclado; botões acessíveis.

## Reconciliar após #42

Sobreposição inevitável: `wall_modeling.py` (somente integração de UI nesta
branch), regras (registro do contrato de interação), status documental.
Não aceitar resolução automática ours/theirs. Preservar o motor do #42 e
reaplicar os pontos de apresentação, repetindo testes de UI/gates e smoke.
