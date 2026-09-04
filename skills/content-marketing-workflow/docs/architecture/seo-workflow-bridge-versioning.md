# SEO Workflow Bridge versioning contract

Date: 2026-09-03
Status: normative product contract

## Rule

Every distributed change to SEO Workflow Bridge, including a minor functional improvement, compatibility adjustment, bug fix, onboarding improvement, probe, safety enhancement, or user-visible behavior change, must increment the plugin version.

The version must be updated consistently in all distribution surfaces:

- WordPress plugin header `Version`;
- `SEO_WORKFLOW_BRIDGE_VERSION` constant;
- tests/assertions that validate the current packaged version;
- release/package metadata where present;
- the downloadable ZIP filename presented to the user.

Do not distribute two materially different ZIPs under the same plugin version.

## Versioning convention

Use semantic-style `MAJOR.MINOR.PATCH` numbering for installable Bridge packages.

- PATCH: bug fix, safety fix, small compatible enhancement, minor UI/onboarding improvement, probe/diagnostic addition.
- MINOR: new backward-compatible capability or substantial feature surface.
- MAJOR: incompatible contract or migration requiring deliberate user action.

Development suffixes may be used internally on non-distributed work in progress, but once a ZIP is presented to a user for installation, it must have a concrete distinct version number.

## Pilot correction

The media-probe package previously distributed under a filename derived from `0.4.0-dev` introduced additional functionality after the earlier OAuth/member-verification builds. The canonical version for that state is now `0.4.2`.

Future onboarding/update guidance must identify the exact Bridge version being installed and must not refer to an old version string after behavior has changed.
