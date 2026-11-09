export const formatDate = (date, lang = "fr") =>
  new Date(date).toLocaleDateString(lang === "fr" ? "fr-FR" : "en-GB", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });