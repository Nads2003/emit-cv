import api from "./axiosInstance";

const MOCK = import.meta.env.VITE_AUTH_MOCK !== "false";
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

const bank = {
  fr: {
    rh: [
      "Pouvez-vous vous présenter en quelques mots ?",
      "Pourquoi souhaitez-vous ce poste de {poste} ?",
      "Quelles sont vos principales qualités et vos points à améliorer ?",
      "Parlez-moi d'un projet dont vous êtes fier.",
      "Comment gérez-vous le stress et les délais serrés ?",
      "Décrivez une situation où vous avez travaillé en équipe malgré un désaccord.",
      "Où vous voyez-vous dans cinq ans ?",
      "Avez-vous des questions pour nous ?",
    ],
    tech: [
      "Quelles compétences techniques maîtrisez-vous le mieux pour un poste de {poste} ?",
      "Décrivez un problème technique difficile que vous avez résolu.",
      "Comment organisez-vous votre travail sur un projet, du début à la fin ?",
      "Comment restez-vous à jour avec les évolutions de votre domaine ?",
      "Expliquez un concept technique de votre domaine à quelqu'un qui n'y connaît rien.",
      "Comment vérifiez-vous la qualité de votre travail ?",
      "Que feriez-vous si vous deviez utiliser un outil que vous ne connaissez pas ?",
      "Parlez d'une erreur technique que vous avez commise et de ce que vous en avez appris.",
    ],
  },
  en: {
    rh: [
      "Can you introduce yourself in a few words?",
      "Why do you want this {poste} position?",
      "What are your main strengths and areas for improvement?",
      "Tell me about a project you are proud of.",
      "How do you handle stress and tight deadlines?",
      "Describe a situation where you worked in a team despite a disagreement.",
      "Where do you see yourself in five years?",
      "Do you have any questions for us?",
    ],
    tech: [
      "Which technical skills do you master best for a {poste} position?",
      "Describe a difficult technical problem you solved.",
      "How do you organize your work on a project, from start to finish?",
      "How do you keep up with developments in your field?",
      "Explain a technical concept from your field to someone with no background.",
      "How do you check the quality of your work?",
      "What would you do if you had to use a tool you don't know?",
      "Tell me about a technical mistake you made and what you learned from it.",
    ],
  },
};

const buildQuestions = (type, poste, count, lang) => {
  const { rh, tech } = bank[lang] ?? bank.fr;
  const list = type === "rh" ? rh : type === "technique" ? tech : rh.flatMap((q, i) => [q, tech[i]]);
  return list.slice(0, count).map((texte, i) => ({ id: i + 1, texte: texte.replaceAll("{poste}", poste) }));
};

// Évaluation simulée : renvoie des CLÉS de traduction (interview.fb.<clé>)
const evaluate = (text) => {
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  const hasExample = /exemple|example|projet|project|stage|internship|expérience|experience/i.test(text);
  const hasResult = /résultat|result|%|amélior|improv|réussi|achiev|appris|learn|atteint|réduit|reduc|augment|increas/i.test(text);
  const hasStructure = /d'abord|ensuite|puis|enfin|first|then|finally|next/i.test(text);

  const good = [];
  const improve = [];
  if (words >= 40) good.push("detailed");
  else if (words < 15) improve.push("short");
  if (hasExample) good.push("example");
  else improve.push("noExample");
  if (hasResult) good.push("result");
  else improve.push("noResult");
  if (hasStructure) good.push("structure");
  if (words > 200) improve.push("long");

  const score = Math.round(
    30 +
      Math.min(words, 60) * 0.5 +
      (hasExample ? 15 : 0) +
      (hasResult ? 15 : 0) +
      (hasStructure ? 10 : 0) -
      (words > 200 ? 10 : 0),
  );
  return { score: Math.max(20, Math.min(100, score)), good, improve };
};

/**
 * POST /api/entretiens/  { poste, type, nombre_questions, langue }
 * Réponse : { id, questions: [{ id, texte }] }
 */
export const startEntretien = async ({ poste, type, count, lang }) => {
  if (MOCK) {
    await wait(800);
    return { id: Date.now(), questions: buildQuestions(type, poste, count, lang) };
  }
  const { data } = await api.post("/entretiens/", { poste, type, nombre_questions: count, langue: lang });
  return data;
};

/**
 * POST /api/entretiens/{id}/reponses/  { question, reponse }
 * Réponse : { score (0-100), good: [clés], improve: [clés] }
 */
export const evaluerReponse = async (entretienId, question, reponse) => {
  if (MOCK) {
    await wait(1000);
    return evaluate(reponse);
  }
  const { data } = await api.post(`/entretiens/${entretienId}/reponses/`, { question: question.id, reponse });
  return data;
};