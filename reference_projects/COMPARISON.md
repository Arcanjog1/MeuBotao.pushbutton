# TORRE EASY × BUTANTÃ
STATUS: EVIDÊNCIA / NÃO NORMA. Revisão offline 2026-09-10.

Fontes: [TORRE EASY](torre_easy_lo_r00/README.md) e
[BUTANTÃ](butanta_r08_lt/README.md), com erratas e JSON.
Não aprovam apoio mínimo, dimensionamento ou top course.

| Aspecto | TORRE EASY | BUTANTÃ |
|---|---|---|
| Peças / aberturas | 67.712 / 484 (+200 furos separados) | 65.747 / 142 |
| Porta, acima | Verga, 248/248 rótulos PORTA | Canaletas, 47/47 rótulos PORTA |
| Porta, abaixo | Nenhuma, 248/248 | Nenhuma quando toca a base; PORTA 7212991 tem peitoril 40 cm |
| Janela, acima | Verga, 130/134 | Canaleta, 58/61 |
| Abaixo de peitoril | Contraverga em 129/134 JANELA | Canaleta 89/89: 61 JANELA + 27 ABERTURA + 1 PORTA |
| Altura do reforço | 9 cm dedicado | 19 cm, própria fiada |
| Verga/contraverga por uso | 392/147 | Zero; 69 tipos carregados |
| Offset superior zero | 392/392 | 135/136 reforços; só CHANNEL: 129/130 |
| Offset inferior zero | 147/147 | 88/89; uma diferença -0,01 cm |
| Apoios | 784 de verga ≥9; 294 de contraverga ≥11,5 cm | Mínimo por abertura acima 4,0; abaixo -1,01 cm; envelope de corrida |
| Canaletas globais | 6.584 | 8.931 |
| Topo 100% canaleta | 465/651 grupos, 71,43% | 251/340, 73,82% |
| Cortados | 3.887: 3.636 altura, 251 comprimento | 286: 124 altura, 162 comprimento |
| Cobertura catálogo atual | 54.298/67.712 = 80,19%, 6/57 tipos | 55.963/65.747 = 85,12%, 6/21 tipos |
| Relações publicadas | 539 peça↔abertura | 3.625; peças podem servir a vários vãos |

## Gramática compartilhada

Grade predominante 20 cm, bloco 19 + junta 1, primeira base +1 cm,
espessura 14 cm, ortogonalidade e núcleo B39/B34/B54/B19/C09/C04.
Meia-fiada: 9+1+9=19. Não é universalidade: TORRE EASY tem 99,35% das
peças de 19 cm na grade; BUTANTÃ possui ajustes locais.
Rótulo e geometria de abertura são dados distintos.

A geometria reforço/borda sustenta planejamento comum de intervalos com duas
estratégias: A ocupa faixas de 9 cm; B substitui preenchimento em 19 cm.
Vazios, colisões, cobertura e amarração devem enxergar ambas.

## Limites

- Tipos carregados sem instâncias sustentam inferência de escolha, não intenção comprovada.
- Tolerância de coleta BUTANTÃ (1,5 cm) não é tolerância construtiva aprovada.
- Não importar apoio ≥9 cm para CHANNEL. Envelope min/max pode conter lacuna
  entre corridas; suporte real requer validação própria.
- Zero segunda fiada INTEIRA sob peitoril não elimina peças isoladas BELOW_WINDOW_2ND.
- Pavimentos repetidos não são amostras independentes; 142 instâncias não são clones.
- Extrações não classificam L/T/X ou orientação do vão menor.
- Cinta de topo universal permanece conflito; graute↔canaleta não foi medido peça a peça.

Proposta: um motor + estratégia configurável.
[Contrato](../docs/architecture/opening-reinforcement-strategies.md) e
[decisão pendente](../docs/decisions/DECISION-OPENING-REINFORCEMENT.md).
