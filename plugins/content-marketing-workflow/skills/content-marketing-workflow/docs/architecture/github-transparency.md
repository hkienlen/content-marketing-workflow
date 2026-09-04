# GitHub transparency contract

Date: 2026-09-01
Status: authoritative architecture contract

## Purpose

GitHub is the durable internal implementation mechanism of the Content / Marketing skill. After initial project setup and repository connection, normal GitHub mechanics must remain transparent to the user.

The user validates business/editorial outcomes, not routine repository plumbing.

This contract supersedes earlier repository wording that required a separate human approval for ordinary branch creation, commits, Pull Requests, branch synchronization or merge after the relevant business/content gates are satisfied.

## Core rule

After onboarding, the skill must perform normal GitHub operations automatically when they are necessary to execute an already-authorized workflow.

Normal internal operations include:

- create or reuse the correct work branch;
- commit durable state and content;
- create or reuse the Pull Request;
- update PR metadata/state;
- synchronize/rebase/merge the work branch with the current base when safe and necessary;
- resolve straightforward repository bookkeeping conflicts when the intended content is unambiguous;
- merge the content PR automatically once all required human **business/content gates** for that stage are satisfied;
- persist and verify the resulting merge/commit state;
- close/update tracking items when their workflow state requires it.

The user must not be asked to approve these GitHub mechanics individually and must not need to know branch names, commit SHAs, PR numbers or merge commands to use the skill normally.

Technical identifiers may be reported for transparency or debugging, but they are not user gates.

## Human gates vs GitHub mechanics

Human approval remains required for decisions that change the user-visible business/content result or trigger an externally visible side effect.

Examples of human gates that remain explicit:

- editorial approval of an article (`Article OK` or equivalent);
- selection/rejection of proposed images or social visuals;
- approval of a materially changed validated component when the change is not merely technical bookkeeping;
- Divi/editor presentation validation when required;
- each externally visible WordPress publication authorization;
- each externally visible social publication/scheduling authorization when the applicable capability contract requires it;
- destructive or ambiguous recovery choices where multiple materially different content outcomes are possible.

These gates authorize the **business result**, not a separate GitHub action.

For example:

```text
Article OK
+ all required images selected/finalized
+ final snapshot requirements satisfied
-> skill verifies PR/branch state
-> skill merges automatically
-> skill verifies merge
-> workflow continues to the next configured stage
```

The skill must not insert an additional `go merge` prompt between editorial/media validation and the merge.

## Exceptions requiring user involvement

The user may be asked about GitHub only when a technical situation cannot be resolved safely without choosing between materially different outcomes, for example:

- repository connection/permissions are missing during onboarding or have been revoked;
- branch protection or repository policy prevents the required operation and there is no authorized automatic path;
- an unrelated human/third-party edit creates a semantic conflict where choosing a side would change validated content;
- a destructive action would remove user-authored work and no safe preservation path exists;
- the user explicitly asks to inspect/control GitHub mechanics.

Routine merge conflicts caused only by the skill's own bookkeeping should be repaired automatically whenever the validated intended state is known.

## Verification

Automatic does not mean unverified.

Every GitHub mutation must still be read back or otherwise verified before being treated as successful.

The skill should report meaningful workflow state to the user, for example `article validated and integrated`, rather than requiring the user to operate GitHub.

## Precedence

When an older document, historical PR body, checklist or capability contract says one of the following for ordinary content workflow mechanics:

- `merge requires explicit human approval`;
- `never merge autonomously`;
- `ask for go merge`;
- equivalent wording that creates a separate GitHub-only gate;

this contract takes precedence.

Those statements remain historically informative but are not the current product behavior unless a later explicit architecture decision supersedes this file.

This precedence does **not** remove or weaken external publication gates or genuine content/visual validation gates.