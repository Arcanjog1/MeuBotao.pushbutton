# Padrão de modulação — medido em projetos reais

> Ao contrário de [REGRAS_MODULACAO_BLOCOS.md](REGRAS_MODULACAO_BLOCOS.md)
> (o que o *solver* do `core/wall_modeling.py` implementa), este arquivo
> registra o que foi **medido de verdade** em projetos Revit reais, via
> `mcp__revit-pyrevit__*`, 100% leitura (ver
> [diagnostico_modulacao_cross_projeto.py](diagnostico_modulacao_cross_projeto.py)
> e o plano de diagnóstico salvo em
> `estou-quero-fazer-isso-wild-stardust.md`). Nenhum `.rvt` diagnosticado
> foi alterado — nenhuma `Transaction`, nenhum `save`/`sync`.
>
> **Status: 2 de N projetos diagnosticados.** Uma regra só vira "padrão de
> escritório" quando a MESMA regra aparecer confirmada em **todos** os
> projetos diagnosticados até aquele momento (ver seção final). Cada item
> é rotulado com de onde veio; quando 2+ projetos batem, isso é destacado
> explicitamente.

## Projetos diagnosticados até agora

| Projeto | Data | Registro bruto |
|---|---|---|
| TORRE EASY-LO-R00 (JARDIM DA COSTA BEACH CLUB) | 2026-08-24 | [diagnosticos/TORRE_EASY-LO-R00.md](diagnosticos/TORRE_EASY-LO-R00.md) |
| CHACARA-TORRE EASY-LO ("TROPICALE BEACH CLUB") — projeto distinto do acima, apesar do nome parecido (confirmado com o usuário) | 2026-08-26 | [diagnosticos/CHACARA-TORRE-EASY-LO.md](diagnosticos/CHACARA-TORRE-EASY-LO.md) |

## O que já foi confirmado

### Confirmado em 2 de 2 projetos (evidência cross-projeto real)

| Regra | Projeto 1 | Projeto 2 | Bate com REGRAS_MODULACAO_BLOCOS.md? |
|---|---|---|---|
| Catálogo núcleo B39/B34/B54/B19/C09/C04 — mesma família, mesmas dimensões (L×19×14, ver seção 1) | Confirmado | Confirmado (medição independente, mesmas dimensões exatas) | ✅ |
| Passo de fiada = 20cm | Delta mais comum (101 ocorrências) | Medido direto nas cotas Z de 20.001 instâncias de B39 — delta constante de 20cm | ✅ |
| Offset da 1ª fiada = +1cm sobre a cota bruta do nível | 19 pares de cotas Z a 1,0cm | Offset de 15.000 instâncias vs. nível mais próximo: 1,0cm é o mais frequente (1.482 ocorrências), seguido pela progressão exata 21/41/61/81/101/121/141/161/181/201/221cm | ✅ `FIRST_COURSE_Z_OFFSET_CM=1` — a progressão completa medida no projeto 2 é evidência mais forte que o par isolado do projeto 1 |
| Fluxo operacional "paredes nativas → blocos → excluir paredes" (Walls/Doors/Windows=0 no modelo já modulado) | Confirmado | Confirmado | ✅ (padrão de processo, não regra geométrica) |

### Confirmado em só 1 dos 2 projetos até agora (não remedido no outro, não é divergência)

| Regra | Onde foi medida | Motivo de não estar nos 2 |
|---|---|---|
| Junta de assentamento entre blocos = 1,0cm | Projeto 1 (87% de 2.135 pares) | Não remedida no projeto 2 nesta sessão (baixo retorno marginal — ver pendências do diagnóstico) |
| Célula B34 (2 assimétricas, menor ≈97cm², maior ≈142cm²) / Célula B54 (3, central menor ~113cm² entre duas ~142cm²) | Projeto 1 | Extração de célula por `EdgeLoops` falhou no projeto 2 (erro de overload do `DB.ElementId` no ambiente de execução usado) — dimensão em cm confirmada por parâmetro, célula não |
| Regra de dígito final da parede (`0/1/6/9`) | **Contrariada** no projeto 1: 29% dos trechos reais fecham terminando em outros dígitos | Não remedida no projeto 2 (mesma ressalva metodológica do projeto 1 — teste tautológico sem a junta de contorno real) |

### Padrão observado em 1 projeto, ainda não confirmado

| Observação | Projeto | Nota |
|---|---|---|
| Última fiada de cada pavimento ajusta ~+11cm acima da última fiada "redonda" antes de subir de nível (pé-direito de 271cm não é múltiplo exato de 20cm) | Projeto 2 | Só 2 ocorrências vistas de relance — ver `diagnosticos/CHACARA-TORRE-EASY-LO.md` |

## Catálogo — núcleo confirmado + peças extras encontradas fora do catálogo fixo

Núcleo (B39/B34/B54/B19/C09/C04) confirmado idêntico ao catálogo fixo do
script. **Peças adicionais encontradas, ainda fora do catálogo do script**
(ver detalhe no registro bruto do projeto): canaleta inteira/J/34, meia
canaleta, variantes "cortado" (meia-altura) e "deitado" (rotacionado),
verga/contraverga (sem parâmetro de dimensão identificado ainda).

## Dados a extrair de cada próximo projeto (checklist, ver plano completo)

1. Catálogo de blocos (família/tipo/dimensões/células) — auto-descoberta,
   nunca por nome hardcoded.
2. Junta de assentamento medida (gap real entre blocos adjacentes).
3. Passo de fiada + offset da 1ª fiada (cotas Z distintas).
4. Regra de fechamento de trecho/pilarete (dígito final vs aritmética
   real) — medir com cautela; ver ressalva metodológica no registro do
   primeiro projeto (teste "mod 5" simples é tautológico, não confirma a
   regra de junta de CONTORNO).
5. Orientação de B34/B54 em encontros L/T/X.
6. Regra de largura de abertura, se o projeto ainda tiver portas/janelas
   nativas do Revit (este primeiro projeto já as tinha excluído).

## Quando algo vira "padrão de escritório"

Só quando a mesma regra aparecer **medida e confirmada** em todos os
projetos diagnosticados até aquele momento. Divergência entre projetos é
registrada explicitamente aqui como "varia por projeto", nunca escondida
nem resolvida por uma "opinião" de qual está certo.
