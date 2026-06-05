import { ShortUrl } from "../types";

interface Props {
  urls: ShortUrl[];
}

export default function UrlList({ urls }: Props) {
  if (urls.length === 0) {
    return <p className="empty-state">No short URLs created yet.</p>;
  }

  return (
    <div className="url-list">
      {urls.map((url) => (
        <article key={url.slug} className="url-card">
          <p className="target-url">Original: <a href={url.target_url} target="_blank" rel="noreferrer">{url.target_url}</a></p>
          <p className="short-url">
            Short URL: <a href={url.short_url} target="_blank" rel="noreferrer">{url.short_url}</a>
          </p>
          {url.expires_at ? (
            <p className="expires">Expires: {new Date(url.expires_at).toLocaleString()}</p>
          ) : null}
        </article>
      ))}
    </div>
  );
}
