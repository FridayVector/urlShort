export interface CreateUrlPayload {
  target_url: string;
  slug?: string;
  ttl?: number; // seconds
  reuse_existing?: boolean;
}

export interface ShortUrl {
  slug: string;
  short_url: string;
  target_url: string;
  expires_at?: string | null;
}
