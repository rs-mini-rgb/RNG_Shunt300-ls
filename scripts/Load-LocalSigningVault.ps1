param(
    [string]$VaultPath = "$env:USERPROFILE\.rng-shunt300ls\signpath-vault.json",
    [ValidateSet('Process','User')]
    [string]$Scope = 'Process'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $VaultPath)) {
    throw "Vault file not found: $VaultPath"
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

$vault = Get-Content -Path $VaultPath -Raw | ConvertFrom-Json
if ($vault.schema -ne 'rng-shunt300ls.signpath.v1') {
    throw "Unsupported vault schema: $($vault.schema)"
}

$required = @(
    'SIGNPATH_API_TOKEN',
    'SIGNPATH_ORGANIZATION_ID',
    'SIGNPATH_PROJECT_SLUG',
    'SIGNPATH_SIGNING_POLICY_SLUG'
)

foreach ($name in $required) {
    $enc = $vault.secrets.$name
    if ([string]::IsNullOrWhiteSpace($enc)) {
        throw "Missing required secret in vault: $name"
    }

    $value = Unprotect-ToPlainText $enc
    [Environment]::SetEnvironmentVariable($name, $value, $Scope)
}

$optional = 'SIGNPATH_ARTIFACT_CONFIG_SLUG'
$optionalEnc = $vault.secrets.$optional
if (-not [string]::IsNullOrWhiteSpace($optionalEnc)) {
    $optionalValue = Unprotect-ToPlainText $optionalEnc
    if (-not [string]::IsNullOrWhiteSpace($optionalValue)) {
        [Environment]::SetEnvironmentVariable($optional, $optionalValue, $Scope)
    }
}

Write-Host ''
Write-Host "✅ SignPath secrets loaded into $Scope environment scope." -ForegroundColor Green
Write-Host 'No secret values were printed.' -ForegroundColor Cyan
