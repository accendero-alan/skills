---
name: deconstruct-fiction
description: >
  Deconstructs a piece of fiction into its constituent scenes, extracting key structural elements for each — characters, setting, time, conflict/tension, narrative purpose, and emotional tone — and presenting them as labeled, self-contained scene cards in structured Markdown. Use this skill whenever a writer pastes or shares fiction and wants it broken down into scenes, wants to see the building blocks of a story laid out separately, wants to pull a story apart so scenes can be reworked or reordered, or asks for a scene breakdown, scene map, or scene inventory. Trigger on any fiction: novels, short stories, flash fiction, screenplays, literary fiction, genre fiction — the format doesn't matter.
---

# Deconstruct Fiction

Your job is to read a piece of fiction and pull it apart into its individual scenes — each one extracted as a self-contained card with its structural elements clearly labeled. The writer will use these cards to understand, rework, or reorder their story.

## What counts as a scene

A scene is a unit of continuous action occurring in a single location and time with a consistent cast. A scene ends and a new one begins when:
- The location shifts
- Significant time passes (a jump cut, a chapter break, a scene break marker like `***` or `---`)
- The POV character or narrative focus changes to a different moment in time or place

A single scene may span several pages or just a paragraph. Don't force breaks that aren't there, and don't lump together passages that clearly belong to separate scenes.

When the text has explicit markers (blank lines, `***`, chapter headers), use them as your primary guide. When it doesn't, use the criteria above and apply judgment.

## Output format

Produce one Markdown block per scene, in reading order. Use this structure exactly:

```
---

## Scene [N] — [brief evocative title you give it, 3–6 words]

**Characters:** [comma-separated list of named or described characters present]

**Setting:** [location + time of day or period, e.g. "the kitchen, early morning" or "a battlefield, winter 1916"]

**Time in narrative:** [where this sits relative to other scenes — e.g. "immediately follows Scene 2", "several days later", "flashback to childhood", "concurrent with Scene 4"]

**Conflict / Tension:** [the central friction or stakes in this scene — what is unresolved, at risk, or in opposition]

**Narrative purpose:** [what this scene does in the story — what it establishes, advances, reveals, or shifts]

**Emotional tone:** [the dominant emotional register — e.g. "grief with dark humor", "menacing calm", "giddy anticipation"]

**Summary:**
[2–4 sentences that capture what actually happens — specific enough that someone who hasn't read the piece could reconstruct the scene's events]

**Source text:**
> [The original text of the scene, quoted verbatim. For scenes longer than ~400 words, include the opening and closing ~100 words with "[…]" in between to mark the elision.]
```

End the output with a **Scene inventory** — a compact list of all scenes with just their number, title, and a one-line summary. This gives the writer a bird's-eye view for reordering:

```
---

## Scene inventory

| # | Title | One-line summary |
|---|-------|-----------------|
| 1 | … | … |
| 2 | … | … |
```

## Things to get right

**Title the scenes yourself.** Don't use the author's chapter titles or section headings — give each scene a short, specific label that captures its action or turning point (e.g. "The offer refused", "First sight of the house", "Argument in the rain"). These become handles the writer can use when thinking about reordering.

**Be specific in the conflict and purpose fields.** "There is tension between the characters" is useless. "Elena threatens to leave unless Marco returns the money" is useful. Name names, name stakes.

**Capture tone with precision.** "Sad" is too flat. Reach for the specific emotional texture — "quiet devastation", "forced cheerfulness masking panic", "savage joy".

**Source text matters.** The writer may want to paste a scene card directly into another tool. Include the verbatim text so each card is self-contained.

**Don't editorialize.** This is deconstruction, not critique. Don't say what the scene should do differently, what's missing, or how it compares to other scenes. Extract what's there.

## If the text is very long

For a full novel chapter or longer: process the whole thing, but use the elision format (`[…]`) for source text in scenes over ~400 words. Always include the scene's opening and closing lines so the card anchors properly.

If the user explicitly asks to skip source text (e.g. "just the cards, no quotes"), omit the **Source text** field entirely.
