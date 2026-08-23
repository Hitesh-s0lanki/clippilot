/**
 * The landing page's in-page anchors, in the order the sections appear.
 *
 * The header does not carry them - it stops at the mark, the ads library, the
 * dashboard and the account menu - so the footer is where a reader jumps back
 * into a section. Anchors, so none of them can 404.
 */
const sectionNav = [
  { label: "How it works", href: "/#how-it-works" },
  { label: "Features", href: "/#features" },
  { label: "Personalisation", href: "/#personalisation" },
  { label: "Questions", href: "/#faq" },
] as const;

export const siteConfig = {
  name: "ClipPilot",
  title: "ClipPilot — interactive video campaigns",
  /** The product's one-line promise. Shared by the landing hero and the account screens. */
  headline: "Personalised video journeys, from setup to response.",
  description:
    "Build personalised, interactive video journeys: configure a campaign, preview it as the customer sees it, and read the response back as analytics.",
  /**
   * The end-to-end journey the product supports, in order.
   *
   * One source of truth for three surfaces - the landing page, the account
   * screens and the footer - so none of them can describe the product
   * differently. One line each: the four steps are a wayfinding device, not a
   * place to argue the product. `surface` says who is looking at that step,
   * which is the part a marketing reader needs and the account panel ignores.
   */
  flow: [
    {
      id: "dashboard",
      step: "01",
      surface: "Console",
      title: "Dashboard",
      description: "Every campaign with its status, schedule, views and interactions.",
    },
    {
      id: "builder",
      step: "02",
      surface: "Console",
      title: "Builder",
      description: "Configure the video, the personalised message and two response options.",
    },
    {
      id: "preview",
      step: "03",
      surface: "Customer",
      title: "Preview",
      description: "The customer view, with {{customer_name}} already resolved.",
    },
    {
      id: "analytics",
      step: "04",
      surface: "Console",
      title: "Analytics",
      description: "Views, interactions and the split between the two options.",
    },
  ],
  /**
   * The public footer's link columns.
   *
   * Every href resolves: in-page anchors on the landing page, or real routes.
   * `/ads` is public; `/dashboard` and `/campaigns/new` are behind the session
   * guard, so a signed-out visitor is sent to sign-in rather than a dead end.
   */
  footerNav: [
    { title: "Product", links: sectionNav },
    {
      title: "Explore",
      links: [
        { label: "Ads library", href: "/ads" },
        { label: "Campaign dashboard", href: "/dashboard" },
        { label: "New campaign", href: "/campaigns/new" },
      ],
    },
    {
      title: "Account",
      links: [
        { label: "Sign in", href: "/login" },
        { label: "Create an account", href: "/register" },
      ],
    },
  ],
} as const;
