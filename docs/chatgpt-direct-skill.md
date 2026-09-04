# Installing Content Marketing Workflow directly as a ChatGPT Skill

Content Marketing Workflow ships a direct-install Skill bundle in addition to the Codex plugin package.

## Which artifact to use

For ChatGPT, prefer the release artifact:

```text
content-marketing-workflow-<version>.skill
```

A ZIP variant is also produced:

```text
content-marketing-workflow-skill-<version>.zip
```

Both contain the same complete Skill folder. The package includes `SKILL.md` and all supporting contracts, scripts and companion resources required by the workflow.

Uploading only `SKILL.md` is possible in ChatGPT interfaces that accept it, but that installs only the playbook file. Because Content Marketing Workflow depends on supporting resources, use the complete `.skill` or Skill ZIP bundle whenever possible.

## ChatGPT installation

In ChatGPT:

1. Open **Skills**.
2. Select **Create**.
3. Select **Upload from your computer**.
4. Upload the `.skill` artifact (preferred) or the Skill ZIP artifact.
5. Review the scan result and install/enable the Skill when offered.
6. Start a new chat and invoke the Skill explicitly or use `/start` to begin/resume project onboarding.

## First project onboarding

The Skill does not contain project-specific site names, repositories, identities, credentials or publication authorizations.

On first use, `/start` should resolve or ask for the target project repository and required project settings. When a connected GitHub tool is available, the Skill should inspect the target repository before asking for values it can safely resolve from repository state.

If an older project repository is used as a migration source, migration is selective: copy only the content/configuration classes the user requests. Generic plugin/Skill source, product tests, CI/release machinery, credentials and unrelated historical implementation material stay out of the new project repository.

## ChatGPT versus Codex

Installing the Skill in ChatGPT does not force execution in Codex. If the active ChatGPT conversation exposes the necessary connected tools, the Skill may perform the governed workflow there, including repository operations supported by those tools.

The Codex plugin remains available for Codex users and repository-heavy execution. Both distributions embed the same canonical Skill content, and repository tests prevent them from drifting apart.

## Updating

For a new release, download the new `.skill` artifact and upload/install it through the same Skills interface. Version identity is carried by the packaged `VERSION` file and is kept in sync with the repository release and Codex plugin manifest.
