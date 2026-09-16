# Redesign visual — referência e protótipo anterior à implementação

Base oficial observada: `55e990d`. Continuação da branch própria de UI e
do draft #44; #42 não é base nem destino de alterações.

## LIÇÕES EXTRAÍDAS DO VÍDEO

Referência examinada no navegador:
[Cotas e Detalhamento automático de Arquitetura no Revit — BIM Coder](https://www.youtube.com/watch?v=XRQ8CZEwTCE).
Análise visual de trechos selecionados, não reprodução integral.

| Trecho observado | Padrão visível | Aplicação proposta |
|---|---|---|
| [4:10](https://www.youtube.com/watch?v=XRQ8CZEwTCE&t=250s) | Janela escura sobre o modelo; configuração à esquerda e desenho explicativo à direita; abas curtas; rodapé separado | Duas colunas, preview esquemático que acompanha a estratégia, ação principal no rodapé |
| [5:51](https://www.youtube.com/watch?v=XRQ8CZEwTCE&t=351s) | Diálogo compacto com lista de categorias, controles agrupados, explicações pequenas e uma ação destacada | Resumos em linhas; lista de problemas curta; comandos secundários discretos |
| [7:20](https://www.youtube.com/watch?v=XRQ8CZEwTCE&t=440s) | Abas estáveis, campos alinhados, títulos de seção e ajuda subordinada | Componentes e espaçamento consistentes; configuração avançada recolhida |

A referência usa um fundo escuro azulado, superfícies próximas, bordas sutis,
texto claro e azul na ação/aba ativa. Não foram medidos pixels, fontes ou
cores do vídeo; os valores abaixo são decisões próprias. Marca, logotipo,
conteúdo de preview e ativos do autor não serão copiados.

## Diagnóstico do candidato anterior

Cabeçalho de 132 px e cards altos consumiam espaço. A configuração conservava
duas colunas antigas sem preview. Tabs nativas claras interrompiam a unidade
visual; tabelas e relatórios expunham IDs e termos internos. O fluxo já separava
cálculo de criação, mas ainda tinha aparência de ferramenta de diagnóstico.

## Sistema visual proposto

- WinForms/CPython/pythonnet preservados. Nenhum browser no produto.
- Janela de referência: 940 × 680 px lógicos; mínimo 740 × 520. Sem maximizar.
- Grafite de fundo, superfície elevada, borda discreta e azul moderado.
- Segoe UI: título 14, seção 10 semibold, campo/corpo 9, ajuda/status 8–9.
- Espaçamento 4/8/12/16/24/32. Rodapé 60, cabeçalho 100, botões 36.
- Campos sem cantos artificiais: controles nativos alinhados, mesmo fundo,
  foco e estados. Sem P/Invoke, skin global ou mudança de tema do Revit.
- Abas como botões nativos com painel de conteúdo: teclado/Tab acessíveis,
  estado selecionado e azul reservado à ação principal.
- Preview 2D desenhado localmente: CAD → paredes, seleção, alvenaria e CHANNEL.
  Legenda permanente: esquema ilustrativo, sem escala, não valida o plano.

## Wireframes detalhados — seis etapas

Cada tela usa cabeçalho compacto (produto, etapa, instrução), conteúdo rolável
e rodapé fixo. Ordem solicitada: Configuração → Paredes → Modulação → Revisão
→ Criação → Resultado. A revisão geométrica anterior ao cálculo fica dentro
de Paredes/Modulação; Revisão designa a conferência do plano calculado.

### 1. Configuração

```text
Modulação Automática                       Configuração · 1/6
Configure as paredes e confira a estratégia.
────────────────────────────────────────────────────────────
 [Projeto e CAD] [Aberturas e reforço]  │ PRÉVIA DA ESTRATÉGIA
 Documento atual                      │
 Nível           [Térreo          v]  │ parede / janela
 Altura (m)      [2,80             ]  │ canaletas em destaque
 Layer paredes   [lista compacta   ]  │
 Referência      [opcional        v]  │ Sem escala. Ilustrativo.
 Espessuras      [lista de opções  ]  │ Estado da escolha
 Modo avançado ▸                     │
────────────────────────────────────────────────────────────
 Status de configuração          [Cancelar] [Criar paredes]
```

Fonte de paredes mantém seleção CAD/existentes e união acessível. Existentes
apresenta instruções do picker real, quantidade já selecionada e reforço;
nunca simula confirmação modeless que o backend não suporta.

### 2. Paredes

```text
Paredes · 2/6 — Confira o modelo antes da análise
34 paredes · 44 aberturas · 1 aviso       [esquema da seleção]
Analisando paredes…
Parede 86 de 128                         72%
██████████████████░░░░░░
Tempo decorrido 00:42
Detalhes técnicos ▸
                     [Pausar] [Cancelar] / [Analisar paredes]
```

### 3. Modulação

```text
Modulação · 3/6
[Paredes e famílias] [Plano de blocos] [Resultado]
1 parede requer revisão · 1 ajuste disponível
Parede 1    Abertura fora da grade       Visualizar no modelo
Famílias e reforço ▸
Detalhes técnicos ▸
          [Aplicar ajustes] [Fechar] [Calcular modulação]
```

Durante cálculo: atividade/contagem reais; criação indisponível; logs fechados.

### 4. Revisão

```text
Revisão · 4/6 — Confira antes de criar
Modulação pronta
34 paredes · 44 aberturas · 58 blocos     [esquema de blocos]
Peça                Quantidade
B39                 50
Canaleta 39          8
Famílias / avisos ▸
Lote existente: quantidade quando conhecida; será substituído.
     [Fechar] [Recalcular] [CRIAR BLOCOS NO REVIT / Atualizar]
```

### 5. Criação

```text
Criação · 5/6 — Criando blocos no Revit
Inserindo as peças da fiada 2
38 de 58 · 66%                 Tempo decorrido 00:18
████████████████░░░░░░░░
Detalhes técnicos ▸
Ações concorrentes indisponíveis durante execução.
```

Não inventar interrupção/rollback ausente no backend nem mudar threading.

### 6. Resultado

```text
Resultado · 6/6
Modulação concluída / Concluída com pendências / Falha
58 blocos criados · 0 falhas de criação
Resumo · Avisos · Paredes não moduladas · Famílias · Tempo
Relatório técnico ▸
Revisão humana e referências ▸
                                  [Copiar relatório] [Fechar]
```

## Estados e compatibilidade

Idle: instrução e próxima ação; Analyzing/Solving/Creating: atividade real;
Validating: texto apenas quando callback indica validação; Done/Error:
resultado do backend, sem sucesso presumido. Preview consome somente escolha
de UI, não consulta Revit nem decide física. Tempo/progresso usam callbacks
existentes; não prometem atualização durante retenção de GIL.

Ensaios: testes de interação/gates, renderização WinForms, janela mínima e
Scale 100/125/150/175/200. Scale não é DPI nativo; smoke real no Revit deve ser
registrado separadamente. Light theme e adaptação automática ao Revit ficam
fora desta rodada para não introduzir risco de integração.
