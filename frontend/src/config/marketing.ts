import {
  BarChart3Icon,
  CalendarClockIcon,
  GaugeIcon,
  type LucideIcon,
  MousePointerClickIcon,
  ScaleIcon,
  SparklesIcon,
  TagIcon,
  UsersIcon,
  VideoIcon,
} from "lucide-react";

/**
 * Copy for the public landing page.
 *
 * Separate from `siteConfig` because this is marketing prose that only `app/`
 * reads, while `siteConfig` is chrome the whole app depends on. Every claim
 * here maps to something the product actually does - the fields come from
 * `docs/campaign-data-model.md`, so the page cannot promise a feature the
 * builder has no input for.
 */
export const marketing = {
  hero: {
    eyebrow: "Interactive video, for campaign teams",
    /** Split in two so the second clause can carry the brand colour. */
    title: "Personalised video journeys,",
    titleAccent: "from setup to response.",
    description:
      "ClipPilot is where a marketing team builds a one-to-one video campaign, sends it to a named customer, and watches the reply come back as a number. Schedule, budget, compliance and tracking included.",
    note: "Drafts stay private. A campaign only goes live once the publish checklist clears.",
  },

  /** The chip strip under the hero: what a campaign carries, in five words each. */
  capabilities: [
    { label: "Timezone-aware scheduling", Icon: CalendarClockIcon },
    { label: "Budget and pacing caps", Icon: GaugeIcon },
    { label: "Compliance disclaimers", Icon: ScaleIcon },
    { label: "UTM and CRM tracking", Icon: TagIcon },
    { label: "Single or list audiences", Icon: UsersIcon },
  ],

  features: [
    {
      id: "message",
      title: "A message written once, addressed to everyone",
      description:
        "Write the copy with {{customer_name}}, {{campaign_name}} and {{option_label}} in it. The resolver substitutes at render, escapes what it inserts, and falls back to “there” when a recipient has no name - so a preview is never broken.",
      Icon: SparklesIcon,
      /** Wide cards lead each bento row. */
      wide: true,
    },
    {
      id: "options",
      title: "Two options, two outcomes",
      description:
        "Each response option carries a label, an intent and its own follow-up - a message or a URL. The recipient always lands somewhere deliberate.",
      Icon: MousePointerClickIcon,
      wide: false,
    },
    {
      id: "video",
      title: "Your video, your CDN",
      description:
        "Point the experience at a video URL you already host. Add a poster image and a headline, and the customer page is built for you.",
      Icon: VideoIcon,
      wide: false,
    },
    {
      id: "compliance",
      title: "Built for regulated categories",
      description:
        "Declare a special category - financial products, credit, employment, housing - and the disclaimer travels with the campaign onto the customer's screen.",
      Icon: ScaleIcon,
      wide: true,
    },
    {
      id: "analytics",
      title: "Counted, not estimated",
      description:
        "Every view and every response is stored as an event against a recipient, so the interaction rate and the option split are arithmetic rather than a guess.",
      Icon: BarChart3Icon,
      wide: true,
    },
    {
      id: "delivery",
      title: "Delivery you can hold back",
      description:
        "Standard or accelerated pacing, a daily send cap, a lifetime budget and a frequency cap per recipient. Nothing goes out faster than you meant it to.",
      Icon: GaugeIcon,
      wide: false,
    },
  ],

  faqs: [
    {
      question: "What does the recipient actually receive?",
      answer:
        "A link to a page of their own. It opens with your video, the message addressed to them by name, and the two response options underneath. No account, no install - and the link is marked no-index, so it never turns up in a search result.",
    },
    {
      question: "How does the personalisation work?",
      answer:
        "You write {{customer_name}} into the message and ClipPilot resolves it against the recipient row when the page renders. An unknown variable is left visible and flagged in the builder rather than silently blanked, and a missing name falls back to “there”.",
    },
    {
      question: "Can I publish a half-finished campaign?",
      answer:
        "No, and that is deliberate. A campaign without a video, a message or two complete options stays a draft; the builder lists exactly what is blocking publication, so you fix a checklist rather than decode an error.",
    },
    {
      question: "Where do the analytics come from?",
      answer:
        "From the campaign itself. Opening the preview records a view, clicking an option records a response, and the analytics screen reads those events back as views, interactions, interaction rate and the split between your two options - including the option nobody clicked.",
    },
    {
      question: "Does it handle financial-services compliance?",
      answer:
        "It handles the part a campaign tool should. You declare the special category and write the disclaimer once; ClipPilot keeps them attached to the campaign and renders the disclaimer on the customer's page. It is not a substitute for your own approval process.",
    },
    {
      question: "Do I need to host the video?",
      answer:
        "Yes. ClipPilot takes a URL rather than an upload, so the file stays on the CDN you already pay for and already have clearance to use.",
    },
  ],
} as const satisfies MarketingConfig;

interface MarketingConfig {
  hero: { eyebrow: string; title: string; titleAccent: string; description: string; note: string };
  capabilities: ReadonlyArray<{ label: string; Icon: LucideIcon }>;
  features: ReadonlyArray<{
    id: string;
    title: string;
    description: string;
    Icon: LucideIcon;
    wide: boolean;
  }>;
  faqs: ReadonlyArray<{ question: string; answer: string }>;
}
