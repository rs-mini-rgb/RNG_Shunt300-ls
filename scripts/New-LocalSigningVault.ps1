param(
    [string]$VaultPath = "$env:USERPROFILE\.rng-shunt300ls\signpath-vault.json",
    [string]$Repo = "rs-mini-rgb/RNG_Shunt300-ls"
)

$ErrorActionPreference = 'Stop'

function Protect-ForCurrentUser([Security.SecureString]$SecureValue) {
    return ($SecureValue | ConvertFrom-SecureString)
}

function Read-Secret([string]$Prompt) {
    return Read-Host -AsSecureString -Prompt $Prompt
}

$vaultDir = Split-Path -Parent $VaultPath
if (-not (Test-Path $vaultDir)) {
    New-Item -ItemType Directory -Path $vaultDir -Force | Out-Null
}

$apiToken = Read-Secret 'Enter SIGNPATH_API_TOKEN'
$organizationId = Read-Secret 'Enter SIGNPATH_ORGANIZATION_ID'
$projectSlug = Read-Secret 'Enter SIGNPATH_PROJECT_SLUG'
$signingPolicySlug = Read-Secret 'Enter SIGNPATH_SIGNING_POLICY_SLUG'
$artifactConfigSlug = Read-Host 'Enter SIGNPATH_ARTIFACT_CONFIG_SLUG (optional, press Enter for default)'

$vault = [ordered]@{
    schema = 'rng-shunt300ls.signpath.v1'
    createdUtc = [DateTime]::UtcNow.ToString('o')
    repo = $Repo
    secrets = [ordered]@{
        SIGNPATH_API_TOKEN = Protect-ForCurrentUser $apiToken
        SIGNPATH_ORGANIZATION_ID = Protect-ForCurrentUser $organizationId
        SIGNPATH_PROJECT_SLUG = Protect-ForCurrentUser $projectSlug
        SIGNPATH_SIGNING_POLICY_SLUG = Protect-ForCurrentUser $signingPolicySlug
        SIGNPATH_ARTIFACT_CONFIG_SLUG = if ([string]::IsNullOrWhiteSpace($artifactConfigSlug)) { '' } else { (ConvertTo-SecureString $artifactConfigSlug -AsPlainText -Force | ConvertFrom-SecureString) }
    }
}

$vault | ConvertTo-Json -Depth 5 | Set-Content -Path $VaultPath -Encoding UTF8

$currentUser = [System.Security.Principal.NTAccount]::new("$env:USERDOMAIN\$env:USERNAME")
$acl = New-Object System.Security.AccessControl.FileSecurity
$acl.SetAccessRuleProtection($true, $false)
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($currentUser, 'FullControl', 'Allow')))
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule('SYSTEM', 'FullControl', 'Allow')))
Set-Acl -Path $VaultPath -AclObject $acl

Write-Host ''
Write-Host '✅ Local signing vault created.' -ForegroundColor Green
Write-Host "Path: $VaultPath"
Write-Host 'Secrets are encrypted with Windows DPAPI and can only be decrypted by this user account on this host.' -ForegroundColor Cyan
