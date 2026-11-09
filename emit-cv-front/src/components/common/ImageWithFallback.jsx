import { useState } from "react";

export default function ImageWithFallback({ src, alt, className = "", fallback }) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return (
      <div className={`flex items-center justify-center bg-gradient-to-br from-brand/40 to-night-card ${className}`}>
        {fallback}
      </div>
    );
  }
  return <img src={src} alt={alt} onError={() => setFailed(true)} className={`object-cover ${className}`} />;
}