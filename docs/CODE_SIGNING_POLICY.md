# Code Signing Policy

This policy defines how executable artifacts for RNG Shunt300 Live Simulator are produced and signed.

## Signing Program

Free code signing provided by [SignPath.io](https://about.signpath.io/), certificate by [SignPath Foundation](https://signpath.org/).

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

## Privacy Statement

This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it.

## Security Response

If you suspect abuse or policy violations in a signed release, open a GitHub issue and include evidence and reproduction details.
