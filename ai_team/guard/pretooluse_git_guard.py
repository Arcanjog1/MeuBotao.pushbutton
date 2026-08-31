#!/usr/bin/env python3
"""Hook `PreToolUse` do Claude Code: BLOQUEIA operacoes perigosas.

Isto e' o cumprimento real da secao 13 do pedido. Nao e' uma instrucao no
prompt (que um modelo pode ignorar) - e' uma decisao tomada na fronteira
da ferramenta, antes do comando existir.

Protocolo: o CLI manda o evento em JSON no stdin e le a decisao no stdout:

    {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": "..."}}

`deny` faz o comando nao rodar; a razao volta para o modelo, que entao
sabe por que aquilo foi recusado.

A funcao `evaluate_command()` e' pura, para ser testada sem subprocesso.
"""

from __future__ import annotations

import json
import re
import sys

#: (regex, motivo). Casado contra o comando NORMALIZADO.
FORBIDDEN: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bgit\s+reset\s+(--hard|--merge|--keep)\b"),
     "git reset destrutivo e' proibido: descarta trabalho sem recuperacao"),
    (re.compile(r"\bgit\s+clean\b.*(-[a-z]*f|--force)"),
     "git clean -f e' proibido: apaga arquivos nao versionados do usuario"),
    (re.compile(r"\bgit\s+push\b.*(--force\b|--force-with-lease\b|(?<![\w-])-f(?![\w-]))"),
     "force push e' proibido"),
    (re.compile(r"\bgit\s+push\b"),
     "o push e' feito pelo orquestrador, nao pelo agente"),
    (re.compile(r"\bgit\s+branch\s+(-D|-d|--delete)\s+(main|master)\b"),
     "apagar a branch main/master e' proibido"),
    (re.compile(r"\bgit\s+push\b.*(:main\b|:master\b|--delete\s+(main|master))"),
     "apagar a branch remota main/master e' proibido"),
    (re.compile(r"\bgit\s+(checkout|switch)\s+(main|master)\b"),
     "o agente trabalha somente na branch da tarefa; nao va' para a main"),
    (re.compile(r"\bgit\s+merge\b"),
     "merge automatico e' proibido na V1: o teto e' READY_FOR_HUMAN_REVIEW"),
    (re.compile(r"\bgit\s+rebase\b"),
     "rebase e' proibido: reescreve historico da branch"),
    (re.compile(r"\bgit\s+filter-(branch|repo)\b"),
     "reescrita de historico e' proibida"),
    (re.compile(r"\bgh\s+pr\s+merge\b"),
     "merge de PR e' decisao humana"),
    (re.compile(r"\bgh\s+(secret|variable)\s+(set|delete|remove)\b"),
     "alterar secrets/variaveis do repositorio e' proibido"),
    (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\s+/(\s|$)"),
     "rm -rf / e' proibido"),
    (re.compile(r"\bgit\s+config\b.*\b(user\.signingkey|credential\.helper)\b"),
     "alterar credenciais do git e' proibido"),
)

#: Nomes de segredo que nao podem ser lidos/ecoados/exfiltrados.
SECRET_NAMES = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GITHUB_TOKEN",
                "GH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")

#: Ler o valor de um segredo. Cobre tanto `$VAR` / `${VAR}` quanto o nome
#: cru, que e' como `printenv OPENAI_API_KEY` e `env | grep TOKEN` acessam.
SECRET_READ = re.compile(
    r"\b(echo|printenv|env|printf|curl|wget|nc|ncat|xxd|base64|set|export|"
    r"cat|grep|sed|awk|tee|python3?|node|jq)\b[^\n]*?\$?\{?\b(" +
    "|".join(SECRET_NAMES) + r")\b"
)
#: Gravar segredo em arquivo dentro do repositorio.
SECRET_WRITE = re.compile(r"\$\{?(" + "|".join(SECRET_NAMES) + r")\}?[^\n]*>\s*\S")


def _normalize(command: str) -> str:
    """Reduz variacoes triviais que escondem o comando real."""
    text = command.replace("\\\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def evaluate_command(command: str) -> tuple[bool, str]:
    """(allowed, reason). Funcao pura - o teste chama isto diretamente."""
    if not command or not command.strip():
        return True, ""
    normalized = _normalize(command)

    for pattern, reason in FORBIDDEN:
        if pattern.search(normalized):
            return False, f"AI Team guard: {reason}"

    if SECRET_READ.search(normalized):
        return False, "AI Team guard: ler ou transmitir o valor de um segredo e' proibido"
    if SECRET_WRITE.search(normalized):
        return False, "AI Team guard: gravar um segredo em arquivo e' proibido"

    return True, ""


def evaluate_event(event: dict) -> dict:
    """Traduz o evento do hook na resposta do protocolo `PreToolUse`."""
    tool = event.get("tool_name") or event.get("toolName") or ""
    tool_input = event.get("tool_input") or event.get("toolInput") or {}

    command = ""
    if tool in ("Bash", "BashOutput"):
        command = str(tool_input.get("command") or "")
    elif tool in ("Write", "Edit", "NotebookEdit"):
        # Proteger os proprios arquivos de politica/guarda contra auto-edicao.
        path = str(tool_input.get("file_path") or "")
        if re.search(r"(^|/)(\.github/workflows/|ai_team/guard/|ai_team/config\.yaml$)", path):
            return _deny(f"AI Team guard: o agente nao altera a propria politica/guarda ({path})")
        return _allow()
    else:
        return _allow()

    allowed, reason = evaluate_command(command)
    return _allow() if allowed else _deny(reason)


def _allow() -> dict:
    # Sem decisao explicita: o fluxo normal de permissao do CLI segue.
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse"}}


def _deny(reason: str) -> dict:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Falha fechada: nao conseguir ler o evento nao pode virar permissao.
        json.dump(_deny("AI Team guard: evento de hook ilegivel"), sys.stdout)
        return 0
    json.dump(evaluate_event(event if isinstance(event, dict) else {}), sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
