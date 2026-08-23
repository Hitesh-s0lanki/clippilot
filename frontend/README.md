# ClipPilot Frontend

Next.js App Router client for the ClipPilot interactive video campaign builder.

## Requirements

- Node.js 20.9+ (22 LTS recommended)
- npm 10+

## Setup

```bash
cd frontend
npm install
cp .env.example .env.local   # defaults point at http://localhost:8000
```

Then add Clerk keys to `.env.local`. Create an application at
[dashboard.clerk.com](https://dashboard.clerk.com) and copy both keys from
**API keys -> Next.js**:

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

The app will not start without the publishable key - `lib/env.ts` fails fast
and names the variable rather than letting Clerk throw from inside the SDK.

Point the backend at the **same** Clerk application, or every campaign request
comes back `401`. In `backend/.env`:

```bash
CLERK_ISSUER=https://<your-subdomain>.clerk.accounts.dev
CLERK_JWKS_URL=https://<your-subdomain>.clerk.accounts.dev/.well-known/jwks.json
```

The backend must be running for anything beyond the static shell:

```bash
cd ../backend && uv run uvicorn src.main:app --reload
```

## Run

```bash
npm run dev      # http://localhost:3002
npm run build    # production build
npm run start    # serve the production build
```

The home page probes `GET /healthz` on every request, so a stopped API or a
wrong `NEXT_PUBLIC_API_BASE_URL` shows up immediately rather than as an empty
screen three clicks later.

## Quality gates

```bash
npm run lint          # eslint (next/core-web-vitals + typescript)
npm run typecheck     # tsc --noEmit
npm run format        # prettier --write .
npm run format:check  # prettier --check .
npm run check         # all three, in the order CI would run them
```

## Architecture

Each layer depends only on the one beneath it. Route files stay thin, so the
data and formatting rules are testable without rendering a page, and moving a
screen is a change of directory rather than a rewrite.

```
route (src/app)            URL -> composition, nothing else
   ↓
components                 presentation; props in, markup out
   ↓
lib/api                    typed calls to the backend, one place per resource
   ↓
lib/env · types            configuration and the wire contract
```

```
frontend/
├── components.json                    # shadcn/ui registry config (radix + nova style)
├── src/
│   ├── proxy.ts                       # Clerk session check (Next 16's middleware)
│   ├── app/                           # routing layer - App Router files only
│   │   ├── layout.tsx                 # html/body, fonts, Clerk + theme providers - no chrome
│   │   ├── page.tsx                   # console home; renders its own header + footer
│   │   ├── error.tsx                  # route-level boundary for uncaught errors
│   │   ├── not-found.tsx              # 404
│   │   ├── globals.css                # design tokens + Tailwind entry
│   │   ├── (auth)/                    # account routes - no session required
│   │   │   ├── layout.tsx             # centred shell around Clerk's own card
│   │   │   ├── _components/           # shared by both account routes
│   │   │   ├── login/[[...login]]/    # <SignIn>; catch-all for Clerk's sub-steps
│   │   │   └── register/[[...register]]/
│   │   └── (protected)/               # session required
│   │       ├── layout.tsx             # auth.protect() guard + the app shell
│   │       └── dashboard/
│   ├── components/
│   │   ├── ui/                        # shadcn/ui primitives - vendored, editable
│   │   ├── layout/                    # chrome: header, footer, auth nav, theme toggle
│   │   └── api-status.tsx             # shared composed component, server-rendered
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts              # fetch wrapper: base URL, query, timeout, JSON, bearer
│   │   │   ├── errors.ts              # ApiError + envelope parsing
│   │   │   ├── health.ts              # GET /healthz
│   │   │   ├── session.ts             # server-only: Clerk token -> Authorization header
│   │   │   └── index.ts               # public surface of the API layer
│   │   ├── env.ts                     # validated environment access
│   │   ├── format.ts                  # dates, rates, money, durations
│   │   └── utils.ts                   # cn()
│   ├── types/
│   │   ├── api.ts                     # error envelope
│   │   └── campaign.ts                # campaign wire types
│   ├── config/site.ts                 # product copy and navigation
│   └── app/icon.png · apple-icon.png  # favicons, cropped from the logo
└── public/
    ├── logo.png                       # source illustration, 1254px (kept for re-crops)
    └── logo-mark.png                  # the mark: logo.png cropped to the clapperboard
```

Chrome is not global. The root layout is providers only; `(protected)` renders
the header and footer as the app shell, the landing page renders its own, and
`(auth)` renders none - a global header would put "Sign in" and "Get started"
buttons on top of the sign-in page itself.

Screens colocate: every route owns a `_components/` folder next to its
`page.tsx`, and a component moves up to the group or to `src/components/` only
when a second route needs it. The full rule set - route groups, the `_components`
ladder, naming and import boundaries - is the `frontend-structure` skill in
[`.claude/skills/`](../.claude/skills/), and component-level rules (size budgets,
server/client split, the four required states) are `frontend-component`.

### Conventions

- **Server Components by default.** `"use client"` is added at the leaf that
  actually needs state or an event handler, not at the top of a page.
- **`snake_case` on the wire, unchanged in the client.** `src/types/campaign.ts`
  mirrors the API exactly; renaming keys on the way in only creates two
  vocabularies for one field.
- **Raw values in, formatted values out.** Rates arrive as decimals and money as
  integer minor units; every human-readable form comes from `lib/format.ts`, so
  one number never renders two ways.
- **Design tokens, not hex codes.** Colours and radii are declared once in
  `globals.css` and used as utilities (`bg-card`, `text-muted-foreground`,
  `border-border`), which is what keeps light and dark in step.

## Component library

[shadcn/ui](https://ui.shadcn.com) on Radix primitives, configured in
[`components.json`](components.json). Components are **vendored, not installed** -
the CLI copies source into `src/components/ui/`, and that source is ours to edit.

```bash
npx shadcn@latest add <component>     # e.g. popover, checkbox, calendar
npx shadcn@latest add <component> -o  # re-pull and overwrite a local edit
```

Already vendored: `accordion` `alert` `badge` `button` `card` `dialog`
`dropdown-menu` `input` `label` `select` `separator` `skeleton` `sonner`
`table` `tabs` `textarea` - the set the dashboard, builder, preview and
analytics screens need.

### Theme

The palette is the ClipPilot one, expressed under shadcn's canonical token names
so every component pulled from the registry inherits the product's look with no
edits. There is **one** set of tokens, defined in `src/app/globals.css`:

| Purpose         | Tokens                                                                 |
| --------------- | ---------------------------------------------------------------------- |
| Surfaces        | `background` `card` `popover` `muted` `accent`                         |
| Text            | `foreground` `card-foreground` `muted-foreground`                      |
| Brand           | `primary` + `primary-foreground`                                       |
| Feedback        | `destructive`, plus `success` and `warning` (ClipPilot additions)      |
| Lines and focus | `border` `input` `ring`                                                |
| Charts          | `chart-1` … `chart-5`, spaced around the wheel to stay distinguishable |
| Shape           | `--radius`, driving `rounded-sm` … `rounded-4xl`                       |

Each has a light value on `:root` and a dark value on `.dark`. `success` and
`warning` are the two shadcn does not ship; the campaign lifecycle needs them,
and `badge.tsx` carries matching variants.

Dark mode is class-based through `next-themes`, defaulting to the operating
system setting, with a toggle in the header. The class strategy is what makes
the `dark:` utilities inside every shadcn component controllable rather than
locked to the OS.

## Authentication

Clerk owns sign-up, sign-in, sessions and the user record. Neither this app nor
the backend ever stores a credential: the backend only verifies the session JWT
Clerk minted, against Clerk's JWKS, and reads `sub` into `campaigns.owner_user_id`.
There is no users table and no auth endpoints.

```
browser  ──▶ src/proxy.ts          clerkMiddleware; anonymous requests never reach a route
             (protected)/layout    auth.protect() - the second lock, on the route tree
             lib/api/session.ts    auth().getToken()
         ──▶ Authorization: Bearer <jwt>
             FastAPI               ClerkVerifier checks the signature, reads `sub`
```

**Route access** is deny-by-default. `src/proxy.ts` lists what is public - the
landing page, `/login`, `/register` and the recipient `/preview` routes - and
protects everything else, so a new screen is private because nobody added it to
that list. Next.js 16 renamed Middleware to Proxy; the file sits in `src/`
beside `app/`, which is where Next looks for it.

**Calling the API.** `lib/api/session.ts` is the one place that moves the token
from Clerk to the backend. It is server-only, and resolves the token per
request - caching it at module scope would hand one session to whoever asked
next:

```ts
import { api } from "@/lib/api";
import { getSessionToken } from "@/lib/api/session";

const campaigns = await api.get<CampaignPage>("/campaigns", {
  token: await getSessionToken(),
});
```

Mutations belong in Server Actions for the same reason - they can call
`getSessionToken()` directly, so the JWT never has to reach the browser bundle.
The recipient-facing `/public/*` routes take no token at all.

**Components.** Clerk Core 3 removed `<SignedIn>`, `<SignedOut>` and
`<Protect>`; the replacement is `<Show when="signed-in">`, used in
`components/layout/auth-nav.tsx`. `<ClerkProvider>` must sit inside `<body>`,
not around `<html>`.

**Dark mode** needs no Clerk theme package. Core 3 reads the page's CSS
`color-scheme`, which `globals.css` sets on `:root` and `.dark` - the same class
next-themes toggles - so Clerk's card follows the header toggle on its own.

## API layer

`api.get` / `.post` / `.patch` / `.put` / `.delete` resolve with the parsed body
or throw an `ApiError`. There is no `{ data, error }` tuple to unpack, so calls
compose with `try/catch` and React error boundaries.

```ts
import { api, isApiError } from "@/lib/api";
import type { Campaign } from "@/types/campaign";

try {
  const campaign = await api.get<Campaign>(`/campaigns/${id}`);
} catch (error) {
  if (isApiError(error) && error.code === "VALIDATION_ERROR") {
    setFieldErrors(error.fieldErrors()); // { "experience.options.0.label": "..." }
  }
}
```

The client handles the parts every call would otherwise repeat:

| Concern       | Behaviour                                                                               |
| ------------- | --------------------------------------------------------------------------------------- |
| Base URL      | `NEXT_PUBLIC_API_BASE_URL` in the browser, `API_BASE_URL` on the server when set        |
| Authorization | `token` option becomes `Authorization: Bearer`; omitted when `null`                     |
| Versioning    | `/api/v1` prefix by default; `versioned: false` for root routes like `/healthz`         |
| Query strings | `query` object, skipping `undefined` and `null`                                         |
| Timeouts      | 10s default, composed with any caller-supplied `AbortSignal`                            |
| Errors        | Backend envelope parsed into `ApiError`; non-JSON failures become `UNEXPECTED_RESPONSE` |
| Empty bodies  | `204` and zero-length responses resolve rather than fail to parse                       |

`ApiError.fieldErrors()` flattens `details[]` into a `field -> message` map,
which is the form the builder needs when publishing returns every unmet
requirement at once.

## Environment variables

See [`.env.example`](.env.example).

| Variable                                          | Default                      | Notes                                                   |
| ------------------------------------------------- | ---------------------------- | ------------------------------------------------------- |
| `NEXT_PUBLIC_API_BASE_URL`                        | `http://localhost:8000`      | Browser-visible; **inlined at build time**              |
| `API_BASE_URL`                                    | falls back to the public URL | Server-side override for split networks                 |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`               | none - **required**          | Clerk frontend key; the app refuses to start without it |
| `CLERK_SECRET_KEY`                                | none - **required**          | Clerk backend key; never exposed to the browser         |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL`                   | `/login`                     | Also read back by `env.authRoutes`                      |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL`                   | `/register`                  | Also read back by `env.authRoutes`                      |
| `NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL` | `/dashboard`                 | Used when there is no `redirect_url`                    |
| `NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL` | `/dashboard`                 | Used when there is no `redirect_url`                    |

`NEXT_PUBLIC_*` values are baked into the bundle by `next build`, so a deployed
build must be rebuilt — not just restarted — to point at a different API.

## Deployment

```bash
npm ci
NEXT_PUBLIC_API_BASE_URL=https://api.example.com \
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_... \
  npm run build
CLERK_SECRET_KEY=sk_live_... npm run start -- --port $PORT
```

Use the production Clerk instance's keys, and set `CLERK_ISSUER` /
`CLERK_JWKS_URL` on the backend from that same instance.

Set the backend's `CORS_ORIGINS` to this app's deployed origin, or client-side
calls will be blocked by the browser.
