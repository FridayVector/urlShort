import { FormEvent, useState } from "react";

interface Props {
  onSubmit: (target_url: string, slug?: string, ttl?: number, reuse_existing?: boolean) => Promise<void>;
}

export default function UrlForm({ onSubmit }: Props) {
  const [value, setValue] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [customSlug, setCustomSlug] = useState("");
  const [lifetimeMinutes, setLifetimeMinutes] = useState<number | "">("");
  const [reuseExisting, setReuseExisting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    event.stopPropagation();
    if (!value.trim()) return;

    setSubmitting(true);
    try {
      const ttl = lifetimeMinutes === "" ? undefined : Number(lifetimeMinutes) * 60;
      await onSubmit(value.trim(), customSlug || undefined, ttl, reuseExisting);
      setValue("");
      setCustomSlug("");
      setLifetimeMinutes("");
      setReuseExisting(false);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="url-form" action="#" onSubmit={handleSubmit}>
      <input
        type="url"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="https://example.com/page"
        required
      />
      <input
        type="text"
        value={customSlug}
        onChange={(e) => setCustomSlug(e.target.value)}
        placeholder="custom-slug (optional)"
      />
      <input
        type="number"
        min={1}
        value={lifetimeMinutes}
        onChange={(e) => setLifetimeMinutes(e.target.value === "" ? "" : Number(e.target.value))}
        placeholder="lifetime (minutes, optional)"
      />
      <label>
        <input
          type="checkbox"
          checked={reuseExisting}
          onChange={(e) => setReuseExisting(e.target.checked)}
        />
        Reuse existing slug for same URL
      </label>
      <button type="submit" disabled={submitting}>
        {submitting ? "Shortening..." : "Shorten URL"}
      </button>
    </form>
  );
}
