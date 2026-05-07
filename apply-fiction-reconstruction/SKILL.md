---
name: apply-fiction-reconstruction
description: >
  Takes three inputs — the original fiction text, the scene-card output from
  deconstruct-fiction, and the revised outline produced by reconstruct-fiction — and
  produces a rewritten draft that implements every structural decision in the reconstruction
  plan while preserving the original's tone, voice, and prose style. Use this skill whenever
  a writer has run deconstruct-fiction and reconstruct-fiction and is ready to produce
  actual prose from the plan. Trigger on phrases like "now write the actual draft", "apply
  the reconstruction plan", "rewrite this using the outline we made", "turn the plan into
  prose", "write the revised version based on our session", "I have the scene cards and the
  outline, now I need the text", or when a writer shares all three inputs and says "go" or
  "now do it." This is the execution step of the deconstruct → reconstruct → apply pipeline.
---

# Apply Fiction Reconstruction

Your job is to take the editorial plan from a `reconstruct-fiction` session and turn it into
actual rewritten prose — implementing every structural decision the writer made while staying
true to their voice, tone, and style.

You are not inventing. You are executing. The writer has already done the thinking; your job
is to render their decisions as prose, using the original text as the style anchor.

---

## What you need before you start

You need three things. If any is missing, ask for it before proceeding:

1. **The original fiction text** — the source material that was passed into `deconstruct-fiction`
2. **The deconstruct-fiction output** — the scene cards with structural analysis
3. **The reconstruct-fiction output** — the revised outline with decisions, notes, and changes

If the writer only has the original and the reconstruct output (skipped deconstruct), you can
still work — but you'll need to read the original carefully yourself to fill in what the scene
cards would have told you.

---

## Step 1: Map the plan to the original

Before writing a single word of new prose, read all three inputs carefully. Build a clear map
in your head of:

- **What stays**: scenes or passages from the original that the reconstruction plan preserved
  as-is or with minor adjustment
- **What changes**: scenes that were restructured, reordered, merged, split, cut, or rewritten
  based on the reconstruction decisions
- **What's new**: anything the plan calls for that doesn't exist in the original text at all
  (new scenes, new beats, new dialogue, new transitions)

Cross-reference the scene cards with the revised outline. The deconstruct cards tell you what
the original text was doing; the reconstruct outline tells you what the new text should do.
The gap between them is your work.

---

## Step 2: Extract the style fingerprint

Before writing, extract the style signature of the original text. You're not analyzing for
critique — you're identifying what to preserve. Look at:

- **Sentence rhythm**: short and punchy, long and flowing, deliberately varied?
- **Narrative distance**: tight interiority, slight remove, fully external?
- **Verb energy**: active and specific, or more atmospheric and ambient?
- **Dialogue style**: terse and elliptical, naturalistic, heightened?
- **Description density**: sparse and functional, or rich and sensory?
- **Tonal register**: the emotional texture — dark, wry, warm, cold, lyrical, matter-of-fact?
- **Point of view and tense**: stay exactly as they are in the original

This fingerprint is the constraint that governs every line you write. When you're rewriting a
scene, the question is never "what's the best prose here" in the abstract — it's "what serves
this writer's voice while implementing this decision."

Don't show this analysis to the writer unless they ask. It's internal scaffolding.

---

## Step 3: Write the rewritten draft

Produce a complete, continuous draft of the rewritten text. Work scene by scene, following the
structure laid out in the reconstruction outline.

**For scenes that stay**: lift them from the original with only the changes the outline
specifies. Don't revise sentences that aren't called out — your instinct to improve the prose
is a distraction here. The writer's voice is correct; just implement what was decided.

**For scenes that change** (reordered, merged, restructured): take the original prose of the
affected scenes and reshape it to fit the new structure. Preserve as much of the original
language as possible. Rewrite the connective tissue — openings, closings, transitions — to
make the new structure feel inevitable rather than patched.

**For new content**: write in the style fingerprint you extracted. Match the writer's rhythm,
register, and interiority. New prose should be indistinguishable in voice from the original;
only the substance is new.

**Format**: present the full rewritten draft as clean, flowing prose — no annotations,
brackets, or inline flags. The writer should be able to read it straight through as a piece
of fiction, not a redlined document.

---

## Step 4: Changes summary

After the draft, provide a **What changed and why** section. Keep it tight — one line per
significant structural change, and no more than 8–10 items even for complex rewrites.

For each change: name what you did, connect it to the specific reconstruction decision that
called for it.

**Example format:**
- *Scene 2 moved to open the story* — outline called for leading with the confrontation to
  create immediate stakes rather than earning them through setup
- *Interior monologue cut from Scene 4* — writer decided during reconstruction to push this
  character toward external action; reflection was slowing the pace
- *New transition added between Scenes 5 and 6* — the reorder created a jump that needed
  bridging; written in close third to match surrounding scenes
- *Scenes 3 and 7 merged* — both were doing the same relationship work; the outline flagged
  them as redundant; the merged version keeps the stronger beats of each

---

## Step 5: Open questions and unresolved decisions

If the reconstruction outline left anything unresolved — open questions the writer couldn't
answer during the session, decisions flagged as TBD, or structural gaps you encountered while
drafting — list them at the end under **Open questions**. Don't speculate about answers; just
surface them so the writer knows what still needs decisions.

If everything was resolved, skip this section.

---

## How to handle scale

**Short pieces (under ~1,000 words)**: Write the complete rewritten draft in full. No shortcuts.

**Medium pieces (1,000–5,000 words)**: Write the complete draft. For scenes that stayed
exactly as they were, you may indicate "[Scene N text unchanged from original]" rather than
reprinting them verbatim — but only for scenes where the outline specified no changes.

**Long pieces (5,000+ words)**: Ask the writer which sections they want drafted first. Work
act-by-act or in chunks of 3–5 scenes rather than attempting the whole thing in one pass.
Produce each chunk as a complete draft and let the writer react before moving to the next.

---

## Things to get right

**Your job is execution, not editorializing.** If you think a decision from the reconstruction
plan is wrong, you can note it briefly in the changes summary — but write what was decided
anyway. The writer owns the choices; you own the craft of implementing them.

**Tone is non-negotiable.** Every structural change in the world can be undone by a rewrite
that doesn't sound like the author. If you're writing new material and you're unsure whether
a sentence sounds like them, look back at the original. Find a parallel moment. Use it as the
model.

**Don't over-smooth.** Stitching restructured scenes together can produce a draft that feels
too polished — all the seams hidden, all the edges rounded. Sometimes a rough joint is right.
Trust the writer's texture and don't sand it into generic prose.

**If the plan is underspecified**, fill in with the most conservative choice — the one that
changes the least and preserves the most. If a decision was flagged as open during the
reconstruction session, make a reasonable call and note it in Open questions.

**Don't ask whether to begin.** When you have all three inputs, start. If something is missing
or genuinely ambiguous before you can proceed, ask — but ask once and specifically.
