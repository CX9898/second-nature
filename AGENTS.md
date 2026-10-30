# Second Nature: Repository Maintenance

This repository contains reusable agent instructions, not model weights.

- Use `Second Nature` as the display name and `second-nature` as the repository identifier.
- Keep `README.md` useful to first-time readers with stable project context: motivation, skill concepts, enduring principles, illustrative structure, and reading paths. Link to `skills/` instead of maintaining a skill list. Adding skills, updating tools, or changing project status should not require a README edit.
- Document environment setup and authoring in `docs/authoring.md`, installation in `docs/usage.md`, evaluation in `evals/README.md`, and repository structure and design decisions in `docs/design.md`.
- Keep required project knowledge in versioned documentation. Public Markdown links and image references must resolve to distributable repository content or public URLs, never ignored or external local files.
- Prefer `.local/research/` for research drafts, `.local/evals/` for evaluation workspaces and results, and `.local/tmp/` for scratch files. Pass these output paths explicitly when invoking tools or delegating research; do not rely on a tool's generic default location.
- Before using a new writer, distinguish publishable deliverables from intermediate output and inspect its actual output defaults. Configure intermediate output to an ignored location where possible. Root-level `tmp/`, `temp/`, `.tmp/`, `research/`, `docs/research/`, `outputs/`, `reports/`, `logs/`, `evals/runs/`, `evals/results/`, and `*-workspace/` are also reserved local-only locations for tool defaults and compatibility.
- Keep temporary outputs out of publication paths even when they are not under `.local/`. Use root-anchored ignore rules for known output locations, not broad file-extension or recursive directory rules that could hide real skill resources and fixtures. Promote useful conclusions into maintained documents with public sources before relying on them.
- Keep each publishable skill in `skills/<name>/SKILL.md`. The frontmatter name must match its directory.
- Treat `skills/` as the source of truth. Keep templates, evaluation cases, and repository documentation outside it.
- Put triggering conditions in the frontmatter description. Keep the body focused on decisions the agent needs for that task.
- Add `references/`, `scripts/`, `assets/`, or tool-specific metadata only when a skill actually needs them. Link supporting references from the skill entrypoint.
- Keep user-facing repository documentation in Chinese. Use lowercase ASCII skill identifiers and portable relative paths inside skills.
- Write shell examples from the repository root and make alternative commands explicit. Keep unfinished templates named `SKILL.md.template` so recursive discovery does not treat them as skills.
- Keep each skill's evaluation bundle in `evals/<skill-name>/`: `cases.yaml` for requests and expectations, `fixtures/` for seed projects, and `inputs/` for additional inputs. Keep their intentional defects unchanged during routine documentation maintenance.
- Prepare evaluations in fresh copies under `.local/evals/<skill-name>/` or another Git-ignored workspace, following `evals/README.md`. Never execute modification tasks in versioned fixtures or the skill repository itself. Reset the workspace for each case, group, and repetition.
- Run `python scripts/validate.py` after repository changes. It checks skill structure, distributable document links, and evaluation inputs, not model behavior. Use `--path` only for a single skill's format check; report behavioral checks separately.
- Do not edit installed user skills as part of repository maintenance. Installation and publication are separate user actions.
- Repository-authored content is licensed under the root MIT `LICENSE`. Include applicable copyright and license notices when distributing a skill independently.
- Before incorporating third-party material, record its source and preserve the applicable license. Do not assume all content in a repository has the root license.
- Update `docs/usage.md` when adding a tool adapter, and keep installation claims tied to current first-party documentation.
