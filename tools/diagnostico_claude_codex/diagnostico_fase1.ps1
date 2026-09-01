<#
.SYNOPSIS
    Diagnostico READ-ONLY (Fase 1) do ambiente Claude Code + Codex CLI no Windows.

.DESCRIPTION
    Este script NAO altera nada no computador:
      - nao faz logout/login
      - nao apaga configuracao
      - nao edita PATH nem variaveis de ambiente permanentes (Machine/User)
      - nao instala nada
      - nao mexe no registry
      - nao mexe em arquivos do "AI Team"
      - nao cria commit nem branch
      - nao imprime segredos/tokens (so' detecta PRESENCA das env vars)

    Ele apenas LE informacoes do sistema e das CLIs (claude / codex / wsl) e
    grava um relatorio de texto sanitizado.

    Chamadas de rede (claude -p / codex minimal call) sao OPCIONAIS e
    DESLIGADAS por padrao, porque podem consumir cota/creditos. So' rodam
    se voce passar -RunLiveCalls.

.PARAMETER RunLiveCalls
    Se presente, tenta 1 chamada minima nao interativa em cada perfil do
    Claude (`claude -p "diagnostico" --max-tokens 8` ou equivalente) e 1
    chamada minima do Codex, so' para confirmar que a autenticacao funciona
    de ponta a ponta. Sem essa flag, esses passos ficam marcados como
    "SKIPPED (use -RunLiveCalls)".

.PARAMETER OutFile
    Caminho do relatorio de saida. Padrao: mesma pasta do script, com
    timestamp no nome.

.EXAMPLE
    # Modo totalmente passivo (recomendado na primeira rodada)
    powershell -ExecutionPolicy Bypass -File .\diagnostico_fase1.ps1

.EXAMPLE
    # Modo passivo + testes minimos de chamada (pode gastar cota)
    powershell -ExecutionPolicy Bypass -File .\diagnostico_fase1.ps1 -RunLiveCalls
#>

[CmdletBinding()]
param(
    [switch]$RunLiveCalls,
    [string]$OutFile
)

$ErrorActionPreference = 'Continue'
$ProgressPreference    = 'SilentlyContinue'

if (-not $OutFile) {
    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    $OutFile = Join-Path $PSScriptRoot "diagnostico_fase1_$ts.txt"
}

$Report = New-Object System.Collections.Generic.List[string]

function Add-Line {
    param([string]$Text = '')
    $Report.Add($Text)
    Write-Host $Text
}

function Add-Section {
    param([string]$Title)
    Add-Line ''
    Add-Line ('=' * 70)
    Add-Line $Title
    Add-Line ('=' * 70)
}

function Redact {
    <# Corta qualquer coisa que pareca token/segredo antes de logar #>
    param([string]$Text)
    if (-not $Text) { return $Text }
    $t = $Text
    # padroes comuns de token/secret/api key
    $t = [regex]::Replace($t, '(sk-[A-Za-z0-9\-_]{10,})', '[REDACTED_TOKEN]')
    $t = [regex]::Replace($t, '(?i)(api[_-]?key["\s:=]+)([A-Za-z0-9\-_\.]{8,})', '$1[REDACTED]')
    $t = [regex]::Replace($t, '(?i)(bearer\s+)([A-Za-z0-9\-_\.]{8,})', '$1[REDACTED]')
    $t = [regex]::Replace($t, '(?i)(token["\s:=]+)([A-Za-z0-9\-_\.]{8,})', '$1[REDACTED]')
    return $t
}

function Get-CommandPathAll {
    param([string]$Name)
    try {
        Get-Command $Name -All -ErrorAction Stop | ForEach-Object { $_.Source }
    } catch {
        @()
    }
}

function Invoke-Safe {
    <# Executa um comando externo e devolve stdout+stderr combinados,
       sem lancar excecao para cima. Usado so' para leitura (--version,
       status, etc.) #>
    param(
        [string]$FilePath,
        [string[]]$ArgList,
        [hashtable]$ExtraEnv,
        [int]$TimeoutSec = 20
    )
    $result = [ordered]@{
        Ran      = $false
        ExitCode = $null
        StdOut   = ''
        StdErr   = ''
        Error    = $null
    }
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $FilePath
        foreach ($a in $ArgList) { [void]$psi.ArgumentList.Add($a) }
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow  = $true

        if ($ExtraEnv) {
            foreach ($k in $ExtraEnv.Keys) {
                $psi.Environment[$k] = $ExtraEnv[$k]
            }
        }

        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $psi
        [void]$p.Start()
        $stdOutTask = $p.StandardOutput.ReadToEndAsync()
        $stdErrTask = $p.StandardError.ReadToEndAsync()
        $exited = $p.WaitForExit($TimeoutSec * 1000)
        if (-not $exited) {
            try { $p.Kill() } catch {}
            $result.Error = "TIMEOUT apos $TimeoutSec s"
        } else {
            $result.ExitCode = $p.ExitCode
        }
        $result.StdOut = $stdOutTask.Result
        $result.StdErr = $stdErrTask.Result
        $result.Ran = $true
    } catch {
        $result.Error = $_.Exception.Message
    }
    return $result
}

function EnvVarPresent {
    param([string]$Name, [string]$Scope = 'Process')
    $val = [Environment]::GetEnvironmentVariable($Name, $Scope)
    return -not [string]::IsNullOrEmpty($val)
}

# ---------------------------------------------------------------------
Add-Line "DIAGNOSTICO FASE 1 - Claude Code (dual) + Codex CLI - READ-ONLY"
Add-Line "Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
Add-Line "Usuario Windows atual: $env:USERNAME"
Add-Line "Este relatorio e' sanitizado: nenhum token/segredo e' impresso."
Add-Line "RunLiveCalls = $($RunLiveCalls.IsPresent)"

# ======================================================================
# 1. Windows version / architecture
# ======================================================================
Add-Section "1. WINDOWS - VERSAO E ARQUITETURA"
try {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
    $cs = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
    Add-Line "Caption: $($os.Caption)"
    Add-Line "Version (build): $($os.Version)"
    Add-Line "OSArchitecture: $($os.OSArchitecture)"
    Add-Line "SystemType (hw): $($cs.SystemType)"
    Add-Line "PowerShell version: $($PSVersionTable.PSVersion)"
    Add-Line "PowerShell edition: $($PSVersionTable.PSEdition)"
    Add-Line "CLR/.NET: $($PSVersionTable.CLRVersion)"
    Add-Line "Processor architecture (env): $env:PROCESSOR_ARCHITECTURE"
} catch {
    Add-Line "ERRO ao coletar info do Windows: $($_.Exception.Message)"
}

# ======================================================================
# 2/3. claude --version e caminho real do executavel
# ======================================================================
Add-Section "2/3. CLAUDE CLI - VERSAO E CAMINHOS"
$claudePaths = Get-CommandPathAll -Name 'claude'
if ($claudePaths.Count -eq 0) {
    Add-Line "Nenhum 'claude' encontrado no PATH."
} else {
    Add-Line "Ocorrencias de 'claude' no PATH (na ordem de resolucao):"
    $claudePaths | ForEach-Object { Add-Line "  - $_" }
}

$claudeVersionResult = $null
if ($claudePaths.Count -gt 0) {
    $claudeVersionResult = Invoke-Safe -FilePath $claudePaths[0] -ArgList @('--version')
    if ($claudeVersionResult.Ran) {
        Add-Line "claude --version (via $($claudePaths[0])):"
        Add-Line "  StdOut: $(Redact ($claudeVersionResult.StdOut.Trim()))"
        if ($claudeVersionResult.StdErr) { Add-Line "  StdErr: $(Redact ($claudeVersionResult.StdErr.Trim()))" }
        Add-Line "  ExitCode: $($claudeVersionResult.ExitCode)"
    } else {
        Add-Line "Falha ao executar claude --version: $($claudeVersionResult.Error)"
    }
} else {
    Add-Line "claude --version: SKIPPED (executavel nao encontrado)"
}

# ======================================================================
# 4. claude auth status (sem mostrar token)
# ======================================================================
Add-Section "4. CLAUDE AUTH STATUS"
$claudeAuthResult = $null
if ($claudePaths.Count -gt 0) {
    # tenta subcomandos comuns; se um nao existir, o proximo e' tentado
    $authCandidates = @(
        @('auth','status'),
        @('/status'),
        @('config','status')
    )
    $done = $false
    foreach ($cand in $authCandidates) {
        $r = Invoke-Safe -FilePath $claudePaths[0] -ArgList $cand -TimeoutSec 15
        if ($r.Ran -and ($r.ExitCode -eq 0 -or $r.StdOut -or $r.StdErr)) {
            Add-Line "Comando testado: claude $($cand -join ' ')"
            Add-Line "  StdOut: $(Redact ($r.StdOut.Trim()))"
            if ($r.StdErr) { Add-Line "  StdErr: $(Redact ($r.StdErr.Trim()))" }
            Add-Line "  ExitCode: $($r.ExitCode)"
            $claudeAuthResult = $r
            $done = $true
            break
        }
    }
    if (-not $done) {
        Add-Line "Nao foi possivel obter auth status por nenhum subcomando testado (auth status / config status)."
    }
} else {
    Add-Line "SKIPPED (claude nao encontrado)"
}

# ======================================================================
# 5. CLAUDE_CONFIG_DIR atual
# ======================================================================
Add-Section "5. CLAUDE_CONFIG_DIR ATUAL"
$currentConfigDir = [Environment]::GetEnvironmentVariable('CLAUDE_CONFIG_DIR', 'Process')
$userConfigDir    = [Environment]::GetEnvironmentVariable('CLAUDE_CONFIG_DIR', 'User')
$machineConfigDir = [Environment]::GetEnvironmentVariable('CLAUDE_CONFIG_DIR', 'Machine')
Add-Line "CLAUDE_CONFIG_DIR (processo atual): $(if ($currentConfigDir) { $currentConfigDir } else { '<nao definida>' })"
Add-Line "CLAUDE_CONFIG_DIR (escopo User):    $(if ($userConfigDir)    { $userConfigDir }    else { '<nao definida>' })"
Add-Line "CLAUDE_CONFIG_DIR (escopo Machine):  $(if ($machineConfigDir) { $machineConfigDir } else { '<nao definida>' })"

# ======================================================================
# 6. Identificar os dois mecanismos/perfis Claude ja existentes
# ======================================================================
Add-Section "6. PERFIS/MECANISMOS CLAUDE DETECTADOS"
$candidateConfigDirs = New-Object System.Collections.Generic.List[object]

function Add-Candidate {
    param([string]$Label, [string]$Path)
    if ($Path -and (Test-Path $Path)) {
        $candidateConfigDirs.Add([pscustomobject]@{ Label = $Label; Path = $Path })
    }
}

Add-Candidate -Label 'CLAUDE_CONFIG_DIR (env atual)' -Path $currentConfigDir
Add-Candidate -Label 'CLAUDE_CONFIG_DIR (User)'       -Path $userConfigDir
Add-Candidate -Label 'Padrao ~/.claude'               -Path (Join-Path $env:USERPROFILE '.claude')
Add-Candidate -Label 'APPDATA\claude'                 -Path (Join-Path $env:APPDATA 'claude')
Add-Candidate -Label 'LOCALAPPDATA\claude'             -Path (Join-Path $env:LOCALAPPDATA 'claude')
Add-Candidate -Label 'LOCALAPPDATA\claude-code'        -Path (Join-Path $env:LOCALAPPDATA 'claude-code')
Add-Candidate -Label 'LOCALAPPDATA\AnthropicClaude'    -Path (Join-Path $env:LOCALAPPDATA 'AnthropicClaude')

if ($candidateConfigDirs.Count -eq 0) {
    Add-Line "Nenhuma pasta de config conhecida foi encontrada nos locais padrao."
    Add-Line "-> Verifique manualmente onde ficam os 2 perfis (pode ser um caminho customizado)."
} else {
    Add-Line "Pastas de configuracao candidatas encontradas:"
    $seen = @{}
    foreach ($c in $candidateConfigDirs) {
        $full = (Resolve-Path $c.Path -ErrorAction SilentlyContinue).Path
        if (-not $full) { $full = $c.Path }
        if ($seen.ContainsKey($full)) { continue }
        $seen[$full] = $true
        Add-Line "  - [$($c.Label)] $full"
    }
}

if ($claudePaths.Count -ge 2) {
    Add-Line ""
    Add-Line "Multiplos executaveis 'claude' distintos no PATH (possiveis 2 instalacoes/mecanismos):"
    $claudePaths | ForEach-Object { Add-Line "  - $_" }
} elseif ($claudePaths.Count -eq 1) {
    Add-Line ""
    Add-Line "Apenas 1 executavel 'claude' no PATH. Se os '2 perfis' sao 2 CLAUDE_CONFIG_DIR"
    Add-Line "diferentes usando o MESMO binario, isso e' esperado (ver pastas candidatas acima)."
}

$distinctDirs = @()
if ($candidateConfigDirs.Count -gt 0) {
    $distinctDirs = $candidateConfigDirs | ForEach-Object {
        (Resolve-Path $_.Path -ErrorAction SilentlyContinue).Path
    } | Where-Object { $_ } | Select-Object -Unique
}

$profileA_Dir = $null
$profileB_Dir = $null
if ($distinctDirs.Count -ge 1) { $profileA_Dir = $distinctDirs[0] }
if ($distinctDirs.Count -ge 2) { $profileB_Dir = $distinctDirs[1] }

Add-Line ""
Add-Line "Perfil A (config dir escolhido para teste): $(if ($profileA_Dir) { $profileA_Dir } else { '<nao identificado>' })"
Add-Line "Perfil B (config dir escolhido para teste): $(if ($profileB_Dir) { $profileB_Dir } else { '<nao identificado>' })"
Add-Line "OBS: se a identificacao acima nao bater com a realidade (ex: os 2 mecanismos sao"
Add-Line "'assinatura OAuth' vs 'API key', nao 2 pastas), me diga os 2 caminhos/nomes exatos"
Add-Line "para eu ajustar a deteccao na Fase 2."

# ======================================================================
# 7/8. Confirmar que os dois perfis respondem separadamente + chamada minima
# ======================================================================
Add-Section "7/8. TESTE SEPARADO DOS PERFIS (claude -p minimo)"

function Test-ClaudeProfile {
    param([string]$Label, [string]$ConfigDir)

    Add-Line "--- Perfil: $Label ---"
    if (-not $ConfigDir) {
        Add-Line "  SKIPPED (config dir nao identificado)"
        return [pscustomobject]@{ Label = $Label; StatusOk = $false; AuthMode = 'UNKNOWN' }
    }
    Add-Line "  CLAUDE_CONFIG_DIR de teste: $ConfigDir"

    if ($claudePaths.Count -eq 0) {
        Add-Line "  SKIPPED (claude nao encontrado no PATH)"
        return [pscustomobject]@{ Label = $Label; StatusOk = $false; AuthMode = 'UNKNOWN' }
    }

    $envOverride = @{ 'CLAUDE_CONFIG_DIR' = $ConfigDir }

    $statusOk = $false
    $authMode = 'UNKNOWN'
    $r = Invoke-Safe -FilePath $claudePaths[0] -ArgList @('auth','status') -ExtraEnv $envOverride -TimeoutSec 15
    if ($r.Ran) {
        Add-Line "  claude auth status (com CLAUDE_CONFIG_DIR=$ConfigDir):"
        Add-Line "    StdOut: $(Redact ($r.StdOut.Trim()))"
        if ($r.StdErr) { Add-Line "    StdErr: $(Redact ($r.StdErr.Trim()))" }
        Add-Line "    ExitCode: $($r.ExitCode)"
        $combined = "$($r.StdOut) $($r.StdErr)"
        if ($r.ExitCode -eq 0 -or $combined -match '(?i)logged in|authenticated|active') {
            $statusOk = $true
        }
        if ($combined -match '(?i)oauth|subscription|pro|max plan|claude\.ai') {
            $authMode = 'SUBSCRIPTION/OAuth'
        } elseif ($combined -match '(?i)api key|anthropic_api_key') {
            $authMode = 'API_KEY'
        }
    } else {
        Add-Line "  Falha ao rodar 'claude auth status' para este perfil: $($r.Error)"
    }

    if ($RunLiveCalls) {
        $lr = Invoke-Safe -FilePath $claudePaths[0] `
            -ArgList @('-p', 'responda apenas: ok', '--max-turns', '1') `
            -ExtraEnv $envOverride -TimeoutSec 40
        if ($lr.Ran) {
            Add-Line "  Chamada minima 'claude -p' (live):"
            Add-Line "    StdOut: $(Redact ($lr.StdOut.Trim()))"
            if ($lr.StdErr) { Add-Line "    StdErr: $(Redact ($lr.StdErr.Trim()))" }
            Add-Line "    ExitCode: $($lr.ExitCode)"
            if ($lr.ExitCode -eq 0 -and $lr.StdOut) { $statusOk = $true }
        } else {
            Add-Line "  Falha na chamada minima live: $($lr.Error)"
        }
    } else {
        Add-Line "  Chamada minima 'claude -p': SKIPPED (use -RunLiveCalls para testar)"
    }

    return [pscustomobject]@{ Label = $Label; StatusOk = $statusOk; AuthMode = $authMode }
}

$profileAResult = Test-ClaudeProfile -Label 'CLAUDE_A' -ConfigDir $profileA_Dir
$profileBResult = Test-ClaudeProfile -Label 'CLAUDE_B' -ConfigDir $profileB_Dir

# ======================================================================
# 9/10. codex --version e caminho real
# ======================================================================
Add-Section "9/10. CODEX CLI - VERSAO E CAMINHOS"
$codexPaths = Get-CommandPathAll -Name 'codex'
if ($codexPaths.Count -eq 0) {
    Add-Line "Nenhum 'codex' encontrado no PATH."
} else {
    Add-Line "Ocorrencias de 'codex' no PATH:"
    $codexPaths | ForEach-Object { Add-Line "  - $_" }
}

$codexVersionResult = $null
$codexHwError = $false
if ($codexPaths.Count -gt 0) {
    $codexVersionResult = Invoke-Safe -FilePath $codexPaths[0] -ArgList @('--version') -TimeoutSec 20
    if ($codexVersionResult.Ran) {
        Add-Line "codex --version (via $($codexPaths[0])):"
        Add-Line "  StdOut: $(Redact ($codexVersionResult.StdOut.Trim()))"
        if ($codexVersionResult.StdErr) { Add-Line "  StdErr: $(Redact ($codexVersionResult.StdErr.Trim()))" }
        Add-Line "  ExitCode: $($codexVersionResult.ExitCode)"
        $combinedCodex = "$($codexVersionResult.StdOut) $($codexVersionResult.StdErr)"
        if ($combinedCodex -match 'HW capability found.*but HW capability requested') {
            $codexHwError = $true
        }
    } else {
        Add-Line "Falha ao executar codex --version: $($codexVersionResult.Error)"
    }
} else {
    Add-Line "codex --version: SKIPPED (executavel nao encontrado)"
}

# ======================================================================
# 11. codex login status
# ======================================================================
Add-Section "11. CODEX LOGIN STATUS"
$codexAuthMode = 'UNKNOWN'
$codexLoginOk = $false
if ($codexPaths.Count -gt 0) {
    $loginCandidates = @(
        @('login','status'),
        @('auth','status'),
        @('status')
    )
    $done = $false
    foreach ($cand in $loginCandidates) {
        $r = Invoke-Safe -FilePath $codexPaths[0] -ArgList $cand -TimeoutSec 15
        if ($r.Ran -and ($r.ExitCode -eq 0 -or $r.StdOut -or $r.StdErr)) {
            Add-Line "Comando testado: codex $($cand -join ' ')"
            Add-Line "  StdOut: $(Redact ($r.StdOut.Trim()))"
            if ($r.StdErr) { Add-Line "  StdErr: $(Redact ($r.StdErr.Trim()))" }
            Add-Line "  ExitCode: $($r.ExitCode)"
            $combined = "$($r.StdOut) $($r.StdErr)"
            if ($combined -match 'HW capability found.*but HW capability requested') { $codexHwError = $true }
            if ($r.ExitCode -eq 0 -or $combined -match '(?i)logged in|authenticated') { $codexLoginOk = $true }
            if ($combined -match '(?i)chatgpt') { $codexAuthMode = 'CHATGPT_LOGIN' }
            elseif ($combined -match '(?i)api key|openai_api_key') { $codexAuthMode = 'API_KEY' }
            $done = $true
            break
        }
    }
    if (-not $done) {
        Add-Line "Nao foi possivel obter login status por nenhum subcomando testado."
    }
} else {
    Add-Line "SKIPPED (codex nao encontrado)"
}

# ======================================================================
# 12. Chamada minima nao interativa do Codex (opcional)
# ======================================================================
Add-Section "12. CHAMADA MINIMA CODEX (opcional)"
if ($codexPaths.Count -eq 0) {
    Add-Line "SKIPPED (codex nao encontrado)"
} elseif (-not $RunLiveCalls) {
    Add-Line "SKIPPED (use -RunLiveCalls para testar)"
} else {
    $execCandidates = @(
        @('exec', '--full-auto', 'responda apenas: ok'),
        @('exec', 'responda apenas: ok')
    )
    $done = $false
    foreach ($cand in $execCandidates) {
        $r = Invoke-Safe -FilePath $codexPaths[0] -ArgList $cand -TimeoutSec 40
        if ($r.Ran) {
            Add-Line "Comando testado: codex $($cand -join ' ')"
            Add-Line "  StdOut: $(Redact ($r.StdOut.Trim()))"
            if ($r.StdErr) { Add-Line "  StdErr: $(Redact ($r.StdErr.Trim()))" }
            Add-Line "  ExitCode: $($r.ExitCode)"
            $combined = "$($r.StdOut) $($r.StdErr)"
            if ($combined -match 'HW capability found.*but HW capability requested') { $codexHwError = $true }
            $done = $true
            break
        }
    }
    if (-not $done) {
        Add-Line "Nao foi possivel executar uma chamada minima do codex (todas as tentativas falharam)."
    }
}

# ======================================================================
# 13. Presenca de ANTHROPIC_API_KEY / OPENAI_API_KEY (nunca valores)
# ======================================================================
Add-Section "13. PRESENCA DE API KEYS (somente presenca, nunca valor)"
$anthropicKeyPresentProcess = EnvVarPresent -Name 'ANTHROPIC_API_KEY' -Scope 'Process'
$anthropicKeyPresentUser    = EnvVarPresent -Name 'ANTHROPIC_API_KEY' -Scope 'User'
$anthropicKeyPresentMachine = EnvVarPresent -Name 'ANTHROPIC_API_KEY' -Scope 'Machine'
$openaiKeyPresentProcess    = EnvVarPresent -Name 'OPENAI_API_KEY' -Scope 'Process'
$openaiKeyPresentUser       = EnvVarPresent -Name 'OPENAI_API_KEY' -Scope 'User'
$openaiKeyPresentMachine    = EnvVarPresent -Name 'OPENAI_API_KEY' -Scope 'Machine'

Add-Line "ANTHROPIC_API_KEY presente (processo): $anthropicKeyPresentProcess"
Add-Line "ANTHROPIC_API_KEY presente (User):     $anthropicKeyPresentUser"
Add-Line "ANTHROPIC_API_KEY presente (Machine):  $anthropicKeyPresentMachine"
Add-Line "OPENAI_API_KEY presente (processo):    $openaiKeyPresentProcess"
Add-Line "OPENAI_API_KEY presente (User):        $openaiKeyPresentUser"
Add-Line "OPENAI_API_KEY presente (Machine):     $openaiKeyPresentMachine"

$anthropicKeyPresentAny = $anthropicKeyPresentProcess -or $anthropicKeyPresentUser -or $anthropicKeyPresentMachine
$openaiKeyPresentAny    = $openaiKeyPresentProcess -or $openaiKeyPresentUser -or $openaiKeyPresentMachine

# ======================================================================
# 14/15. Modo de autenticacao (subscription/OAuth vs API)
# ======================================================================
Add-Section "14/15. MODO DE AUTENTICACAO (deducao)"
Add-Line "Claude Perfil A -> AuthMode deduzido: $($profileAResult.AuthMode)"
Add-Line "Claude Perfil B -> AuthMode deduzido: $($profileBResult.AuthMode)"
Add-Line "ANTHROPIC_API_KEY presente em algum escopo: $anthropicKeyPresentAny"
Add-Line ""
Add-Line "Codex -> AuthMode deduzido: $codexAuthMode"
Add-Line "OPENAI_API_KEY presente em algum escopo: $openaiKeyPresentAny"
Add-Line ""
Add-Line "OBS: a deducao acima e' heuristica (baseada no texto de 'auth status'/'login status'"
Add-Line "e na presenca de env vars). Nao e' garantia de qual mecanismo esta sendo FATURADO;"
Add-Line "para confirmar 100%, verifique o dashboard de billing correspondente manualmente."

# ======================================================================
# 16. Erro de hardware do Codex
# ======================================================================
Add-Section "16. CODEX HW CAPABILITY ERROR"
Add-Line "Erro 'HW capability found ... but HW capability requested ...' detectado: $codexHwError"

# ======================================================================
# 17. WSL disponivel?
# ======================================================================
Add-Section "17. WSL DISPONIVEL (como possivel runtime alternativo p/ Codex)"
$wslAvailable = $false
$wslPaths = Get-CommandPathAll -Name 'wsl'
if ($wslPaths.Count -gt 0) {
    $wr = Invoke-Safe -FilePath $wslPaths[0] -ArgList @('--status') -TimeoutSec 15
    if ($wr.Ran) {
        Add-Line "wsl --status:"
        Add-Line "  StdOut: $(Redact ($wr.StdOut.Trim()))"
        if ($wr.StdErr) { Add-Line "  StdErr: $(Redact ($wr.StdErr.Trim()))" }
        Add-Line "  ExitCode: $($wr.ExitCode)"
        if ($wr.ExitCode -eq 0) { $wslAvailable = $true }
    }
    $wl = Invoke-Safe -FilePath $wslPaths[0] -ArgList @('-l','-v') -TimeoutSec 15
    if ($wl.Ran) {
        Add-Line "wsl -l -v:"
        Add-Line "  StdOut: $(Redact ($wl.StdOut.Trim()))"
        if ($wl.StdErr) { Add-Line "  StdErr: $(Redact ($wl.StdErr.Trim()))" }
        if ($wl.ExitCode -eq 0 -and $wl.StdOut -and $wl.StdOut.Trim()) { $wslAvailable = $true }
    }
} else {
    Add-Line "Comando 'wsl' nao encontrado no PATH. WSL provavelmente nao esta instalado/habilitado."
}
Add-Line "WSL_AVAILABLE (deduzido): $wslAvailable"
Add-Line "NOTA: nada foi instalado ou alterado. Esta e' apenas uma checagem de presenca."

# ======================================================================
# RESUMO FINAL
# ======================================================================
Add-Section "RESUMO FINAL"

$CLAUDE_A = if ($profileAResult.StatusOk) { 'PASS' } else { 'FAIL' }
$CLAUDE_B = if ($profileBResult.StatusOk) { 'PASS' } else { 'FAIL' }
$CLAUDE_A_AUTH = $profileAResult.AuthMode
$CLAUDE_B_AUTH = $profileBResult.AuthMode
$CLAUDE_DUAL_PROFILE = if (($CLAUDE_A -eq 'PASS') -and ($CLAUDE_B -eq 'PASS')) { 'PASS' } else { 'FAIL' }

$CODEX_WINDOWS = if (($codexPaths.Count -gt 0) -and ($codexVersionResult -and $codexVersionResult.Ran -and $codexVersionResult.ExitCode -eq 0) -and (-not $codexHwError)) { 'PASS' } else { 'FAIL' }
$CODEX_AUTH = if ($codexLoginOk) { $codexAuthMode } else { "NAO_CONFIRMADO ($codexAuthMode)" }
$CODEX_HW_ERROR = if ($codexHwError) { 'YES' } else { 'NO' }
$WSL_AVAILABLE_STR = if ($wslAvailable) { 'YES' } else { 'NO' }

$ANTHROPIC_PAID_API_IN_USE = if ($anthropicKeyPresentAny -and $CLAUDE_A_AUTH -notmatch 'SUBSCRIPTION') { 'UNKNOWN' } elseif ($anthropicKeyPresentAny) { 'UNKNOWN' } else { 'NO' }
$OPENAI_PAID_API_IN_USE    = if ($openaiKeyPresentAny -and $codexAuthMode -eq 'API_KEY') { 'UNKNOWN' } elseif ($openaiKeyPresentAny) { 'UNKNOWN' } else { 'NO' }

$blockers = New-Object System.Collections.Generic.List[string]
if ($claudePaths.Count -eq 0) { $blockers.Add('claude CLI nao encontrado no PATH.') }
if (-not $profileA_Dir -or -not $profileB_Dir) { $blockers.Add('Nao foi possivel identificar automaticamente os 2 perfis/mecanismos Claude (verifique secao 6 e confirme manualmente os 2 caminhos).') }
if ($codexPaths.Count -eq 0) { $blockers.Add('codex CLI nao encontrado no PATH.') }
if ($codexHwError) { $blockers.Add('Codex apresenta erro de HW capability no Windows nativo -> candidato a rodar via WSL.') }
if ($codexHwError -and -not $wslAvailable) { $blockers.Add('WSL nao esta disponivel/habilitado -> nao ha runtime alternativo pronto para o Codex agora.') }
if (-not $RunLiveCalls) { $blockers.Add('Chamadas minimas (-p / exec) nao foram testadas nesta rodada (rode com -RunLiveCalls para confirmar autenticacao ponta-a-ponta, se aceitar o custo).') }

$selfHostedReady = if (($CLAUDE_DUAL_PROFILE -eq 'PASS') -and ($CODEX_WINDOWS -eq 'PASS' -or $wslAvailable)) { 'YES' } else { 'NO' }

$statusFinal = if ($blockers.Count -eq 0 -and $CLAUDE_DUAL_PROFILE -eq 'PASS' -and $CODEX_WINDOWS -eq 'PASS') { 'LOCAL_RUNTIME_READY' } else { 'NEEDS_HUMAN' }

Add-Line "CLAUDE_A = $CLAUDE_A"
Add-Line "CLAUDE_B = $CLAUDE_B"
Add-Line "CLAUDE_A_AUTH = $CLAUDE_A_AUTH"
Add-Line "CLAUDE_B_AUTH = $CLAUDE_B_AUTH"
Add-Line "CLAUDE_DUAL_PROFILE = $CLAUDE_DUAL_PROFILE"
Add-Line ""
Add-Line "CODEX_WINDOWS = $CODEX_WINDOWS"
Add-Line "CODEX_AUTH = $CODEX_AUTH"
Add-Line "CODEX_HW_ERROR = $CODEX_HW_ERROR"
Add-Line "WSL_AVAILABLE = $WSL_AVAILABLE_STR"
Add-Line ""
Add-Line "ANTHROPIC_PAID_API_IN_USE = $ANTHROPIC_PAID_API_IN_USE"
Add-Line "OPENAI_PAID_API_IN_USE = $OPENAI_PAID_API_IN_USE"
Add-Line ""
Add-Line "SELF_HOSTED_RUNNER_READY = $selfHostedReady"
Add-Line ""
Add-Line "BLOCKERS:"
if ($blockers.Count -eq 0) {
    Add-Line "  (nenhum)"
} else {
    $blockers | ForEach-Object { Add-Line "  - $_" }
}
Add-Line ""
Add-Line "NEXT_STEP:"
if ($statusFinal -eq 'LOCAL_RUNTIME_READY') {
    Add-Line "  Ambiente parece pronto. Revisar este relatorio com o usuario antes de qualquer"
    Add-Line "  migracao/automatizacao (Fase 2)."
} else {
    Add-Line "  Resolver os BLOCKERS acima manualmente (ou confirmar com o usuario os caminhos"
    Add-Line "  reais dos 2 perfis Claude e do runtime do Codex) antes de prosseguir para a Fase 2."
}
Add-Line ""
Add-Line "STATUS:"
Add-Line "  $statusFinal"

# ======================================================================
# Gravar relatorio (somente escrita de arquivo NOVO de log; nada do sistema
# e' alterado)
# ======================================================================
try {
    $Report | Out-File -FilePath $OutFile -Encoding utf8 -Force
    Write-Host ""
    Write-Host "Relatorio salvo em: $OutFile"
} catch {
    Write-Host ""
    Write-Host "ERRO ao salvar relatorio em '$OutFile': $($_.Exception.Message)"
}
