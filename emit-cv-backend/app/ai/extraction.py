"""Validation stricte et extraction de texte d'un fichier CV (PDF ou DOCX).

Contrôles : octets magiques (pas l'extension), taille, contenu actif (JavaScript, lancement de programme, fichiers incorporés,
macros VBA), bombes de décompression (DOCX), chiffrement, fichier corrompu, PDF sans texte (scanné => OCR nécessaire)."""
import io
import re
import zipfile

from docx import Document
from pypdf import PdfReader

MAX_DOCX_DECOMPRESSE = 60 * 1024 * 1024  # 60 Mo une fois décompressé
MAX_DOCX_ENTREES = 3000
MAX_PAGES = 15
MARQUEURS_PDF_ACTIFS = (b"/JavaScript", b"/JS", b"/Launch", b"/EmbeddedFile", b"/OpenAction", b"/AA", b"/RichMedia", b"/XFA")


class FichierInvalide(ValueError):
    pass


def detect_type(data: bytes) -> str:
    """Détermine le type d'après les octets magiques (on ne fait pas confiance à l'extension/MIME)."""
    if not data:
        raise FichierInvalide("Le fichier est vide.")
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:4] == b"PK\x03\x04":
        return "docx"
    raise FichierInvalide("Format non supporté : seuls les fichiers PDF et DOCX sont acceptés.")


def valider_securite(data: bytes, kind: str) -> None:
    """Refuse les fichiers au contenu actif ou piégés. (Un antivirus type ClamAV reste recommandé en production.)"""
    if kind == "pdf":
        # on ne cherche que les clés PDF « /Nom » suivies d'un délimiteur, pour éviter de refuser un texte contenant « /AA » par hasard
        for m in MARQUEURS_PDF_ACTIFS:
            if re.search(re.escape(m) + rb"(?![A-Za-z0-9])", data):
                raise FichierInvalide("Le PDF contient du contenu actif (script, fichier incorporé ou action automatique) : fichier refusé.")
    else:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                infos = z.infolist()
                if len(infos) > MAX_DOCX_ENTREES or sum(i.file_size for i in infos) > MAX_DOCX_DECOMPRESSE:
                    raise FichierInvalide("Le document est anormalement volumineux une fois décompressé : fichier refusé.")
                noms = {i.filename.lower() for i in infos}
                if "word/document.xml" not in noms:
                    raise FichierInvalide("Ce fichier n'est pas un document Word valide.")
                if any(n.endswith("vbaproject.bin") or n.startswith("word/embeddings/") or n.startswith("word/activex/") for n in noms):
                    raise FichierInvalide("Le document contient des macros ou des objets incorporés : fichier refusé.")
        except zipfile.BadZipFile as exc:
            raise FichierInvalide("Le fichier est illisible ou corrompu.") from exc


def extract_text_info(data: bytes) -> tuple[str, str, str]:
    """Retourne (type, texte, etat). etat : 'ok' | 'ocr_requis' (PDF sans couche texte, probablement scanné) | 'vide'.
    Lève FichierInvalide si le fichier est refusé, corrompu ou chiffré."""
    kind = detect_type(data)
    valider_securite(data, kind)
    try:
        if kind == "pdf":
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise FichierInvalide("Le PDF est protégé par un mot de passe.")
            pages = reader.pages[:MAX_PAGES]
            text = "\n".join((p.extract_text() or "") for p in pages)
            a_images = any(len(p.images) > 0 for p in pages) if len(text.strip()) < 30 else False
        else:
            doc = Document(io.BytesIO(data))
            parts = [p.text for p in doc.paragraphs]
            for table in doc.tables:
                for row in table.rows:
                    parts.append(" | ".join(c.text for c in row.cells))
            text, a_images = "\n".join(parts), False
    except FichierInvalide:
        raise
    except Exception as exc:  # fichier corrompu, structure invalide
        raise FichierInvalide("Le fichier est illisible ou corrompu.") from exc
    text = text.strip()
    if len(text) >= 30:
        return kind, text, "ok"
    return kind, text, ("ocr_requis" if kind == "pdf" and a_images else "vide")


def extract_text(data: bytes) -> tuple[str, str]:
    """Compatibilité : (type, texte) ; lève FichierInvalide si aucun texte exploitable."""
    kind, text, etat = extract_text_info(data)
    if etat == "ocr_requis":
        raise FichierInvalide("PDF scanné : aucun texte exploitable (une reconnaissance de caractères serait nécessaire).")
    if etat == "vide":
        raise FichierInvalide("Aucun texte exploitable dans ce fichier.")
    return kind, text
