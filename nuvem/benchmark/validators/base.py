# -*- coding: utf-8 -*-
"""Base dos validadores: taxonomia de erro, estrutura do achado e o
registro que o runner percorre.

DUAS DECISOES QUE VALEM PARA TODOS OS VALIDADORES:

1. **Cada validador e' independente** (item 8 do pedido). Nenhum deles
   devolve "CORRETO/ERRADO" do projeto - cada um responde por UMA classe
   de problema, sobre UMA parede de cada vez, e devolve achados. Um
   validador nunca chama outro nem depende da ordem de execucao.

2. **NIVEL 1 x NIVEL 2** (item 10). Nivel 1 e' regra OBRIGATORIA: falhar
   e' erro, ponto. Nivel 2 e' PREFERENCIA: uma solucao diferente da do
   projetista humano nao e' erro se cumprir o nivel 1. Por isso o nivel
   e' propriedade da CLASSE DE ERRO, nao do validador - o mesmo validador
   pode emitir os dois (ex.: `compensators` emite
   COMPENSATOR_CONSECUTIVE, obrigatorio, e COMPENSATOR_COUNT_ABOVE_HUMAN,
   preferencia).

Nada aqui usa Revit nem IA: o pedido (item 19) e' explicito - regra que
da' pra conferir com geometria/aritmetica e' conferida em codigo.
"""

LEVEL_MANDATORY = 1
LEVEL_PREFERENCE = 2

SEVERITY_CRITICAL = "critical"
SEVERITY_MAJOR = "major"
SEVERITY_MINOR = "minor"
SEVERITY_INFO = "info"

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"

# Categorias = um validador cada (item 13: metricas POR CATEGORIA).
CATEGORY_PRISM = "prism"
CATEGORY_COMPENSATORS = "compensators"
CATEGORY_JUNCTIONS = "junctions"
CATEGORY_OPENINGS = "openings"
CATEGORY_COVERAGE = "wall_coverage"
CATEGORY_POSITIONS = "block_positions"

ALL_CATEGORIES = (
    CATEGORY_PRISM, CATEGORY_COMPENSATORS, CATEGORY_JUNCTIONS,
    CATEGORY_OPENINGS, CATEGORY_COVERAGE, CATEGORY_POSITIONS,
)


class ErrorClass(object):
    """Uma classe de erro da taxonomia (item 9). Existe como objeto, e nao
    como string solta espalhada pelos validadores, por um motivo pratico:
    o nivel/severidade/regra de origem de um erro precisa ser respondido
    em UM lugar so' - se cada validador escrevesse o seu, a primeira
    divergencia entre dois validadores viraria um score errado sem
    ninguem perceber."""

    def __init__(self, code, category, level, severity, summary, rule_ref=""):
        self.code = code
        self.category = category
        self.level = level
        self.severity = severity
        self.summary = summary
        # De onde a regra vem - secao do REGRAS_MODULACAO_BLOCOS.md ou
        # funcao do motor. Nunca vazio para erro de nivel 1.
        self.rule_ref = rule_ref

    def as_dict(self):
        return {
            "code": self.code,
            "category": self.category,
            "level": self.level,
            "severity": self.severity,
            "summary": self.summary,
            "rule_ref": self.rule_ref,
        }


def _c(code, category, level, severity, summary, rule_ref=""):
    return ErrorClass(code, category, level, severity, summary, rule_ref)


# ------------------------------------------------------------- taxonomia
#
# FONTE UNICA da verdade. `knowledge/error_classes.json` e' GERADO daqui
# (ver `dump_error_classes`), nunca escrito a mao - um arquivo .json
# editado por fora divergiria do codigo no primeiro descuido.
ERROR_CLASSES = [
    # ---- prisma (junta vertical corrida entre fiadas) -----------------
    _c("PRISM_CONTINUOUS_JOINT", CATEGORY_PRISM, LEVEL_MANDATORY,
       SEVERITY_CRITICAL,
       "junta vertical alinhada em fiadas consecutivas (prisma)",
       "REGRAS_MODULACAO_BLOCOS.md secao 11 (regra #1)"),
    _c("PRISM_JOINT_STACK", CATEGORY_PRISM, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "junta vertical repetida em muitas fiadas da mesma paridade",
       "REGRAS_MODULACAO_BLOCOS.md secao 11.7"),
    _c("PRISM_STAGGER_BELOW_TARGET", CATEGORY_PRISM, LEVEL_PREFERENCE,
       SEVERITY_MINOR,
       "desencontro menor que o alvo, sem chegar a alinhar",
       "REGRAS_MODULACAO_BLOCOS.md secao 10.6"),

    # ---- compensadores ------------------------------------------------
    _c("COMPENSATOR_CONSECUTIVE", CATEGORY_COMPENSATORS, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "dois ou mais compensadores encostados na mesma fiada",
       "REGRAS_MODULACAO_BLOCOS.md secao 2 (regra dos compensadores)"),
    _c("COMPENSATOR_EXCESS_IN_RUN", CATEGORY_COMPENSATORS, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "compensadores acima do teto permitido no trecho",
       "MAX_COMPENSATORS_PER_TRECHO (core/engine/wall_stepper.py)"),
    _c("COMPENSATOR_VERTICAL_STRIP", CATEGORY_COMPENSATORS, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "faixa vertical de compensadores empilhados entre fiadas",
       "REGRAS_MODULACAO_BLOCOS.md secao 11.5"),
    _c("COMPENSATOR_AVOIDABLE", CATEGORY_COMPENSATORS, LEVEL_PREFERENCE,
       SEVERITY_MINOR,
       "compensador usado onde o vao fecharia com peca inteira",
       "REGRAS_MODULACAO_BLOCOS.md secao 2"),

    # ---- amarracoes ---------------------------------------------------
    _c("JUNCTION_MISSING_BINDING", CATEGORY_JUNCTIONS, LEVEL_MANDATORY,
       SEVERITY_CRITICAL,
       "encontro sem nenhuma peca de amarracao",
       "REGRAS_MODULACAO_BLOCOS.md secao 5"),
    _c("JUNCTION_NOT_ALTERNATING", CATEGORY_JUNCTIONS, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "amarracao do encontro nao alterna entre fiadas",
       "REGRAS_MODULACAO_BLOCOS.md secao 5 / 18.4"),
    _c("JUNCTION_WRONG_PIECE", CATEGORY_JUNCTIONS, LEVEL_PREFERENCE,
       SEVERITY_MINOR,
       "peca de amarracao diferente da usada pelo projetista no mesmo tipo de encontro",
       "padrao observado (benchmark/patterns.py)"),
    _c("JUNCTION_HALF_BLOCK_ADJACENT", CATEGORY_JUNCTIONS, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "meio-bloco encostado na amarracao do encontro",
       "REGRAS_MODULACAO_BLOCOS.md secao 11.6 (regra #2)"),

    # ---- aberturas ----------------------------------------------------
    _c("OPENING_BLOCK_INSIDE_DOOR", CATEGORY_OPENINGS, LEVEL_MANDATORY,
       SEVERITY_CRITICAL,
       "bloco dentro do vao de uma porta (peitoril 0)",
       "REGRAS_MODULACAO_BLOCOS.md secao 3 (zona de exclusao absoluta)"),
    _c("OPENING_BLOCK_INSIDE_WINDOW", CATEGORY_OPENINGS, LEVEL_MANDATORY,
       SEVERITY_CRITICAL,
       "bloco dentro da faixa vertical do vao de uma janela",
       "REGRAS_MODULACAO_BLOCOS.md secao 4"),
    _c("OPENING_BLOCK_CROSSES_JAMB", CATEGORY_OPENINGS, LEVEL_MANDATORY,
       SEVERITY_CRITICAL,
       "bloco atravessa a jamba, entrando parcialmente no vao",
       "REGRAS_MODULACAO_BLOCOS.md secao 3"),
    _c("OPENING_MISSING_LINTEL", CATEGORY_OPENINGS, LEVEL_PREFERENCE,
       SEVERITY_MAJOR,
       "vao sem verga/canaleta na fiada imediatamente acima",
       "REGRAS_MODULACAO_BLOCOS.md secao 10.2/10.3"),
    _c("OPENING_MISSING_COUNTER_LINTEL", CATEGORY_OPENINGS, LEVEL_PREFERENCE,
       SEVERITY_MINOR,
       "janela sem contraverga abaixo do peitoril",
       "REGRAS_MODULACAO_BLOCOS.md secao 10.4"),
    _c("OPENING_SOLID_BELOW_SILL_MISSING", CATEGORY_OPENINGS, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "fiada abaixo do peitoril da janela ficou vazia (deveria ser solida)",
       "REGRAS_MODULACAO_BLOCOS.md secao 4"),

    # ---- cobertura ----------------------------------------------------
    _c("COVERAGE_WALL_NOT_MODULATED", CATEGORY_COVERAGE, LEVEL_MANDATORY,
       SEVERITY_CRITICAL,
       "parede sem nenhum bloco",
       "REGRAS_MODULACAO_BLOCOS.md secao 18.8"),
    _c("COVERAGE_MISSING_ROW", CATEGORY_COVERAGE, LEVEL_MANDATORY,
       SEVERITY_CRITICAL,
       "fiada faltando no meio da parede",
       "REGRAS_MODULACAO_BLOCOS.md secao 18.8"),
    _c("COVERAGE_GAP_IN_ROW", CATEGORY_COVERAGE, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "trecho sem blocos numa fiada, fora de qualquer abertura",
       "REGRAS_MODULACAO_BLOCOS.md secao 18.8"),
    _c("COVERAGE_ROW_MOSTLY_EMPTY", CATEGORY_COVERAGE, LEVEL_MANDATORY,
       SEVERITY_CRITICAL,
       "fiada praticamente vazia numa parede que tem outras fiadas cheias",
       "REGRAS_MODULACAO_BLOCOS.md secao 18.8"),
    _c("COVERAGE_PARTIAL_WALL", CATEGORY_COVERAGE, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "parede modulada so' em parte do comprimento",
       "REGRAS_MODULACAO_BLOCOS.md secao 18.8"),
    _c("COVERAGE_ORPHAN_BLOCKS", CATEGORY_COVERAGE, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "blocos que nao pertencem a nenhuma parede reconstruida",
       "benchmark/extract/reconstruct.py"),

    # ---- posicionamento -----------------------------------------------
    _c("POSITION_OVERLAP", CATEGORY_POSITIONS, LEVEL_MANDATORY,
       SEVERITY_CRITICAL,
       "dois blocos ocupando o mesmo volume na mesma fiada",
       "REGRAS_MODULACAO_BLOCOS.md secao 18.7"),
    _c("POSITION_OUTSIDE_WALL", CATEGORY_POSITIONS, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "bloco alem da ponta da parede",
       "REGRAS_MODULACAO_BLOCOS.md secao 7 (regra #1: nunca aumentar a parede)"),
    _c("POSITION_OFF_AXIS", CATEGORY_POSITIONS, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "bloco fora do eixo da parede (desvio perpendicular)",
       "BLOCK_TO_WALL_PERP_TOLERANCE_CM (benchmark/model.py)"),
    _c("POSITION_BAD_ORIENTATION", CATEGORY_POSITIONS, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "bloco com orientacao incompativel com o eixo da parede",
       "REGRAS_MODULACAO_BLOCOS.md secao 12"),
    _c("POSITION_LENGTH_MISMATCH", CATEGORY_POSITIONS, LEVEL_MANDATORY,
       SEVERITY_MAJOR,
       "comprimento ocupado nao bate com o comprimento da peca do catalogo",
       "benchmark/extract"),
]

ERROR_CLASS_BY_CODE = dict((e.code, e) for e in ERROR_CLASSES)


def error_class(code):
    try:
        return ERROR_CLASS_BY_CODE[code]
    except KeyError:
        raise KeyError(
            "classe de erro '{0}' nao existe na taxonomia. Toda classe "
            "nova entra em ERROR_CLASSES (validators/base.py) - e' de la' "
            "que sai knowledge/error_classes.json.".format(code)
        )


def finding(code, wall=None, detail="", **extra):
    """Um achado estruturado (item 9). `extra` carrega o que aquele
    validador tem de concreto - fiadas, blocos, coordenada da junta,
    largura medida. Nunca texto solto: `detail` e' so' a frase para o
    relatorio; quem for corrigir o algoritmo le' os campos."""
    klass = error_class(code)
    row = {
        "validator": klass.category,
        "code": code,
        "status": STATUS_FAIL,
        "level": klass.level,
        "severity": klass.severity,
        "wall": wall,
        "reason": klass.summary,
        "rule_ref": klass.rule_ref,
        "detail": detail,
    }
    row.update(extra)
    return row


def dump_error_classes():
    """Taxonomia inteira em forma serializavel - o que vai para
    `knowledge/error_classes.json`."""
    return {
        "schema_version": 1,
        "levels": {
            str(LEVEL_MANDATORY): "regra obrigatoria - falhar e' erro",
            str(LEVEL_PREFERENCE): (
                "preferencia/similaridade - divergir do projeto humano NAO "
                "e' erro se todo o nivel 1 passar"
            ),
        },
        "categories": list(ALL_CATEGORIES),
        "classes": [e.as_dict() for e in ERROR_CLASSES],
    }


# --------------------------------------------------------------- registro
_REGISTRY = []


def register(name, function):
    """Registra um validador. Assinatura: `function(project, context) ->
    lista de achados`. `context` traz o que o validador nao consegue
    deduzir sozinho (ex.: o gabarito, para os achados de nivel 2)."""
    _REGISTRY.append((name, function))
    return function


def registered():
    return list(_REGISTRY)


def clear_registry():
    """So' para os testes - nunca chamado em producao."""
    del _REGISTRY[:]
