param(
    [ValidateSet('Auto','SignPath','LocalSelfSigned')]
    [string]$Mode = 'Auto',
    [string]$Tag = 'v1.0.1',
    [string]$Repo = 'rs-mini-rgb/RNG_Shunt300-ls',
    [string]$CertSubject = 'CN=rs-mini-rgb Community (Local Test Signing)'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$buildDir = Join-Path $repoRoot 'build'

function Test-SignPathReady {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        return $false
    }

    $required = @(
        'SIGNPATH_API_TOKEN',
        'SIGNPATH_ORGANIZATION_ID',
        'SIGNPATH_PROJECT_SLUG',
        'SIGNPATH_SIGNING_POLICY_SLUG'
    )

    $available = @((gh secret list --repo $Repo --json name | ConvertFrom-Json).name)
    foreach ($name in $required) {
        if ($name -notin $available) {
            return $false
        }
    }

    return $true
}

function Ensure-BuildInputFiles([string]$ReleaseNotesFile) {
    Copy-Item (Join-Path $repoRoot 'src\shunt300_live_simulator.py') $buildDir -Force
    Copy-Item (Join-Path $repoRoot 'src\shunt300_live_ui.html') $buildDir -Force
    Copy-Item (Join-Path $repoRoot 'src\shunt300_database.py') $buildDir -Force

    Copy-Item (Join-Path $repoRoot 'resources\RSHST-B02P300.webp') $buildDir -Force
    Copy-Item (Join-Path $repoRoot 'resources\installer_icon.ico') $buildDir -Force
    Copy-Item (Join-Path $repoRoot 'resources\installer_logo_banner.bmp') $buildDir -Force
    Copy-Item (Join-Path $repoRoot 'resources\installer_logo_small.bmp') $buildDir -Force

    Copy-Item (Join-Path $repoRoot 'LICENSE.txt') $buildDir -Force
    Copy-Item (Join-Path $repoRoot 'README.md') $buildDir -Force
    Copy-Item (Join-Path $repoRoot 'QUICKSTART.md') $buildDir -Force
    Copy-Item (Join-Path $repoRoot $ReleaseNotesFile) $buildDir -Force
}

function New-OrGetLocalCodeSigningCert {
    $now = Get-Date
    $existing = Get-ChildItem Cert:\CurrentUser\My |
        Where-Object { $_.Subject -eq $CertSubject -and $_.HasPrivateKey -and $_.NotAfter -gt $now.AddDays(7) } |
        Sort-Object NotAfter -Descending |
        Select-Object -First 1

    if ($null -ne $existing) {
        return $existing
    }

    return New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject $CertSubject `
        -CertStoreLocation 'Cert:\CurrentUser\My' `
        -HashAlgorithm 'SHA256' `
        -KeyExportPolicy Exportable `
        -NotAfter $now.AddYears(2)
}

function Sign-FileWithCert([string]$FilePath, $Cert) {
    if (-not (Test-Path $FilePath)) {
        throw "File not found for signing: $FilePath"
    }

    $result = Set-AuthenticodeSignature -FilePath $FilePath -Certificate $Cert -HashAlgorithm SHA256
    if ($null -eq $result.SignerCertificate) {
        throw "No signer certificate on file after signing: $FilePath"
    }

    $verified = Get-AuthenticodeSignature -FilePath $FilePath
    if ($null -eq $verified.SignerCertificate) {
        throw "Signature verification failed for: $FilePath"
    }

    Write-Host "Signed: $FilePath" -ForegroundColor Green
    Write-Host "  Signature status: $($verified.Status)" -ForegroundColor DarkGray
}

function Invoke-LocalSelfSignedFlow {
    $pythonExe = 'C:/ha/.venv/Scripts/python.exe'
    if (-not (Test-Path $pythonExe)) {
        throw "Python executable not found at $pythonExe"
    }

    Write-Host ''
    Write-Host '=== Local Self-Signed Build + Sign ===' -ForegroundColor Cyan
    Write-Host 'This produces locally signed artifacts for immediate/internal use.' -ForegroundColor Yellow

    $releaseNotesFile = "RELEASE_NOTES_${Tag}.md"
    if (-not (Test-Path (Join-Path $repoRoot $releaseNotesFile))) {
        $releaseNotesFile = 'RELEASE_NOTES_v1.0.0.md'
    }

    Ensure-BuildInputFiles -ReleaseNotesFile $releaseNotesFile

    Push-Location $buildDir
    try {
        & $pythonExe -m PyInstaller --noconfirm --clean Shunt300LiveSimulator.spec
        .\build_installer.ps1
    }
    finally {
        Pop-Location
    }

    $cert = New-OrGetLocalCodeSigningCert

    $appExe = Join-Path $buildDir 'dist\Shunt300LiveSimulator\Shunt300LiveSimulator.exe'
    $debugExe = Join-Path $buildDir 'dist\Shunt300LiveSimulator\Shunt300LiveSimulator_Debug.exe'
    $installerExe = Join-Path $buildDir 'installer_output\Renogy_Shunt300LS_Setup.exe'

    Sign-FileWithCert -FilePath $appExe -Cert $cert
    if (Test-Path $debugExe) {
        Sign-FileWithCert -FilePath $debugExe -Cert $cert
    }
    Sign-FileWithCert -FilePath $installerExe -Cert $cert

    Copy-Item $installerExe (Join-Path $repoRoot 'Renogy_Shunt300LS_Setup.exe') -Force

    $portableZip = Join-Path $repoRoot 'Renogy_Shunt300LS_Portable.zip'
    if (Test-Path $portableZip) {
        Remove-Item $portableZip -Force
    }
    Compress-Archive -Path (Join-Path $buildDir 'dist\Shunt300LiveSimulator\*') -DestinationPath $portableZip -CompressionLevel Optimal

    $setupHash = (Get-FileHash -Path (Join-Path $repoRoot 'Renogy_Shunt300LS_Setup.exe') -Algorithm SHA256).Hash
    $zipHash = (Get-FileHash -Path $portableZip -Algorithm SHA256).Hash

    Write-Host ''
    Write-Host '✅ Local signing completed.' -ForegroundColor Green
    Write-Host 'Signer certificate subject:' -ForegroundColor Cyan
    Write-Host "  $($cert.Subject)" -ForegroundColor White
    Write-Host 'Updated hashes:' -ForegroundColor Cyan
    Write-Host "  Setup.exe    $setupHash" -ForegroundColor White
    Write-Host "  Portable.zip $zipHash" -ForegroundColor White
    Write-Host ''
    Write-Host 'Note: Local self-signed artifacts are not equivalent to publicly trusted CA/SignPath signatures.' -ForegroundColor Yellow
}

if ($Mode -eq 'Auto') {
    if (Test-SignPathReady) {
        $Mode = 'SignPath'
    }
    else {
        $Mode = 'LocalSelfSigned'
    }
}

if ($Mode -eq 'SignPath') {
    Write-Host ''
    Write-Host '=== SignPath Mode ===' -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot 'Start-SignedRelease.ps1') -Tag $Tag -Repo $Repo
    exit 0
}

Invoke-LocalSelfSignedFlow
