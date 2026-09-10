# Mapeamento de famílias e configuração do plugin
STATUS: PROPOSED / PENDING USER APPROVAL. Nenhuma UI/API implementada.

## Antes de modular

Campo obrigatório futuro: **ESTRATÉGIA DE REFORÇO DE ABERTURAS**.

- Verga / Contraverga
- Canaletas

Escolha antes de calcular, com resumo de projeto/nível/recorte, catálogo e
pendências. Detectar famílias sugere candidatos, não escolhe estratégia:
BUTANTÃ tem 69 tipos dedicados sem instâncias.
Escopo inicial proposto: uma estratégia por modulação/recorte no mesmo
nível, preservando segregação §10.1. Mistura por abertura exige contrato posterior.

## Detectar → selecionar → mapear → validar

1. Inventariar tipos, dimensões e capacidades do documento.
2. Sugerir correspondências revisáveis por dimensão/perfil/parâmetros.
3. Exibir tipo lógico ↔ família/tipo escolhido, papel, medida e fonte.
4. Validar completude para a estratégia e peças efetivamente necessárias.
5. Fixar snapshot do mapping antes do solve.

~~~
FamilyMappingEntry:
  logical_type_id, mapping_version, document_fingerprint
  family_identity, type_identity, exact_family_name, exact_type_name
  realization: DEDICATED_TYPE | INSTANCE_PARAMETERS
  parameter_bindings[]:
    stable_parameter_id, scope, storage_type, unit, writable, allowed_range
  local_origin, axes, mirrored_support, geometric_signature
  verified_dimensions_cm, verified_roles, evidence_ref
~~~

IDs persistidos são locais; reabertura/recarregamento exige resolução e
revalidação. Não serializar objeto Revit para o motor ou ElementId isolado
entre projetos. Nomes são rótulos/fallback com revisão, não prova de capacidade.

Verga fixa usa comprimento discreto de tipo; variável pode usar parâmetro
de instância. Preferir identificador estável/GUID quando disponível, com
escopo/unidade explícitos. Parâmetro ausente ou somente leitura não permite
substituição silenciosa. Não editar tipo compartilhado para uma peça.
Não carregar/duplicar família ou escrever modelo durante simples detecção.

## Falta de família e feedback

Bloquear início e listar papel/tipo lógico, dimensão, candidatos e motivo:
“Falta uma canaleta de 19 cm de altura compatível com este catálogo.
Selecione o tipo e confira as dimensões para continuar.”
Não trocar verga↔canaleta, cortado↔inteiro ou U↔J automaticamente.
Outra estratégia exige escolha explícita e novo cálculo.

Se inspeção sem escrita não comprovar geometria, marcar VALIDATION_PENDING.
Ensaio em cópia de projeto é etapa separada; não prometer compatibilidade.

## Materialização

Conversão cm↔unidade interna na fronteira, mantendo datum, cotas, eixos e pose.
Bbox inflada não define dimensão. Cortes alteram apenas parâmetros autorizados.
Mapear piece_id ↔ ID local criado, contabilizando compartilhados uma vez.
Mudança de entrada/configuração/catálogo/mapping invalida assinatura.

Criação atômica/retenção e assinatura existem em candidatos beta;
não presumir sua integração à main. A CR futura precisa revisão específica
dessas proteções ou contrato equivalente validado.

## Consulta API

Referência 2027 consultada, sem certificar host histórico 2026:
[FilteredElementCollector/GetElementIdIterator](https://www.revitapidocs.com/2027/0b1cdbeb-21ce-a4c5-6cae-253595818085.htm)
e [FamilyInstanceFilter](https://www.revitapidocs.com/2027/ec0bdad7-e213-f22a-94ef-bc0fd96ac641.htm).
Documentam iteração filtrada e seleção de instâncias de tipo; não validam
particularidades das famílias humanas. Reconsultar API 2027 para cada
método efetivamente usado na futura CR.
