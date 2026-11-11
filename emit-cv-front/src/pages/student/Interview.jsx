import { useState } from "react";
import { HeartHandshake } from "lucide-react";
import SetupForm from "@/components/interview/SetupForm";
import InterviewSession from "@/components/interview/InterviewSession";
import InterviewResult from "@/components/interview/InterviewResult";
import { startEntretien } from "@/api/interview.api";
import { useCv } from "@/hooks/useCv";
import { useLanguage } from "@/hooks/useLanguage";

export default function Entretien() {
  const { t, lang } = useLanguage();
  const { cv } = useCv();
  const [step, setStep] = useState("setup"); // setup | chat | result
  const [config, setConfig] = useState(null);
  const [session, setSession] = useState(null); // { id, questions }
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const handleStart = async (cfg) => {
    setLoading(true);
    setError(false);
    try {
      const data = await startEntretien({ ...cfg, lang });
      setConfig(cfg);
      setSession(data);
      setStep("chat");
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="mx-auto max-w-3xl px-5 py-10 lg:px-12">
      <h1 className="text-3xl font-semibold">{t("interview.title")}</h1>
      <p className="mt-2 text-slate-500 dark:text-slate-400">{t("interview.subtitle")}</p>

      <div className="mt-6 flex items-start gap-3 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-5 py-4 text-sm text-emerald-500">
        <HeartHandshake size={20} className="mt-0.5 shrink-0" />
        {t("interview.reassure")}
      </div>

      <div className="mt-8">
        {step === "setup" && (
          <SetupForm
            defaultPoste={cv.profil.poste}
            loading={loading}
            error={error}
            onStart={handleStart}
          />
        )}

        {step === "chat" && session && (
          <InterviewSession
            key={session.id}
            entretienId={session.id}
            questions={session.questions}
            onFinish={(a) => {
              setAnswers(a);
              setStep("result");
            }}
            onQuit={() => setStep("setup")}
          />
        )}

        {step === "result" && (
          <InterviewResult answers={answers} onRetry={() => handleStart(config)} onNew={() => setStep("setup")} />
        )}
      </div>
    </section>
  );
}