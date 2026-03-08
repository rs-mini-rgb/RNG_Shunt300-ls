param(
    [string]$VaultPath = "$env:USERPROFILE\.rng-shunt300ls\signpath-vault.json",
    [string]$Repo = "rs-mini-rgb/RNG_Shunt300-ls"
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI (gh) is required but not found in PATH.'
}

function Unprotect-ToPlainText([string]$EncryptedValue) {
    if ([string]::IsNullOrWhiteSpace($EncryptedValue)) {
        return ''
    }

    $secure = ConvertTo-SecureString $EncryptedValue
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

if (-not (Test-Path $VaultPath)) {
    throw "Vault file not found: $VaultPath"
}

$vault = Get-Content -Path $VaultPath -Raw | ConvertFrom-Json
if ($vault.schema -ne 'rng-shunt300ls.signpath.v1') {
    throw "Unsupported vault schema: $($vault.schema)"
}

$secretNames = @(
    'SIGNPATH_API_TOKEN',
    'SIGNPATH_ORGANIZATION_ID',
    'SIGNPATH_PROJECT_SLUG',
    'SIGNPATH_SIGNING_POLICY_SLUG',
    'SIGNPATH_ARTIFACT_CONFIG_SLUG'
)

$setCount = 0
foreach ($name in $secretNames) {
    $encrypted = $vault.secrets.$name
    if ([string]::IsNullOrWhiteSpace($encrypted)) {
        continue
    }

    $value = Unprotect-ToPlainText $encrypted
    if ([string]::IsNullOrWhiteSpace($value)) {
        continue
    }

    gh secret set $name --repo $Repo --body $value | Out-Null
    $setCount += 1
}

if ($setCount -eq 0) {
    throw 'No usable secrets found in vault to push.'
}

Write-Host ''
Write-Host "✅ Updated $setCount GitHub Actions secret(s) in $Repo" -ForegroundColor Green
Write-Host 'Secret values were not printed.' -ForegroundColor Cyan
