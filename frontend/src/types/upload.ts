/**
 * The direct-to-S3 video upload contract.
 *
 * Mirrors `backend/src/schemas/upload.py`. The file itself never travels
 * through the ClipPilot API: the backend signs a short-lived S3 policy, the
 * browser POSTs the bytes straight to the bucket, and a second call confirms
 * the object landed before its URL is saved on the campaign.
 */

export interface UploadConfig {
  /** False when the backend has no S3 bucket configured. */
  enabled: boolean;
  max_bytes: number;
  accepted_content_types: string[];
}

export interface VideoUploadRequest {
  filename: string;
  content_type: string;
  size_bytes: number;
}

export interface VideoUploadTicket {
  key: string;
  upload_url: string;
  /** Signed policy fields. Must be appended to the form **before** the file. */
  fields: Record<string, string>;
  /** Where the object becomes readable once the upload succeeds. */
  video_url: string;
  expires_in_seconds: number;
  max_bytes: number;
}

export interface VideoUploadResult {
  key: string;
  video_url: string;
  content_type: string | null;
  size_bytes: number | null;
}
