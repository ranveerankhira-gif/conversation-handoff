# Conversation handoff format

## Bundle contents

- `FULL_TRANSCRIPT.jsonl`: canonical UTF-8 JSONL containing accessible user-visible messages in order.
- `CONVERSATION_INDEX.json`: compact message index with sequence, role, timestamp, preview, and text hash.
- `BUNDLE_METADATA.json`: source identity, coverage statement, counts, cutoff, and preparation/finalization state.
- `DETAILED_HANDOFF.md`: semantic working memory written from the full transcript.
- `START_NEW_CHAT.md`: receiving-chat verification and startup contract.
- `BUNDLE_MANIFEST.json`: hashes and byte sizes for every other finalized bundle member.
- `<handoff-directory>.zip`: portable archive produced at finalization.

Every manifest file record contains an exact relative POSIX path, byte size, and lowercase SHA-256. Paths with traversal, absolute roots, backslashes, control characters, Windows reserved names, trailing dots/spaces, or case/Unicode collisions are invalid. The verifier also rejects unlisted files, links, encrypted ZIP members, duplicate names, unreferenced attachments, and archives above its configured expansion limit.

## Canonical transcript record

Each line of `FULL_TRANSCRIPT.jsonl` is one JSON object:

```json
{
  "sequence": 1,
  "timestamp": "2026-09-11T08:00:00Z",
  "role": "user",
  "phase": null,
  "content": [
    {"type": "text", "text": "Exact visible message text"}
  ]
}
```

`sequence` is one-based and contiguous inside this transcript. A content item may instead be an exported image with `type`, relative `path`, MIME type, byte size, and SHA-256.

## Imported JSONL accepted by `prepare-jsonl`

The import file must contain one JSON object per non-empty line. Required fields:

- `role`: exactly `user` or `assistant`.
- `content`: either a string, or an array containing `{ "type": "text", "text": "..." }` objects.

Optional fields:

- `timestamp`: string or null.
- `phase`: string or null.

Imported image/file references are intentionally rejected unless already embedded in a verified bundle. Attach the original files separately and record the coverage limitation rather than silently dropping them. Codex data-URL images are accepted only for PNG, JPEG, GIF, or WebP, with a matching file signature and a maximum decoded size of 20 MiB per image.

## Required `DETAILED_HANDOFF.md` sections

- Purpose And Requested Outcome
- Chronological Narrative
- Decisions And Rationale
- Work Performed
- Files And Artifacts
- Failures, Corrections, And Rejected Approaches
- Current State
- Unresolved Questions And Next Actions
- User Preferences And Constraints
- Verification And Evidence

Each section must contain substantive content. Use “None known” only after checking the full transcript. Cite message sequences for decisions, corrections, and constraints.

## Completeness language

Use precise claims:

- `complete-visible-codex-log`: all user-visible user/assistant records in the stable selected Codex task log through the cutoff were exported; protected runtime records were excluded.
- `complete-supplied-jsonl`: every valid record in the user-supplied JSONL was exported; completeness relative to the original ChatGPT conversation depends on that supplied file.
- `partial`: the source itself was incomplete or inaccessible. Name the missing interval or category when known.

Never equate these labels with hidden model state, system/developer instructions, or internal reasoning.

Hashes prove that bytes match the finalized manifest; they do not prove that the semantic handoff understood the conversation. Image bytes are integrity-checked, but text credential detection does not inspect words rendered inside images.

