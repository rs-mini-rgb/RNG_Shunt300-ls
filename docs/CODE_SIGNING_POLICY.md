# Code Signing Policy

This policy defines how executable artifacts for RNG Shunt300 Live Simulator are produced and signed.

## Signing Program

Free code signing provided by [SignPath.io](https://about.signpath.io/), certificate by [SignPath Foundation](https://signpath.org/).

## Current Status

- Until SignPath onboarding is approved, releases may show Windows SmartScreen warnings.
- After onboarding, release binaries are produced and signed through GitHub Actions.
- Only signed artifacts are intended for public release downloads.

## Scope

- Applies to Windows release artifacts published from this repository.
- Applies to installer and portable distributions listed on GitHub Releases.

## Team Roles

- Committers and reviewers: project maintainers and approved contributors in this repository.
- Approvers: repository owner(s) at rs-mini-rgb.

Only approvers may authorize code-signing release requests.

## Release and Signing Rules

- We sign only binaries built from this repository and maintained by this project.
- Build scripts and CI configuration are part of trusted source and must be code reviewed.
- Version metadata must be present and consistent across signed artifacts.
- Release artifacts must include SHA256 hashes in release notes.

## CI Signing Workflow

- Workflow: `.github/workflows/release-build-sign.yml`
- Trigger: GitHub Release publish event (and optional manual dispatch)
- Pipeline responsibilities:
	- build executable and installer on GitHub-hosted Windows runners
	- upload unsigned artifact bundle to GitHub Actions artifacts
	- submit signing request to SignPath
	- verify Authenticode signature status before release upload
	- upload signed artifacts and SHA256SUMS to the GitHub release

## Required GitHub Secrets

- `SIGNPATH_API_TOKEN`
- `SIGNPATH_ORGANIZATION_ID`
- `SIGNPATH_PROJECT_SLUG`
- `SIGNPATH_SIGNING_POLICY_SLUG`
- Optional: `SIGNPATH_ARTIFACT_CONFIG_SLUG` (defaults to `default`)

If required secrets are missing, the signing workflow fails and does not publish signed assets.

## Local Secret Vault (Maintainer Host)

Use the provided scripts to keep SignPath secrets encrypted on the maintainer host:

- `scripts/New-LocalSigningVault.ps1` creates an encrypted DPAPI vault file.
- `scripts/Sync-GitHubSigningSecrets.ps1` pushes vault entries to GitHub Actions secrets without printing values.
- `scripts/Start-SignedRelease.ps1 -Tag vX.Y.Z` triggers the signed release workflow after secrets are configured.

## Privacy Statement

This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it.

## Security Response

If you suspect abuse or policy violations in a signed release, open a GitHub issue and include evidence and reproduction details.
