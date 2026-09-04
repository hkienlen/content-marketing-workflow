# Prompt-as-contract

Date: 2026-09-04
Status: contrat d'architecture faisant autorité

## Principe

Les tâches éditoriales structurées utilisent un **prompt canonique versionné en Markdown dans GitHub**.

Le prompt Markdown est le contrat de travail. L'exécuteur peut être ChatGPT dans la conversation principale, OpenAI Work lorsqu'une seconde exécution indépendante est souhaitée, ou un autre moteur explicitement autorisé plus tard. Le moteur ne doit pas modifier silencieusement le contrat.

Les noms historiques contenant `work` sont conservés pour stabilité des chemins. Ils ne signifient plus qu'OpenAI Work est obligatoire.

Les capacités `seo-plan-article`, `seo-create-article` et `seo-update-article` appliquent ce contrat.

Les règles de sourcing d'images fournies par l'utilisateur sont en plus gouvernées par :

```text
docs/architecture/user-provided-images.md
docs/architecture/capabilities/visual-source-resolve.md
```

## Séparation des responsabilités

### `strategy/**` et contrats d'architecture

Ils portent les règles durables globales : stratégie SEO, style, images, social, stockage, publication, persistance, sécurité et architecture.

La préférence visuelle structurée de l'utilisateur/projet (`visual_preferences`) appartient au profil utilisateur/projet ; le prompt d'article peut seulement porter une conséquence/surcharge locale propre à cet article.

### `prompts/work-article-template.md`

Il porte les règles communes d'exécution des articles du site actif et référence les autorités globales sans les dupliquer.

### `prompts/work-items/article-<N>-<slug>.md`

C'est le brief d'exécution spécifique faisant autorité pour le Work Item : angle, requêtes, matière terrain, limites de cannibalisation, contraintes spécifiques, chemins, branche/PR, livrables, gates métier et éventuelle surcharge visuelle locale.

Une ancienne consigne spécifique imposant un `go merge`, un stockage binaire GitHub normal ou un ordre universel `rédiger puis générer 3 x A/B/C` est supersédée par les contrats globaux plus récents lorsqu'ils s'appliquent.

### Human Item / Work Item

Le Human Item porte l'opportunité stratégique. Le Work Item porte suivi/pointeurs/état, pas un second prompt complet concurrent.

## Autorité et résolution des conflits

Règle globale : fichier de stratégie/architecture autoritaire.

Instruction spécifique article : prompt Work Item canonique.

Préférence de sourcing durable : profil actif `visual_preferences`.

Surcharge pour un article uniquement : état/prompt spécifique de cet article.

État réel d'exécution : GitHub / Google Drive / système externe relu et vérifié.

Si des sources durables divergent matériellement, les réconcilier avant exécution plutôt que deviner.

## Ordre obligatoire avant rédaction ou révision importante

1. identifier Work Item ;
2. identifier/lire prompt Markdown spécifique ;
3. lire toutes directives référencées ;
4. lire/créer checklist d'exécution ;
5. vérifier branche/PR/article réel ;
6. vérifier Drive pertinent ;
7. charger le profil actif et résoudre la politique visuelle effective ;
8. appeler `visual-source-resolve` **before drafting** / avant rédaction lorsqu'une image utilisateur est requise/prioritaire ;
9. si l'état est `awaiting_user_images`, arrêter avant rédaction et présenter l'action d'intake réelle ;
10. si l'exécution peut continuer, effectuer recherche/rédaction depuis cette version durable ;
11. persister article/briefs avant toute génération/transformation autorisée ;
12. vérifier les écritures ;
13. présenter le résultat à l'utilisateur dans ChatGPT pour revue humaine ;
14. reporter les décisions durables de revue au bon endroit.

Une rédaction improvisée qui ne part pas du contrat canonique et de la politique visuelle effective ne doit pas être présentée comme une exécution contrôlée.

## Exécuteurs

### ChatGPT conversation principale

Exécuteur éditorial par défaut lorsque ses capacités couvrent la tâche et interface normale de revue humaine.

### OpenAI Work

Optionnel : second rédacteur/regard/exécuteur alternatif. Il utilise le même contrat durable, pas un contrat parallèle.

## Gate de sources visuelles avant rédaction

L'ordre dépend de la politique résolue :

```text
création demandée
        ↓
chargement profil + surcharge article
        ↓
visual-source-resolve
        ↓
source_ready | ai_generation_allowed | continue_without_visuals | awaiting_user_images
```

### Si `awaiting_user_images`

Ne pas rédiger l'article avant l'arrivée/repérage des images requises.

Si Google Drive est utilisé, créer/réutiliser et vérifier :

```text
<drive-root>/<site-domain>/articles/<article-slug>/source-user/
```

puis afficher **les deux** :

```text
chemin canonique exact
+ lien Google Drive direct cliquable résolu depuis l'ID réel du dossier
```

Une image envoyée dans le chat est également valable si la pièce jointe réelle est disponible : la vérifier, l'inspecter et conserver sa provenance. Ne jamais prétendre qu'une image existe sans l'avoir réellement résolue.

### Si `source_ready`

Inspecter les images réelles avant rédaction et n'utiliser dans le texte que ce qui est réellement visible/vérifié. Ne pas inventer matière, dimensions, performances ou identité non établies par l'image ou les données utilisateur.

### Surcharge locale

Une consigne du type :

```text
Pour cet article seulement, rédige d'abord ; je fournirai les photos après.
```

peut décaler le gate pour cet article uniquement. La persister comme surcharge locale tant qu'elle gouverne l'exécution, sans modifier la préférence projet.

## Production complète avant première revue

Une fois le gate pré-rédaction satisfait :

```text
recherche + rédaction complète
        ↓
article + briefs/rôles images persistés et commités dans GitHub
        ↓
PAS DE QUESTION / PAS DE GO pour une production visuelle déjà autorisée
        ↓
réutilisation du dossier Drive article
        ↓
production visuelle selon rôle/politique
        ↓
stockage + vérification Drive
        ↓
revue groupée dans ChatGPT : article complet + tous les visuels à décider
```

### Visuels générés ou matériellement transformés

Retenir exactement trois propositions A/B/C réellement reviewables par visuel requis, après inspection interne et régénération des sorties hors brief/trompeuses/de mauvaise qualité.

### Source `use_as_is`

Lorsque la photo source exacte est destinée à être utilisée telle quelle avec `ai_treatment: none` ou simple normalisation non matérielle, **ne pas fabriquer deux variantes synthétiques supplémentaires** uniquement pour satisfaire l'ancien compte A/B/C. Présenter/vérifier la source/candidate finale exacte et conserver le gate de validation média humain.

### Fidélité

`strict`/`high` interdit d'inventer silencieusement l'apparence du sujet réel. Une transformation plus créative ne vaut jamais autorisation de dénaturer un sujet soumis à forte fidélité.

## Google Drive pour sources, revue média et finals

Google Drive est un prérequis actuel et l'espace canonique de staging/revue/final provider-backed.

Article :

```text
<drive-root>/<site-domain>/articles/<article-slug>/
  source-user/
  proposals/
    round-01/
      image-01/
      image-02/
      image-03/
  final/
```

`source-user/` contient les originaux privés fournis par l'utilisateur et **ne doit jamais être écrasé** par traitement/normalisation/finalisation.

GitHub reste la vérité éditoriale/workflow et persiste provenance source + identité/hash/métadonnées du final. Le binaire final normal reste dans Drive privé.

`assets/articles/<slug>/` est réservé à la compatibilité explicite `repository_file` et n'est jamais un fallback silencieux.

Si Drive requis est inaccessible, l'opération média est bloquée ; ne pas inventer de stockage éphémère non prévu.

## Revue humaine groupée

La première revue normale après rédaction présente dans la même conversation :

- contenu public complet ;
- métadonnées SEO utiles ;
- pour chaque image : contexte, **Emplacement / Objectif / Description**, rôle source/fidélité/traitement pertinent ;
- A/B/C pour génération/transformation ;
- candidate exacte pour `use_as_is` ;
- gates métier restant à valider.

Les éléments médias doivent avoir été réellement persistés/vérifiés avant présentation.

Validation éditoriale, source/intake, sélection image et publication restent distinctes.

## Liaison de la revue à une version exacte

Conserver au minimum :

```text
article_path
article_commit_sha
review_round
état de revue
références Drive des sources/propositions/finals affichés lorsque pertinent
```

Avant modification après retour, relire/vérifier la version persistée.

## États de revue éditoriale

```text
review_ready
awaiting_human_validation
corrections_requested
human_validated
```

États médias/source restent indépendants.

Seule une validation explicite et non ambiguë de l'article complet permet `human_validated`.

Ne pas déduire validation complète de silence, `merci`, validation d'une section/image ou réaction positive ambiguë.

## Format Markdown public

Si section finale `## Références`, elle est précédée de deux lignes blanches complètes dans le Markdown source avant première revue.

## Boucle de corrections ciblées

Après retours :

1. classer les décisions selon persistence ;
2. identifier composants à modifier ;
3. identifier impacts nécessaires ;
4. persister décisions durables/locales ;
5. retravailler uniquement éléments concernés ;
6. conserver composants validés/inchangés ;
7. régénérer uniquement séries réellement rejetées/impactées ;
8. ne jamais écraser une source utilisateur originale ;
9. vérifier écritures GitHub/Drive ;
10. présenter tour adapté ;
11. répéter jusqu'à résolution.

Une correction locale ne déclenche pas une réécriture/régénération globale sans nécessité.

## Revue intermédiaire vs snapshot final

Tours intermédiaires : montrer surtout passages modifiés, visuels régénérés, composants conservés et décisions ouvertes.

Avant intégration finale ou WordPress lorsque workflow l'exige : présenter snapshot final complet/cohérent, lié à version persistée exacte.

## GitHub transparent

Après onboarding, l'utilisateur ne valide pas les opérations GitHub.

```text
validation article
+ sélection/finalisation médias
+ snapshot requis validé
-> synchronisation branche/PR automatique
-> merge automatique
-> vérification merge
```

Ne pas demander `go merge`/validation commit/PR.

## WordPress et publication

Après intégration, `wordpress-prepare-article` peut préparer un brouillon si activé/demandé.

`WordPress OK` valide le rendu du brouillon et peut terminer le workflow en `draft`. Il ne vaut pas publication et n'active pas automatiquement candidat/preflight/permission/publish_now.

`wordpress-publish-article` n'est invoqué que si publication explicitement dans le scope. Une publication réelle requiert le `publish_now` exact prévu par son contrat.

L'intake d'une photo utilisateur ou sa sélection ne vaut jamais autorisation WordPress/social.

## Fichiers de tour de revue

Ne pas créer mécaniquement un fichier de revue à chaque échange. Petite correction : pas de fichier ; gros lot de décisions spécifiques : contexte/revue optionnel référencé ; règle globale : autorité globale.

## Garde-fous

- Le prompt peut évoluer mais l'évolution précède l'exécution gouvernée.
- `visual-source-resolve` s'exécute avant rédaction lorsque la politique le requiert.
- Une source utilisateur n'est jamais supposée présente sans vérification réelle.
- Une source originale n'est jamais écrasée.
- `strict_user_images`/fidélité forte interdit le fallback synthétique silencieux.
- Une surcharge locale ne devient pas préférence globale.
- Une proposition/image/source n'est jamais finale sans validation humaine applicable.
- Sélection image != validation éditoriale.
- Validation article+média n'autorise jamais publication WordPress.
- GitHub merge n'est pas un gate utilisateur séparé.
- `WordPress OK` != `publish_now`.
- Propositions rejetées ne vont pas dans GitHub.
- Branches/PR existantes sont réutilisées.
- Un autre moteur n'est pas automatiquement prioritaire : validation humaine décide.

## Principe produit

L'utilisateur relit le contenu et prend les décisions métier. GitHub assure persistance/version/traçabilité. Google Drive assure sources utilisateur privées, staging/review et finals provider-backed. ChatGPT/future interface présente les éléments à décider.
