---
name: frontend-structure
description: The canonical folder structure for frontend/src — App Router route groups ((auth), (protected)), per-route _components folders, the shared src/components boundary, and naming rules. Use before creating, moving, renaming, or importing any file under frontend/src, and whenever deciding where a component, hook, type, or helper belongs.
---

# Frontend folder structure

`frontend/src` has one rule behind every other rule: **code lives as close to the route
that uses it as possible, and moves up only when a second route needs it.**

## The tree

```
frontend/src/
├── app/
│   ├── layout.tsx                     # root shell — html/body, fonts, chrome
│   ├── globals.css                    # Tailwind v4 theme + semantic tokens
│   ├── error.tsx  not-found.tsx
│   ├── page.tsx                       # public landing
│   │
│   ├── (auth)/                        # unauthenticated account routes
│   │   ├── layout.tsx                 # centred card shell, no app chrome
│   │   ├── _components/               # shared by EVERY auth route
│   │   │   ├── auth-card.tsx
│   │   │   └── auth-alt-action.tsx
│   │   ├── login/
│   │   │   ├── page.tsx
│   │   │   └── _components/
│   │   │       ├── login-form.tsx
│   │   │       └── login-form-fields.tsx
│   │   └── register/
│   │       ├── page.tsx
│   │       └── _components/
│   │           └── register-form.tsx
│   │
│   ├── (protected)/                   # requires a session
│   │   ├── layout.tsx                 # session guard + app shell
│   │   ├── _components/               # shared by EVERY protected route
│   │   │   ├── app-sidebar.tsx
│   │   │   └── app-topbar.tsx
│   │   ├── dashboard/
│   │   │   ├── page.tsx
│   │   │   ├── loading.tsx
│   │   │   ├── error.tsx
│   │   │   └── _components/
│   │   │       ├── campaign-list.tsx
│   │   │       ├── campaign-card.tsx
│   │   │       ├── campaign-card-metrics.tsx
│   │   │       ├── campaign-filters.tsx
│   │   │       └── campaign-empty-state.tsx
│   │   └── campaigns/
│   │       ├── _components/           # shared by campaigns/* only
│   │       │   └── campaign-status-badge.tsx
│   │       ├── new/
│   │       │   ├── page.tsx
│   │       │   └── _components/
│   │       └── [campaignId]/
│   │           ├── edit/
│   │           │   ├── page.tsx
│   │           │   └── _components/
│   │           │       ├── campaign-builder-form.tsx      # orchestrator
│   │           │       ├── builder-video-section.tsx
│   │           │       ├── builder-message-section.tsx
│   │           │       ├── builder-options-section.tsx
│   │           │       └── builder-actions.tsx
│   │           └── analytics/
│   │               ├── page.tsx
│   │               └── _components/
│   │                   ├── analytics-summary.tsx
│   │                   ├── analytics-metric-tile.tsx
│   │                   └── response-breakdown.tsx
│   │
│   └── preview/[campaignId]/          # public customer preview — no session
│       ├── page.tsx
│       └── _components/
│           ├── preview-player.tsx
│           ├── preview-message.tsx
│           └── preview-options.tsx
│
├── components/                        # CROSS-GROUP only
│   ├── ui/                            # primitives: button, card, badge, input, …
│   ├── layout/                        # site-header, site-footer
│   └── api-status.tsx
├── config/site.ts                     # static app config
├── lib/
│   ├── api/                           # client.ts, errors.ts, <resource>.ts, index.ts
│   ├── env.ts  format.ts  utils.ts
└── types/                             # api.ts, campaign.ts — shared contracts
```

Route groups `(auth)` and `(protected)` are parentheses-wrapped, so they shape the layout
tree without appearing in the URL: `app/(protected)/dashboard/page.tsx` serves
`/dashboard`. Folders prefixed with `_` are opted out of routing entirely — `_components`
is never a URL, which is exactly why colocation is safe.

## Where does this file go?

Answer in order; the first match wins.

1. **Is it a Next.js special file?** (`page` `layout` `loading` `error` `not-found`
   `template` `route` `default`) → the route folder itself, nowhere else.
2. **Used by exactly one route?** → that route's `_components/`. This is the default and
   most components end here. Do not "promote it early because it feels reusable."
3. **Used by 2+ routes inside one group?** → that group's `_components/`
   (`app/(protected)/_components/`), or the nearest shared parent segment
   (`app/(protected)/campaigns/_components/` for `new/` + `[campaignId]/edit/`).
4. **Used by 2+ groups and free of domain knowledge?** → `src/components/ui/`.
   A primitive knows about variants and sizes, never about campaigns.
5. **Used by 2+ groups and domain-aware?** → `src/components/<domain>/`, e.g.
   `src/components/campaign/`. Add the folder only when the second consumer actually
   exists.
6. **Site chrome rendered by a layout?** → `src/components/layout/`.

Non-component code follows the same ladder:

| Kind | One route | Shared |
| --- | --- | --- |
| Hook | `<route>/_hooks/use-campaign-form.ts` | `src/hooks/` |
| Helper, validation, mappers | `<route>/_lib/build-payload.ts` | `src/lib/` |
| Types local to a screen | `<route>/_types.ts` | `src/types/` |
| Server actions | `<route>/_actions.ts` | `src/lib/actions/` |
| HTTP calls | — | `src/lib/api/<resource>.ts` **always** |

## Import rules

- A page imports its own components relatively: `import { CampaignList } from "./_components/campaign-list"`.
- Everything crossing a folder boundary uses the alias: `@/components/ui/button`,
  `@/lib/api`, `@/types/campaign`.
- **Never import another route's `_components/`** — not with `../../`, not with `@/app/…`.
  If you want to, stop and promote the component per the ladder above, then import it
  through `@/`. A `../` climbing out of a `_components` folder is a structural bug.
- Nothing in `src/components/ui` imports from `app/`. Dependencies point downward only:
  `app/` → `components/` → `lib/` / `types/`.

## Naming

| Thing | Rule | Example |
| --- | --- | --- |
| File / folder | `kebab-case.tsx` | `campaign-card-metrics.tsx` |
| Component | named `PascalCase` export matching the file | `CampaignCardMetrics` |
| Dynamic segment | `[camelCase]` | `[campaignId]` |
| Hook | `use-*.ts` exporting `use*` | `use-campaign-form.ts` |
| Default export | Next.js special files only | `page.tsx` |

Useful suffixes that say what a component is without opening it: `-form`, `-list`,
`-card`, `-section`, `-empty-state`, `-skeleton`, `-badge`, `-tile`, `-actions`.

## Adding a route — the scaffold

```
app/(protected)/<segment>/
├── page.tsx          # fetch + compose, thin
├── loading.tsx       # skeleton, if the page awaits data
├── error.tsx         # "use client" boundary, if the fetch can fail
└── _components/      # every piece of this screen
```

A `page.tsx` reads params, calls `src/lib/api`, and composes named components. If it
contains a JSX block you would describe in a comment, that block is a component in
`_components/` instead.

```tsx
// app/(protected)/dashboard/page.tsx
import { listCampaigns } from "@/lib/api";

import { CampaignEmptyState } from "./_components/campaign-empty-state";
import { CampaignFilters } from "./_components/campaign-filters";
import { CampaignList } from "./_components/campaign-list";

export default async function DashboardPage({ searchParams }: PageProps<"/dashboard">) {
  const { status } = await searchParams;
  const campaigns = await listCampaigns({ status });

  return (
    <main className="mx-auto w-full max-w-5xl px-5 py-8">
      <CampaignFilters activeStatus={status} />
      {campaigns.length === 0 ? <CampaignEmptyState /> : <CampaignList campaigns={campaigns} />}
    </main>
  );
}
```

## Checklist before you finish

- [ ] Every new component sits in the nearest `_components/` that covers its consumers.
- [ ] Nothing route-specific leaked into `src/components/`.
- [ ] No import reaches sideways into another route's `_components/`.
- [ ] `page.tsx` composes; it does not contain the screen.
- [ ] File names are kebab-case and match their exported component.
- [ ] `npm run check` passes from `frontend/`.
