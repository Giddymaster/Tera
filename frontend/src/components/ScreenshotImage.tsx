import { useEffect, useState } from "react";
import { getScreenshotImage } from "../api/endpoints";

// Loads a screenshot via an authenticated request and shows it as an object URL
// (a plain <img src> cannot send the bearer token).
export function ScreenshotImage({
  id,
  className,
}: {
  id: number;
  className?: string;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;
    setUrl(null);
    setFailed(false);
    getScreenshotImage(id)
      .then((blob) => {
        if (active) {
          objectUrl = URL.createObjectURL(blob);
          setUrl(objectUrl);
        }
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [id]);

  if (failed) return <div className="shot-ph shot-missing">unavailable</div>;
  if (!url) return <div className="shot-ph shot-loading" />;
  return <img src={url} alt="device screenshot" className={className} />;
}
