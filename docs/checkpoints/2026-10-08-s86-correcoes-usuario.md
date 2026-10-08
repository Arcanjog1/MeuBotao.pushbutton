# §86 — correções do usuário de 05 e 08/10 sobre o pavimento recriado (tocos, canaletas, pastilhas, meia canaleta, B54 da cinta)

Estado CANDIDATO local da branch `claude/revit-butanta-modulation-8611b5` — sem PR, sem push, sem merge. Não é
estado oficial nem aprovação normativa.

```json
{
  "date": "2026-10-08",
  "scope": "historical",
  "branch": "claude/revit-butanta-modulation-8611b5",
  "head": "06ecb87cb39303969b35ee8e65d9c7479d353509",
  "base": "894e3f5278ffa9cb030efe01a70c7305b252af15",
  "pr": "not-created",
  "objective": "Aplicar as correcoes do usuario feitas na revisao do pavimento recriado no butanta testes (2026-10-05 e 2026-10-08) e gerar outra modulacao: paredes nao moduladas porque o humano nao modula (tocos), pastilhas nao alinhadas perto de aberturas, canaletas de 34/39 desalinhadas com a modulacao abaixo, meia canaleta que nao existe, B54 da ultima fiada como canaleta 34 + 19.",
  "changes": [
    "0a968f3/3eb6e13 86.9: tocos modulados (STUB_TRIM_ENABLED = False); so' a sobra de eixo <= 10 cm alem da face (erro de CAD) continua aparada (W8, 5 cm).",
    "70c20b5 86.12 (novo modulo channel_grid_follow.py): verga, contraverga e cinta seguem a grade da fiada de mesma paridade abaixo; o ajuste de fase fica sobre o vao.",
    "0e398bf 86.13: compensador/pastilha encostados no vao e alinhados entre as fiadas, B19 atras (falha dura + termo do objetivo no recompositor da jamba).",
    "77a8986 86.13: segunda passada da jamba depois do alinhamento das canaletas (JAMB_SECOND_PASS_AFTER_GRID_FOLLOW).",
    "152a5ac 86.15: T com toco - a peca da fiada que passa atravessa a face (B54 medido na fiada do T); paredes de 99 cm sem junta a prumo.",
    "06ecb87 86.14 + 86.16: sem meia canaleta (U19) fora da cinta - meio bloco/compensador abaixo completados por U34/U39 (juntas entre blocos inteiros continuam seguidas); B54 da ultima fiada (inclusive o de amarracao do T) vira U34 + U19.",
    "DOCS: REGRAS 86.0 (linha nova), 86.9, 86.12-86.16; este checkpoint; evidencias em docs/checkpoints/evidence/2026-10-08-s86-correcoes-usuario/; PROJECT_STATUS; o checkpoint de 2026-10-05 vira historico.",
    "REVIT (butanta testes, instancia unica porta 48884; COBERTURA BALCONY aberto e intocado; troca de documento ativo autorizada pelo usuario): lote 20261005-154813 substituido pelo lote 20261008-143828 (6 526 pecas); 35 vistas S86 refeitas; arquivo NAO salvo; copia previa 'butanta testes - BACKUP antes S86 rodada5 2026-10-08.rvt'."
  ],
  "tests": [
    "HEAD 06ecb87: py -3 -m pytest tests/test_script.py tests/test_sem_meia_canaleta_86_14.py tests/test_b54_cinta_86_16.py tests/test_channel_grid_follow_86_12.py tests/test_top_bond_beam.py tests/test_junta_no_toco_86_15.py tests/test_compensator_at_jamb_face_86_13.py tests/test_stub_trim_86_9.py -q -> 422 passaram (9 min 23 s).",
    "77a8986: test_script + 86.13 + 86.12 + jamb_* + top_bond_beam + opening_structural + regras_gerais -> 456 + 25 passaram; falha antiga test_dois_compensadores_evitaveis_viram_meio_bloco.",
    "Suite completa NAO executada (memoria curta da maquina).",
    "Calculo completo offline r7_13 (motor 06ecb87, 13 fiadas, aberturas originais) e leitura de volta do Revit: 6 526 pecas, celulas identicas ao calculo (0,0 cm)."
  ],
  "known_failures": [
    "tests/test_regras_gerais_composicao.py::test_dois_compensadores_evitaveis_viram_meio_bloco (ja' falhava na base).",
    "Revit: 3 verga/contraverga nao resolvidas (topo fora da grade, 51.8)."
  ],
  "physical_deltas": [
    "F1 de pecas contra o humano 56,2 % (2026-10-05) -> 56,5 %; furos quebrados 417 -> 342 (humano 407); septos sem apoio 107 -> 83 (humano 60); pastilhas 360 -> 395 (humano 486).",
    "Canaletas: juntas no meio de BLOCO INTEIRO da fiada c-2 53 -> 21 (as que restam: a canaleta precisa avancar sobre o bloco vizinho para cobrir meio bloco/pastilha com U34/U39); meia canaleta 128 -> 23, todas do B54 da cinta (U34 + U19).",
    "Pastilha atras de bloco encostado no vao 51 -> 20 (restam W0 395-464, W3 1565, W11 409, W27 shaft - prisma primeiro; W0 1630 e' o pilarete de 54 do catalogo).",
    "Paredes reprovadas na auditoria final 3 (W28-W30, junta a prumo em x=49,5 nas 13 fiadas) -> 0.",
    "U_CUT no Revit com comprimento real 9/14/24/29 cm (a leitura de volta le 39 - defeito so' da leitura)."
  ],
  "decisions_taken": [
    "Usuario (2026-10-05): os tocos sao modulados; pastilhas alinhadas perto de aberturas; canaletas alinhadas com a modulacao abaixo.",
    "Usuario (2026-10-05): a meia canaleta nao existe; meio bloco abaixo e' completado por canaleta de 34 ou 39.",
    "Usuario (2026-10-08): o B54 da ultima fiada vira uma canaleta 34 e uma canaleta 19 (aplicado tambem ao B54 de amarracao do T - excecao a' regra 75 so' para esse caso).",
    "Integracao: a sobra de eixo de 5 cm da W8 (erro de CAD) continua aparada; prisma primeiro nos casos de pastilha sem solucao."
  ],
  "decisions_pending": [
    "B54 centrado do T na cinta: a junta U34|U19 cai na face da parede que chega, onde a verga ja' tem junta (achado TOP_BOND_BEAM_B54_JOINT_COINCIDENT) - manter ou deixar esse B54 como bloco.",
    "Pastilha fora da face nas 4 jambas listadas (exigiria quebrar o prisma).",
    "Pendencias anteriores: 30.5 x R4, shaft W27/W33, calco de C09 deitado e fiada partida H9 (51.8), lado fechado do C09 (R10)."
  ],
  "next_steps": ["Aguardar a revisao do usuario no Revit (vistas S86); merge so' com autorizacao especifica."],
  "references": [
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "nuvem/core/engine/channel_grid_follow.py"},
    {"path": "nuvem/core/engine/opening_reinforcement.py"},
    {"path": "nuvem/core/engine/b34_run_arrangement.py"},
    {"path": "nuvem/core/engine/wall_stepper.py"},
    {"path": "nuvem/core/engine/wall_pairing.py"},
    {"path": "docs/checkpoints/2026-10-05-s86-aproximacao-humano-revit.md"},
    {"path": "docs/checkpoints/evidence/2026-10-08-s86-correcoes-usuario/readback_revit_2026-10-08.json"},
    {"path": "docs/checkpoints/evidence/2026-10-08-s86-correcoes-usuario/placar_r7.txt"},
    {"path": "docs/checkpoints/evidence/2026-10-08-s86-correcoes-usuario/s5_create_r7.out"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## Onde está cada coisa

- Regras: `nuvem/REGRAS_MODULACAO_BLOCOS.md` §86.0 (tabela), §86.9, §86.12–§86.16.
- Evidência: `docs/checkpoints/evidence/2026-10-08-s86-correcoes-usuario/` (leitura de volta do Revit, placar,
  saída da criação, réguas `diag_hard.py`/`diag_face.py`/`diag_joints.py` com as saídas, vista 3D e elevações W04/W28).
- Solução injetada: `sol_r7_13.json` (SHA-256 `671cb384f54dee6abf6e09e258cb38fb91853226505748f9deb192c35420e2dc`), só no
  rascunho local `.claude/checkpoints/2026-10-01-s86-humano/` com as 35 imagens e o relatório HTML.
- Relatório visual (privado): https://claude.ai/artifact/DNiNe57WC9FsaE3cY3SoXM
