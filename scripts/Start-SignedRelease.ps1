param(
    [Parameter(Mandatory = $true)]
    [string]$Tag,
    [string]$Repo = "rs-mini-rgb/RNG_Shunt300-ls"
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI (gh) is required but not found in PATH.'
}

$requiredSecrets = @(
    'SIGNPATH_API_TOKEN',
    'SIGNPATH_ORGANIZATION_ID',
    'SIGNPATH_PROJECT_SLUG',
    'SIGNPATH_SIGNING_POLICY_SLUG'
)

$availableNames = (gh secret list --repo $Repo --json name | ConvertFrom-Json).name
$missing = @($requiredSecrets | Where-Object { $_ -notin $availableNames })
if ($missing.Count -gt 0) {
    throw "Missing required GitHub secrets: $($missing -join ', '). Run scripts/Sync-GitHubSigningSecrets.ps1 first."
}

gh workflow run release-build-sign.yml --repo $Repo -f tag=$Tag

Write-Host ''
Write-Host "✅ Signing workflow started for tag: $Tag" -ForegroundColor Green
Write-Host "Track runs: https://github.com/$Repo/actions/workflows/release-build-sign.yml" -ForegroundColor Cyan
