# -*- coding: utf-8 -*-
"""Loader ONLINE rastreavel (2026-09-23): commit resolvido, download pinado no
commit, cache com manifest verificavel e banner de proveniencia. Tudo fora do
Revit: as funcoes do loader sao extraidas do Script.py por AST e executadas
com dubles de rede (nenhum acesso ao GitHub)."""
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
FUNCOES = ("_package_digest", "_sha256_file", "_read_cache_manifest", "_verify_cache", "_loader_path",
           "_provenance", "_provenance_banner", "_sync_core_package", "_entry_point_from_existing_cache",
           "_load_entry_point")
COMMIT_A = "a" * 40
COMMIT_B = "b" * 40
ARQUIVOS_A = {"nuvem/core/wall_modeling.py": "# motor A\n", "nuvem/core/__init__.py": "",
              "nuvem/core/engine/__init__.py": "", "nuvem/core/engine/wall_stepper.py": "# stepper A\n"}
ARQUIVOS_B = dict(ARQUIVOS_A, **{"nuvem/core/wall_modeling.py": "# motor B\n"})


class _Forms(object):
    def __init__(self):
        self.alerts = []

    def alert(self, message, title=None, **_kw):
        self.alerts.append((title, message))


def loader(tmp_path, arquivos=None, commit=None, rede_ok=True):
    """Namespace com as funcoes do loader + dubles: `chamadas` registra o que
    tocou a rede."""
    tree = ast.parse((ROOT / "Script.py").read_text(encoding="utf-8-sig"))
    defs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in FUNCOES]
    assert {n.name for n in defs} == set(FUNCOES)
    chamadas = []
    forms = _Forms()

    def resolve(_token):
        chamadas.append("commit")
        if not rede_ok:
            raise RuntimeError("Falha ao contatar o GitHub (commit)")
        return commit

    def lista(_token, ref):
        chamadas.append(("tree", ref))
        return sorted(arquivos)

    def baixa(_token, repo_path, ref):
        chamadas.append(("raw", repo_path, ref))
        return arquivos[repo_path]

    ns = {"os": os, "io": io, "sys": sys, "json": json, "hashlib": hashlib, "re": __import__("re"),
          "shutil": __import__("shutil"), "datetime": __import__("datetime"),
          "PKG_CACHE_DIR": str(tmp_path / "pkg_cache"), "PKG_CACHE_TMP_DIR": str(tmp_path / "pkg_cache_tmp"),
          "CORE_CLOUD_DIR": "nuvem", "CORE_REPO_PREFIX": "nuvem/core/",
          "ENTRY_POINT_REPO_PATH": "nuvem/core/wall_modeling.py", "GITHUB_BRANCH": "main",
          "CACHE_MANIFEST_NAME": "manifest.json",
          "PROVENANCE_FIELDS": ("CHANNEL", "SOURCE_BRANCH", "RESOLVED_COMMIT", "PACKAGE_SHA",
                                "CACHE_STATUS", "LOADER_PATH", "CORE_PATH"),
          "__file__": str(tmp_path / "Script.py"),
          "_resolve_branch_commit": resolve, "_list_remote_core_files": lista, "_fetch_file_raw": baixa,
          "_pasta_do_loader": lambda: str(tmp_path), "_get_token": lambda force_reprompt=False: None,
          "_forget_token": lambda: None, "forms": forms, "print": lambda *a, **k: chamadas.append(("print", a)),
          "chamadas": chamadas}
    exec(compile(ast.Module(body=defs, type_ignores=[]), "loader-test", "exec"), ns)
    return ns


def test_primeira_sincronizacao_baixa_pinado_no_commit_e_grava_manifest(tmp_path):
    ns = loader(tmp_path, ARQUIVOS_A, COMMIT_A)
    entry, prov = ns["_sync_core_package"](None)
    assert Path(entry) == tmp_path / "pkg_cache" / "core" / "wall_modeling.py"
    assert prov["CHANNEL"] == "ONLINE" and prov["SOURCE_BRANCH"] == "main"
    assert prov["RESOLVED_COMMIT"] == COMMIT_A and prov["CACHE_STATUS"] == "MISS"
    # todo download e' pinado no SHA resolvido, nunca no nome da branch
    assert all(c[-1] == COMMIT_A for c in ns["chamadas"] if isinstance(c, tuple) and c[0] in ("tree", "raw"))
    manifest = json.loads((tmp_path / "pkg_cache" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["commit"] == COMMIT_A and manifest["channel"] == "ONLINE"
    assert set(manifest["sha256"]) == {p[len("nuvem/"):] for p in ARQUIVOS_A}
    assert manifest["package_sha"] == prov["PACKAGE_SHA"] == ns["_package_digest"](manifest["sha256"])
    # bytes do cache == bytes do blob (LF preservado): o hash bate com `git show`
    assert (tmp_path / "pkg_cache" / "core" / "wall_modeling.py").read_bytes() == b"# motor A\n"


def test_mesmo_commit_e_cache_integro_valida_sem_baixar(tmp_path):
    ns = loader(tmp_path, ARQUIVOS_A, COMMIT_A)
    ns["_sync_core_package"](None)
    del ns["chamadas"][:]
    entry, prov = ns["_sync_core_package"](None)
    assert prov["CACHE_STATUS"] == "VALIDATED" and prov["RESOLVED_COMMIT"] == COMMIT_A
    assert ns["chamadas"] == ["commit"]           # UMA chamada: so' o SHA da branch


def test_main_mudou_cache_antigo_nao_continua_em_silencio(tmp_path):
    ns = loader(tmp_path, ARQUIVOS_A, COMMIT_A)
    ns["_sync_core_package"](None)
    ns2 = loader(tmp_path, ARQUIVOS_B, COMMIT_B)
    entry, prov = ns2["_sync_core_package"](None)
    assert prov["CACHE_STATUS"] == "MISS" and prov["RESOLVED_COMMIT"] == COMMIT_B
    assert (tmp_path / "pkg_cache" / "core" / "wall_modeling.py").read_text() == "# motor B\n"
    assert json.loads((tmp_path / "pkg_cache" / "manifest.json").read_text())["commit"] == COMMIT_B


@pytest.mark.parametrize("dano", ["alterado", "faltando", "extra"])
def test_cache_adulterado_e_ressincronizado(tmp_path, dano):
    ns = loader(tmp_path, ARQUIVOS_A, COMMIT_A)
    ns["_sync_core_package"](None)
    alvo = tmp_path / "pkg_cache" / "core" / "engine" / "wall_stepper.py"
    if dano == "alterado":
        alvo.write_text("# mexido\n")
    elif dano == "faltando":
        alvo.unlink()
    else:
        (tmp_path / "pkg_cache" / "core" / "engine" / "sobra.py").write_text("# modulo velho\n")
    manifest = json.loads((tmp_path / "pkg_cache" / "manifest.json").read_text())
    assert ns["_verify_cache"](manifest) is False
    del ns["chamadas"][:]
    entry, prov = ns["_sync_core_package"](None)
    assert prov["CACHE_STATUS"] == "MISS"
    assert any(c[0] == "raw" for c in ns["chamadas"] if isinstance(c, tuple))
    assert ns["_verify_cache"](json.loads((tmp_path / "pkg_cache" / "manifest.json").read_text())) is True


def test_sem_rede_usa_cache_verificado_e_diz_qual_commit_e(tmp_path):
    ns = loader(tmp_path, ARQUIVOS_A, COMMIT_A)
    ns["_sync_core_package"](None)
    ns2 = loader(tmp_path, ARQUIVOS_A, COMMIT_A, rede_ok=False)
    entry = ns2["_load_entry_point"]()
    prov = ns2["RUNTIME_PROVENANCE"] if "RUNTIME_PROVENANCE" in ns2 else None
    # o namespace do teste nao e' o modulo: a proveniencia sai pelo banner impresso
    banner = [c[1][0] for c in ns2["chamadas"] if isinstance(c, tuple) and c[0] == "print"][-1]
    assert "cache=OFFLINE_FALLBACK" in banner and "commit=" + COMMIT_A in banner
    assert Path(entry) == tmp_path / "pkg_cache" / "core" / "wall_modeling.py"
    titulo, mensagem = ns2["forms"].alerts[-1]
    assert COMMIT_A[:12] in titulo and "VERIFICADA" in mensagem and "pode estar desatualizada" in mensagem


def test_sem_rede_e_sem_manifest_nao_roda_cache_legado(tmp_path):
    cache = tmp_path / "pkg_cache" / "core"
    cache.mkdir(parents=True)
    (cache / "wall_modeling.py").write_text("# cache antigo, sem prova de versao\n")
    ns = loader(tmp_path, ARQUIVOS_A, COMMIT_A, rede_ok=False)
    with pytest.raises(SystemExit):
        ns["_load_entry_point"]()
    titulo, mensagem = ns["forms"].alerts[-1]
    assert "VERIFICAVEL" in mensagem


def test_banner_online_e_beta_tem_as_mesmas_linhas_obrigatorias(tmp_path):
    ns = loader(tmp_path, ARQUIVOS_A, COMMIT_A)
    online = ns["_provenance"]("ONLINE", "main", COMMIT_A, "f" * 64, "VALIDATED", "C:/x/core/wall_modeling.py")
    beta = ns["_provenance"]("BETA_OFFLINE", "main", COMMIT_A, "f" * 64, "VERIFIED_OFFLINE", "C:/y/core/wall_modeling.py")
    b_on, b_beta = ns["_provenance_banner"](online), ns["_provenance_banner"](beta)
    assert b_on.splitlines()[:5] == [u"MODULA\u00c7\u00c3O AUTOM\u00c1TICA", "canal=ONLINE", "branch=main",
                                     "commit=" + COMMIT_A, "cache=VALIDATED"]
    assert b_beta.splitlines()[:4] == [u"MODULA\u00c7\u00c3O AUTOM\u00c1TICA", "canal=BETA_OFFLINE",
                                       "commit=" + COMMIT_A, "package_verified=true"]
    for campo in ns["PROVENANCE_FIELDS"]:
        assert any(l.startswith(campo + "=") for l in b_on.splitlines())
        assert any(l.startswith(campo + "=") for l in b_beta.splitlines())


def test_package_sha_e_o_mesmo_nos_dois_canais_para_o_mesmo_commit(tmp_path):
    """O digest so' cobre core/: o manifest do pacote beta (que tambem lista
    Script.py e beta_package.py) da' o MESMO PACKAGE_SHA do cache online."""
    ns = loader(tmp_path, ARQUIVOS_A, COMMIT_A)
    core = {"core/wall_modeling.py": "1" * 64, "core/engine/wall_stepper.py": "2" * 64}
    beta = dict(core, **{"Script.py": "3" * 64, "beta_package.py": "4" * 64})
    assert ns["_package_digest"](core) == ns["_package_digest"](beta)


def test_beta_offline_registra_proveniencia_verificada(tmp_path):
    conteudos = {"Script.py": b"# loader\n", "beta_package.py": (ROOT / "beta_package.py").read_bytes(),
                 "core/wall_modeling.py": b"# motor\n", "core/__init__.py": b""}
    for rel, dados in conteudos.items():
        alvo = tmp_path / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_bytes(dados)
    manifest = {"schema": 1, "controlled_beta": True, "head": COMMIT_A, "branch": "main",
                "sha256": {p: hashlib.sha256(v).hexdigest() for p, v in conteudos.items()}}
    (tmp_path / "beta-package.json").write_text(json.dumps(manifest))
    ns = loader(tmp_path, ARQUIVOS_A, COMMIT_B)
    entry = ns["_load_entry_point"]()
    assert Path(entry) == tmp_path / "core" / "wall_modeling.py"
    assert ns["CONTROLLED_BETA"] is True and ns["CONTROLLED_BETA_HEAD"] == COMMIT_A
    prov = ns["RUNTIME_PROVENANCE"]
    assert prov["CHANNEL"] == "BETA_OFFLINE" and prov["RESOLVED_COMMIT"] == COMMIT_A
    assert prov["CACHE_STATUS"] == "VERIFIED_OFFLINE" and prov["SOURCE_BRANCH"] == "main"
    assert prov["PACKAGE_SHA"] == ns["_package_digest"](manifest["sha256"])
    assert "commit" not in ns["chamadas"]      # o beta NUNCA toca a rede
