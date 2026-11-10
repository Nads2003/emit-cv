import { useEffect, useRef, useState } from "react";
import { Bot, Send, Loader2, Check, Lightbulb, ArrowRight, AlertCircle } from "lucide-react";
import { evaluerReponse } from "@/api/entretien.api";
import { useLanguage } from "@/hooks/useLanguage";

function AiBubble({ children }) {
  const { t } = useLanguage();
  return (
    <div className="flex items-start gap-3">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand/15 text-brand">
        <Bot size={20} />
      </span>
      <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-white px-5 py-3.5 text-[15px] leading-relaxed shadow-sm dark:bg-night-card">
        <p className="mb-1 text-xs font-semibold text-brand">{t("interview.chat.ai")}</p>
        {children}
      </div>
    </div>
  );
}

function UserBubble({ children }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tr-sm bg-brand px-5 py-3.5 text-[15px] leading-relaxed text-white">
        {children}
      </div>
    </div>
  );
}

function FeedbackCard({ answer }) {
  const { t } = useLanguage();
  return (
    <div className="ml-0 rounded-2xl border border-slate-200 bg-white p-5 dark:border-night-line dark:bg-night-card sm:ml-13">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold">{t("interview.chat.feedback")}</p>
        <span className="rounded-full bg-brand/15 px-3 py-1 text-sm font-bold text-brand">
          {answer.score}/100
        </span>
      </div>

      {answer.good.length > 0 && (
        <ul className="mt-4 space-y-1.5">
          {answer.good.map((k) => (
            <li key={k} className="flex items-start gap-2 text-sm text-emerald-500">
              <Check size={16} className="mt-0.5 shrink-0" /> {t(`interview.fb.${k}`)}
            </li>
          ))}
        </ul>
      )}
      {answer.improve.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {answer.improve.map((k) => (
            <li key={k} className="flex items-start gap-2 text-sm text-amber-500">
              <Lightbulb size={16} className="mt-0.5 shrink-0" /> {t(`interview.fb.${k}`)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function InterviewSession({ entretienId, questions, onFinish, onQuit }) {
  const { t } = useLanguage();
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [draft, setDraft] = useState("");
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState(false);
  const bottomRef = useRef(null);

  const total = questions.length;
  const answeredCurrent = answers.length > index;
  const isLast = index === total - 1;
  const progress = ((index + (answeredCurrent ? 1 : 0)) / total) * 100;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [index, answers.length, evaluating]);

  const send = async () => {
    const text = draft.trim();
    if (!text || evaluating) return;
    setEvaluating(true);
    setError(false);
    try {
      const res = await evaluerReponse(entretienId, questions[index], text);
      setAnswers((a) => [...a, { question: questions[index].texte, reponse: text, ...res }]);
      setDraft("");
    } catch {
      setError(true);
    } finally {
      setEvaluating(false);
    }
  };

  const next = () => (isLast ? onFinish(answers) : setIndex((i) => i + 1));

  return (
    <div>
      {/* Progression */}
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">
          {t("interview.chat.question")} {index + 1} / {total}
        </span>
        <button onClick={onQuit} className="text-slate-500 transition hover:text-red-500 dark:text-slate-400">
          {t("interview.chat.quit")}
        </button>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-night-line">
        <div className="h-full rounded-full bg-brand transition-all duration-500" style={{ width: `${progress}%` }} />
      </div>

      {/* Conversation */}
      <div className="mt-8 space-y-6">
        {questions.slice(0, index + 1).map((q, i) => (
          <div key={q.id} className="space-y-4">
            <AiBubble>{q.texte}</AiBubble>
            {answers[i] && (
              <>
                <UserBubble>{answers[i].reponse}</UserBubble>
                <FeedbackCard answer={answers[i]} />
              </>
            )}
          </div>
        ))}

        {evaluating && (
          <p className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
            <Loader2 size={16} className="animate-spin" /> {t("interview.chat.analyzing")}
          </p>
        )}

        {error && (
          <p className="flex items-center gap-2 text-sm text-red-500">
            <AlertCircle size={16} /> {t("interview.error")}
          </p>
        )}

        {/* Zone de réponse ou bouton suivant */}
        {answeredCurrent ? (
          <button
            onClick={next}
            className="inline-flex items-center gap-2 rounded-full bg-brand px-7 py-3 text-sm font-semibold text-white transition hover:brightness-110"
          >
            {isLast ? t("interview.chat.finish") : t("interview.chat.next")}
            <ArrowRight size={16} />
          </button>
        ) : (
          <div className="rounded-2xl border border-slate-200 bg-white p-3 dark:border-night-line dark:bg-night-card">
            <textarea
              rows={5}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) send();
              }}
              disabled={evaluating}
              placeholder={t("interview.chat.placeholder")}
              className="w-full resize-none bg-transparent p-3 text-sm outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500"
            />
            <div className="flex items-center justify-between gap-3 px-2 pb-1">
              <span className="text-xs text-slate-400">{t("interview.chat.hint")}</span>
              <button
                onClick={send}
                disabled={!draft.trim() || evaluating}
                className="inline-flex items-center gap-2 rounded-full bg-brand px-5 py-2.5 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Send size={15} /> {t("interview.chat.send")}
              </button>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}