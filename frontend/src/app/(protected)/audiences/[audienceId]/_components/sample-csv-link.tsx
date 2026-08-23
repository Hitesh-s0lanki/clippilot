"use client";

import { DownloadIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

import { SAMPLE_CSV_FILENAME, sampleMemberCsv } from "../_lib/audience-csv";

/**
 * Hands over a file already in the shape the importer wants.
 *
 * Describing the columns in prose only gets someone so far - the questions
 * that stop an upload are the ones prose is bad at answering (does a blank
 * cell need a placeholder? what does a header row look like?). A file they can
 * open, overwrite and re-upload answers all of them at once.
 *
 * Built in the browser from the column list rather than served as a static
 * asset, so it cannot fall out of step with the parser.
 */
export function SampleCsvLink() {
  function download() {
    const url = URL.createObjectURL(new Blob([sampleMemberCsv()], { type: "text/csv" }));
    const link = document.createElement("a");

    link.href = url;
    link.download = SAMPLE_CSV_FILENAME;
    link.click();

    // Released on the next tick, not immediately: some browsers have not
    // finished reading the blob by the time click() returns.
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  return (
    <Button type="button" variant="link" size="sm" className="h-auto px-0" onClick={download}>
      <DownloadIcon aria-hidden />
      Download a sample CSV
    </Button>
  );
}
