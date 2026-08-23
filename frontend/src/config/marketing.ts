import {
  BarChart3Icon,
  CalendarClockIcon,
  GaugeIcon,
  type LucideIcon,
  MousePointerClickIcon,
  ScaleIcon,
  SparklesIcon,
  TagIcon,
  VideoIcon,
} from "lucide-react";

/**
 * Copy for the public landing page.
 *
 * Separate from `siteConfig` because this is marketing prose that only `app/`
 * reads, while `siteConfig` is chrome the whole app depends on.
 *
 * The rule this file follows: **state the value, do not describe it**. Every
 * `facts` entry is a real enum member, field limit or file extension taken
 * from `docs/campaign-data-model.md` and the schemas in `backend/src/schemas`,
 * so a reader learns what the product actually accepts instead of reading an
 * adjective about it - and the page cannot promise a feature the builder has
 * no input for.
 */
export const marketing = {
  hero: {
    eyebrow: "Interactive video, for campaign teams",
    /** Split in two so the second clause can carry the brand colour. */
    title: "Personalised video journeys,",
    titleAccent: "from setup to response.",
    description:
      "Build a one-to-one video campaign, send it to a named customer, and count the reply.",
    note: "Drafts stay private until the publish checklist clears.",
  },

  /** The chip strip under the hero: what a campaign carries, as numbers. */
  capabilities: [
    { label: "5 campaign objectives", Icon: SparklesIcon },
    { label: "Timezone-aware scheduling", Icon: CalendarClockIcon },
    { label: "4 special categories", Icon: ScaleIcon },
    { label: "Budget and pacing caps", Icon: GaugeIcon },
    { label: "UTM and CRM tracking", Icon: TagIcon },
  ],

  features: [
    {
      id: "message",
      title: "One message, addressed to everyone",
      description: "Variables resolve at render, escaped, and never leave a blank.",
      facts: [
        "{{customer_name}}",
        "{{campaign_name}}",
        "{{option_label}}",
        "falls back to “there”",
      ],
      Icon: SparklesIcon,
      /** Wide cards lead each bento row. */
      wide: true,
    },
    {
      id: "options",
      title: "Two options, two outcomes",
      description: "Each answer carries an intent and its own follow-up.",
      facts: ["Positive", "Neutral", "Negative", "Message or link"],
      Icon: MousePointerClickIcon,
      wide: false,
    },
    {
      id: "video",
      title: "Your video, your CDN",
      description: "A URL you already host, plus a poster and a headline.",
      facts: [".mp4", ".webm", ".mov", "https only"],
      Icon: VideoIcon,
      wide: false,
    },
    {
      id: "compliance",
      title: "Built for regulated categories",
      description: "Declare one and the disclaimer travels to the customer's screen.",
      facts: ["Financial products", "Credit", "Employment", "Housing"],
      Icon: ScaleIcon,
      wide: true,
    },
    {
      id: "analytics",
      title: "Counted, not estimated",
      description: "Every view and response is a stored event against a recipient.",
      facts: ["Views", "Interactions", "Interaction rate", "Unique viewers", "Option split"],
      Icon: BarChart3Icon,
      wide: true,
    },
    {
      id: "delivery",
      title: "Delivery you can hold back",
      description: "Nothing goes out faster than you meant it to.",
      facts: ["Daily or lifetime budget", "Send caps", "Standard or accelerated"],
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
    /** Real enum members, limits and extensions - never adjectives. */
    facts: ReadonlyArray<string>;
    Icon: LucideIcon;
    wide: boolean;
  }>;
  faqs: ReadonlyArray<{ question: string; answer: string }>;
}
