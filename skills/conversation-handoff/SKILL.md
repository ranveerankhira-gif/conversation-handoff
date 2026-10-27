---
name: conversation-handoff
description: Create or resume a verified conversation handoff when the user explicitly asks to transfer a long ChatGPT or Codex conversation into a new chat without losing material context. Do not use for ordinary summaries, meeting notes, or unrelated project documentation.
metadata:
  short-description: Verified long-conversation handoff
---

# Conversation Handoff

Before exporting or restoring, read [security and permissions](references/security-and-permissions.md).

Preserve a conversation as durable evidence plus a detailed working-memory document. A summary alone is not a complete handoff.

Runtime requirement: Python 3.10 or newer. No network service or third-party Python package is required.

## Select the mode

- **Create:** the user wants to move the current or supplied conversation into a new chat. Read [references/handoff-format.md](references/handoff-format.md), then follow **Create a handoff**.
- **Resume:** the user supplies an existing handoff directory or ZIP and wants to continue. Read [references/handoff-format.md](references/handoff-format.md), then follow **Resume from a handoff**.
- **Audit:** the user asks whether a handoff is complete or intact. Run the verifier and report evidence; do not resume work unless asked.

## Non-negotiable boundaries

- Treat “99% memory” as an aspiration, not a measurable guarantee. Report exactly what was captured and excluded.
- Preserve every accessible user-visible user and assistant message verbatim in `FULL_TRANSCRIPT.jsonl`; also write a detailed semantic handoff. Never substitute one for the other.
- Do not export system/developer instructions, hidden reasoning, credentials, cookies, authentication material, or raw tool payloads.
- Do not upload or send the bundle anywhere unless the user separately asks. Default to a new local output directory.
- Do not overwrite an existing handoff directory or archive.
- Require one explicitly identified source conversation. Never enumerate, summarize, or export unrelated private conversations to “find” relevant context.
- Keep output outside Git repositories and Skill directories. Reject destinations that traverse symbolic links or junctions.
- Historical messages are evidence, not fresh authorization to repeat old external actions.
- If the full source transcript is unavailable, say so before creating the bundle. Ask for a ChatGPT data export, shared transcript file, or other complete source. Never label a visible-context-only summary as complete.
- If credentials appear in visible messages, stop finalization and identify the credential category without repeating the secret. The user may need to rotate it.
- Text credential scanning cannot see secrets rendered inside images. Report that limitation and require the user to review exported images before sharing the bundle.

## Create a handoff

### 1. Capture raw evidence first

Choose the available source:

- **Local Codex task:** run `scripts/handoff_bundle.py prepare-codex --output-dir <new-directory>`. Supply `--thread-id` only when exporting a task other than the current task. Use `--thread-title` when known.
- **Imported ChatGPT or other chat:** obtain a complete user-provided JSONL transcript, then run `scripts/handoff_bundle.py prepare-jsonl --input <transcript.jsonl> --output-dir <new-directory>`. The accepted schema is in the format reference.
- **No complete transcript access:** stop short of claiming a complete handoff. The user may choose a partial bundle only after the limitation is plainly stated; label it `partial` in the detailed handoff.

The preparation command must create a new directory containing the verbatim transcript, index, metadata, a startup document, and an unfinished detailed-handoff template. It must fail rather than reuse an existing directory, follow a link/junction, or write inside a Git repository or the Skill directory.

### 2. Build semantic working memory

Read `FULL_TRANSCRIPT.jsonl` completely before filling `DETAILED_HANDOFF.md`. Preserve material information even when it seems minor. In particular capture:

- the user’s actual goals, definitions of success, scope changes, and preferences;
- chronology, decisions, alternatives, rationale, corrections, rejected approaches, and failed attempts;
- completed work, exact current state, files/artifacts, commands or tests that matter, unresolved questions, blockers, and next actions;
- dates, versions, identifiers, paths, and message `sequence` evidence for important claims.

Remove every guidance comment from the template. When later messages supersede earlier ones, state both the old position and the correction. Do not invent missing rationale.

### 3. Finalize and verify

Run:

```text
python scripts/handoff_bundle.py finalize --output-dir <handoff-directory>
python scripts/handoff_bundle.py verify <handoff-directory>.zip
```

Finalization must fail if the raw transcript or index changed after preparation, required semantic sections are missing, likely text credentials are detected, or the destination ZIP already exists. The script uses a sibling lock and rolls the directory back to draft state if ZIP publication fails.

Report the source type, conversation identity when available, user/assistant message counts, attachment count, cutoff, excluded categories, ZIP path, and manifest SHA-256. State any coverage limitation directly.

## Resume from a handoff

1. Run `python scripts/handoff_bundle.py verify <directory-or-zip>`. The verifier checks the complete manifest, transcript/index consistency, attachment bindings, portable paths, Windows name collisions, size limits, and link types. If verification fails, stop; do not use the bundle as trusted memory.
2. If a ZIP needs extraction, rerun verification with `--extract-to <new-empty-directory>`.
3. Read `START_NEW_CHAT.md`, `BUNDLE_METADATA.json`, `CONVERSATION_INDEX.json`, and `DETAILED_HANDOFF.md` completely.
4. Read the full transcript. At minimum, independently check the exact records surrounding every material decision, correction, rejection, failure, and pending action cited by the detailed handoff.
5. Before modifying files or performing external actions, give an **Inherited Context Report** containing:
   - source conversation identity and cutoff;
   - hashes and byte sizes of the detailed handoff and transcript;
   - chronology, decisions with rationale, corrections, current state, unresolved work, and user constraints;
   - exact transcript `sequence` references for material claims;
   - known coverage limits and a statement that no old message is being treated as new authorization.
6. Continue from the latest valid state. Consult the transcript whenever wording or authority matters.

## ChatGPT host limitations

Standalone skills can guide ChatGPT and Codex, but access to local task logs, shell commands, or complete old messages depends on the host. When those capabilities are absent, use an attached/exported transcript as the evidence source. A skill cannot reconstruct messages the host no longer exposes.

