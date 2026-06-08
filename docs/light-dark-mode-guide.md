---
type: guide
category: guides
title: Applying Light & Dark Mode to an existing Next.js project
version: 1.0
source: "design-system articles (Nathan Curtis) + light/dark theming + field experience"
---

# Applying Light & Dark Mode to an existing Next.js project

A practical, accessibility-first playbook for adding a Light / Dark / System theme to a
Next.js (App Router) app **without** the usual mess. It distills three lessons sources —
the "light/dark theming struggles" write-up, Nathan Curtis's *Color in Design Systems* and
*Light & Dark Color Modes in Design Systems* — plus hard-won field experience, into a
go-to recipe.

> TL;DR: put the theme class on `<html>`, tokenize **every** color as CSS custom
> properties, expose a Light/Dark/System switch that can't get stuck, and **validate WCAG
> contrast in both themes** before shipping.

## Why this is harder than it looks (the traps)

- **Specificity wars.** A `.dark-theme` class on `<body>` fighting a
  `@media (prefers-color-scheme)` query yields half-light/half-dark pages. Fix: one source
  of truth, applied high in the DOM (`<html>`).
- **Hardcoded colors everywhere.** If colors are baked into components, theming means
  rewriting two apps at once. Fix: tokens.
- **Not DRY.** Duplicated `body.light` / `body.dark` / media-query rules drift apart. Fix:
  define values once as variables; override only the variables per theme.

## The go-to stack

- **Next.js App Router** + **`next-themes`** (handles system preference, persistence, the
  `class` strategy, and SSR without flashes).
- **CSS custom properties** for *all* colors (works with or without Tailwind).
- **Tailwind v4** (`@theme inline` mapping vars → utilities) or v3 (colors backed by
  `hsl(var(--x))`). Optional **shadcn/ui** is already token-based and a good accelerator.

## Step 1 — Put the theme class on `<html>`, not `<body>`

```tsx
// app/layout.tsx
<html lang="en" suppressHydrationWarning>
  <body>
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      {children}
    </ThemeProvider>
  </body>
</html>
```

`next-themes` with `attribute="class"` toggles `class="dark"` (or `light`) on
`document.documentElement` — the cascade stays clean and specificity problems disappear.
`suppressHydrationWarning` avoids the server/client class-mismatch warning;
`disableTransitionOnChange` prevents a color-transition flash when switching.

## Step 2 — Tokenize EVERY color as CSS custom properties

Define a **semantic** token set in `:root`, override the same names in `.dark`. Never
hardcode a hex in a component — reference a token. Go beyond "bg/text" — model the types
the articles call for:

| Group | Tokens | Notes |
|-------|--------|-------|
| Surfaces | `background` (canvas), `card`/`popover` (layer 1), `muted` (subtle fill) | mind background-on-background contrast |
| Text | `foreground` (primary), `muted-foreground` (secondary), `interactive`/link, `destructive` (error); disabled via opacity | "type your types" |
| Borders | `border` (separators/hairlines), `input` (controls), `ring` (focus halo) | keep control strokes strong enough |
| Feedback | `success`, `warning`, `info`, `error` | reserve red/green/amber/blue meanings |

```css
:root {
  --background: oklch(0.99 0.004 83);
  --foreground: oklch(0.20 0.014 58);   /* primary text */
  --muted-foreground: oklch(0.50 0.02 58); /* secondary text */
  --card: oklch(1 0.002 83);
  --brand: oklch(0.55 0.13 42);         /* also used as link text — see Step 4 */
  --brand-foreground: oklch(0.99 0.004 83);
  --destructive: oklch(0.55 0.20 27);
  --border: oklch(0.90 0.011 74);
  --ring: var(--brand);
  --success: oklch(0.50 0.14 150);
  --warning: oklch(0.52 0.12 70);
  --info: oklch(0.52 0.14 245);
}
.dark {
  --background: oklch(0.175 0.01 58);
  --foreground: oklch(0.96 0.006 83);
  --muted-foreground: oklch(0.71 0.016 78);
  --card: oklch(0.213 0.012 58);
  --brand: oklch(0.72 0.12 48);
  --brand-foreground: oklch(0.175 0.01 58);
  --destructive: oklch(0.65 0.19 25);   /* lighter — see Step 4 */
  --border: oklch(1 0 0 / 0.1);
  --success: oklch(0.72 0.13 152);
  --warning: oklch(0.80 0.12 78);
  --info: oklch(0.70 0.10 240);
}
```

Tailwind v4 then maps them to utilities with no JS config:

```css
@custom-variant dark (&:is(.dark *));
@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-brand: var(--brand);
  /* …one line per token… */
}
```

Neutrals guidance (from the articles): **name tints by lightness** (`gray-05 … gray-95`),
**limit the count**, **avoid muddy medium grays**, and consider **cool slate/charcoal**
neutrals over flat grays.

## Step 3 — A Light / Dark / System switch that can't get stuck

```tsx
"use client";
import { useEffect, useState } from "react";
import { Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

const OPTIONS = [
  { value: "light", icon: Sun }, { value: "system", icon: Monitor }, { value: "dark", icon: Moon },
] as const;

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []); // gate active state to avoid hydration mismatch
  return (
    <div role="group" aria-label="Theme" className="inline-flex gap-0.5 rounded-full border bg-card p-0.5">
      {OPTIONS.map(({ value, icon: Icon }) => (
        <button key={value} type="button" aria-label={value} aria-pressed={mounted && theme === value}
          onClick={() => setTheme(value)}
          className={mounted && theme === value ? "bg-brand text-brand-foreground rounded-full p-1.5" : "text-muted-foreground p-1.5"}>
          <Icon className="size-4" />
        </button>
      ))}
    </div>
  );
}
```

**Field-tested gotcha:** prefer **three always-visible buttons** over a dropdown menu. A
popup whose positioning library fails to run renders the menu **off-screen and unclickable**
— the user appears "stuck" on whatever theme they were on, with no way out. Inline buttons
can't get stuck and make the current choice obvious. Always gate the active highlight on a
`mounted` flag, since `theme` is only known on the client.

## Step 4 — Validate WCAG contrast in BOTH themes (the step everyone skips)

Targets: **AA = 4.5:1** for normal text, **3:1** for large/bold text and UI components.
Use a tool (EightShapes **Contrast Grid**, `contrast-grid.eightshapes.com`) or compute the
ratio yourself. The articles' rule: *check early and ritually*, and **explore a range** to
"tune the dial" rather than guess.

The recurring failure modes (you *will* hit these):

1. **A mid-tone brand/accent fails as link text — and as a white-backed button.** Those are
   the *same symmetric pair* (`brand` vs near-white). Darken the brand in **light** mode
   until both pass (≈ L 0.55 for a terracotta hits ~5:1). Keep a separate, lighter brand in
   dark mode.
2. **Red error text fails on a dark canvas.** A single saturated red can't be both readable
   text on dark *and* a white-label badge. Fix: **lighten** the dark-mode red so text passes
   on the canvas, and put a **dark label** on the lighter red badge.
3. **Amber/light feedback colors fail as text on a pale background.** Make feedback tokens
   **dark enough in light mode and light enough in dark mode** — the "solve the reverse
   light-on-dark / dark-on-light" lesson. Don't use a near-white "foreground" token as text
   on a subtle tint in dark mode (it lands on a dark surface and disappears).

Quick contrast computation (OKLCH → sRGB → WCAG), handy in a build/CI check:

```python
import math
def _lin(L,C,h):
    a,b=C*math.cos(math.radians(h)),C*math.sin(math.radians(h))
    l=(L+0.3963377774*a+0.2158037573*b)**3; m=(L-0.1055613458*a-0.0638541728*b)**3; s=(L-0.0894841775*a-1.2914855480*b)**3
    R=4.0767416621*l-3.3077115913*m+0.2309699292*s; G=-1.2684380046*l+2.6097574011*m-0.3413193965*s; B=-0.0041960863*l-0.7034186147*m+1.7076147010*s
    return [max(0,min(1,x)) for x in (R,G,B)]
def lum(c): R,G,B=_lin(*c); return 0.2126*R+0.7152*G+0.0722*B
def contrast(fg,bg):
    a,b=lum(fg),lum(bg); hi,lo=max(a,b),min(a,b); return (hi+0.05)/(lo+0.05)
# contrast((0.55,0.13,42),(0.99,0.004,83)) -> ~5.0  (brand link on light canvas: PASS)
```

## Step 5 — Weave tokens through the components

- **Find leftovers:** `grep -rE '#[0-9a-fA-F]{3,6}|slate-|gray-[0-9]'` and replace with token
  utilities (`bg-background`, `text-muted-foreground`, `border-border`, …).
- **States via opacity** (article-endorsed): hover/active as `bg-accent`, `/10`–`/20` tints,
  or `hover:opacity-90` rather than hand-picked per-theme colors.
- **Backgrounds on backgrounds:** when a card sits on a near-equal surface, add a subtle
  `border` or `shadow` instead of relying on color contrast alone.
- **Reverse pairings:** for every token, confirm it works *both* dark-on-light and
  light-on-dark before shipping.

## Definition of done (checklist)

- [ ] Theme class is on `<html>`; `defaultTheme="system"` + `enableSystem`.
- [ ] Light / Dark / System switch works, shows the active choice, and **can't get stuck**.
- [ ] No hardcoded colors remain (`grep` is clean).
- [ ] Every text / badge / border / link pair passes **AA in both themes** (verified, not
      eyeballed).
- [ ] Toggling flips cleanly — no half-themed regions, no transition flash
      (`disableTransitionOnChange`).
- [ ] Tokens are documented; contrast rationale is commented where a value was tuned.
