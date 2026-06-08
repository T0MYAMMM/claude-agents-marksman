# UI Redesign Spec — "Warm Editorial" on shadcn/ui (new-york)

Redesign of the **Agent Orchestrator** Next.js dashboard from the current minimal slate / Tailwind v3
theme to a warm editorial aesthetic on **shadcn/ui (new-york)**, **Tailwind v4** (CSS-variable
`@theme inline`, no JS config), light + dark via **next-themes**, in a sidebar dashboard shell.

This is a spec only. No frontend code is changed by this document. Class patterns and token values are
given concretely so a frontend engineer can implement without guessing.

## 0. Current state (baseline being replaced)

- Next 14 App Router, Tailwind **v3** with a JS `tailwind.config.ts` (`surface`/`panel` colors), dark-only,
  `color-scheme: dark`, no theme toggle.
- Shell = `app/layout.tsx` with a plain top `<header>` + `max-w-6xl` `<main>`. No sidebar.
- Hand-rolled components: `ProjectCard`, `ProgressBar`, `StateBadge`, `FeedbackForm` (client + server
  action), `ApproveButton` (client), `MarkdownRenderer` (ToC + rehype-highlight), `CommitTimeline`.
- All data fetching is **server-side** in async server components via `src/lib/api-client.ts`
  (`cache: "no-store"`). Mutations go through `app/sessions/[id]/actions.ts` (`"use server"`). **This
  pattern is preserved exactly** — see §10.
- Types in `src/types/index.ts`: `Project`, `SessionSummary`, `SessionState` (8 states), `Commit`,
  `CommitType` (4), `Feedback`, `CommitPage`. No bookshelf types yet — added in §9.

The migration from Tailwind v3 → v4 means deleting `tailwind.config.ts` and `postcss.config` autoprefixer
setup, and moving all theme into `globals.css` via `@theme inline` (§1).

---

## 1. `globals.css` token block + font setup

### 1.1 Dependencies for the CSS layer

Tailwind v4 uses the PostCSS plugin `@tailwindcss/postcss` (replaces the v3 `tailwindcss` + `autoprefixer`
+ `postcss-import` chain). `postcss.config.mjs`:

```js
export default { plugins: { "@tailwindcss/postcss": {} } };
```

Delete `tailwind.config.ts`. Delete the `@tailwind base/components/utilities` directives and the
`@import "highlight.js/.../github-dark.css"` line from the current `globals.css` (highlight theming moves
to token-driven CSS, see §8).

### 1.2 `globals.css`

```css
@import "tailwindcss";
@import "tw-animate-css";

/* Tell v4 that .dark on an ancestor toggles dark variants (next-themes uses class strategy). */
@custom-variant dark (&:is(.dark *));

/* Fonts injected as CSS vars by next/font in layout.tsx (see §1.3). */

:root {
  --radius: 0.5rem;

  --background: oklch(0.992 0.004 83);
  --foreground: oklch(0.205 0.014 58);
  --card: oklch(1 0.002 83);
  --card-foreground: oklch(0.205 0.014 58);
  --popover: oklch(1 0.002 83);
  --popover-foreground: oklch(0.205 0.014 58);
  --primary: oklch(0.245 0.018 55);
  --primary-foreground: oklch(0.992 0.004 83);
  --secondary: oklch(0.955 0.01 80);
  --secondary-foreground: oklch(0.245 0.018 55);
  --muted: oklch(0.958 0.009 80);
  --muted-foreground: oklch(0.515 0.02 58);
  --accent: oklch(0.95 0.013 70);
  --accent-foreground: oklch(0.245 0.018 55);
  --brand: oklch(0.585 0.13 42);            /* terracotta */
  --brand-foreground: oklch(0.992 0.004 83);
  --destructive: oklch(0.577 0.245 27.325);
  --destructive-foreground: oklch(0.992 0.004 83);
  --border: oklch(0.9 0.011 74);
  --input: oklch(0.9 0.011 74);
  --ring: oklch(0.585 0.13 42);             /* focus ring uses brand */

  /* Sidebar slots (shadcn sidebar reads these). */
  --sidebar: oklch(0.985 0.006 82);
  --sidebar-foreground: oklch(0.205 0.014 58);
  --sidebar-primary: oklch(0.245 0.018 55);
  --sidebar-primary-foreground: oklch(0.992 0.004 83);
  --sidebar-accent: oklch(0.95 0.013 70);
  --sidebar-accent-foreground: oklch(0.245 0.018 55);
  --sidebar-border: oklch(0.9 0.011 74);
  --sidebar-ring: oklch(0.585 0.13 42);

  /* Editorial shadows. */
  --shadow-soft: 0 1px 2px oklch(0.205 0.014 58 / 0.05), 0 4px 12px oklch(0.205 0.014 58 / 0.04);
  --shadow-lift: 0 6px 24px oklch(0.205 0.014 58 / 0.10);
}

.dark {
  --background: oklch(0.175 0.01 58);
  --foreground: oklch(0.96 0.006 83);
  --card: oklch(0.213 0.012 58);
  --card-foreground: oklch(0.96 0.006 83);
  --popover: oklch(0.213 0.012 58);
  --popover-foreground: oklch(0.96 0.006 83);
  --primary: oklch(0.96 0.006 83);
  --primary-foreground: oklch(0.205 0.014 58);
  --secondary: oklch(0.27 0.014 58);
  --secondary-foreground: oklch(0.96 0.006 83);
  --muted: oklch(0.27 0.014 58);
  --muted-foreground: oklch(0.71 0.016 78);
  --accent: oklch(0.3 0.016 60);
  --accent-foreground: oklch(0.96 0.006 83);
  --brand: oklch(0.72 0.12 48);
  --brand-foreground: oklch(0.175 0.01 58);
  --destructive: oklch(0.577 0.245 27.325);
  --destructive-foreground: oklch(0.96 0.006 83);
  --border: oklch(1 0 0 / 0.1);
  --input: oklch(1 0 0 / 0.15);
  --ring: oklch(0.72 0.12 48);

  --sidebar: oklch(0.195 0.011 58);
  --sidebar-foreground: oklch(0.96 0.006 83);
  --sidebar-primary: oklch(0.96 0.006 83);
  --sidebar-primary-foreground: oklch(0.205 0.014 58);
  --sidebar-accent: oklch(0.3 0.016 60);
  --sidebar-accent-foreground: oklch(0.96 0.006 83);
  --sidebar-border: oklch(1 0 0 / 0.1);
  --sidebar-ring: oklch(0.72 0.12 48);

  --shadow-soft: 0 1px 2px oklch(0 0 0 / 0.3), 0 4px 12px oklch(0 0 0 / 0.25);
  --shadow-lift: 0 6px 24px oklch(0 0 0 / 0.45);
}

/* Map the CSS vars to Tailwind v4 utilities — no JS config. */
@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-brand: var(--brand);
  --color-brand-foreground: var(--brand-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);

  --color-sidebar: var(--sidebar);
  --color-sidebar-foreground: var(--sidebar-foreground);
  --color-sidebar-primary: var(--sidebar-primary);
  --color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
  --color-sidebar-accent: var(--sidebar-accent);
  --color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
  --color-sidebar-border: var(--sidebar-border);
  --color-sidebar-ring: var(--sidebar-ring);

  --font-sans: var(--font-hanken), ui-sans-serif, system-ui, sans-serif;
  --font-display: var(--font-fraunces), ui-serif, Georgia, serif;

  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);

  --shadow-soft: var(--shadow-soft);
  --shadow-lift: var(--shadow-lift);

  /* Editorial motion. */
  --ease-editorial: cubic-bezier(0.22, 1, 0.36, 1);
}

@layer base {
  * { @apply border-border outline-ring/50; }
  body {
    @apply bg-background text-foreground antialiased;
    font-family: var(--font-sans);
    /* Subtle grain texture over the warm bg. */
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.025'/%3E%3C/svg%3E");
  }
  h1, h2, h3, h4 {
    font-family: var(--font-display);
    font-weight: 600;
    letter-spacing: -0.018em;
  }
}

/* Editorial helpers reused across pages. */
@utility card-lift {
  transition: transform 0.28s var(--ease-editorial),
              box-shadow 0.28s var(--ease-editorial),
              border-color 0.18s var(--ease-editorial);
  box-shadow: var(--shadow-soft);
}
@utility card-lift-hover {   /* apply on hover: */
  transform: translateY(-4px);
  box-shadow: var(--shadow-lift);
}
```

> Notes: card hover = `-translate-y-1 hover:shadow-[var(--shadow-lift)] hover:border-brand/40` with
> `transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]`. Button press = `active:scale-[0.985]`
> (already baked into the shadcn button via an added variant, see §4). Quick interactions use `0.18s`,
> lifts use `0.28s`.

### 1.3 Fonts in `layout.tsx` (next/font/google)

```tsx
import { Hanken_Grotesk, Fraunces } from "next/font/google";

const hanken = Hanken_Grotesk({
  subsets: ["latin"],
  variable: "--font-hanken",
  display: "swap",
});
const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  display: "swap",
});
```

`<html lang="en" suppressHydrationWarning className={`${hanken.variable} ${fraunces.variable}`}>`,
then `<body>` wraps children in `<ThemeProvider>` (next-themes, `attribute="class"`,
`defaultTheme="system"`, `enableSystem`) and the sidebar shell (§3). Add `<Toaster />` (sonner) at the end
of `<body>`.

Display-serif usage: page titles `font-display text-2xl md:text-3xl`. Occasional editorial flourish:
section eyebrows / pull quotes may use `italic` Fraunces (`font-display italic`).

---

## 2. shadcn components + dependencies to install

Init shadcn with **style: new-york**, base color neutral, CSS variables on (it will respect the tokens
already placed in `globals.css`; do not let it overwrite them — review the diff).

```bash
npx shadcn@latest init        # style: new-york, RSC: yes, css vars: yes
npx shadcn@latest add button card badge input textarea sidebar dropdown-menu \
  tooltip separator scroll-area skeleton sonner tabs breadcrumb avatar
```

`empty-state` is not in the stock registry as one primitive — implement a small local
`components/ui/empty-state.tsx` (icon slot + title + description + optional action) following new-york
conventions, used by all empty states below.

Runtime deps to add: `next-themes`, `lucide-react`, `class-variance-authority`, `clsx`,
`tailwind-merge`, `sonner`, `@radix-ui/*` (pulled in by shadcn add), `tw-animate-css`.
Dev/build: `@tailwindcss/postcss`, `tailwindcss@4`. Remove: `autoprefixer`, `tailwindcss@3` JS config.
Keep existing markdown stack (`react-markdown`, `remark-gfm`, `rehype-highlight`, `rehype-slug`,
`highlight.js`).

`cn()` helper in `src/lib/utils.ts` (`clsx` + `tailwind-merge`) — standard shadcn.

---

## 3. Sidebar shell structure

Replace the current header/main in `layout.tsx`. Structure:

```
<ThemeProvider>
  <SidebarProvider>
    <AppSidebar />                         {/* components/layout/AppSidebar.tsx (client) */}
    <SidebarInset>
      <Topbar />                           {/* components/layout/Topbar.tsx (client) */}
      <main className="flex-1 p-4 md:p-6">
        <div className="mx-auto w-full max-w-6xl">{children}</div>
      </main>
    </SidebarInset>
  </SidebarProvider>
  <Toaster richColors />
</ThemeProvider>
```

**AppSidebar** (`Sidebar` collapsible="icon"):
- `SidebarHeader`: brand lockup — terracotta hexagon mark (lucide `Hexagon` filled `text-brand`) +
  wordmark "Agent Orchestrator" in `font-display`.
- `SidebarContent` → one `SidebarGroup` "Navigate" with `SidebarMenu`:
  - Dashboard → `/` — lucide `LayoutDashboard`
  - Projects → `/projects` (or `/` if no separate index; use `/`) — lucide `FolderGit2`
  - Bookshelf → `/bookshelf` — lucide `Library`
  Active item via `usePathname()` → `isActive` on `SidebarMenuButton` (brand-tinted: active uses
  `data-[active=true]:bg-sidebar-accent data-[active=true]:text-brand`).
- `SidebarFooter`: small muted build/version line.
- `SidebarRail` for drag-resize.

**Topbar** (sticky, `h-14 border-b bg-background/80 backdrop-blur`):
- left: `SidebarTrigger` + `Separator orientation="vertical"` + `Breadcrumb` (per-page, see each page).
- right: `ThemeToggle` (dropdown-menu with Light / Dark / System, lucide `Sun`/`Moon`/`Monitor`;
  client component using `useTheme`).

Because the sidebar/topbar are client components, **keep page bodies as server components** — they render
inside `SidebarInset` but are passed as `children`, so server data-fetching is unaffected (§10).

---

## 4. Button press + brand variant

Extend the generated shadcn `button.tsx` cva:
- add `active:scale-[0.985] transition-transform` to the base classes (motion: press feedback).
- add a `brand` variant: `bg-brand text-brand-foreground shadow-soft hover:bg-brand/90`.
Map usages: primary actions (Send feedback) → `variant="brand"`; Approve → `variant="default"` styled
success is unnecessary, use `brand` for the dominant CTA and `outline` for secondary. (Approve semantics
handled by a check icon + brand, not green — keeps the warm palette; success color only on the resulting
state badge.)

---

## 5. Per-page redesigns

Shared: every page renders an `<h1 className="font-display text-2xl md:text-3xl">` and sets its breadcrumb
via the Topbar (pass crumbs through a server-rendered `<PageHeader>` or a layout segment; simplest:
each page renders a `<Breadcrumb>`-feeding `PageHeader` server component at top).

### 5.1 Dashboard — `app/page.tsx`

- Breadcrumb: `Dashboard`.
- Header row: `PageHeader` with title "Projects" (`font-display`) + muted subtitle, and a `Badge variant="secondary"`
  showing `{projects.length} total` on the right.
- Grid: `grid gap-4 sm:grid-cols-2 lg:grid-cols-3` of **ProjectCard** rebuilt on shadcn `Card`:
  - `Card` with `card-lift` + hover `-translate-y-1 hover:border-brand/40 hover:shadow-[var(--shadow-lift)]`.
  - `CardHeader`: `CardTitle` (`font-display text-lg`) = project name; `CardDescription` =
    `line-clamp-2` description.
  - `CardContent`/`CardFooter`: muted row — lucide `FolderGit2` + truncated `gdrive_folder_id` (mono,
    first 12 chars) on the left, `Updated {date}` on the right. Whole card is a `<Link>`.
- **Empty state**: `EmptyState` with lucide `FolderPlus`, title "No projects yet", description "Projects
  appear here once registered with a Drive folder."
- **Loading**: add `app/loading.tsx` rendering 6 `Card` skeletons (`Skeleton` blocks for title + 2 lines +
  footer). API failure: keep the try/catch, but render `EmptyState` (icon `WifiOff`, destructive-tinted)
  reading "Could not reach the backend API…".

### 5.2 Project detail — `app/projects/[id]/page.tsx`

- Breadcrumb: `Dashboard / {project.name}`.
- Header: `PageHeader` title = project name (`font-display`), description as muted lead paragraph. A
  `Button variant="ghost"` "← All projects" is replaced by the breadcrumb (drop the inline back-link).
- Optional right-side meta: small `Badge`s for session count.
- Section heading "Sessions" as an eyebrow (`text-xs font-medium uppercase tracking-wide text-muted-foreground`).
- Sessions list → vertical stack of `Card`s (one per session), each a `<Link>` to `/sessions/[id]`:
  - left: session `title` (`font-medium`) + **StateBadge** (§7) inline; below, muted `started {date}`.
  - right: `ProgressBar` (rebuilt, §6) in a `w-40 shrink-0` column.
  - hover: `card-lift` lift + `hover:border-brand/40`.
- **Empty state**: `EmptyState` icon lucide `Bot`, "No agent sessions yet".
- **Loading**: `app/projects/[id]/loading.tsx` — header skeleton + 3 row skeletons.

### 5.3 Session / Topic Manager — `app/sessions/[id]/page.tsx`

- Breadcrumb: `Dashboard / {project} / {session.title}`.
- Header: title (`font-display`) + **StateBadge**, then a `max-w-md` ProgressBar.
- Two-column `grid gap-6 lg:grid-cols-2`:
  - **Review & Feedback** `Card`:
    - `CardHeader` eyebrow "Review & Feedback".
    - When `state === "WAITING_FOR_HUMAN"`: **FeedbackForm** using shadcn `Textarea` + `Button variant="brand"`
      (`useFormStatus` pending → "Sending…", spinner via lucide `Loader2 animate-spin`). On success the
      server action calls `revalidatePath`; add a `toast.success("Feedback sent")` via sonner triggered in
      the client form after the action resolves. `Separator` then **ApproveButton** (lucide `Check`,
      `variant="brand"`, success `toast`).
    - Otherwise: muted info block (use `EmptyState` compact variant, icon `Hourglass`): "Not awaiting review.
      Feedback can be injected when the state is WAITING FOR HUMAN."
    - Open feedback list: each item a subtle `rounded-md border bg-accent/40 px-3 py-2 text-sm` row with a
      lucide `MessageSquare` icon; uses `accent`/`muted-foreground`, not amber. A `Badge variant="outline"`
      shows count.
  - **Commit History** `Card`:
    - `CardHeader` eyebrow "Commit History" + `Badge` count.
    - `ScrollArea` (`max-h-[60vh]`) wrapping **CommitTimeline** (§ below).
- **CommitTimeline** rebuild: same vertical rail (`border-l border-border pl-6`); dot color per `CommitType`
  via brand-family tints (PLAN → `bg-brand`, REVISION → `bg-accent-foreground`, STAGE_REPORT →
  `bg-muted-foreground`, COMPLETION → `bg-[--color-state-completed]` green token from §7). Each node: mono
  `type` + `time` (muted), message in `text-foreground`, blocker count as `Badge variant="destructive"`
  (`{n} blockers`), artifact ref as a `<Link>` to `/artifacts/{gdrive_ref_id}` styled
  `text-brand hover:underline font-mono text-xs` (currently it is just text — make it a link).
- **Empty state**: timeline "No commits yet" via small muted note.
- **Loading**: `loading.tsx` — header skeleton + two `Card` skeletons with line skeletons.

### 5.4 Artifact Viewer — `app/artifacts/[fileId]/page.tsx`

- Breadcrumb: `… / Artifact / {fileId}` (or `Bookshelf / {category} / {book}` when opened from the shelf —
  pass via `?from=` search param; optional).
- Header: book/file title (if available) in `font-display`; the `gdrive_file_id` shown as a small mono
  `Badge variant="outline"`.
- Layout `grid gap-8 lg:grid-cols-[240px_1fr]`:
  - **ToC** left column inside a `ScrollArea` (`sticky top-20`), eyebrow "Contents", links
    `text-muted-foreground hover:text-brand`, active heading optional via scroll-spy (nice-to-have, can be
    deferred — keep static for v1).
  - **Article**: keep `MarkdownRenderer` but restyle the `.prose-md` rules with tokens — body
    `text-foreground/90 leading-relaxed`, links `text-brand`, inline code `bg-muted`, `pre` `bg-card border`,
    headings `font-display`. Use shadcn typography spacing. Swap the github-dark highlight import for a
    token-aware approach: import a neutral highlight.js theme and override a few `.hljs-*` colors in
    `globals.css` so it reads in both light and dark (or load `github.css` for light and `github-dark.css`
    scoped under `.dark`).
- **Empty/error**: artifact fetch failure → `EmptyState` (icon `FileWarning`, destructive tint):
  "Could not load artifact {fileId} from Google Drive."
- **Loading**: `loading.tsx` — ToC skeleton + paragraph skeletons.

### 5.5 NEW — Bookshelf browser

Route group `app/bookshelf/`:
- `app/bookshelf/page.tsx` — project picker (if entering globally): grid of project `Card`s (reuse
  ProjectCard styling) linking to `/bookshelf/[projectId]`. If the bookshelf is always project-scoped, this
  page lists projects with a `Library` icon accent.
- `app/bookshelf/[projectId]/page.tsx` — the shelf for one project.
- `app/bookshelf/[projectId]/[category]/page.tsx` — optional deep view of one category (full doc list);
  also usable as a `Tabs` panel target. v1 can render all categories on the project shelf page and treat
  `[category]` as an anchor; the route exists for direct linking.

**Shelf page layout (the "library" feel):**
- Breadcrumb: `Bookshelf / {project.name}`.
- Header: `font-display` title "{project} Library" + muted lead "Browse the project's living
  documentation."
- The 6 categories are fixed and ordered: **overview, architecture, guides, tutorials, reference, rules**.
  Each gets a section ("shelf") rendered as:
  - A **shelf header**: eyebrow row with a category icon (lucide: overview→`BookOpen`,
    architecture→`Network`, guides→`Compass`, tutorials→`GraduationCap`, reference→`BookMarked`,
    rules→`Scale`), the category name in `font-display text-lg`, and a `Badge variant="secondary"` with the
    doc count.
  - A **shelf surface**: the documents render as "book spines/cards" in a
    `grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`. Each book = a small `Card`
    (`card-lift`, hover `-translate-y-1 hover:border-brand/40`) that is a `<Link>` to
    `/artifacts/{fileId}?from=bookshelf`:
    - a thin left **spine accent**: `border-l-4 border-brand/60` (the warm "book spine"),
    - `CardTitle font-display text-base` = book/file title (strip `.md`),
    - muted footer: lucide `FileText` + last-modified date.
  - Visual library cue: under each shelf grid render a thin "shelf board" — a 2px
    `bg-gradient-to-r from-border to-transparent` rule with a faint `shadow-soft` — so rows read as physical
    shelves. A category with zero books renders a compact inline `EmptyState` ("No documents in {category}
    yet", muted, icon = the category icon).
- **Tabs option (alternative dense layout):** wrap the 6 categories in shadcn `Tabs`
  (`TabsList` = 6 triggers with icon+label, `TabsContent` = that category's book grid). Use Tabs on small
  screens, the stacked-shelf layout on `lg+`. Implementer may pick one; default recommendation = **stacked
  shelves** for the editorial library feel, Tabs as a `md:hidden`/`lg:hidden` fallback is optional.
- **Empty state (whole shelf)**: if the bookshelf folder is empty across all categories → full `EmptyState`
  (icon `LibraryBig`): "This bookshelf is empty. Documents added to the project's Drive folder will appear
  here, sorted into categories."
- **Loading**: `app/bookshelf/[projectId]/loading.tsx` — 6 shelf-header skeletons each with a row of 4 book
  skeletons.

---

## 6. ProgressBar rebuild

Keep the component API (`value: number`). Track = `bg-muted`, fill = `bg-brand` with
`transition-[width] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]`, `h-2 rounded-full`. Keep the
`role="progressbar"` aria attrs and the right-aligned `{pct}%` in `text-xs text-muted-foreground`. At
`value === 100` the fill may switch to the completed green token (§7) for a satisfying "done" cue.

---

## 7. StateBadge — token color mapping

Rebuild on shadcn `Badge`. Define 3 extra state tokens in `globals.css` `:root` and `.dark` (success /
warning / info), since the base palette has no green/amber/blue. Suggested light values (and dark in
parens):

```css
/* :root  (and .dark variants) */
--state-success:    oklch(0.62 0.13 150);   /* dark: oklch(0.72 0.13 152) */
--state-success-fg: oklch(0.99 0.004 83);   /* dark: oklch(0.18 0.01 58) */
--state-warning:    oklch(0.78 0.12 75);    /* dark: oklch(0.80 0.12 78) */  /* amber */
--state-warning-fg: oklch(0.24 0.018 55);   /* dark: oklch(0.18 0.01 58) */
--state-info:       oklch(0.62 0.11 240);   /* dark: oklch(0.70 0.10 240) */ /* slate-blue */
--state-info-fg:    oklch(0.99 0.004 83);   /* dark: oklch(0.18 0.01 58) */
```

Map each `SessionState` to a `Badge`-like pill. Pattern: `inline-flex rounded-full px-2.5 py-0.5 text-xs
font-medium` with a tinted background (`/15`) + solid-ish foreground, label = `state.replace(/_/g," ")`:

| State              | Token / class intent                                   | Reads as |
|--------------------|--------------------------------------------------------|----------|
| `INIT`             | `bg-muted text-muted-foreground`                       | neutral / idle |
| `PLANNING`         | `bg-[--state-info]/15 text-[--state-info]`             | info (in progress) |
| `WAITING_FOR_HUMAN`| `bg-[--state-warning]/20 text-[--state-warning-fg]` on `bg-[--state-warning]`-tint; effectively `bg-amber/20 text-amber-900` | warning — needs you |
| `REFINING`         | `bg-brand/15 text-brand`                               | brand (active terracotta) |
| `EXECUTING`        | `bg-[--state-info]/15 text-[--state-info]`             | info (running) |
| `COMPLETED`        | `bg-[--state-success]/15 text-[--state-success]`       | success |
| `FAILED`           | `bg-destructive/15 text-destructive`                   | error |
| `TERMINATED`       | `bg-muted text-muted-foreground line-through opacity-70`| stopped |

Implement as a `Record<SessionState, string>` of class strings (mirrors current `STYLES` map). The brand
terracotta is intentionally reserved for `REFINING` (the human-in-loop refinement) so the warm accent
signals "your input is shaping this".

---

## 8. Markdown / code-highlight theming

- Move `.prose-md` rules into `globals.css` rewritten against tokens (see §5.4).
- highlight.js: instead of importing `github-dark.css` globally, import `github.css` for base and override
  under `.dark` (or use a single theme and re-map `--hljs` colors). Inline code `bg-muted text-foreground`,
  fenced `pre` = `bg-card border border-border rounded-lg`. Headings get `scroll-mt-20` (preserved) and
  `font-display`.

---

## 9. New types (for Bookshelf)

Add to `src/types/index.ts` and a matching `api-client` method (server-side fetch, §10):

```ts
export type BookCategory =
  | "overview" | "architecture" | "guides" | "tutorials" | "reference" | "rules";

export interface Book {
  file_id: string;          // gdrive file id → /artifacts/[fileId]
  title: string;            // display name (filename minus .md)
  category: BookCategory;
  updated_at: string;
}

export interface Bookshelf {
  project_id: string;
  categories: Record<BookCategory, Book[]>;   // always all 6 keys, possibly empty arrays
}
```

`api.getBookshelf(projectId)` → `GET /projects/{id}/bookshelf` returning `Bookshelf`. The 6-category order
is enforced in the UI (constant array), not relied on from the API. Until the backend endpoint exists, the
shelf page may derive books from existing artifact listing — keep the fetch server-side regardless.

---

## 10. Keeping all data-fetching server-side (unchanged contract)

- Every `page.tsx` (Dashboard, Project, Session, Artifact, Bookshelf) stays an **async Server Component**
  calling `src/lib/api-client.ts` (`cache: "no-store"`). The sidebar/topbar being client components does
  **not** change this — they receive server-rendered `children`.
- Mutations stay in `app/sessions/[id]/actions.ts` (`"use server"`, `submitFeedbackAction`, `approveAction`)
  with `revalidatePath`. Client components (`FeedbackForm`, `ApproveButton`, `ThemeToggle`) only handle
  interaction + call bound server actions; they fetch **no** data directly.
- Add `loading.tsx` per route (Suspense-backed skeletons) rather than client loading state. Use
  `EmptyState` for empty/error branches inside the server component (the Dashboard/Artifact try/catch
  pattern is preserved).
- sonner toasts are fired client-side **after** a server action resolves (in the form/button client
  component) — purely presentational, no data fetch on the client.
- Theme is class-based via next-themes with `suppressHydrationWarning` on `<html>`; no server data
  involved. Keep `NEXT_PUBLIC_API_BASE` usage as-is.

---

## 11. Implementation order (suggested)

1. Tailwind v4 + tokens + fonts (§1), delete v3 config; verify build.
2. shadcn init + add components (§2), `cn()` util, button brand/press variant (§4).
3. Sidebar shell + theme toggle (§3) in `layout.tsx`.
4. Rebuild shared primitives: ProgressBar (§6), StateBadge (§7), EmptyState, PageHeader/Breadcrumb.
5. Restyle existing pages 5.1–5.4 + their `loading.tsx`.
6. Markdown/highlight theming (§8).
7. New types + bookshelf API (§9), then Bookshelf routes (§5.5).
8. Pass: dark-mode QA, focus rings (brand `--ring`), motion timings, grain texture legibility.
