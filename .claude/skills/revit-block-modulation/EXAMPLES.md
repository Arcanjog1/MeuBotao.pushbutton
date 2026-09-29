# Casos válidos — medidos em projetos reais

Fonte detalhada: REGRAS (seções citadas) + `nuvem/diagnosticos/*.md` +
`nuvem/PADRAO_MODULACAO.md`. Todo caso aqui vem de medição real via MCP
(100% leitura) ou de uma parede que o usuário modulou à mão no Revit para
servir de referência — nunca um exemplo inventado.

## Catálogo confirmado cross-projeto

Núcleo B39/B34/B54/B19/C09/C04, mesma família, mesmas dimensões (L×19×14)
— confirmado por medição independente em 2 projetos distintos (TORRE
EASY-LO-R00 e CHACARA-TORRE-EASY-LO), dimensões exatas idênticas. Ver
`nuvem/PADRAO_MODULACAO.md`.

## Cotas Z e passo de fiada — confirmado cross-projeto

- Passo de fiada = 20cm: medido diretamente nas cotas Z de 20.001
  instâncias de B39 num dos dois projetos — delta constante de 20cm.
- Offset da 1ª fiada = +1cm sobre a cota bruta do nível: 1,0cm é o valor
  mais frequente (1.482 de 15.000 instâncias comparadas contra o nível
  mais próximo), seguido pela progressão exata 21/41/61/81/…/221cm.

## Parede de referência — 319cm, `L_CORNER` + `STRAIGHT_CONTINUATION` (2026-08-28)

Parede real modulada **à mão** pelo usuário no Revit, usada para validar
a correção do bug de reserva indevida em `STRAIGHT_CONTINUATION`
(ERROR_HISTORY.md). Depois de zerar a reserva incorreta, a Fiada A gerada
pelo solver saiu **idêntica** à parede de referência, peça por peça e
posição por posição:

```
B34 + 7×B39 + C04
X = 857,7 / 895,2 / 935,2 / 975,2 / 1015,2 / 1055,2 / 1095,2 / 1135,2 / 1157,7
```

Esse é o padrão de prova a seguir para qualquer correção futura de
reserva/geometria: comparar a saída do solver, posição por posição,
contra uma parede real modulada à mão — não só "a modulação fecha", mas
"fecha exatamente como o usuário modulou".

## Exceção 11.8 — peça pequena alinhada contra abertura

A mesma parede de referência acima também confirmou a exceção da regra
#1: a última junta contra o vão (pastilha/compensador/meio-bloco
encostado numa abertura ou na ponta do próprio eixo) pode coincidir entre
Fiada A e Fiada B sem ser reprovada. Ver BONDING.md, regra #1, exceção
11.8.

## Amarração em cruz (X) — B54 correto, sem sobreposição (REGRAS §18.1)

Confirmado no projeto `TESTE MODULAÇÃO`: `X_INTERSECTION` usa dois B54 a
90° com células centrais alinhadas, validado geometricamente
(`validate_x_intersection`). Onde isso falhava era na **convivência** com
nós vizinhos muito próximos — ver caso de colisão abaixo.

## Colisões medidas numa fiada real (REGRAS §18.7) — o que É erro genuíno

Medição sobre uma fiada física real (OBB/SAT) no projeto `TESTE
MODULAÇÃO`: 9 colisões na fiada A, zero na fiada B —

- 4× B34 do preenchimento comum caindo dentro do volume do B54 de um
  T_INTERSECTION;
- 4× B19 do preenchimento comum caindo dentro do volume do B54 de um
  T_INTERSECTION;
- 1× B54 × B54 de dois nós em T diferentes na mesma parede, próximos
  demais para os dois caberem sem sobrepor.

Nenhum desses é amarração legítima — são exemplos de referência do que a
validação de colisão (VALIDATION.md, item 1) deve pegar.

## Sistema 2 (canaleta) — dois vãos medidos em detalhe (REGRAS §10.2/§10.3)

- Janela, largura 166cm, nível TP1, vão 6829-6995cm: sequência
  fino-jamba + fino-cheio + canaleta confirmada acima e abaixo do vão
  (janela tem peitoril).
- Porta, largura 121cm, mesmo nível, vão 7594-7715cm: mesma sequência só
  acima (porta não tem contraverga, REGRAS §10.4); canaleta medida
  7525-7844cm — ~319cm, bem mais larga que o vão de 121cm, confirmando o
  apoio além das jambas (REGRAS §10.3).

Dump bruto completo em `nuvem/diagnosticos/TORRE_EASY-LO-R00.md`.

## Nós `AMBIGUOUS` = peitoril + verga colineares (REGRAS §15.2)

92 nós `AMBIGUOUS` medidos no projeto `TESTE MODULAÇÃO`: só 4 eram ângulo
oblíquo de verdade; os outros 88 tinham 3-7 pontas no mesmo ponto, sempre
com duas pontas na mesma direção (0° entre si) — assinatura de peitoril +
trecho de verga ocupando o mesmo eixo em planta, em faixas de altura
diferentes. Por isso `AMBIGUOUS` reserva espaço de amarração mesmo sem
casar com T/X — ali existe peça de verdade, só que na outra faixa de
altura (ver BONDING.md).

## Faixa de compensação na jamba — medida no Revit (REGRAS §84, 2026-09-28)

Arquivo de teste `butanta testes`, motor main `1db4876`, NONE, 14 fiadas.

- **W1 (porta, jamba t = 79 cm, T no início do eixo)** — antes: fiada par
  `B34(nó) | B34 | C09 | vão`, ímpar `B34 | C09 | B19 | vão` (C09 a 0 e a
  20 cm do vão, vazado do B19 10,9 cm fora do vazado de baixo). Depois:
  ímpar `B34 | B19 | C09 | vão` — C09 encostado nas 11 fiadas, vazado do
  B19 a 0,9 cm do vazado de baixo.
- **W0 (pilarete 975–1044 entre janelas)** — antes: `B39 | C09 | B19` sobre
  `B19 | B39 | C09`; depois: `B39 | B19 | C09` — faixa de C09 na jamba de
  1044 em todas as fiadas.
- **Não é para mexer**: pilarete de 54 cm da W0 (800–854) fechado com
  `B19 B34` sem compensador — a composição que tira compensador vem antes
  do alinhamento.

## Como registrar um novo exemplo

Sempre que uma medição nova (via MCP) ou uma parede modulada à mão pelo
usuário confirmar, refutar ou detalhar uma regra: adicionar aqui a
medição bruta (ou apontar para `nuvem/diagnosticos/`), o projeto de
origem, a data, e qual regra ela confirma/refuta — nunca só "funcionou",
sempre com o número/posição medido quando houver.
