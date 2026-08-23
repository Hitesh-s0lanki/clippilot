export { api } from "./client";
export type { QueryParams, RequestOptions } from "./client";
export { ApiError, isApiError } from "./errors";
export { getHealth, probeHealth } from "./health";
export type { HealthProbe, HealthResponse } from "./health";
export { getPublicPreview, listPublicCampaigns, recordResponse, recordView } from "./public";
export type { ListPublicCampaignsInput, RecordEventInput, RecordResponseInput } from "./public";

// `./session`, `./campaigns` and `./analytics` are deliberately absent: they
// are server-only, and re-exporting them here would break every Client
// Component that imports `@/lib/api`. Import them by path from Server
// Components and Server Actions instead.
