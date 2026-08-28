# Modulação de Blocos no Revit (MCP + pyRevit)

Camada permanente de conhecimento e controle de qualidade para toda
geração/modulação automática de blocos de alvenaria estrutural no Revit
via MCP + pyRevit, neste projeto e em qualquer projeto arquitetônico
futuro que use este mesmo motor.

## Quando esta Skill é obrigatória

Sempre que o usuário pedir algo como "gere os blocos no Revit", "modula
essa parede", "lança os blocos", ou qualquer pedido relacionado a:

- geração/edição de blocos via `mcp__revit-pyrevit__*`;
- lógica de `core/wall_modeling.py` (o solver de modulação);
- amarração, encontros L/T/X, aberturas, pilaretes, fiadas;
- qualquer correção de erro de modulação apontado pelo usuário.

**Consultar esta Skill inteira ANTES de gerar ou alterar qualquer
bloco.** Ela não é documentação opcional — é a fonte de regras que a
geração deve obedecer, em qualquer arquitetura, em qualquer projeto.

## Fonte única da verdade (não duplicar, não divergir)

Esta Skill é uma camada de **navegação e disciplina de processo** por
cima do conhecimento que já existe no repositório. As regras técnicas
detalhadas moram em um único lugar canônico:

- **`nuvem/REGRAS_MODULACAO_BLOCOS.md`** — fonte oficial das regras
  implementadas em `core/wall_modeling.py` (catálogo, amarração,
  aberturas, validação, histórico de bugs/conflitos, numerado por seção).
- **`nuvem/PADRAO_MODULACAO.md`** — o que foi **medido de verdade** via
  MCP em projetos reais (distinto do que o solver implementa).
- **`nuvem/diagnosticos/*.md`** — registros brutos de medição por projeto.
- **`core/wall_modeling.py`** — implementação real do solver.
- **`tests/test_script.py`** — testes que travam o comportamento descrito.

Os arquivos desta Skill (`RULES.md`, `BLOCKS.md`, `BONDING.md`,
`OPENINGS.md`, `VALIDATION.md`, `ERROR_HISTORY.md`, `EXAMPLES.md`)
**resumem e indexam** essas fontes por seção (`REGRAS §N`), para consulta
rápida antes/durante uma geração. **Nunca copiar uma regra aqui de forma
que ela possa divergir da fonte** — em caso de dúvida ou atualização,
o `REGRAS_MODULACAO_BLOCOS.md` manda, e esta Skill deve ser atualizada
junto (ver "Como esta Skill aprende" abaixo).

## Estrutura

| Arquivo | Conteúdo |
|---|---|
| [RULES.md](RULES.md) | Fluxo de execução obrigatório (6 etapas) + princípios permanentes |
| [BLOCKS.md](BLOCKS.md) | Catálogo de blocos, dimensões, juntas, papel de cada peça |
| [BONDING.md](BONDING.md) | Amarração: L/T/X, alinhamento vertical entre fiadas, meio-bloco, compensadores |
| [OPENINGS.md](OPENINGS.md) | Portas, janelas, vergas/contravergas/canaletas, pilaretes |
| [VALIDATION.md](VALIDATION.md) | Validações obrigatórias e checklist final antes de dar por concluída |
| [ERROR_HISTORY.md](ERROR_HISTORY.md) | Bugs reais já corrigidos, conflitos abertos, pendências de código |
| [EXAMPLES.md](EXAMPLES.md) | Casos válidos medidos em projetos reais, usados como referência |

## Fluxo obrigatório (resumo — detalhe em RULES.md)

1. **Carregar a Skill** — ler RULES/BLOCKS/BONDING/OPENINGS/VALIDATION/
   ERROR_HISTORY relevantes ao pedido antes de tocar no Revit.
2. **Ler o projeto no Revit via MCP** — paredes, níveis, aberturas,
   interseções, catálogo de famílias reais. Nunca assumir que o projeto
   novo tem a mesma arquitetura do anterior.
3. **Analisar antes de modelar** — classificar paredes, encontros,
   regiões críticas, resolver amarrações e aberturas, definir estratégia
   por parede/trecho.
4. **Gerar a modulação** — só depois da solução geométrica validada
   logicamente.
5. **Validação automática** — auditoria completa (ver VALIDATION.md).
6. **Corrigir e revalidar** — repetir até passar em todas as checagens.
   Nenhuma parede fica "sem solução" sem motivo registrado (VALIDATION.md,
   REGRAS §18.8).

## Adaptação a novas arquiteturas

As regras são geométricas e paramétricas (comprimentos, ângulos,
interseções, faixas verticais de abertura) — nunca coordenadas fixas de
um projeto específico. Um projeto novo muda comprimentos de parede,
posição de portas/janelas, encontros e pé-direito; a Skill não muda. Ver
RULES.md, princípio "paramétrico, nunca hardcoded".

## Como esta Skill aprende (não repetir erro)

Esta regra também está em `CLAUDE.md` (obrigatória para todo o projeto) e
se aplica aqui com uma etapa extra:

1. Quando o usuário apontar um erro/correção de modulação: identificar a
   causa real (não só o sintoma visual).
2. Registrar a regra em `nuvem/REGRAS_MODULACAO_BLOCOS.md` (fonte
   canônica — rotulada REGRA OBRIGATÓRIA / PREFERENCIAL / EXCEÇÃO
   PERMITIDA / PADRÃO OBSERVADO / CONFLITO, conforme o cabeçalho daquele
   arquivo já define).
3. Atualizar o(s) arquivo(s) desta Skill que indexam aquela seção
   (BONDING.md, OPENINGS.md, etc.) para apontar/resumir a regra nova —
   nunca deixar a Skill referenciando uma seção desatualizada.
4. Adicionar/atualizar uma entrada em `ERROR_HISTORY.md` quando for um
   bug real corrigido (não uma regra nova sem erro prévio).
5. Adicionar um caso a `EXAMPLES.md` quando a correção vier de uma medição
   real no Revit ou de uma parede de referência modulada à mão pelo
   usuário.
6. Garantir que existe (ou fica registrada como pendência) uma validação
   automática que detectaria esse erro se ele se repetisse — ver
   VALIDATION.md.

Uma correção feita num projeto **tem que** melhorar o comportamento em
todos os projetos futuros — nunca ficar só na conversa, nunca ficar só
"consertado visualmente" naquele caso específico.

## Documentação da API do Revit

Sempre que precisar consultar classes/métodos/propriedades/namespaces do
RevitAPI durante a modulação, pesquisar em
https://www.revitapidocs.com/2027/ antes de implementar (regra já em
`CLAUDE.md`).
