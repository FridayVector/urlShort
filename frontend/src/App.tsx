import { useState } from "react";
import { createShortUrl } from "./api";
import { ShortUrl } from "./types";
import UrlForm from "./components/UrlForm";
import UrlList from "./components/UrlList";

function App() {
  const [urls, setUrls] = useState<ShortUrl[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(target_url: string, slug?: string, ttl?: number, reuse_existing?: boolean) {
    setError(null);

    try {
      const result = await createShortUrl({ target_url, slug, ttl, reuse_existing });
      setUrls((current) => [result, ...current]);
    } catch (err) {
      setError("Unable to create short URL. Please try again.");
    }
  }

  return (
    <div className="app-shell">
      <header>
        <h1>URL Shortener</h1>
        <p>Paste a link to receive a short redirect URL instantly.</p>
      </header>

      <UrlForm onSubmit={handleSubmit} />

      {error ? <div className="error">{error}</div> : null}

      <UrlList urls={urls} />
    </div>
  );
}

export default App;
