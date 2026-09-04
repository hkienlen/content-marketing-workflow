# GitHub App installation token format compatibility

Date: 2026-09-04
Status: normative compatibility contract

## Purpose

GitHub App installation access tokens are opaque credentials. The skill/runtime must not depend on a historical token length, payload structure or internal encoding.

GitHub has announced a stateless installation-token format that retains the `ghs_` prefix but may be substantially longer than older tokens. Generic workflows must remain compatible without code changes.

## Invariant

```text
GitHub installation token
= opaque bearer credential supplied by GitHub
```

Never:

- validate it by exact length;
- parse the characters after `ghs_`;
- store it in repository/user-profile content;
- use a regex that assumes a fixed token body length;
- truncate it to a database/variable field sized for an old format;
- confuse it with a GitHub Actions OIDC identity token.

## Current workflow behavior

Generic schedulers use the runtime-provided GitHub token through the normal Actions context, for example:

```yaml
env:
  GH_TOKEN: ${{ github.token }}
```

and pass it opaquely to `gh`/GitHub API clients.

The WordPress relay authentication path is separate: GitHub Actions obtains a short-lived **OIDC JWT** through `ACTIONS_ID_TOKEN_REQUEST_URL`, and the Bridge verifies that JWT's issuer/audience/repository/workflow claims. GitHub App installation-token format changes do not change that OIDC contract.

## Test requirement

CI must guard the generic package/workflows against reintroducing fixed-format assumptions. The guard checks that:

- no generic runtime source contains a literal `ghs_` parsing rule;
- no generic workflow/script validates `github.token`/`GH_TOKEN` by exact length;
- schedulers continue to pass `${{ github.token }}` opaquely.

## Secret ownership

Any GitHub-generated installation token is ephemeral runtime credential material. It never belongs in `user-data/profile.json` or the distributable skill's durable configuration.

## References

- `docs/architecture/skill-package-boundary.md`
- `docs/architecture/user-profile-data-contract.md`
- `.github/workflows/linkedin-scheduler.yml`
- `.github/workflows/facebook-scheduler.yml`
