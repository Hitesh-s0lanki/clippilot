import "server-only";

import { cache } from "react";

import type {
  AgeGroup,
  AudienceWritePayload,
  AudienceImportResult,
  AudienceMemberInput,
  AudienceMemberPage,
  AudiencePage,
  Audience,
  AudienceSegments,
  AudienceUpdatePayload,
  Gender,
} from "@/types/audience";

import { api } from "./client";
import { getSessionToken } from "./session";

/**
 * The authenticated audience resource.
 *
 * Server-only, like every authenticated resource: the Clerk token is read per
 * request rather than held in a module-level variable, so one user's session
 * can never be handed to the next request on the same process.
 *
 * Audiences are account-level, not nested under a campaign — that is what
 * makes a list reusable across campaigns.
 */

export interface ListAudiencesParams {
  search?: string;
  limit?: number;
  offset?: number;
}

export const listAudiences = cache(
  async ({ search, limit = 20, offset = 0 }: ListAudiencesParams = {}): Promise<AudiencePage> => {
    return api.get<AudiencePage>("/audiences", {
      query: { search: search || undefined, limit, offset },
      token: await getSessionToken(),
      cache: "no-store",
    });
  },
);

export const getAudience = cache(async (audienceId: string): Promise<Audience> => {
  return api.get<Audience>(`/audiences/${audienceId}`, {
    token: await getSessionToken(),
    cache: "no-store",
  });
});

export interface ListMembersParams {
  /** Matches name, email, phone or CRM reference. */
  search?: string;
  city?: string;
  country?: string;
  ageGroup?: AgeGroup;
  gender?: Gender;
  /** Only people reachable by email. */
  hasEmail?: boolean;
  /** Only people reachable by phone. */
  hasPhone?: boolean;
  limit?: number;
  offset?: number;
}

/**
 * One filtered page of people.
 *
 * Always a page, never the whole list: an audience can hold thousands, and
 * every screen that shows members shows a window of them.
 */
export const listMembers = cache(
  async (audienceId: string, params: ListMembersParams = {}): Promise<AudienceMemberPage> => {
    const { search, city, country, ageGroup, gender, hasEmail, hasPhone } = params;
    const { limit = 25, offset = 0 } = params;

    return api.get<AudienceMemberPage>(`/audiences/${audienceId}/members`, {
      query: {
        search: search || undefined,
        city,
        country,
        age_group: ageGroup,
        gender,
        has_email: hasEmail,
        has_phone: hasPhone,
        limit,
        offset,
      },
      token: await getSessionToken(),
      cache: "no-store",
    });
  },
);

export const getSegments = cache(async (audienceId: string): Promise<AudienceSegments> => {
  return api.get<AudienceSegments>(`/audiences/${audienceId}/segments`, {
    token: await getSessionToken(),
    cache: "no-store",
  });
});

export async function createAudience(payload: AudienceWritePayload): Promise<Audience> {
  return api.post<Audience>("/audiences", { body: payload, token: await getSessionToken() });
}

export async function updateAudience(
  audienceId: string,
  payload: AudienceUpdatePayload,
): Promise<Audience> {
  return api.patch<Audience>(`/audiences/${audienceId}`, {
    body: payload,
    token: await getSessionToken(),
  });
}

/**
 * Add people in bulk. One CSV upload is one call.
 *
 * Returns a partial result rather than failing the file: a repeated email in a
 * 200-row upload costs that row, and every skipped row is named.
 */
export async function addMembers(
  audienceId: string,
  members: AudienceMemberInput[],
): Promise<AudienceImportResult> {
  return api.post<AudienceImportResult>(`/audiences/${audienceId}/members`, {
    body: { members },
    token: await getSessionToken(),
  });
}

export async function removeMember(audienceId: string, memberId: string): Promise<void> {
  await api.delete<void>(`/audiences/${audienceId}/members/${memberId}`, {
    token: await getSessionToken(),
  });
}

export async function deleteAudience(audienceId: string): Promise<void> {
  await api.delete<void>(`/audiences/${audienceId}`, { token: await getSessionToken() });
}
