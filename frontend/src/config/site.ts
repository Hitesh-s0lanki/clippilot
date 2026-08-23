/**
 * The landing page's in-page anchors, in the order the sections appear.
 *
 * One list, two consumers - the header's marketing nav and the footer's
 * "Product" column - so a section can never be renamed in one and not the
 * other, and every link is an anchor that cannot 404.
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
   * differently. `surface` says who is looking at that step, which is the part
   * a marketing reader needs and the account panel ignores.
   */
  flow: [
    {
      id: "dashboard",
      step: "01",
      surface: "Console",
      title: "Dashboard",
      description: "Every campaign with its status, schedule, views and interactions.",
      detail: "Filter by status, search by name, and see the live counters without opening a row.",
    },
    {
      id: "builder",
      step: "02",
      surface: "Console",
      title: "Builder",
      description: "Configure the video, the personalised message and two response options.",
      detail: "Schedule, budget, delivery caps, compliance and tracking sit in the same form.",
    },
    {
      id: "preview",
      step: "03",
      surface: "Customer",
      title: "Preview",
      description: "The customer view, with {{customer_name}} already resolved.",
      detail: "The exact page the recipient opens - watch it, answer it, and get the follow-up.",
    },
    {
      id: "analytics",
      step: "04",
      surface: "Console",
      title: "Analytics",
      description: "Views, interactions and the split between the two options.",
      detail: "Every VIEW and RESPONSE is an event, so the split is counted rather than estimated.",
    },
  ],
  sectionNav,
  /**
   * The public footer's link columns.
   *
   * Every href resolves: in-page anchors on the landing page, or real routes.
   * `/dashboard` and `/campaigns/new` are behind the session guard, so a
   * signed-out visitor is sent to sign-in rather than to a dead end.
   */
  footerNav: [
    { title: "Product", links: sectionNav },
    {
      title: "Console",
      links: [
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
