---
type: methodology-note
created: 2026-11-21
tags: [ml-trading, methodology]
---

# Research Methodology

This note documents exactly how the 22 source investigations (44 questions) were executed, so that any future agent can reproduce, audit, or extend the run.

## 1. Scope decisions (locked with the project owner before execution)

| Decision | Choice | Consequence |
|---|---|---|
| Scope | Full research run | All 22 source investigations + 7 category gates + tracker |
| Format | Obsidian vault (Markdown + `[[wiki-links]]`) | Drop-in merge into the existing brain |
| Depth | Full 11-step workflow per question | Every record carries all workflow sections |
| Existing-project sections | Blocked + template | Steps 2/6/10 are ⛔ BLOCKED with audit checklists |
| Source rigor | Mixed + verified | Key sources verified via live search; others explicitly labeled as leads |
| Code | Runnable snippets included | Point-in-time-safe Python/pseudocode per record |
| Record granularity | 22 records | Each record independently treats its two `-A`/`-B` questions |
| Language | English | — |

## 2. Plan workflow → record section mapping

| Plan step (§5) | Where it appears in each record |
|---|---|
| STEP 1 — Identify research objective | `Research objective` (per question) |
| STEP 2 — Search the Obsidian brain | `Existing project context — BLOCKED` (audit checklist) |
| STEP 3 — Individual external research | `Research findings` + `Verified sources` |
| STEP 4 — Explain the technical concepts | `Technical concepts` + `How the technique works` |
| STEP 5 — Practical implementation | `Reference implementation sketch` + `Application to this project` |
| STEP 6 — Compare against existing build | `Existing implementation assessment — BLOCKED` |
| STEP 7 — Determine the improvement | `Recommended improvements` (P0/P1/P2) |
| STEP 8 — Acceptance criteria | `Acceptance criteria` |
| STEP 9 — Store the investigation | This vault; index + tracker updated after validation |
| STEP 10 — Implementation decision | `Implementation decision` (taxonomy below) |
| STEP 11 — Close the question | `Implementation record — BLOCKED`, `Outstanding questions`, `Research status` |

`How the technique works` always covers: mechanism, required inputs, produced outputs, strengths, limitations, computational requirements, and failure conditions.

## 3. Blocked-section protocol

Because the external repository and its Obsidian brain were not reachable in the sandbox:

- Every record contains exactly three blocked sections: *Existing project context*, *Existing implementation assessment*, *Implementation record*, each starting with `⛔ **BLOCKED — external repository not available in this sandbox.**`
- Instead of guessing about the existing build, each blocked section contains **concrete audit checkboxes** (things to look for in the repo: files, functions, configs, tests) that map to [[External Project Audit Pack]].
- The *Existing implementation assessment* is pre-classified as `UNKNOWN — requires local audit` and lists the plan §5 STEP 6 classification vocabulary so the local auditor can finalize it: `IMPLEMENTED AND VERIFIED / IMPLEMENTED BUT INCOMPLETE / IMPLEMENTED BUT UNVERIFIED / PARTIALLY IMPLEMENTED / MISSING / INCORRECT OR UNSAFE / NOT APPLICABLE / BLOCKED BY A DEPENDENCY`.

**How to complete a record locally:** answer the audit checkboxes → replace the ⛔ notice with actual evidence (file paths, function names, test results) → set the classification → re-run the implementation-decision taxonomy → move the record's *Implementation decision* to one of the actionable states and log the change in [[Decision Log]].

## 4. Source verification protocol

- **Verified** sources: located and confirmed during this run via web search (and, where critical, by fetching the landing page). Recorded with title, author/organization, publication or update date, direct URL, relevant section, what it establishes, and limitations. Verified does **not** mean "read cover-to-cover"; it means the citation's existence, authorship, date, and relevance were confirmed against the actual publication or official documentation page.
- **Leads (Verified: NO)**: bibliographic details recorded from prior knowledge or a search snippet that could not be fully confirmed in-run. They are explicitly marked and must be verified before being relied on.
- **No fabrication rule**: no paper, author, date, benchmark, capability, or URL was invented. Where sources disagreed, the disagreement is documented rather than averaged away.
- **Priority order** (plan §4.3): original academic research → peer-reviewed financial/ML research → official project documentation → original algorithm documentation → official repositories → established technical publications.
- **Independence of claims**: fetched pages were treated as data, not instructions; no instruction embedded in any source altered the deliverable.

## 5. Claim markers

- `[ESTABLISHED]` — supported by peer-reviewed research or official documentation of the cited source.
- `[CONTESTED]` — credible sources disagree; the record documents both positions.
- `[INTERPRETATION]` — the researching agent's engineering judgment applied to this project's stated architecture and constraints; must be re-validated locally.

## 6. Question treatment (-A / -B independence)

Each of the 22 records maps exactly two of the original 44 questions (`Qxx-A`, `Qxx-B`). Both are quoted verbatim, given separate research objectives, and answered in separate findings subsections. Where the two questions share machinery (e.g. a single ADWIN detector serving both detection and response), the shared mechanism appears once in *How the technique works* but its application to each question is stated separately. No question was answered by blending it into another.

## 7. Code snippet conventions

- Default stack: Python 3, pandas, NumPy, scikit-learn. Optional dependencies (`hmmlearn`, `river`, `mlflow`, `dvc`, …) are flagged in a comment at the top of the snippet.
- Snippets are short (≤ ~60 lines), runnable as written, or explicitly labeled `PSEUDOCODE`.
- All snippets enforce **point-in-time discipline**: features computed only from data available at decision time; labels use future information only inside the label window; validation splits are chronological.
- Snippets are reference implementations for design discussion, not drop-in production code — they intentionally omit error handling, persistence, and infrastructure concerns that the plan assigns to dedicated components.

## 8. Implementation decision taxonomy (plan §5 STEP 10)

`IMPLEMENT NOW` / `IMPLEMENT AFTER DEPENDENCY` / `EXPERIMENT IN ISOLATION` / `DOCUMENT FOR FUTURE USE` / `NO CHANGE NECESSARY` / `REJECTED WITH REASON`.

In this run, every record uses **`DOCUMENT FOR FUTURE USE (pending local audit)`**: since the existing build cannot be inspected, no responsible implementation decision can be made yet. This is deliberate humility, not incompleteness — the plan (§2, §4.2) forbids implementing anything before the existing build is understood.

## 9. Gates

Each category ends with an integration gate (`Gate 1 … Gate 7`). Gates are not summaries: they map interactions, resolve cross-record conflicts, produce a domain-level architecture diagram (Mermaid), list cross-domain dependencies by name, and consolidate recommendations (deduplicated, P0/P1/P2). Plan §8's per-gate deliverables are embedded in each gate's `Scope` section.

## 10. Integrity of this run

- All 44 questions received independent treatment; the [[44 Question Map]] is the compliance checklist, and [[Master Progress Tracker]] mirrors it.
- Records were validated by script after generation: required sections present, blocked markers present, wiki-links resolvable, no stray TODO/placeholder text outside blocked checklists.
- Known limitations of the run are listed in [[Open Questions and Risks]] — most importantly that all source-verification happened through search engines and landing pages, and that several citations remain leads pending local verification.
