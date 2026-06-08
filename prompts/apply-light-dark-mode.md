# Apply light & dark mode prompt (copy-paste ready)

Open Claude Code CLI **at the root of the Next.js project** you want to theme, then paste
the fenced block below. It reads the authoritative guide from its URL and applies a
Light / Dark / System theme accessibly. The machine must be on the Tailscale tailnet to
fetch the guide.

---

```
You are a frontend engineer. Add an accessible Light / Dark / System theme to THIS Next.js
project (the repository in your current working directory), following the authoritative
guide exactly.

## Step 0 — Read the guide FIRST
Fetch and read it; it defines the approach, the token taxonomy, the non-fragile theme
switch, and the WCAG contrast rules. Obey it.
  GET https://edts025131.iguana-wezen.ts.net/api/v1/artifacts/1uhIcVDol3XEMo6rHElC_luH-87zSvf07
(It returns {"content":"<markdown>"} — read the content.)

## Step 1 — Inventory the current setup (do not assume)
Detect: Next.js version + App or Pages Router; Tailwind (v3 vs v4) or plain CSS/CSS-modules;
whether next-themes / shadcn/ui are already present; where colors are defined today (grep
for hex `#`, `rgb(`, `hsl(`, `slate-`, `gray-[0-9]`, and any existing `.dark`/`prefers-color-scheme`).
Write down what exists so you extend it rather than duplicate it.

## Step 2 — Theme at the <html> level
Install/keep `next-themes`. Wrap the app (root layout) in a ThemeProvider with
attribute="class", defaultTheme="system", enableSystem, disableTransitionOnChange; add
suppressHydrationWarning on <html>. The class must land on <html> (documentElement), never
<body>. Remove any conflicting body-level theme classes or bare prefers-color-scheme rules
that would fight it.

## Step 3 — Tokenize EVERY color
Define semantic CSS custom properties in :root and override the SAME names under .dark.
Replace hardcoded colors in components with token references. Cover the full taxonomy:
surfaces (background/card/muted), text types (foreground/muted-foreground/interactive/
destructive + disabled via opacity), borders (border/input/ring), feedback (success/warning/
info/error). Name neutral tints by lightness; avoid muddy medium grays. If the project uses
Tailwind v4, map vars via @theme inline; v3, back the theme colors with hsl(var(--x)).

## Step 4 — A switch that CAN'T get stuck
Add a Light / Dark / System control. Prefer three always-visible segmented buttons over a
dropdown menu — a popup whose positioning fails renders off-screen and unreachable, trapping
the user on one theme. Show the active choice; gate the active state on a mounted flag to
avoid a hydration mismatch.

## Step 5 — Validate WCAG contrast in BOTH themes (do not skip)
Target AA: 4.5:1 normal text, 3:1 large/UI. Check every text / link / badge / border pair in
light AND dark. Fix the known failure modes from the guide:
- a mid-tone brand/accent failing as link text AND as a white-backed button (darken it in light);
- red error text failing on a dark canvas (lighten it in dark; dark label on the lighter badge);
- amber/light feedback colors failing as text on a pale canvas (dark in light, light in dark).
Compute ratios (don't eyeball) — use the contrast function in the guide or a Contrast Grid.
Tune lightness until each pair passes, then record the rationale in a comment.

## Step 6 — Weave tokens through components & verify
- Replace remaining hardcoded colors (re-grep until clean). States via opacity/tint utilities.
- For cards on near-equal surfaces, add a subtle border/shadow rather than relying on color alone.
- Run `npx tsc --noEmit` and the project's build; both must pass.
- Manually toggle Light/Dark/System: the whole UI flips cleanly with no half-themed regions
  and no transition flash.

## Definition of done
Theme class on <html>; system + a switch that works and can't get stuck; zero hardcoded
colors; every pair passes AA in both themes (verified, not eyeballed); build + typecheck
green. Summarize what you changed and the contrast values you tuned.
```

---

The guide it reads in Step 0 is `docs/light-dark-mode-guide.md`, published at the URL above.
