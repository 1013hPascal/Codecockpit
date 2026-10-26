"""Die Texte der Erklärungen (Wunsch des Nutzers vom 25.10.2026).

Jede Erklärung hat einen Titel, zum Beispiel "Menü Datei". Unter diesem Titel steht sie auch in den
Einstellungen des Features, dort hakt man sie einzeln ab. Die Titel bleiben deshalb gleich.

Eine Erklärung ist eine Folge kurzer Absätze. Das Wichtigste steht vorne. Für jede Aktion gibt es
zwei bis drei Sätze. Die Erklärung der Aktionen entsteht aus den Aktionen, die gerade in der Liste
stehen (ui/explanations.py), so passt sie auch zu neuen Aktionen.
"""
from __future__ import annotations

from cockpit.core.actions import Target

ROW_TEXT = "Erklärung: Projektliste"             # oberste Zeile der Projektliste
ACTIONS_ROW = "Erklärung: Aktionen"              # oberste Zeile der Aktionen
ENTRY_TEXT = "Erklärung …"                       # erster Eintrag in Menüs, Knopf in Fenstern
HIDE_TEXT = "Diese Erklärung nicht mehr &anzeigen"
SETTINGS_TEXT = "&Einstellungen für Erklärungen …"
HIDDEN_SAID = ("Diese Erklärung wird nicht mehr angezeigt. Wieder einschalten: Menü Features, "
               "Feature-Verwaltung, Erklärungen, Einstellungen.")
CLOSING = ("Mit Tab kommen Sie zu: Diese Erklärung nicht mehr anzeigen, Einstellungen für "
           "Erklärungen und Schließen. Escape schließt die Erklärung.")

# -- Projektliste ---------------------------------------------------------------------------------
PROJECT_LIST = "Projektliste"
PROJECT_LIST_TEXT = (
    "Links steht die Projektliste, rechts die Aktionen. Tab wechselt zwischen beiden.",
    "Ganz oben stehen drei Einträge zum Anlegen: Neue Projektsammlung, Projekt vom Rechner "
    "hinzufügen und Projekt von GitHub herunterladen. Enter auf dem Eintrag startet ihn.",
    "Darunter steht die Zeile Anzeigen. Enter öffnet den Filter, zum Beispiel nur Projekte mit "
    "offenen Änderungen.",
    "Dann folgen Ihre Projekte und Projektsammlungen, das zuletzt Geänderte oben.",
    "Pfeil rechts öffnet ein Projekt. Darunter stehen dann Repository, der Main-Branch, die "
    "Branches, Releases und die Exe. Mit Pfeil runter kommen Sie dorthin.",
    "Pfeil links klappt das Projekt wieder zu und springt zurück auf das Projekt.",
    "Eine Projektsammlung öffnen Sie mit Pfeil rechts oder Enter. Dann stehen nur ihre Projekte "
    "in der Liste. Rücktaste oder Pfeil links schließt die Sammlung.",
    "Auf jeder Zeile führt Tab zu den Aktionen dieser Zeile, zum Beispiel beim Projekt, beim "
    "Repository und bei den Releases. Die Menütaste zeigt dieselben Aktionen als Kontextmenü.",
    "Hochladen: Gehen Sie auf den Main-Branch oder einen Branch und wählen Sie mit Tab die "
    "Aktion Änderungen auf GitHub hochladen.",
    "Strg+R liest alle Projekte neu ein und fragt ihren Stand ab. Strg+T öffnet ein Terminal im "
    "Ordner der markierten Zeile.",
    "F1 öffnet die Hilfe mit Kurzanleitungen. Umschalt+F1 öffnet die KI-Hilfe für Fragen zur "
    "Bedienung. Strg+K sucht einen Befehl. Strg+F1 sagt, welche Tasten hier etwas tun.",
)

# -- Aktionen -------------------------------------------------------------------------------------
TARGET_TITLES = {
    Target.NEW_COLLECTION: "Neue Projektsammlung",
    Target.ADD_LOCAL: "Projekt vom Rechner",
    Target.ADD_REMOTE: "Projekt von GitHub",
    Target.LIST_FILTER: "Zeile Anzeigen",
    Target.COLLECTION: "Projektsammlung",
    Target.PROJECT: "Projektzeile",
    Target.REPOSITORY: "Repository",
    Target.CODE: "Main-Branch und Branches",
    Target.REMOTE_BRANCH: "Branch nur auf GitHub",
    Target.RELEASES: "Releases",
    Target.EXE: "Exe-main",
    Target.RELEASE: "Release eines Branches",
    Target.REMOTE_REPO: "Repository nur auf GitHub",
}

TARGET_INTROS = {
    Target.NEW_COLLECTION: "Eine Projektsammlung fasst Projekte zusammen, zum Beispiel alle "
                           "Webseiten. So bleibt die Projektliste kurz.",
    Target.ADD_LOCAL: "Hier holen Sie ein Projekt in das Cockpit, das schon auf Ihrem Rechner "
                      "liegt.",
    Target.ADD_REMOTE: "Hier laden Sie ein Projekt von GitHub auf Ihren Rechner.",
    Target.LIST_FILTER: "Der Filter bestimmt, welche Projekte in der Liste stehen.",
    Target.COLLECTION: "Das sind die Aktionen für die markierte Projektsammlung.",
    Target.PROJECT: "Das sind die Aktionen für das ganze Projekt: Ordner, Verwaltung und "
                    "Features. Die Arbeit am Code machen Sie auf dem Main-Branch darunter.",
    Target.REPOSITORY: "Das Repository ist der Speicher Ihres Codes mit allen gespeicherten "
                       "Ständen. Hier stehen die Aktionen für das Repository und für GitHub.",
    Target.CODE: "Hier arbeiten Sie am Code: Änderungen speichern und hochladen, Änderungen "
                 "holen, Verlauf und Pull Requests. Auf einem Branch gelten die Aktionen für "
                 "den Ordner dieses Branches.",
    Target.REMOTE_BRANCH: "Dieser Branch liegt nur auf GitHub, noch nicht auf Ihrem Rechner.",
    Target.RELEASES: "Ein Release ist eine fertige Fassung Ihres Programms, meist als Exe. Hier "
                     "erstellen, veröffentlichen und entfernen Sie Releases.",
    Target.EXE: "Exe-main ist die Exe aus dem Main-Branch, also die Hauptfassung Ihres "
                "Programms.",
    Target.RELEASE: "Das ist das Release eines Branches. Damit probieren Sie eine neue "
                    "Funktion aus, bevor sie in main kommt.",
    Target.REMOTE_REPO: "Dieses Repository liegt nur auf GitHub, noch nicht auf Ihrem Rechner.",
}

ACTIONS_END = (
    "Enter oder Leertaste führt die markierte Aktion aus. Steht hinter einer Aktion nicht "
    "verfügbar, folgt der Grund.",
    "Seltene Aktionen stehen unter Weitere. Enter öffnet sie als Untermenü.",
    "Umschalt+Tab führt zurück zur Zeile in der Projektliste.",
)

MORE_TEXT = "Darunter stehen seltene Aktionen. Enter öffnet sie als Untermenü:"

ACTION_TEXTS = {
    # oberste Einträge
    "new_collection": "Legt eine neue Projektsammlung an. Sie geben einen Namen ein und wählen "
                      "danach die Projekte dafür.",
    "add_local": "Fügt einen Projektordner von Ihrem Rechner hinzu. Das Cockpit erkennt Git, "
                 "Repository und Exe selbst.",
    "add_remote": "Lädt ein Repository von GitHub auf Ihren Rechner. Danach steht es als "
                  "Projekt in der Liste.",
    "list_filter": "Wählt, welche Projekte in der Liste stehen, zum Beispiel alle oder nur "
                   "die mit offenen Änderungen. Die Wahl bleibt nach dem Neustart erhalten.",
    # Sammlung
    "collection_members": "Wählt, welche Projekte zu dieser Sammlung gehören. Ein Projekt ist "
                          "in höchstens einer Sammlung.",
    "rename_collection": "Gibt der Sammlung einen neuen Namen.",
    "dissolve_collection": "Löst die Sammlung auf. Die Projekte bleiben erhalten und stehen "
                           "danach wieder einzeln in der Liste.",
    # Projekt
    "create_repo": "Legt für das Projekt ein Repository auf GitHub an und lädt den Code hoch. "
                   "Vorher prüft das Cockpit, ob Geheimnisse wie Tokens im Code stehen.",
    "relocate": "Erscheint, wenn der Projektordner fehlt. Sie geben den neuen Ort des Ordners "
                "an.",
    "manage_project": "Öffnet die Verwaltung des Projekts, zum Beispiel Name, Ordner und "
                      "Entfernen aus dem Cockpit.",
    "project_features": "Schaltet Features nur für dieses Projekt ein oder aus. Die Auswahl "
                        "steht in der Datei cockpit.toml.",
    "add_exe": "Richtet für das Projekt einen Ordner für die Exe ein. Danach erstellen Sie "
               "Exe-Dateien aus dem Code.",
    "open_project_dir": "Öffnet den Projektordner im Windows-Explorer.",
    "rename_folders": "Benennt die Ordner Code und Exe in Repository und Release um. So heißen "
                      "sie wie im Cockpit.",
    "rename_folders_back": "Gibt den Ordnern wieder ihre alten Namen.",
    # Repository
    "branch_show": "Wählt, welche Branches unter dem Projekt stehen: nur main, die auf Ihrem "
                   "Rechner, die nur auf GitHub oder alle. Hier legen Sie auch neue Branches an.",
    "manage_repo": "Öffnet die Verwaltung des Repositorys auf GitHub, zum Beispiel "
                   "Beschreibung, Sichtbarkeit, Mitarbeiter und Löschen.",
    "links": "Zeigt die Links des Repositorys, zum Beispiel die Seite auf GitHub und die "
             "Adresse zum Klonen. Sie lassen sich kopieren.",
    "readme": "Zeigt, schreibt und übersetzt die README. Die README ist die Beschreibung, die "
              "auf GitHub als Erstes erscheint.",
    "license": "Wählt oder zeigt die Lizenz. Sie sagt, was andere mit Ihrem Code machen "
               "dürfen.",
    "actions_list": "Zeigt die Läufe von GitHub Actions, zum Beispiel automatische Tests nach "
                    "dem Hochladen, mit Ergebnis und Protokoll.",
    "git_identity": "Name und E-Mail-Adresse, die Git zu jeder Ihrer Änderungen schreibt.",
    "open_repo_remote": "Öffnet die Seite des Repositorys auf GitHub im Browser.",
    "open_repo_dir": "Öffnet den Ordner Repository im Windows-Explorer.",
    # Code und Branches
    "finish_exe_branch": "Nach dem Exe-Bau auf einem Branch: Sie überführen die Änderungen in "
                         "main oder verwerfen sie.",
    "resolve_conflicts": "Erscheint, wenn sich Änderungen widersprechen. Das Cockpit zeigt "
                         "jede Konfliktstelle und Sie wählen, welche Fassung gilt.",
    "upload_existing": "Lädt ein Projekt hoch, das schon ein Repository hat, aber noch nicht "
                       "auf GitHub liegt.",
    "push_changes": "Speichert Ihre Änderungen als Commit und lädt sie auf GitHub hoch. Vorher "
                    "sehen Sie die geänderten Dateien und schreiben eine kurze Nachricht.",
    "publish_branch": "Lädt diesen Branch zum ersten Mal auf GitHub hoch. Danach können andere "
                      "ihn sehen.",
    "pull_changes": "Holt Änderungen von GitHub auf Ihren Rechner, zum Beispiel was Sie an "
                    "einem anderen Rechner gemacht haben.",
    "update_from_original": "Bei einem Fork: Holt die neuen Änderungen aus dem Original-"
                            "Repository.",
    "create_pull": "Schlägt die Änderungen dieses Branches zur Übernahme in main vor. Ein Pull "
                   "Request lässt sich prüfen und kommentieren.",
    "pull_requests": "Zeigt die Pull Requests des Repositorys. Sie prüfen, kommentieren und "
                     "übernehmen sie.",
    "pull_requests_branch": "Zeigt die Pull Requests dieses Branches.",
    "issues": "Zeigt die Issues, also Aufgaben und Fehlermeldungen zum Projekt. Sie legen neue "
              "an und schließen erledigte.",
    "history": "Zeigt den Verlauf: jeden gespeicherten Stand mit Nachricht und Datum. Von dort "
               "kommen Sie zu einem früheren Stand zurück.",
    "upload_history": "Zeigt, was wann hochgeladen wurde.",
    "discard": "Verwirft Änderungen, die noch nicht gespeichert sind. Vorher legt das Cockpit "
               "eine Sicherheitskopie an.",
    "stash_push": "Legt Ihre Änderungen beiseite, ohne sie zu speichern. Später holen Sie sie "
                  "zurück.",
    "stashes": "Zeigt die beiseitegelegten Änderungen. Sie holen sie zurück oder löschen sie.",
    "connect_repo": "Verbindet den Ordner mit einem Repository, das es auf GitHub schon gibt.",
    "repair_venv": "Legt die virtuelle Umgebung für Python neu an. Das hilft, wenn Pakete "
                   "fehlen oder kaputt sind.",
    "build_branch_exe": "Erstellt eine Exe aus dem Code dieses Branches. Sie liegt dann unter "
                        "Releases.",
    "setup_branch_folders": "Richtet eigene Ordner für Branches ein. So arbeiten Sie an "
                            "mehreren Branches gleichzeitig.",
    "open_in_editor": "Öffnet den Code im eingestellten Editor.",
    "open_code_dir": "Öffnet den Ordner dieses Branches im Windows-Explorer.",
    # Branch nur auf GitHub
    "pin_branch": "Lädt den Branch auf Ihren Rechner. Danach steht er unter dem Projekt.",
    "open_branch_remote": "Öffnet den Branch auf GitHub im Browser.",
    # Releases und Exe
    "create_release": "Erstellt eine Exe aus einem Branch. So probieren Sie eine neue Funktion "
                      "aus, ohne main zu ändern.",
    "publish_release": "Veröffentlicht ein Release auf GitHub. Andere können die Exe dann "
                       "herunterladen.",
    "remove_release": "Entfernt ein Release von Ihrem Rechner. Vorher fragt das Cockpit nach.",
    "releases_list": "Zeigt die veröffentlichten Releases auf GitHub mit ihren Versionshinweisen.",
    "open_releases_dir": "Öffnet den Ordner Release im Windows-Explorer.",
    "run_exe": "Startet die Exe.",
    "run_release_exe": "Startet die Exe dieses Releases.",
    "build_exe": "Erstellt die Exe aus dem Code von main. Ein Assistent führt Sie durch die "
                 "Schritte.",
    "build_release_exe": "Erstellt die Exe dieses Releases neu aus dem Code des Branches.",
    "finish_exe": "Schließt den Exe-Bau ab, zum Beispiel mit einer neuen Versionsnummer.",
    "finish_exe_release": "Überführt die Änderungen des Branches in main oder verwirft sie. "
                          "Danach ist der Exe-Bau abgeschlossen.",
    "publish_exe": "Veröffentlicht die Exe als Release auf GitHub.",
    "import_exe": "Holt eine Exe aus einem veröffentlichten Release auf Ihren Rechner.",
    "exe_settings": "Einstellungen für den Exe-Bau, zum Beispiel Name, Symbol und welche "
                    "Dateien dazugehören.",
    "exe_links": "Zeigt die Links zum Herunterladen der Exe.",
    "exe_guide": "Erklärt Schritt für Schritt, wie aus Ihrem Code eine Exe wird.",
    "remove_this_release": "Entfernt dieses Release von Ihrem Rechner. Vorher fragt das Cockpit "
                           "nach.",
    "open_exe_dir": "Öffnet den Ordner der Exe im Windows-Explorer.",
    "open_release_dir": "Öffnet den Ordner dieses Releases im Windows-Explorer.",
    # Repository nur auf GitHub
    "download": "Lädt das Repository auf Ihren Rechner. Danach steht es als Projekt in der "
                "Liste.",
    "open_remote": "Öffnet das Repository auf GitHub im Browser.",
    "delete_remote_repo": "Löscht das Repository endgültig auf GitHub. Zur Sicherheit tippen "
                          "Sie vorher seinen Namen ein.",
    "hide_remote": "Nimmt das Repository aus der Liste. Auf GitHub bleibt es erhalten.",
}

# Gleiche Aktionen auf vielen Zeilen
PREFIX_TEXTS = (
    ("terminal_", "Öffnet ein Terminal in diesem Ordner. Für Befehle, die das Cockpit nicht "
                  "selbst anbietet. Mit KI erklärt es Fehlermeldungen."),
    ("reread_", "Liest diese Zeile neu ein und fragt den Stand ab, zum Beispiel nach Änderungen "
                "außerhalb des Cockpits."),
)


def actions_title(target: Target) -> str:
    return f"Aktionen: {TARGET_TITLES.get(target, target.value)}"


def action_text(action_id: str) -> str:
    """Zwei bis drei Sätze zur Aktion, leer wenn es keine gibt."""
    if action_id in ACTION_TEXTS:
        return ACTION_TEXTS[action_id]
    return next((text for prefix, text in PREFIX_TEXTS if action_id.startswith(prefix)), "")


# -- Menüs ----------------------------------------------------------------------------------------
MENUS = {
    "Datei": (
        "Im Menü Datei holen Sie Projekte in das Cockpit und lesen sie neu ein.",
        "Projekt vom Rechner hinzufügen: Ein Ordner auf Ihrem Rechner wird zum Projekt.",
        "Projekt von GitHub herunterladen: Ein Repository kommt auf Ihren Rechner.",
        "Projekte neu einlesen, Strg+R: Sucht neue Projekte und fragt den Stand aller ab.",
        "Sicherheitskopien: Das Cockpit legt vor jeder Änderung an Dateien eine Kopie an. Hier "
        "stellen Sie eine wieder her.",
        "Terminal hier öffnen, Strg+T: Terminal im Ordner der markierten Zeile.",
        "Beenden, Strg+Q.",
    ),
    "Features": (
        "Features sind Zusatzfunktionen, zum Beispiel Pull Requests, Paketübersicht oder diese "
        "Erklärungen.",
        "Feature-Verwaltung: Schaltet Features für alle Projekte ein oder aus. Mit Tab kommen "
        "Sie zur Beschreibung, zur Einführung und zu den Einstellungen eines Features.",
        "Für ein einzelnes Projekt wählen Sie auf der Projektzeile die Aktion Features dieses "
        "Projekts.",
    ),
    "Pakete": (
        "Das Menü Pakete zeigt, welche Pakete Ihre Projekte und Ihr Rechner nutzen.",
        "Paketübersicht, Strg+Umschalt+P: Alle Quellen wie Python, Node oder KI-Modelle mit "
        "ihren Paketen.",
        "Aufräumen: Findet Pakete, die nichts mehr nutzt, und entfernt sie nach Rückfrage.",
        "Ordner nach Modellen durchsuchen: Findet KI-Modelle in einem Ordner.",
        "Liste speichern und Liste einlesen: Damit richten Sie einen neuen Rechner mit "
        "denselben Paketen ein.",
    ),
    "KI": (
        "Im Menü KI richten Sie die KI ein. Ohne KI funktioniert das Cockpit auch.",
        "Der erste Eintrag zeigt, ob die KI auf Ihren Rechner eingestellt ist.",
        "KI-Verwaltung: Wählt lokale oder externe KI für Text und Sprache.",
        "KI-Features: Die Feature-Verwaltung mit den Features, die eine KI nutzen.",
    ),
    "Konten": (
        "Im Menü Konten verwalten Sie Zugänge, zum Beispiel zu GitHub.",
        "Kontenverwaltung: Konten anlegen, prüfen, ändern und entfernen.",
        "Tresor-Einstellungen: Wo die Zugangsdaten geschützt liegen.",
        "Tresor sperren und entsperren: Nur bei der Tresordatei mit Master-Passwort.",
    ),
    "Einstellungen": (
        "Im Menü Einstellungen ändern Sie, wie das Cockpit arbeitet.",
        "Grundeinstellungen: Zum Beispiel der Projekte-Hauptordner und der Editor.",
        "Signaltöne: Welche Töne erklingen, wenn das Programm oder die KI arbeitet und wenn "
        "etwas geklappt hat. Hier schalten Sie alle Töne aus.",
        "Einrichtungsassistent: Führt noch einmal durch die ersten Schritte.",
    ),
    "Neuigkeiten": (
        "Das Menü Neuigkeiten zeigt, was andere an Ihren Projekten getan haben.",
        "Neuigkeiten seit dem letzten Start, Strg+Umschalt+N: Zum Beispiel neue Issues, Pull "
        "Requests und Sterne.",
        "Aktivität der Projekte: Aufrufe, Downloads und Sterne über einen Zeitraum.",
    ),
    "Hilfe": (
        "Im Menü Hilfe finden Sie Anleitungen und Hilfe zur Bedienung.",
        "Hilfe und Kurzanleitungen, F1. Tastenkürzel, Strg+Umschalt+F1.",
        "KI-Hilfe, Umschalt+F1: Fragen zur Bedienung in eigenen Worten.",
        "Befehl suchen, Strg+K: Tippen Sie ein Wort, zum Beispiel hoch, und wählen Sie den "
        "Befehl.",
        "Tasten hier ansagen, Strg+F1: Sagt, welche Tasten beim Fokus etwas tun.",
        "Letzte Meldung wiederholen, Strg+Umschalt+M. Meldungen, Strg+Umschalt+L.",
        "Darunter stehen Anleitungen, zum Beispiel Git installieren und GitHub-Token erstellen.",
    ),
    "Schnellnavigation": (
        "Die Schnellnavigation spart die Wege durch die Zeilen des Projekts.",
        "Hilfe und Tastenbefehle öffnen die Hilfe und die Liste der Tastenkürzel.",
        "Projekt, Repository, Branches und Releases verwalten springen direkt zur Zeile und "
        "öffnen das Fenster dafür.",
    ),
}


def menu_title(name: str) -> str:
    return f"Menü {name}"


# -- Fenster --------------------------------------------------------------------------------------
# Kennung ist der Name der Klasse. Fenster ohne Eintrag bekommen keinen Knopf "Erklärung".
DIALOGS: dict[str, tuple[str, tuple[str, ...]]] = {
    "CommitDialog": ("Änderungen speichern und hochladen", (
        "Hier speichern Sie Ihre Änderungen als Commit. Ein Commit ist ein gespeicherter Stand "
        "mit einer kurzen Nachricht.",
        "Oben stehen die geänderten Dateien. Mit der Leertaste nehmen Sie eine Datei heraus "
        "oder wieder dazu.",
        "Die Nachricht sagt in wenigen Worten, was sich geändert hat. Mit KI bekommen Sie einen "
        "Vorschlag.",
        "Vor dem Hochladen prüft das Cockpit, ob Geheimnisse wie Tokens in den Dateien stehen.",
    )),
    "HunksDialog": ("Abschnitte einer Datei", (
        "Hier wählen Sie einzelne Abschnitte einer Datei für den Commit.",
        "Jeder Eintrag ist eine zusammenhängende Änderung. Mit der Leertaste haken Sie ihn an "
        "oder ab.",
    )),
    "ConflictDialog": ("Konflikte beim Zusammenführen", (
        "Zwei Änderungen widersprechen sich. Die Liste zeigt die betroffenen Dateien.",
        "Für jede Datei wählen Sie Ihre Fassung, die andere Fassung oder Sie lösen die Stellen "
        "einzeln.",
        "Erst wenn alle Konflikte gelöst sind, geht das Zusammenführen weiter.",
    )),
    "ConflictBlocksDialog": ("Konfliktstellen", (
        "Hier sehen Sie jede Stelle einer Datei, an der sich zwei Änderungen widersprechen.",
        "Für jede Stelle wählen Sie, welche Fassung gilt. Mit KI bekommen Sie einen Vorschlag.",
    )),
    "HistoryDialog": ("Verlauf", (
        "Der Verlauf zeigt jeden gespeicherten Stand, das Neueste oben.",
        "Jede Zeile nennt Nachricht, Datum und wer es war.",
        "Mit Tab kommen Sie zu den Aktionen für den markierten Stand, zum Beispiel ansehen, "
        "zurückholen oder einen Branch ab hier anlegen.",
    )),
    "VersionDialog": ("Ein gespeicherter Stand", (
        "Hier sehen Sie einen gespeicherten Stand mit seinen geänderten Dateien.",
        "Von hier holen Sie den Stand zurück oder legen einen Branch ab hier an.",
    )),
    "ReorderDialog": ("Reihenfolge und Zusammenfassen", (
        "Hier ordnen Sie Commits, die noch nicht hochgeladen sind, neu oder fassen sie zusammen.",
        "Vorher legt das Cockpit eine Sicherheitskopie an.",
    )),
    "AmendDialog": ("Commit nachbessern", (
        "Hier ändern Sie den letzten Commit, solange er noch nicht hochgeladen ist.",
        "Sie ändern die Nachricht oder nehmen neue Änderungen mit hinein.",
    )),
    "DiscardDialog": ("Änderungen verwerfen", (
        "Hier verwerfen Sie Änderungen, die noch nicht gespeichert sind.",
        "Mit der Leertaste wählen Sie die Dateien. Vorher legt das Cockpit eine "
        "Sicherheitskopie an.",
    )),
    "UploadHistoryDialog": ("Hochladeverlauf", (
        "Hier sehen Sie, wann welcher Stand hochgeladen wurde.",
    )),
    "UploadDialog": ("Hochladen", (
        "Hier laden Sie Ihr Projekt auf GitHub hoch.",
        "Sie wählen den Namen des Repositorys und ob es öffentlich oder privat ist.",
        "Vorher prüft das Cockpit, ob Geheimnisse wie Tokens im Code stehen.",
    )),
    "SafetyDialog": ("Sicherheitsprüfung", (
        "Die Sicherheitsprüfung sucht vor dem Hochladen nach Geheimnissen wie Tokens und "
        "Passwörtern.",
        "Jeder Fund steht mit Datei und Zeile in der Liste. Entfernen Sie Geheimnisse, bevor "
        "Sie hochladen.",
    )),
    "StashDialog": ("Beiseitegelegte Änderungen", (
        "Hier stehen Änderungen, die Sie beiseitegelegt haben.",
        "Sie holen sie zurück, machen daraus einen Branch oder löschen sie.",
    )),
    "BranchesDialog": ("Branches", (
        "Ein Branch ist ein eigener Arbeitsstand. So probieren Sie etwas aus, ohne main zu "
        "ändern.",
        "Hier wählen Sie, welche Branches unter dem Projekt stehen, und legen neue an.",
        "Fertige Branches führen Sie in main zusammen oder löschen sie.",
    )),
    "PullRequestsDialog": ("Pull Requests", (
        "Ein Pull Request schlägt die Änderungen eines Branches zur Übernahme vor.",
        "Die Liste zeigt die offenen Pull Requests. Mit Tab kommen Sie zu Details, "
        "Kommentaren, Prüfen und Übernehmen.",
    )),
    "PullDetailsDialog": ("Details eines Pull Requests", (
        "Hier sehen Sie Beschreibung, Dateien und Stand der Prüfungen.",
    )),
    "PullCommentsDialog": ("Kommentare", (
        "Hier lesen und schreiben Sie Kommentare zu einem Pull Request.",
    )),
    "CreatePullRequestDialog": ("Pull Request erstellen", (
        "Hier schlagen Sie die Änderungen eines Branches zur Übernahme vor.",
        "Sie schreiben Titel und Beschreibung. Mit KI bekommen Sie einen Vorschlag.",
    )),
    "ReviewDialog": ("Pull Request prüfen", (
        "Hier geben Sie Ihre Prüfung ab: zustimmen, Änderungen wünschen oder nur kommentieren.",
    )),
    "MergeDialog": ("Pull Request übernehmen", (
        "Hier übernehmen Sie die Änderungen in den Ziel-Branch.",
        "Sie wählen, wie die Commits übernommen werden und ob der Branch danach gelöscht wird.",
    )),
    "IssuesDialog": ("Issues", (
        "Issues sind Aufgaben und Fehlermeldungen zu einem Projekt.",
        "Die Liste zeigt die Issues. Mit Tab kommen Sie zu Details, Neues Issue und Schließen.",
    )),
    "IssueDetailsDialog": ("Ein Issue", (
        "Hier lesen Sie ein Issue mit allen Kommentaren und antworten darauf.",
    )),
    "CreateIssueDialog": ("Neues Issue", (
        "Hier legen Sie ein neues Issue an: Titel und Beschreibung.",
    )),
    "ManageRepoDialog": ("Repository verwalten", (
        "Hier verwalten Sie das Repository auf GitHub.",
        "Sie ändern Beschreibung und Sichtbarkeit, laden Mitarbeiter ein und setzen "
        "Schutzregeln für Branches.",
        "Ganz hinten steht das Löschen. Es fragt zur Sicherheit nach dem Namen.",
    )),
    "LinksDialog": ("Links", (
        "Hier stehen die Links des Repositorys. Strg+C kopiert den markierten.",
    )),
    "CollaboratorsDialog": ("Mitarbeiter", (
        "Hier sehen Sie, wer am Repository mitarbeiten darf, und laden neue Personen ein.",
    )),
    "InviteDialog": ("Mitarbeiter einladen", (
        "Geben Sie den Namen auf GitHub ein und wählen Sie, was die Person darf.",
    )),
    "ProtectionDialog": ("Schutzregeln", (
        "Schutzregeln verhindern, dass ein Branch aus Versehen geändert oder gelöscht wird.",
    )),
    "ProjectManageDialog": ("Projekt verwalten", (
        "Hier verwalten Sie das Projekt im Cockpit: Name, Ordner und Sammlung.",
        "Entfernen nimmt das Projekt nur aus dem Cockpit. Die Dateien bleiben erhalten.",
    )),
    "MembersDialog": ("Projekte für die Sammlung", (
        "Hier wählen Sie mit der Leertaste die Projekte der Sammlung.",
        "Ein Projekt ist in höchstens einer Sammlung.",
    )),
    "ReleasesDialog": ("Releases auf GitHub", (
        "Hier stehen die veröffentlichten Releases mit Version und Datum.",
        "Sie bearbeiten Versionshinweise und entfernen alte Releases.",
    )),
    "ReleaseListDialog": ("Releases wählen", (
        "Hier wählen Sie ein Release aus der Liste.",
    )),
    "NotesDialog": ("Versionshinweise", (
        "Versionshinweise sagen, was in dieser Version neu ist. Sie stehen auf GitHub beim "
        "Release.",
    )),
    "ActionsDialog": ("GitHub Actions", (
        "GitHub Actions führt nach dem Hochladen Aufgaben aus, zum Beispiel Tests.",
        "Die Liste zeigt die Läufe mit Ergebnis. Mit Tab kommen Sie zum Protokoll.",
    )),
    "BuildSettingsDialog": ("Exe-Einstellungen", (
        "Hier stellen Sie ein, wie die Exe gebaut wird: Startdatei, Name und Symbol.",
        "Die Einstellungen gelten für jeden Bau dieses Projekts.",
    )),
    "BuildDialog": ("Exe erstellen", (
        "Das Cockpit baut gerade die Exe. Die Liste zeigt, was passiert.",
        "Am Ende sehen Sie, ob es geklappt hat, und wo die Exe liegt.",
    )),
    "PublishDialog": ("Exe veröffentlichen", (
        "Hier veröffentlichen Sie die Exe als Release auf GitHub.",
        "Sie wählen die Version und schreiben Versionshinweise.",
    )),
    "TerminalDialog": ("Terminal", (
        "Im Terminal geben Sie Befehle ein. Enter führt sie aus.",
        "Die Ausgabe steht in der Liste darunter. Mit KI erklärt das Cockpit Fehlermeldungen.",
    )),
    "SourcesDialog": ("Paketübersicht", (
        "Die Paketübersicht zeigt jede Quelle von Paketen, zum Beispiel Python, Node und "
        "KI-Modelle.",
        "Ganz oben steht Paketübersicht aktualisieren. Nur dort liest das Cockpit alle Quellen "
        "neu und prüft, was veraltet ist. Sonst sehen Sie den gespeicherten Stand.",
        "Darunter stehen der Speicherplatz und die Zeile Kritisch mit allen Bibliotheken, die "
        "eine bekannte Sicherheitslücke haben.",
        "Enter auf einer Quelle zeigt ihre Pakete. Der Filter oben zeigt alle, nur die im "
        "Cockpit oder nur die auf dem Rechner.",
    )),
    "PackagesDialog": ("Pakete einer Quelle", (
        "Hier stehen die Pakete einer Quelle mit Version und Größe.",
        "Ganz oben wählen Sie, ob alle Pakete erscheinen oder nur die veralteten.",
        "Mit Tab kommen Sie zu Aktualisieren, Entfernen und Aufräumen. Vorher fragt das "
        "Cockpit nach.",
    )),
    "GlobalFeaturesDialog": ("Feature-Verwaltung", (
        "Hier schalten Sie Features für alle Projekte ein oder aus. Die Leertaste hakt an oder "
        "ab.",
        "Mit Tab kommen Sie zur Beschreibung und zu Für neue Projekte einschalten.",
        "Einführung erklärt ein Feature Schritt für Schritt. Einstellungen gibt es nur bei "
        "manchen Features, zum Beispiel bei diesen Erklärungen.",
        "Speichern übernimmt die Auswahl.",
    )),
    "ProjectFeaturesDialog": ("Features dieses Projekts", (
        "Hier schalten Sie Features nur für dieses Projekt ein oder aus.",
        "Die Auswahl steht in der Datei cockpit.toml im Repository.",
    )),
    "FeatureSettingsDialog": ("Einstellungen eines Features", (
        "Hier ändern Sie die Einstellungen eines Features. Speichern übernimmt sie.",
    )),
    "SettingsDialog": ("Grundeinstellungen", (
        "Hier stellen Sie das Cockpit ein, zum Beispiel den Projekte-Hauptordner und den Editor.",
        "Speichern übernimmt die Einstellungen.",
    )),
    "SoundsDialog": ("Signaltöne", (
        "Hier wählen Sie die Töne, wenn das Programm arbeitet, wenn die KI arbeitet und wenn "
        "etwas geklappt hat.",
        "Beim Wechsel der Auswahl hören Sie den Ton. Alle Signaltöne aus schaltet alle ab.",
    )),
    "AccountsDialog": ("Kontenverwaltung", (
        "Hier stehen Ihre Konten, zum Beispiel bei GitHub.",
        "Mit Tab kommen Sie zu Anlegen, Bearbeiten, Prüfen und Entfernen.",
    )),
    "AccountEditDialog": ("Konto einrichten", (
        "Hier verbinden Sie das Cockpit mit einem Konto, im Browser oder mit einem Token.",
        "Das Cockpit speichert den Zugang geschützt im Tresor.",
    )),
    "VaultSettingsDialog": ("Tresor-Einstellungen", (
        "Der Tresor schützt Ihre Zugangsdaten.",
        "Sie wählen die Windows-Anmeldeinformationsverwaltung oder eine Tresordatei mit "
        "Master-Passwort.",
    )),
    "GitIdentityDialog": ("Git-Name und E-Mail", (
        "Git schreibt Namen und E-Mail-Adresse zu jeder Ihrer Änderungen.",
        "Statt Ihrer eigenen Adresse können Sie eine anonyme Adresse von GitHub nehmen.",
    )),
    "AIManagerDialog": ("KI-Verwaltung", (
        "Hier richten Sie die KI ein: lokal auf Ihrem Rechner oder extern im Internet.",
        "Lokal bleiben Ihre Daten bei Ihnen. Extern ist meist schneller, kann aber Geld kosten.",
        "Das Standard-Werkzeug nutzen alle KI-Features, die nichts anderes eingestellt haben.",
    )),
    "ModelDialog": ("Modell wählen", (
        "Hier wählen Sie das KI-Modell. Größere Modelle sind klüger, brauchen aber mehr "
        "Arbeitsspeicher.",
    )),
    "SpeechDialog": ("Sprach-KI", (
        "Die Sprach-KI wandelt Gesprochenes in Text um. Damit diktieren Sie mit Strg+D.",
    )),
    "AITuningDialog": ("KI einstellen", (
        "Das Cockpit misst, wie schnell die KI auf Ihrem Rechner antwortet, und stellt sie "
        "passend ein.",
    )),
    "AIHelpDialog": ("KI-Hilfe", (
        "Stellen Sie eine Frage zur Bedienung in eigenen Worten, zum Beispiel: Wie lade ich "
        "hoch?",
        "Enter fragt. Die Antwort steht darunter, ein Satz pro Zeile.",
    )),
    "BackupsDialog": ("Sicherheitskopien", (
        "Vor jeder Änderung an Dateien legt das Cockpit eine Sicherheitskopie an.",
        "Hier stellen Sie eine Kopie wieder her. Alte Kopien löscht das Cockpit nach einiger "
        "Zeit.",
    )),
    "BackupFilesDialog": ("Dateien einer Sicherheitskopie", (
        "Hier stehen die Dateien der Sicherheitskopie. Sie stellen alle oder einzelne wieder "
        "her.",
    )),
    "NewsDialog": ("Neuigkeiten", (
        "Hier steht, was andere an Ihren Projekten getan haben, zum Beispiel neue Issues und "
        "Sterne.",
        "Mit Tab wählen Sie den Zeitraum.",
    )),
    "ActivityDialog": ("Aktivität", (
        "Hier sehen Sie Aufrufe, Downloads und Sterne Ihrer Projekte.",
        "Mit Tab wählen Sie den Zeitraum.",
    )),
    "MessagesDialog": ("Meldungen", (
        "Hier stehen die letzten Meldungen des Cockpits, die neueste oben. Strg+C kopiert eine.",
    )),
    "CommandSearchDialog": ("Befehl suchen", (
        "Tippen Sie ein Wort, zum Beispiel hoch. Darunter stehen die passenden Aktionen und "
        "Menüs.",
        "Pfeil runter wählt, Enter führt aus.",
    )),
    "ReadmeTextDialog": ("README", (
        "Die README beschreibt Ihr Projekt. Auf GitHub erscheint sie als Erstes.",
        "Mit KI schreiben und übersetzen Sie die README.",
    )),
    "LanguagesDialog": ("README-Einstellungen", (
        "Hier wählen Sie, in welche Sprachen die README übersetzt wird.",
    )),
}


def dialog_title(class_name: str) -> str:
    return f"Fenster {DIALOGS[class_name][0]}"


ALL_TITLES: tuple[str, ...] = (
    (PROJECT_LIST,)
    + tuple(actions_title(t) for t in TARGET_TITLES)
    + tuple(menu_title(n) for n in MENUS)
    + tuple(dialog_title(c) for c in DIALOGS)
)
