# Redesign premium — auditoria e decisões antes da implementação

Pedido de 2026-09-16. Base buscada: `55e990d962ed22ae1021f0d335db197607bddda1`.
Branch `codex/modulation-ui-premium-redesign`, criada de origin/main; reaproveita
por fast-forward o trabalho UI isolado até `78a79fc`, sem commits do #42.
Novo draft separado do #44, nenhuma instalação ou merge.

## Referência e diagnóstico

[BIM Coder, vídeo de referência](https://www.youtube.com/watch?v=XRQ8CZEwTCE):
estudo visual anterior em 4:10, 5:51 e 7:20, registrado em
[UI_VISUAL_REFERENCE](UI_VISUAL_REFERENCE.md). Nova conferência nesta rodada.
O aspecto profissional vem da proporção, alinhamento e uniformidade de controles;
a linguagem de programação não pode ser identificada pela aparência.
Stack encontrado: CPython/pythonnet, WinForms, desenho System.Drawing.
Trocar para WPF não é requisito: reconstruir componentes locais preserva o
contrato de execução e permite verificar a janela real neste runtime.

Crítica ao #44: abas com moldura de botão; cabeçalho vertical longo sem stepper;
campos com alturas inconsistentes; prévia plana e sem legenda; grandes vazios
na estratégia; fonte e controles herdados demais; status do rodapé excessivo;
famílias em textarea; resultados sem hierarquia suficiente.

## Inventário por decisão do usuário

| Tela | Fazer / entender agora | Ação | Decisão visual e informação secundária |
|---|---|---|---|
| Inicial | Escolher origem das paredes | Continuar | REDESIGN: escolhas compactas, desenho contextual; união em opção avançada |
| Configuração / Projeto e CAD | Definir nível, altura, layers e espessuras | Criar paredes | REDESIGN: seções alinhadas; KEEP validação, valores e callbacks |
| Aberturas e reforço | Identificar aberturas e escolher NONE/CHANNEL | Criar paredes | REDESIGN: seletor, helper curto, prévia com legenda; modo de referência em ADVANCED |
| Seleção / existentes | Selecionar no Revit e confirmar contagem real | Selecionar / confirmar | IMPROVE: instrução curta, mesma linguagem; KEEP picker nativo |
| Criação de paredes | Entender operação em curso | Cancelar quando suportado | KEEP execução; IMPROVE apresentação de progresso |
| Paredes / análise | Conferir resumo e iniciar análise | Analisar paredes | IMPROVE densidade; REMOVE FROM MAIN VIEW log bruto |
| Progresso | Etapa e quantidade quando informadas | Pausa/cancelamento existente | KEEP eventos e relógio; não inventar percentual ou etapas |
| Modulação | Calcular / entender plano e quantidades | Analisar modulação | IMPROVE estado vazio, tabela e contexto; KEEP backend |
| Revisão | Resolver pendências e conferir famílias | Criar blocos no Revit | REDESIGN lista de famílias com símbolos e status; IDs em detalhes |
| Criação de blocos | Acompanhar quantidade realmente reportada | Cancelar conforme backend | KEEP handler e progresso; IMPROVE exclusão de ações concorrentes |
| Erros / warnings | Entender impedimento e próximo passo | Revisar / reanalisar | IMPROVE ícone + texto + cor; original em detalhes |
| Resultado | Conferir contagens, falhas e tempo | Fechar | IMPROVE síntese visual; relatório e revisão humana secundários |
| Relatório / logs | Investigar quando necessário | Expandir / copiar | MOVE TO ADVANCED, preservando conteúdo |
| Advanced mode | Alterar referência / inspecionar IDs | Expandir | KEEP disclosure; sem nova física |

## Sistema visual e wireframe

Grafite em três níveis; azul para ação/seleção/foco; sucesso e erro também
com símbolo e texto. Spacing 4/8/12/16/20/24/32; controles 28/32/36;
raios 4/6/8 onde desenho local suporta. Segoe UI: título 14, seção 10,
campo/corpo/status 9, helper/caption 8.25. Janela alvo 860×640, mínimo
740×520; conteúdo principal com scroll e rodapé fixo. Sem chrome customizado.

```text
Modulação Automática                    Etapa 1 de 6 · Configuração
Configure as paredes e a estratégia antes de iniciar.
● Configuração ─ ○ Paredes ─ ○ Modulação ─ ○ Revisão ─ ○ Criação ─ ○ Resultado
Projeto e CAD     Aberturas e reforço
─────────────
PROJETO                            PRÉVIA ILUSTRATIVA
Nível [                  ▾]       desenho de alvenaria, abertura
Altura [2,80 m]                    e peças de reforço com profundidade
PAREDES                            01 Canaleta superior
Layer [lista compacta    ]         02 Canaleta inferior
Referência [             ▾]       ESTRATÉGIA
Espessuras [✓ 14] [  19]           Canaletas / Sem reforço
▸ Opções avançadas                 ○ Famílias não verificadas
──────────────────────────────────────────────────────────────────
! Selecione uma espessura                 Cancelar   Criar paredes
```

Revisão mantém o mesmo shell: problemas à esquerda, famílias e estratégia
à direita; plano usa tabela de peças; resultado usa resumo curto e disclosures.
Stepper representa etapas percorridas, não certificação de validade física.
O caso de análise pulada continua explícito.

## Critérios de verificação

Renderizar componentes WinForms reais com dados sintéticos; testar seleção,
abas, NONE/CHANNEL, gates, famílias e estados. Verificar dimensões e escala
100/125/150/175/200 em 1366×768, 1920×1080, 2560×1440. Ensaio de escala
não equivale a mudança real de DPI do Windows: essa limitação deve permanecer
explícita. Segunda inspeção visual após implementação e correções antes da
entrega. Sem READY enquanto smoke Revit e DPI real não estiverem comprovados.
