# -*- coding: utf-8 -*-
"""Construtor das fixtures minimas do corpus BUTANTA.

POR QUE ISTO EXISTE
-------------------
Os defeitos fisicos que a missao de correcoes do BUTANTA vem atacando -
vazado menor do B34 desalinhado, peca sem apoio, especiais encostados,
canaleta, microajuste de abertura - nao tem NENHUMA fixture permanente no
repositorio. A unica coisa que existe e' script avulso em
`docs/checkpoints/evidence/_scripts/`, que e' registro datado, nao corpus
mantido. Uma regressao em qualquer um deles passaria despercebida.

O QUE ISTO E' - E O QUE AINDA NAO E'
------------------------------------
E': a GEOMETRIA de entrada de cada caso, no mesmo `input.json` do
benchmark (`schema_version` 2), pequena o suficiente para caber num teste
rapido, escrita a partir do PRINCIPIO FISICO medido - nunca copiada de um
projeto.

NAO E': gabarito. Enquanto o PR #42 estiver mudando a fisica, gravar um
`expected` a partir da saida corrente congelaria como "certo" um estado
que ainda esta' em movimento - e `golden/compare.py::_critical_regressions`
conta codigo novo como REGRESSAO CRITICA. Por isso cada caso traz um
`expected.PENDING.json` que diz, em texto, QUAL asercao vai valer, e
nenhum numero de saida do solver. Capturar a referencia e' missao
separada, depois do #42 estabilizar, com autorizacao de baseline.

POR QUE FICA FORA DE `projects/`
--------------------------------
`runner.list_projects()` varre `nuvem/benchmark/projects/` e devolve todo
diretorio com `input.json`. Um projeto novo ali entraria HOJE nas
parametrizacoes de `tests/regression/test_benchmark_baselines.py` e
mudaria o portao de corpus enquanto o #42 esta' em voo. Esta pasta e'
area de preparo: quando houver gabarito autorizado, o caso migra para
`projects/butanta_r08_lt_1pav/`.

NAO OVERFIT
-----------
Nenhuma fixture usa ElementId, nome `W0xx`, coordenada de projeto ou
qualquer identidade do BUTANTA. Cada uma e' construida a partir de
medidas em cm no referencial local, e o que ela representa e' um
PRINCIPIO que vale em qualquer projeto com este catalogo.

    python3 nuvem/benchmark/corpus_butanta/build_fixtures.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # raiz do repo

# Catalogo REAL do dominio (mesmo de `projects/piloto_sintetico_2x2`), nao
# uma invencao da fixture: o B34 e' assimetrico e o vazado MENOR dele
# (`cells_local_cm[0]`, 10,7cm em -10,2) e' justamente o que a regra 52
# manda alinhar entre fiadas vizinhas.
CATALOG_SOURCE = os.path.join(
    ROOT, "nuvem", "benchmark", "projects", "piloto_sintetico_2x2", "input.json")

COURSE_STEP_CM = 20.0
BLOCK_HEIGHT_CM = 19.0
THICKNESS_CM = 14.0


def _catalog():
    with open(CATALOG_SOURCE, encoding="utf-8") as handle:
        return json.load(handle)["catalog"]


def _wall(wall_id, start, end, height_cm, openings=None):
    (x0, y0), (x1, y1) = start, end
    length = round(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5, 4)
    angle = 0.0 if abs(y1 - y0) < 1e-9 else 90.0
    key = "W|{0},{1}|{2},{3}|t{4}".format(x0, y0, x1, y1, THICKNESS_CM)
    rows = []
    for index, opening in enumerate(openings or [], start=1):
        opening = dict(opening)
        opening.setdefault("source_element_id", None)
        opening.setdefault("confidence", "synthetic")
        opening["width_cm"] = round(opening["t_end_cm"] - opening["t_start_cm"], 4)
        opening["height_cm"] = round(opening["head_cm"] - opening["sill_cm"], 4)
        opening["id"] = "{0}-O{1:02d}".format(wall_id, index)
        opening["key"] = "{0}|O|{1}-{2}|s{3}".format(
            key, opening["t_start_cm"], opening["t_end_cm"], opening["sill_cm"])
        rows.append(opening)
    return {
        "id": wall_id,
        "key": key,
        "start_cm": [float(x0), float(y0)],
        "end_cm": [float(x1), float(y1)],
        "length_cm": length,
        "angle_deg": angle,
        "thickness_cm": THICKNESS_CM,
        "base_z_cm": 0.0,
        "height_cm": float(height_cm),
        "openings": rows,
        "junctions": [],
        "rows": [],
        "source_element_ids": [],
    }


def _opening(kind, t_start_cm, t_end_cm, sill_cm, head_cm):
    return {"kind": kind, "t_start_cm": float(t_start_cm), "t_end_cm": float(t_end_cm),
            "sill_cm": float(sill_cm), "head_cm": float(head_cm)}


def _project(project_id, walls, num_courses, notes):
    height = max(w["height_cm"] for w in walls)
    return {
        "schema_version": 2,
        "project_id": project_id,
        "source": "input",
        "settings": {
            "base_z_cm": 0.0,
            "course_step_cm": COURSE_STEP_CM,
            "block_height_cm": BLOCK_HEIGHT_CM,
            "num_courses": num_courses,
            "expected_rows": num_courses,
            "wall_thickness_cm": THICKNESS_CM,
            "walls_already_extended": False,
        },
        "catalog": _catalog(),
        "orphan_blocks": [],
        "metadata": {
            "synthetic": True,
            "generator": "nuvem/benchmark/corpus_butanta/build_fixtures.py",
            "derived_from": "principio fisico medido no BUTANTA R08_LT; nenhuma "
                            "identidade, ElementId ou coordenada do projeto",
            "wall_height_cm": height,
            "notes": notes,
        },
        "walls": walls,
    }


# =====================================================================
# Os casos. Cada um: (subpasta, nome, principio, o que o expected vai
# afirmar quando houver gabarito, projeto).
# =====================================================================

def cases():
    out = []

    # -- B34: vazado menor alinhado entre fiadas -----------------------
    # Parede reta com as DUAS pontas livres e comprimento que o
    # preenchimento fecha com varios B34. O princípio nao depende do
    # comprimento exato: e' a relacao ENTRE FIADAS VIZINHAS.
    out.append((
        "b34_alignment", "b34_single_wall",
        "REGRAS 52 - o vazado MENOR de um B34 de meio de parede tem de cair "
        "sobre um vazado menor (B34) ou sobre o vazado central de um B54 na "
        "fiada vizinha. Peca de no' nunca gira.",
        "Para todo B34 de preenchimento e toda fiada vizinha, a peca de "
        "alvenaria que cobre o centro do vazado menor oferece vazado menor "
        "ou vazado central naquele ponto. Contador de violacoes = 0.",
        _project("butanta_b34_single_wall",
                 [_wall("A", (0.0, 0.0), (219.0, 0.0), 60.0)],
                 3, "duas pontas livres; 3 fiadas bastam para exercitar N-1/N/N+1")))

    # Duas fiadas em que girar UM B34 nao resolve: so' o giro do PAR alinha
    # os dois vazados menores (caso `test_pair_rotation_*` do PR #42).
    out.append((
        "b34_alignment", "b34_pair_courses",
        "REGRAS 52 - existe configuracao em que nenhum giro individual "
        "alinha; a decisao e' sobre o PAR de fiadas, nao sobre uma peca.",
        "O alinhamento e' atingido girando os dois B34 juntos, e o "
        "resultado e' invariante a translacao, a ordem de entrada e ao "
        "sentido dos endpoints.",
        _project("butanta_b34_pair_courses",
                 [_wall("A", (0.0, 0.0), (149.0, 0.0), 40.0)],
                 2, "trecho curto: forca o par de fiadas a decidir junto")))

    # -- CHANNEL --------------------------------------------------------
    # Janela: canaleta na verga (offset 0,00cm em 99,26% dos 136 medidos)
    # E uma fiada de canaleta imediatamente sob o peitoril (100%, 89/89).
    # Vao de 120cm: a faixa 120-149cm tem canaleta acima em 57/57.
    out.append((
        "channel_window", "window_head_sill",
        "REGRAS 41/51 - janela recebe canaleta apoiada no topo do vao E uma "
        "unica fiada de canaleta imediatamente sob o peitoril; nunca uma "
        "segunda fiada abaixo (0/89).",
        "Uma canaleta na fiada do topo do vao com offset 0; exatamente uma "
        "sob o peitoril; nenhuma peca de canaleta dentro do vao; "
        "MISSING_REQUIRED_CHANNEL = 0 e EXTRA_CHANNEL = 0.",
        _project("butanta_channel_window",
                 [_wall("A", (0.0, 0.0), (300.0, 0.0), 260.0,
                        [_opening("window", 90.0, 210.0, 100.0, 220.0)])],
                 13, "janela de 120cm, peitoril 100, verga 220")))

    # Porta: canaleta na verga, e NADA abaixo (nao ha' peitoril).
    out.append((
        "channel_door", "door_head_only",
        "REGRAS 41/51 - porta recebe canaleta no topo do vao (47/47 medidos) "
        "e nunca canaleta inferior: nao existe peitoril.",
        "Uma canaleta na fiada do topo do vao; zero canaleta abaixo; "
        "zero peca de alvenaria dentro do vao ate' a verga.",
        _project("butanta_channel_door",
                 [_wall("A", (0.0, 0.0), (300.0, 0.0), 260.0,
                        [_opening("door", 100.0, 190.0, 0.0, 210.0)])],
                 13, "porta de 90cm, sem peitoril")))

    # -- T com B54 -------------------------------------------------------
    # Vao encostado no no' T: a jamba cai na face da parede que chega.
    out.append((
        "t_with_b54", "t_jamb_on_incoming_face",
        "REGRAS 51 - com a jamba na face da parede que chega, a canaleta "
        "cruza o no' (como o humano faz) e o B54 da principal que ficaria "
        "sobre o vao e' dividido, sem criar junta alinhada nova.",
        "Canaleta cobre o no'; nenhuma peca de amarracao fica suspensa "
        "sobre o vao (TIE_OVER_SPAN = 0); PRISM_CONTINUOUS_JOINT = 0.",
        _project("butanta_t_with_b54",
                 [_wall("A", (0.0, 0.0), (300.0, 0.0), 260.0,
                        [_opening("door", 150.0, 240.0, 0.0, 210.0)]),
                  _wall("B", (150.0, 0.0), (150.0, 200.0), 260.0)],
                 13, "T: a parede B chega no meio de A, jamba do vao na face de B")))

    # -- Especiais --------------------------------------------------------
    # C09+C09 em pe encostados: o humano tem ZERO. HARD ERROR.
    out.append((
        "special_clusters", "c09_c09_upright",
        "REGRAS 56.2 - dois compensadores de mesmo codigo em pe encostados "
        "sao proibidos: medido 0 no projeto humano.",
        "COMPENSATOR_CONSECUTIVE = 0 nesta parede, em todas as fiadas.",
        _project("butanta_c09_c09_upright",
                 [_wall("A", (0.0, 0.0), (117.0, 0.0), 60.0)],
                 3, "resto que o guloso fecharia com C09 C09 encostados")))

    # C04+C04 que deveria virar o compensador do vao total (secao 54).
    out.append((
        "special_clusters", "c04_c04_span",
        "REGRAS 54 - dois compensadores iguais encostados viram o "
        "compensador do vao total (C04+C04 -> C09), mesmo vao, uma peca.",
        "Zero par C04+C04 encostado; o vao coberto e' identico ao de antes "
        "da fusao; peca de no' nunca e' fundida.",
        _project("butanta_c04_c04_span",
                 [_wall("A", (0.0, 0.0), (127.0, 0.0), 60.0)],
                 3, "resto de 9cm que o guloso parte em C04+C04")))

    # -- Sob janela --------------------------------------------------------
    # Junta de argamassa de ~1,6cm sob o peitoril NAO e' vazio fisico.
    out.append((
        "under_window", "sill_joint_1_6cm",
        "Junta de argamassa de ate' ~1,6cm sob o peitoril e' JUNTA, nao "
        "vazio: MISSING_UNDER_WINDOW cru conta como se fosse buraco.",
        "OPENING_SOLID_BELOW_SILL_MISSING = 0 (a folga e' junta); e o "
        "contador cru de sub-preenchimento registra a folga como junta.",
        _project("butanta_under_window_joint",
                 [_wall("A", (0.0, 0.0), (300.0, 0.0), 260.0,
                        [_opening("window", 90.0, 210.0, 101.6, 221.6)])],
                 13, "peitoril 101,6: deixa 1,6cm acima da ultima fiada cheia")))

    # -- Microajuste de abertura ------------------------------------------
    # Faixa de 20-35cm entre a peca de no' e a jamba: B34+junta (35cm) nao
    # cabe e a fiada e' obrigada a fechar com peca de acerto. 41 faixas
    # assim foram censadas no BUTANTA.
    out.append((
        "opening_adjustment", "strip_20_35cm",
        "REGRAS 66 - entre a peca de no' e a jamba sobra 20-35cm: um B34 "
        "mais junta (35cm) nao cabe e a fiada fecha com peca de acerto. "
        "Deslocar o vao em multiplo do modulo (5cm) abre espaco.",
        "Menor deslocamento vence; 0 vence empate; o deslocamento TOTAL "
        "desde a posicao do projeto nunca passa de 10cm em execucoes "
        "repetidas; largura, altura, peitoril e nivel nao mudam.",
        _project("butanta_opening_strip",
                 [_wall("A", (0.0, 0.0), (300.0, 0.0), 260.0,
                        [_opening("door", 89.0, 179.0, 0.0, 210.0)]),
                  _wall("B", (0.0, 0.0), (0.0, 200.0), 260.0)],
                 13, "canto L em t=0; do B54 do no' ate' a jamba sobram ~30cm")))

    # -- Apoio -------------------------------------------------------------
    out.append((
        "support", "small_block_over_empty_course",
        "REGRAS 53 - peca pequena nao pode ficar suspensa sobre fiada "
        "vazia; peca sobre vao ativo e' reforco, nao falta de apoio.",
        "UNSUPPORTED_SMALL_BLOCK = 0 fora de vao; peca com metade ou mais "
        "de apoio nunca e' acusada; apoio vindo de parede perpendicular "
        "conta; a ordem do relato e' deterministica.",
        _project("butanta_support_empty_course",
                 [_wall("A", (0.0, 0.0), (86.0, 0.0), 60.0),
                  _wall("B", (86.0, 0.0), (86.0, 115.0), 60.0)],
                 3, "anel curto: miolos fora do modulo deixavam fiada sem preenchimento")))

    return out


def write():
    written = []
    for folder, name, principle, pending, project in cases():
        directory = os.path.join(HERE, "fixtures", folder, name)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        input_path = os.path.join(directory, "input.json")
        with open(input_path, "w", encoding="utf-8") as handle:
            json.dump(project, handle, indent=1, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        pending_path = os.path.join(directory, "expected.PENDING.json")
        with open(pending_path, "w", encoding="utf-8") as handle:
            json.dump({
                "status": "PENDING_REFERENCE",
                "why_pending": "O PR #42 ainda esta' mudando a fisica. Gravar "
                               "expected a partir da saida corrente congelaria "
                               "um estado em movimento e faria codigo novo "
                               "contar como regressao critica "
                               "(golden/compare.py::_critical_regressions).",
                "principle": principle,
                "assertion_when_frozen": pending,
                "reference_kind": None,
                "confidence": "NONE",
                "authorization_required": "captura de referencia + --save-baseline, "
                                          "em missao separada, depois do #42 estabilizar",
            }, handle, indent=1, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        written.append(os.path.relpath(input_path, ROOT))
    return written


if __name__ == "__main__":
    for path in write():
        print(path)
