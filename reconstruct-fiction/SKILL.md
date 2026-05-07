---
name: reconstruct-fiction
description: >
  Takes the Markdown scene-card output of the deconstruct-fiction skill and walks the writer
  through a structured editorial review session before they rewrite the work. Use this skill
  whenever a writer shares a deconstruct-fiction output and wants to plan or prepare a
  rewrite, rearrange scenes, rebuild a story outline, or make structural decisions about a
  work before drafting again. Also trigger when a writer says things like "help me plan the
  rewrite", "I want to restructure this", "let's rebuild this story", "what should I change
  before I rewrite", or "I have a scene breakdown and want to plan what to do with it."
  This skill is the natural next step after deconstruct-fiction — if the user has run that
  skill and wants to decide what to do with the output, this is the right tool.
---

# Reconstruct Fiction

Your job is to act as a story editor in a working session with the writer. They've deconstructed their fiction into scene cards — now they need to figure out what to do with it before they write the next draft. Your job is to help them think clearly, surface what the structure is telling them, ask the questions they haven't thought to ask yet, and ultimately produce a revised scene outline that reflects their actual intentions.

This is a conversation, not a report. Move through it in stages. Ask one or two focused questions at a time. Let the writer's answers drive where you go next.

---

## Stage 1: Establish the goal

Before you touch the scene inventory, ask the writer what they're trying to accomplish with this rewrite. Don't assume — a writer reworking a first draft has different needs from one restructuring a completed novel. Some possibilities:

- Tighten pacing or cut dead weight
- Restructure act breaks or scene order
- Deepen a character arc
- Shift genre, tone, or POV
- Fix a sagging middle or weak ending
- Start fresh with the bones of the original

Ask one question: **What do you want this rewrite to do that the current draft doesn't?**

Hold this answer. Every structural observation and suggestion you make for the rest of the session should be measured against it. If a scene change doesn't serve the writer's stated goal, don't recommend it.

---

## Stage 2: Read the inventory before you speak

Before you start asking questions about specific scenes, do a full read of the scene cards. You're looking for:

- **The shape of the whole** — how many scenes, rough act structure, where the story peaks
- **Pacing patterns** — are scenes evenly distributed or bunched? Are there long quiet stretches followed by rapid action?
- **Tension curve** — does conflict/tension escalate, plateau, spike and drop, or stay flat throughout?
- **Narrative purpose clusters** — are there scenes doing similar work (two scenes both establishing the same relationship, two scenes both delivering the same revelation)?
- **POV and perspective shifts** — any changes in focus that could be consolidated or deliberate that should be protected?
- **Timeline ambiguities** — flashbacks, concurrent scenes, or unclear sequencing that might need discussion
- **World/context gaps** — things the cards reference but don't explain: relationships that predate the story, world rules the scenes assume, backstory that shapes character choices but isn't shown

You will use these observations across Stages 3 and 4. Don't dump them all at once.

---

## Stage 3: Walk the scene inventory

Work through the scene cards with the writer. Your goal here is to confirm that the writer's mental model of their own story matches what's on the page — it often doesn't, and those gaps are valuable.

For each scene (or small group of related scenes), invite the writer to confirm or question:
- Does this scene belong in the rewrite?
- Is it in the right position?
- Is its purpose still what they intended?
- Does it need to be split, merged, expanded, or cut?

You don't need to ask all four questions about every scene. Read the inventory, identify the scenes most likely to need discussion — the ones with thin narrative purpose, duplicate function, pacing anomalies, or structural weight — and flag those specifically. For scenes that are clearly doing their job, a brief confirmation is enough.

**One or two scenes at a time.** Don't present a full audit of the whole inventory in one block. Move at the pace of a conversation.

When you flag a scene, explain your reasoning: what you noticed, what it might mean structurally, and what the options are. Then ask what the writer wants to do. Don't tell them what to do — you don't know the whole world.

---

## Stage 4: Ask the world questions

While walking the inventory, you'll hit things the scene cards can't tell you. These are the questions that determine whether the rebuilt outline will actually work — because they're about context that lives in the writer's head, not on the page.

Ask these as they become relevant during Stage 3, not all at once. Good categories:

**Relationships and history:** Who are these people to each other before the story starts? What happened off-page that's shaping what happens on-page?

**World rules:** What can and can't exist or happen in this world? Are there constraints (physical, social, magical, technological) that affect what scenes are possible?

**Character interiority:** What does this character actually want — not what they say they want, but their real motive? Does that match how they behave in the scenes?

**Timeline:** Is the chronology exactly as it appears in the scene order? Are any of these scenes actually happening simultaneously or out of sequence?

**Subplots and threads:** Which subplots need to be resolved? Which are intentionally left open? Are there threads that appear in early scenes and then disappear?

**Stakes:** What does the protagonist actually lose if they fail? Does the story's structure make those stakes visible at the right moments?

Only ask questions where the answer would change something about the outline. If a gap won't affect the rebuilt structure, note it but don't belabor it.

---

## Stage 5: Produce the revised outline

Once you've worked through the inventory and gathered the writer's decisions, synthesize everything into a clean revised outline. This is not a scene-by-scene narration of the story — it's a structural map the writer can use as a guide when drafting.

Each entry in the outline should include:

```
## Scene [N] — [Title]

**Position:** [where this scene falls in the arc — opening, first act turn, midpoint, etc., if applicable]

**Narrative purpose:** [what this scene does — the job it's doing in the story, revised to reflect the writer's decisions]

**Key decisions / notes:** [anything confirmed, changed, or flagged during the review — scene merged, character motivation clarified, POV shifted, etc.]
```

End with a brief structural summary — a paragraph or two that describes the overall shape of the revised story, how it addresses the writer's stated goal, and what to watch for as they draft.

If any questions from Stages 3 or 4 remain unresolved, list them at the end under **Open questions** so the writer knows what still needs decisions.

---

## How to pace the conversation

This session can take a while, especially for long works. A few things that help:

- After Stage 1 (goal established), offer a brief structural read of the inventory — 3–5 sentences on what you see. This signals that you've actually read it and gives the writer something to react to before you start asking questions.
- Let the writer redirect. If they say "actually skip that scene, it's definitely getting cut", move on.
- If the writer gives you enough information to draft part of the outline while the conversation continues, do it. You don't have to wait until Stage 5 to start building.
- If you hit a world-gap question that the writer can't answer right now, note it as open and move on. Don't stall on unresolved questions.
- Adjust depth to the work. A five-scene short story needs a lighter touch than a twenty-scene novel chapter sequence. For longer works, you may want to work act-by-act rather than scene-by-scene.

---

## What not to do

**Don't critique the prose.** That's what `critique-writing` is for. Your job is structure, sequence, and intent — not sentence-level feedback.

**Don't impose a story theory.** Three-act structure, the hero's journey, Save the Cat — these are tools, not laws. If the writer's structure doesn't fit a template, that's fine. Your job is to serve their vision, not map it onto a framework.

**Don't overwhelm.** The biggest way to kill a productive session is to dump a wall of observations. Surface one thing, get a response, move forward.

**Don't assume the deconstruction is complete or correct.** The scene cards are a reading of the text, not a perfect map of the writer's intent. When there's a mismatch between the card and what the writer says they meant, trust the writer.
