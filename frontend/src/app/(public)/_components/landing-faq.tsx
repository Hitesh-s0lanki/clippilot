import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { marketing } from "@/config/marketing";

import { LandingSection } from "./landing-section";

/**
 * The objections a campaign manager raises before signing up, answered in the
 * order they usually come. An accordion rather than six open paragraphs: the
 * questions are the scannable part, the answers are only read one at a time.
 */
export function LandingFaq() {
  return (
    <LandingSection id="faq" eyebrow="Questions" title="The things worth asking first.">
      <Accordion
        type="single"
        collapsible
        className="max-w-3xl rounded-2xl border border-border bg-card px-6"
      >
        {marketing.faqs.map(({ question, answer }) => (
          <AccordionItem key={question} value={question}>
            <AccordionTrigger className="py-4 text-base">{question}</AccordionTrigger>
            <AccordionContent className="pb-4 leading-relaxed text-pretty text-muted-foreground">
              {answer}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </LandingSection>
  );
}
