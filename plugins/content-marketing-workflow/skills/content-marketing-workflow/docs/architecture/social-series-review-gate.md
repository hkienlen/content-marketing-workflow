# Social series review gate

Date: 2026-09-02
Status: architecture contract

## Decision

For article-derived social content, automatic inventory and complete series-plan persistence happen before any human intervention, but the first new post from a newly created or materially revised series must not be drafted until the user has reviewed and validated the complete series.

The validation is strategic, not merely a yes/no check of titles. The user must be shown how the series is intended to move readers from recognition of a problem toward understanding of the professional, the method and, when relevant, the offer.

This gate applies to `/social create` whenever the selected article's current `series-plan.md` has not yet been human validated for production.

## Required sequence

```text
select next eligible article
-> automatic inventory audit
-> automatic complete deduplicated series extraction
-> classify each concept by strategic function
-> propose balanced editorial order
-> persist + re-read series-plan.md
-> present complete detailed series to human
-> human validates/corrects concepts + functions + order
-> persist revised/validated series
-> automatically accept/select first eligible concept
-> draft first post without another generic go
-> continue normal text/visual review workflow
```

## Four functions to explain during every series review

The review presentation must explicitly explain these functions every time a new/materially revised series is submitted:

| Function durable | Libellé utilisateur | Rôle |
|---|---|---|
| `identification` | Identification | Le lecteur se reconnaît dans une situation/problème. |
| `expertise` | Expertise / compréhension | Le lecteur apprend, distingue ou comprend mieux le problème. |
| `positioning` | Méthode / positionnement | Le lecteur comprend qui est le professionnel, comment il travaille, ses choix et limites. |
| `conversion` | Offre / conversion | Le lecteur comprend le service, sa pertinence, ses bénéfices légitimes ou la prochaine étape/CTA. |

The labels may be translated/localized, but the durable semantic functions must remain stable.

## Required review projection

For every concept, show at least:

- proposed editorial order;
- concept/title;
- concise angle/territory;
- strategic function;
- concrete role in the reader journey;
- current state;
- source/article/offer/link note when useful;
- important deduplication/reservation note when applicable.

Also show:

1. a coverage summary by function;
2. any intentionally missing function and why it is not supported by durable source truth;
3. a short explanation that the proposed order deliberately avoids clustering commercial/CTA posts;
4. any exceptional adjacency of two commercial posts and its reason.

A bare list of topics without functions/roles/order is not sufficient for this gate.

## Editorial balance invariant

The series should normally mix functions rather than group all posts of one type.

In particular:

- avoid two `conversion` posts consecutively when reasonably possible;
- avoid a sequence of strong explicit CTAs even across series when scheduling context is known;
- do not automatically put all conversion posts at the end of the series;
- interleave identification/expertise/positioning so repeated exposure does not feel like repeated selling;
- keep a coherent progression, but do not impose a rigid funnel pattern when the source/article does not support it.

Indicative proportions are strategy guidance, not validation quotas. The user may approve a different balance when it is deliberate and truthful.

## Existing validated series

If a series has already been human validated and still contains an eligible non-materialized concept, `/social create` may directly select the next eligible concept and start drafting it. It must not ask the user to revalidate an unchanged series.

A material change includes additions/removals/merges/splits/reframes, material changes of strategic function/role, or order changes that alter the validated editorial progression. Such changes invalidate prior validation for affected future production.

## Series validation evidence

At minimum persist:

```yaml
inventory_state: validated
validated_at: <timezone-aware timestamp>
validated_revision: <stable commit/blob/fingerprint or equivalent exact plan identity>
```

The validated revision necessarily includes the concept functions and editorial order that were shown to the user.

Equivalent existing fields may be used when they bind unambiguously to the exact reviewed plan version.

## Human feedback

During review the user may:

- accept the list as-is;
- add/remove concepts;
- merge/split concepts;
- reword/reframe an angle;
- change a concept's strategic function or role;
- defer/reject concepts;
- change ordering/priority;
- request more or less explicit offer/CTA coverage.

All decisions are persisted before drafting begins.

The user does not need to send another generic `go` after validating the list. Validation authorizes progression to drafting of the first eligible concept, not publication.

## Safety invariant

Series validation is not post editorial validation, visual selection, scheduling approval or publication authorization. Those remain separate gates.

## Free posts

`/social create free <topic>` has no article series and therefore no whole-series gate. It still requires normal post text/visual review and downstream publication gates. Its strategic function should still be persisted when useful for global scheduling balance.
