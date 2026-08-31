RODADA PROVISORIA / DIAGNOSTIC ONLY - Etapa 2B (2026-08-31).

O catalogo destes arquivos veio do reference.json, ou seja, das pecas
que a PESSOA usou. Isso e' vazamento do gabarito para a entrada do
solver. Score 6,6% desta rodada NAO e' baseline historica oficial -
esta' guardado so' para auditoria da Etapa 2B.1, que refez tudo com
catalogo extraido dos tipos carregados no documento INPUT.

Catalogo contaminado desta rodada (15 codigos, vindos do gabarito):
B19, B19_C, B34, B34_C, B39, B39_C, B54, B54_C, C04, C09, C09_C,
CAN34, CAN39, CJ19, CM19.

Catalogo correto (Etapa 2B.1, vindo dos FamilySymbol carregados no
documento INPUT - ver input.json/input_real.json na raiz do projeto):
6 codigos - B19, B34, B39, B54, C04, C09. Os 9 a mais desta rodada
provisoria sao pecas cortadas/canaletas que o solver de hoje nao
implementa (ver catalog_comparison.json).

167 paredes nos dois casos (o Wall Modeling nao muda entre as duas
rodadas - so' o catalogo entregue ao solver muda).

O input.json completo desta rodada (91KB) nao foi mantido - ele e'
regenerado por revit_catalog_dump.py trocando o catalogo do
input_from_snapshot.build_input() pelo catalog_comparison.json
"only_in_reference"; o wall_modeling_snapshot.json e' o mesmo dos
dois lados.
