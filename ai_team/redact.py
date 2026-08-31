"""Redacao de segredos.

Regra do projeto (secao 13 do pedido): nenhuma chave pode aparecer em log,
em arquivo de estado ou no resumo do GitHub. Tudo que sai do orquestrador
passa por `redact()`.

Duas camadas:

1. valores EXATOS lidos do ambiente (a defesa que realmente importa - se a
   chave existe em `ANTHROPIC_API_KEY`, qualquer eco dela some);
2. padroes conhecidos, para o caso de um segredo que o orquestrador nunca
   viu no ambiente aparecer numa saida de agente.
"""

from __future__ import annotations

import os
import re
from typing import Any, Iterable

PLACEHOLDER = "***REDACTED***"

#: Variaveis de ambiente cujo VALOR nunca pode vazar.
SECRET_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "AI_TEAM_GITHUB_TOKEN",
)

#: Padroes de segredo reconhecidos mesmo sem estarem no ambiente.
SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"sk-proj-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{16,}"),
    re.compile(r"gho_[A-Za-z0-9]{16,}"),
    re.compile(r"ghs_[A-Za-z0-9]{16,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    # `https://x-access-token:<token>@github.com/...` usado pelo runner
    re.compile(r"(?<=x-access-token:)[^@\s]+"),
)

#: Comprimento minimo para tratar um valor de ambiente como segredo. Evita
#: que uma variavel vazia ou com "1" transforme todo texto em [REDACTED].
_MIN_SECRET_LEN = 8


def _env_secrets(environ: dict[str, str] | None = None) -> list[str]:
    env = os.environ if environ is None else environ
    found = []
    for name in SECRET_ENV_VARS:
        value = env.get(name, "")
        if value and len(value) >= _MIN_SECRET_LEN:
            found.append(value)
    # Os mais longos primeiro: se um segredo contem outro, o maior some antes
    # e nao sobra um fragmento reconhecivel.
    return sorted(set(found), key=len, reverse=True)


def redact(text: Any, extra_secrets: Iterable[str] = (), environ: dict[str, str] | None = None) -> Any:
    """Devolve `text` sem segredos. Nao-strings voltam inalterados."""
    if not isinstance(text, str) or not text:
        return text

    out = text
    for secret in _env_secrets(environ):
        out = out.replace(secret, PLACEHOLDER)
    for secret in extra_secrets:
        if secret and len(secret) >= _MIN_SECRET_LEN:
            out = out.replace(secret, PLACEHOLDER)
    for pattern in SECRET_PATTERNS:
        out = pattern.sub(PLACEHOLDER, out)
    return out


def redact_obj(obj: Any, extra_secrets: Iterable[str] = (), environ: dict[str, str] | None = None) -> Any:
    """`redact()` recursivo em dict / list / tuple / str."""
    if isinstance(obj, str):
        return redact(obj, extra_secrets, environ)
    if isinstance(obj, dict):
        return {k: redact_obj(v, extra_secrets, environ) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [redact_obj(v, extra_secrets, environ) for v in obj]
    return obj


def contains_secret(text: str, environ: dict[str, str] | None = None) -> bool:
    """True se `text` ainda carrega algum segredo. Usado pelos testes."""
    if not isinstance(text, str):
        return False
    for secret in _env_secrets(environ):
        if secret in text:
            return True
    return any(p.search(text) for p in SECRET_PATTERNS)
