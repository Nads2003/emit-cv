import { useState } from "react";
import { Link } from "react-router-dom";
import { ROUTES } from "@/constants/routes";

// Placez votre logo dans public/images/logo-emit.png
export default function Logo() {
  const [failed, setFailed] = useState(false);

  return (
    <Link to={ROUTES.HOME} className="flex items-center gap-3">
      {failed ? (
        <span className="flex h-11 w-11 items-center justify-center rounded-full border-2 border-brand bg-white text-[11px] font-bold text-brand">
          EMIT
        </span>
      ) : (
        <img
          src="/images/logo-emit.png"
          alt="EMIT"
          onError={() => setFailed(true)}
          className="h-11 w-11 rounded-full border-2 border-brand bg-white object-contain"
        />
      )}
      <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
        EMIT-<span className="text-brand">CV-IA</span>
      </span>
    </Link>
  );
}