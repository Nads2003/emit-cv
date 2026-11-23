"""Génère le fichier Excel de 100 étudiants FICTIFS de test (docs/etudiants_test_100.xlsx).

Les données sont volontairement artificielles et sans équivoque (Nom « TEST001 », matricule « TEST-EMIT-0001 », e-mail @example.org,
domaine réservé aux exemples) : aucune identité réelle n'est utilisée. À REMPLACER par la liste officielle fournie par l'EMIT."""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo

SORTIE = Path(__file__).resolve().parents[2] / "docs" / "etudiants_test_100.xlsx"


def main(n: int = 100) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Etudiants"
    ws.append(["Nom", "Prénom", "Email", "Matricule"])
    for i in range(1, n + 1):
        ws.append([f"TEST{i:03d}", f"Etudiant{i:03d}", f"etudiant{i:03d}@example.org", f"TEST-EMIT-{i:04d}"])
    for c in ws[1]:
        c.font, c.fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="0F2D3A")
        c.alignment = Alignment(horizontal="center")
    for col, w in zip("ABCD", (16, 18, 34, 20)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"
    tab = Table(displayName="EtudiantsTest", ref=f"A1:D{n + 1}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
    ws.add_table(tab)

    lisez = wb.create_sheet("LISEZ-MOI")
    for l in [
        "DONNÉES FICTIVES DE TEST : aucune de ces personnes n'existe.",
        "",
        f"Ce fichier contient {n} entrées artificielles (noms TESTnnn, matricules TEST-EMIT-nnnn, e-mails @example.org, domaine réservé aux exemples).",
        "Il sert uniquement à tester l'import et l'inscription. Aucun e-mail réel ne peut être envoyé à ces adresses.",
        "",
        "AVANT LA MISE EN PRODUCTION :",
        "1. Obtenir la liste officielle des étudiants auprès de l'EMIT, avec son autorisation et dans le respect de la protection des données personnelles.",
        "2. Remplacer ces données : colonnes Nom, Prénom, Email, Matricule, en-têtes sur la première ligne de la première feuille.",
        "3. Importer la liste via l'interface administrateur (Étudiants autorisés > Importer) : aperçu, vérification des erreurs et doublons, puis confirmation.",
        "4. Ne conserver aucune donnée de test dans la base de production.",
        "",
        "Seule la première feuille (« Etudiants ») est lue par le système ; cette feuille est ignorée.",
    ]:
        lisez.append([l])
    lisez.column_dimensions["A"].width = 130
    lisez["A1"].font = Font(bold=True, color="C8382D", size=13)
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    wb.save(SORTIE)
    return SORTIE


if __name__ == "__main__":
    print(main())
