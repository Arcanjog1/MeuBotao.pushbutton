# CR-S1 / PR #25 — revisão independente: condições e risco residual

> **Isto NÃO é uma review formal do GitHub.** O `PR #25` não tem nenhuma
> review registrada (`get_reviews` → lista vazia). Este documento é o
> registro escrito de uma revisão independente conduzida em sessão
> separada, e não substitui aprovação humana nem autoriza merge.
>
> **Nenhuma linha do código aprovado da CR-S1 foi alterada.** O `HEAD` do
> `PR #25` continua `33d035f` e este documento vive em branch própria.

## Estado verificado do PR #25

| item | valor |
|---|---|
| HEAD | `33d035f84e61dd8162e5f3aeebb0bdd6284e5159` |
| código de produção | `98ae935` (o commit seguinte é **só documentação**, conferido) |
| base / merge-base | `91258dd627af97fe437a56c0506eb096ca5aa267` — idênticos, sem divergência |
| estado | `open`, **draft**, `mergeable_state: clean`, **não mesclado** |
| checks reais | **`check-status-doc` ×2, `success`** — e nada mais |
| reviews formais | **nenhuma** |

**Não existe CI de pytest neste repositório.** Toda evidência de teste vem
de execução manual, e é assim que deve ser lida.

## Veredito da revisão independente

**`APPROVE_WITH_EXPLICIT_CONDITIONS`.**

Verificado de forma independente (reexecutado, não conferido no relatório):

- `tests/test_solver_l_node_alternation_cr_s1.py` — **16/16** passam;
- controles: `tests/test_script.py` **260/260** + `tests/test_block_bonding.py`
  **32/32** = **292/292** (superconjunto dos 53 controles citados);
- as **2 falhas** de `tests/regression/test_benchmark_baselines.py` foram
  reproduzidas **nas duas árvores**, pelo revisor:
  - base limpa `91258dd`, **sem** o patch → `2 failed, 7 passed in 359.52s`
  - branch do PR, **com** o patch → `2 failed, 7 passed in 378.97s`
  - mesmas asserções, mesmos valores: TGD `compensators` 52→61 (+9);
    TP1 `JUNCTION_MISSING_BINDING` 8→9 (+1).

  Como os dois números são **idênticos** com e sem o patch, ficam provadas
  duas coisas ao mesmo tempo: as falhas são **pré-existentes**, e o patch
  tem **delta zero** no corpus oficial.
- causa-raiz **confirmada** por leitura do código: a ordem
  *não mexer → trocar papéis → girar* é logicamente sã e a decisão depende
  só de `busy_blocked`, nunca da ordem de entrada das paredes.

## Risco residual do gate — investigado, e o resultado mudou a recomendação

A revisão levantou que a equivalência bit a bit do predicado booleano
depende de uma premissa **não imposta em código**:
`_node_default_reservation_cm` (metade da maior espessura do nó) ≤
`T_INTERSECTION_B54_HALF_ROOM_FT` (27cm) — isto é, espessura ≤ **54cm**.

### O que foi medido

1. **Corpus real**: espessura máxima de parede = **14cm** (reserva ≤ 7cm),
   contra um teto de 27cm. A premissa vale com folga de ~4×.
2. **Busca ativa por contraexemplo**: o predicado
   `_corner_bond_blocked_by_other_node` foi executado **nas duas árvores**
   (`91258dd` × branch da S1) sobre a **mesma** geometria, em **100
   combinações** — 10 espessuras (10, 14, 20, 30, 40, 54, 56, 60, 80,
   **120cm**) × 10 distâncias do encontro vizinho (15 a 90cm, cobrindo a
   faixa crítica `34+27 = 61cm`).

   **Resultado: ZERO divergências**, incluindo as **40 combinações com
   espessura acima de 54cm** — onde a premissa está violada.

### Por que NÃO foi proposto um guard

O guard óbvio seria limitar o alcance cruzado a 27cm
(`min(reserva, T_INTERSECTION_B54_HALF_ROOM_FT)`). Ele preservaria a
equivalência booleana **por construção** em vez de por premissa — mas, para
uma parede muito espessa, **reduziria** o alcance de proteção da fiada de
fora, que é justamente o que impede colisão com o corpo da peça
perpendicular.

Ou seja: o guard troca uma garantia de **compatibilidade histórica** por
uma perda de **proteção física**. Isso é uma **escolha de domínio**, não
uma correção inequivocamente segura — e o critério para prepará-la
(*"correção pequena e inequivocamente segura"*) **não** é atendido.

**Conclusão: nenhum patch proposto.** A condição fica **documentada**, com
a premissa explícita e a evidência de que não foi possível construir um
contraexemplo. A equivalência **não** é declarada universal: ela vale sob a
premissa medida (espessura ≤ 54cm), e o corpus atual está muito abaixo
disso.

## Condições explícitas para o merge

Não são defeitos de qualidade — são decisões que pertencem ao usuário.

1. **Aceitar a alternativa A dos compensadores**: preservar a alternância e
   assumir `COMPENSATOR_CONSECUTIVE` +8 e `COMPENSATOR_EXCESS_IN_RUN` +8
   por projeto (**8 eventos físicos**, não 16 — o mesmo par `C04`+`C09`
   dispara os dois códigos). A prova de impossibilidade dentro do contrato
   foi revisada e é válida: trecho de 49cm, `B34` obrigatório no nó,
   residual de **14cm**, e nenhuma composição do catálogo fecha 14cm com
   ≤1 compensador. As alternativas **B** (`B19` como amarração, revoga a
   seção 35) e **E** (`B54` do `T` na fiada ímpar) são **normativas** e
   **não** foram implementadas.
2. **Ciência das 2 falhas de baseline** — pré-existentes, não bloqueiam
   este PR, e **continuam vermelhas** até serem tratadas em CR própria.
   Atribuição correta: a do TP1 (`JUNCTION_MISSING_BINDING` 8→9) é herdada
   da CR-V1; a do TGD (`compensators` 52→61) é **dívida histórica de
   baseline** e **não** deve ser atribuída à V1.

## Riscos remanescentes registrados

| risco | severidade | estado |
|---|---|---|
| premissa espessura ≤ 54cm na equivalência do gate | baixa | documentada; 100 combinações sem contraexemplo; corpus com máx. 14cm |
| `COMPENSATOR_VERTICAL_STRIP` a **uma fiada** do limiar (`8/17 = 0,47` contra `0,50`) | baixa-média | declarada, sem alterar threshold nem criar exceção |
| custo de +8/+8 compensadores | aceito na alternativa A | **pendente de decisão do usuário** |

## O que não foi feito

Não foi marcado `ready`, não foi feito merge, não foi criada review
formal, não foi alterado o código aprovado, não foi criado monitoramento
automático e nenhuma outra CR foi iniciada a partir deste documento.
