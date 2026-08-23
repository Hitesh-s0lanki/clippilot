---
name: frontend-component
description: How to write a React component in frontend/src — size budgets, when and how to split a screen into sub-components instead of one long file, server/client boundaries, props and state placement, required loading/empty/error states, and styling with the semantic Tailwind tokens. Use when writing, extending, or refactoring any .tsx component, and whenever a file is growing past a screenful.
---

# Writing components

Companion to `frontend-structure`, which decides *where* a file goes. This decides *what
goes in it* — and above all, keeps one screen from becoming one file.

## Size budgets

| File | Soft cap | What it means |
| --- | --- | --- |
| `page.tsx` | ~60 lines | Params, one data call, composition. Nothing else. |
| Component | ~150 lines | Past this, a section wants its own file. |
| Anything | 200 lines | Hard stop — split before adding a line. |
| Exports per file | 1 component | Plus its own `Props` type. That is all. |

Caps are a smoke alarm, not the fire. Split on responsibility, not on line count.

## Split when any of these is true

- The file exports, or wants to export, a second component.
- A JSX block would need a comment to explain what it is — that comment is the new
  component's name.
- Nesting passes ~4 levels of JSX.
- A `.map()` callback body grows past ~15 lines — the row is a component.
- The same markup shape appears twice.
- A section has its own state that nothing else in the file reads.
- Part of the file needs `"use client"` and the rest does not. Split so the client half is
  as small as possible.

## Don't split when

- The piece is under ~30 lines and is only ever edited together with its parent.
- The extraction would be a pass-through wrapper that adds a name and nothing else.
- You would have to lift state up and thread 6 props down to do it. Draw the boundary
  where the data already is.

## The shape of a screen

One orchestrator that owns layout and shared state, several leaf sections that own their
own markup. The campaign builder is the canonical case — one form, five files:

```
app/(protected)/campaigns/[campaignId]/edit/_components/
├── campaign-builder-form.tsx     "use client" — form state, submit, section order
├── builder-video-section.tsx     video URL field + preview thumbnail
├── builder-message-section.tsx   message textarea + {{customer_name}} hint
├── builder-options-section.tsx   option 1 / option 2 label + response pairs
└── builder-actions.tsx           Save as Draft / Publish + pending state
```

```tsx
// campaign-builder-form.tsx — the orchestrator holds state, not markup
"use client";

export function CampaignBuilderForm({ campaign }: CampaignBuilderFormProps) {
  const { values, errors, setField, submit, pending } = useCampaignForm(campaign);

  return (
    <form onSubmit={submit} className="flex flex-col gap-6">
      <BuilderVideoSection value={values.videoUrl} error={errors.videoUrl} onChange={setField} />
      <BuilderMessageSection value={values.message} error={errors.message} onChange={setField} />
      <BuilderOptionsSection options={values.options} errors={errors.options} onChange={setField} />
      <BuilderActions pending={pending} status={campaign.status} />
    </form>
  );
}
```

Each section renders fields and errors and knows nothing about submitting. The form logic
itself belongs in `_hooks/use-campaign-form.ts`, not inline — a component file holds
markup, a hook file holds behaviour.

## Server and client

- Server Component by default. No directive at the top of most files.
- `"use client"` goes on the **smallest leaf** that needs state, effects, refs, browser
  APIs, or event handlers. Never on a `layout.tsx` or a `page.tsx`.
- A client component can receive server-rendered `children`. Use that instead of pulling
  a whole subtree across the boundary.
- Data fetching happens in the server `page.tsx` (or a server action) through
  `src/lib/api`. A presentational component receives data as props and never calls
  `fetch` itself.
- Props crossing the server→client boundary must be serialisable — plain objects, no
  class instances, no functions.

## Props and state

- Props interface named `<Component>Props`, exported next to the component.
- Prefer 2–5 props. More usually means the component is doing two jobs, or that an object
  from `src/types` should be passed whole (`campaign: Campaign`) instead of field by field.
- No boolean soup. Three `isX` flags that are mutually exclusive want one `variant` union.
- State lives at the lowest node that needs it. Lift only when a sibling needs to read it.
- Derive, do not duplicate: compute from props during render rather than mirroring props
  into `useState` and syncing with an effect.

## Every data-driven surface ships four states

The brief is graded on this. A list or a fetch is not done until it handles:

1. **Loading** — a `loading.tsx` skeleton for the route, or a `-skeleton.tsx` component
   for an inner region. Not a bare spinner where a shape is possible.
2. **Empty** — a `-empty-state.tsx` with a sentence explaining what to do and the action
   that does it.
3. **Success** — the real content.
4. **Error** — an `error.tsx` boundary with a retry, and inline field errors on forms.
   Surface the message from `ApiError`; never a silent failure.

## Styling

- Tailwind utilities only, in `className`. No CSS modules, no inline `style` objects
  except for genuinely dynamic values.
- Use the semantic tokens defined in `src/app/globals.css`. They already have a dark
  variant; raw palette values (`bg-slate-800`, `#131318`) do not, and are a review finding.

  | Purpose | Tokens |
  | --- | --- |
  | Surfaces | `bg-background` `bg-card` `bg-popover` `bg-muted` `bg-accent` |
  | Text | `text-foreground` `text-card-foreground` `text-muted-foreground` |
  | Borders | `border-border` `border-input`, focus ring `ring-ring` |
  | Brand | `bg-primary` `text-primary` `text-primary-foreground` |
  | Status | `destructive`, plus `success` and `warning`; use `/10` for a chip fill |
  | Charts | `text-chart-1` … `text-chart-5` |
  | Shape | `rounded-md` `rounded-lg` `rounded-xl`, all derived from `--radius` |
- Merge classes with `cn()` from `@/lib/utils` so a caller's utility can win.
- Variants come from `cva()`, the way the vendored shadcn components in
  `src/components/ui/` declare them. No ternary chains inside `className`.
- Mobile first: base styles are the phone layout, `sm:`/`md:`/`lg:` add the desktop one.

## Accessibility, non-negotiable

- Semantic elements first: `button` for actions, `a`/`Link` for navigation, real `label`
  bound to every input via `htmlFor`/`id`.
- Errors linked with `aria-describedby` and marked `aria-invalid`.
- Icon-only controls carry `aria-label`; decorative marks carry `aria-hidden`.
- Every interactive element is keyboard reachable with a visible focus ring.
- `alt` on informative images, `alt=""` on decorative ones.

## Before you finish

- [ ] No file over 200 lines; no file exporting two components.
- [ ] `page.tsx` composes named components and holds no screen markup.
- [ ] `"use client"` appears only on leaves that need it.
- [ ] Loading, empty, success and error states all exist.
- [ ] Semantic tokens, not raw colours; `cn()` for merging.
- [ ] Labels, focus states and keyboard paths checked.
- [ ] `npm run check` passes from `frontend/`.
