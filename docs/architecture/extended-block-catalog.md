# Catálogo lógico estendido e cortes
STATUS: PROPOSED / PENDING USER APPROVAL. Produção intacta.
[Estratégias](opening-reinforcement-strategies.md) · [Mapping](revit-family-mapping.md).

## Catálogo lógico ↔ realização no documento

Tipo lógico define geometria/capacidades/restrições; FamilyMapping resolve
família/tipo. Não é nome de família ou ElementId. O catálogo atual permanece
vigente até CR aprovada.

| Grupo proposto | ID/capacidade | Dados necessários |
|---|---|---|
| Núcleo atual | B39/B34/B54/B19/C09/C04 | Dimensões, células, compensador, usos |
| Canaleta U | CHANNEL_U_39 / _34 / _19 | Perfil, 19 cm em Z, juntas, orientação |
| Canaleta J | CHANNEL_J + variante | Seção assimétrica, lados 9/19 quando comprovados |
| Variável | CHANNEL_U_VARIABLE / CHANNEL_J_VARIABLE | Faixa de comprimento e parametrização aprovadas |
| Verga/contraverga | DEDICATED_LINTEL / COUNTERLINTEL | 9 cm, comprimentos discretos, papéis aptos |
| Meia-altura | Variante de base com HEIGHT_CUT | Geometria/células próprias em 9 cm |
| Corte longitudinal | Variante com LENGTH_CUT | Comprimento final, células preservadas |
| Compensador deitado | COMPENSATOR_LAID | Pose/dimensões próprias; não corte implícito |
| Outras peças comprovadas | Entrada versionada, não habilitada inicialmente | Evidência e aprovação |

Envelope não descreve integralmente canaleta J; validação fina usa volume e
células. Não deduzir capacidade de amarração da peça cortada por chamar-se B34/B54.
Vedação e capacidade estrutural são explícitas; dimensão igual não aprova tipo VEDAÇÃO.

## Dados propostos

~~~
LogicalBlockType:
  id, catalog_version, description
  nominal_dimensions_cm {length, width, height}
  solid_profile, void_cells_local, small_cell_reference
  allowed_roles, structural_scope, orientation_capabilities
  supported_cuts, permitted_dimensions, evidence_refs, approval_ref

PieceSpec:
  piece_id, logical_type_id, wall_ids, opening_ids, roles
  nominal_dimensions_cm, effective_dimensions_cm
  cut_operations[], pose {origin_cm, axes, mirrored}
  course_index, subcourse_id, z_lo_cm, z_hi_cm
  support_refs, catalog_version, policy_version

CutOperation:
  kind: HEIGHT_CUT | LENGTH_CUT
  axis: LOCAL_Z | LOCAL_U
  original_dimension_cm, final_dimension_cm
  removed_side, resulting_profile_id, evidence_ref, approval_ref
~~~

HEIGHT_CUT reduz Z (19→9), preservando comprimento.
LENGTH_CUT reduz u (39→24), preservando altura.
Duas operações no mesmo item só com permissão explícita; senão
CUT_COMBINATION_UNSUPPORTED. CUT_BLOCK ambíguo não é contrato.
Deitar/rotacionar é pose, não sinônimo de corte.

Preservar dimensões nominais/finais e manufacturing_variant:
DEDICATED_TYPE ou PARAMETRIC. Referências demonstram representação, não
provam serra/fabricação real. Família pronta de 9 cm não implica operação
física executada pelo plugin.

Cortes são candidatos sujeitos a limite, apoio, células, junta e catálogo,
não solução automática para todo residual. Exigir final>0 e final≤nominal
no eixo cortado; demais eixos preservados; valores finitos. Não arredondar
silenciosamente ou criar tolerância nova.

## Evolução do candidato atual e Revit

_make_block_candidate contém logical_code, course, origin_world, eixos,
length_cm/width_cm e células. A extensão precisa de altura/Z por peça;
_block_height_ft/_course_height_ft globais não bastam.
Futura CR introduz adaptador versionado de candidatos legados sem remover
campos ou mudar defaults inadvertidamente.

Materialização resolve PieceSpec em família/tipo e parâmetros permitidos.
Meia-altura dedicada e comprimento variável são realizações diferentes.
Releitura verifica dimensões/pose após criação; discrepância invalida
recorte e exige rollback.

Validar IDs, esquema, unidades, perfis/células, intervalos, papéis e mapping.
Negativos: família homônima errada, VEDAÇÃO, bbox inflada, corte fora da
faixa, corte proibido e perda de célula. Hash acompanha resultado/cache/exportação.
Não sobrescrever versões nem reclassificar benchmark nesta entrega.
