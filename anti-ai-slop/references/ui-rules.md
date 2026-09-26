# UI anti-slop: full rule catalog + named tells + delivery gate

Source: miqdadbadjuber/anti-slop (38 rules, 3 tiers) + Nutlope/hallmark (named tells). `antislop.md` is a **filter, not a style guide**: it imposes no aesthetic and bans no technique outright — it rejects technique WITHOUT purpose and requires liveliness. Direction (soul) comes from `DESIGN.md`/the user; this filters on top.

## Warning-sign scan (Part 1 — diagnostic, not a ban list)
Slop = many of these clustered with no reason.

**Visual/color:** generic blue-purple gradient, gradient-fill headline, excessive glassmorphism (blur on navbar+cards+modals+sidebar), everything pill-shaped, soft shadow on everything (page floats), glow everywhere, AI default palette (neon/pastel/radial orbs), background grid/dot/blueprint, trend-stacking, dark-mode-for-no-reason, 5–7 colors with no system, one accent color on everything, sterile flat white/thin-grey default, skeleton bars used as the product shot, pure #000/#fff.

**Layout/components:** monotonous Hero→Subtitle→2 CTAs→Screenshot→Feature grid→Testimonials→FAQ→CTA→Footer; identical copy-paste feature cards; bento grid as default; fake terminal window hero; uniform spacing; broken mobile; template animations (Fade Up/Floating/Scale/Bounce on all); "How It Works" always 3 steps; "Trusted By" logo bar under hero; "Most Popular" middle pricing card; always 3 pricing tiers; 4-col Product/Company/Resources/Legal footer; every section = centered title+subtitle+identical grid; card-in-card nesting; side-stripe cards; full-viewport centered hero.

**Copy:** em dash; generic CTAs (Get Started/Learn More/Try Now/Explore/Discover); buzzwords (AI Powered/Revolutionary/Next Generation/Seamless/Cutting Edge); fake stats (10K+ Users/99.9% Uptime); fake testimonials; fabricated trust claims (SOC 2/ISO 27001/300% faster); demo without a real product.

**Decoration:** generic AI icons (sparkle/star/magic/lightning/diamond/cube/robot/orb); Lucide-everywhere thin-stroke look; colored left stripe; → / ↗ on every button; AI capsule badges (pill+border+glow+dot+uppercase "AI Powered/Beta/New"); eyebrow badge above H1; large-monospace headings; HOW IT WORKS wide-tracking uppercase; typeface with no reason; Undraw/Storyset/3D-blob illustrations.

**Identity:** swap-the-logo-and-nothing-changes; clone of Linear/Vercel/Stripe/Notion.

## The 38 rules by tier

### Hard Gate (absolute — any breach = FAIL)
- R-02 no em dash in text (use , . : or ()). R-03 mobile perfect: no overflow, text stays in container, cards don't clip, 44px min tap. R-17 no numbers without a real source (empty > deceptive). R-18 no fake testimonials. R-23 ask before creating any asset (logo/avatar/stats/nav) or use a labeled placeholder. R-24 no navbar links to nonexistent destinations. R-25 WCAG AA contrast 4.5:1 normal / 3:1 large, tested across the whole area behind the text. R-26 every interactive element has real behavior or is removed. R-27 every data view has empty+loading+error states. R-28 no generic FAQ. R-32 keyboard: Tab/Enter/Space/Escape work, visible focus, never `outline:none` without replacement. R-33 no feature added by a script rewriting CSS/source — build in source. R-34 every shipped theme fully works in both modes. R-35 run/build + record a per-element click-through before declaring done. R-36 no fabricated security/compliance/performance claims. R-37 load direction (DESIGN.md/brand) or label output "draft without direction" + dials ENERGY 1/RHYTHM 1/MOTION 1. R-38 real content or explicitly-labeled placeholder.

### Purpose-Gate (technique allowed; FAILS as default without a written reason)
R-01 gradients/glow, R-04 icons (relevant, not library-look), R-06 typography (brand character not AI default Inter/Geist/Space Grotesk), R-07 background pattern, R-08 button arrows, R-09 badges (real status only), R-10 glassmorphism (≤1–2 elements; never navbar+card+modal+sidebar), R-12 shadow (elevation reason), R-13 glow (≤1–2 focus elements), R-14 feature cards (vary by hierarchy), R-19 animations (UX purpose + match MOTION dial), R-22 illustrations (product connection).

### Quality Locks (consistency)
R-05 no template layouts / 3-step How-It-Works / bento default / fake terminal / 3 pricing cols / 4-col footer / uniform section rhythm. R-11 radius variation, not all-pills. R-15 specific CTAs ("Start Your Free Trial", "Watch Live Demo"). R-16 no buzzwords. R-20 strong deliberate identity. R-21 dark mode by reason; build the toggle if unsure; never defer requested work. R-29 palette ≤2–3 core + 1 accent (neutrals excluded). R-30 don't clone popular products unasked. R-31 **keystone: write a one-line reason for every major decision** (color/layout/type/spacing/cards/icon); if you can't, revisit it.

## Liveliness Toolkit
Three dials, set explicitly, held section to section (three levels only — checkable):
- ENERGY 1 Linear/GOV.UK · 2 Stripe/Vercel · 3 Awwwards. "How hard does it say hello?"
- RHYTHM 1 uniform grid · 2 consistent w/ breaks · 3 asymmetric/mixed. "How much do sections differ?"
- MOTION 1 hover only · 2 scroll-reveal/transitions · 3 parallax/pin/choreography.
Levers: one focal point per screen; hierarchical contrast (size/weight/color on purpose); whitespace as structure; one deliberate accent (zero=sterile, everywhere=slop); one repeated identity motif.
Design Read (one line before generating): "Reading this as: <page kind> for <audience>, in a <visual language> style, dial ENERGY x/RHYTHM y/MOTION z."

## Craftsmanship standard (C-1..C-5)
Intentionality · Functional completeness · Content-driven composition · Resilience (state/theme/breakpoint/keyboard) · Evidence over claims.

## Delivery Gate (run BEFORE delivering; output PASS/FAIL, one line each, every PASS with evidence)
Block 1 Hard Gate — all answers **no**: em dash? mobile overflow/broken? stats without source? fake testimonials? assets made without instruction/placeholder? ghost navbar links? contrast < AA? dead controls? missing empty/loading/error? generic FAQ? not keyboard-navigable / no focus? feature added by patch script? a theme mode breaks? delivered without run + click-through? fabricated claims? built without direction and unlabeled? realistic fabricated content?
Block 2 Purpose-Gate — FAIL if technique appears as default with no written reason (R-01,04,06,07,08,09,10,12,13,14,19,22).
Block 3 Liveliness — all **yes**: dials set & explicit? output matches dials? ≥1 focal point per screen? whitespace structural? one deliberate accent? identity motif present? Design Read declared?
Block 4 Craftsmanship & Quality Locks — all **no**: any decision justified only by "AI default"? dead control? template-filler section? breaks in any state/theme/breakpoint/keyboard? fabricated stat/claim? template layout? all-pills? generic CTAs? buzzwords? generic if logo swapped? dark forced / toggle deferred? palette > 2–3+1? clone of popular product? any major decision with no one-line reason?
Any FAIL (or Block-3 "no") → fix, re-run, then ship. This gate cannot be delegated to another workflow's summary.
