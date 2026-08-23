"use client";

import type { ReactNode } from "react";

import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import type { BuilderSection as BuilderSectionMeta } from "../_lib/campaign-form-sections";

export interface BuilderSectionProps {
  section: BuilderSectionMeta;
  /** How many fields in this section are currently in error. */
  errorCount: number;
  children: ReactNode;
}

/**
 * One accordion section of the builder.
 *
 * The error count sits on the trigger for the case progressive disclosure
 * otherwise breaks: a rejected publish marks fields inside sections that are
 * folded shut. The form opens those sections, and this badge keeps the count
 * visible if the user folds one again.
 */
export function BuilderSection({ section, errorCount, children }: BuilderSectionProps) {
  return (
    <AccordionItem value={section.id}>
      <AccordionTrigger className="gap-3 py-4 hover:no-underline">
        <span className="flex min-w-0 flex-col gap-0.5">
          <span className="flex items-center gap-2">
            <span className="font-heading text-base font-medium">{section.title}</span>
            {errorCount > 0 ? (
              <Badge variant="destructive">
                {errorCount} {errorCount === 1 ? "issue" : "issues"}
              </Badge>
            ) : null}
          </span>
          <span className="text-sm font-normal text-muted-foreground">{section.description}</span>
        </span>
      </AccordionTrigger>
      <AccordionContent className="h-auto pb-6">
        <div className="space-y-5">{children}</div>
      </AccordionContent>
    </AccordionItem>
  );
}
