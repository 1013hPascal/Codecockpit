# Module von CodeCockpit

Eine Zeile je Datei. Die Zeile ist die erste Zeile des Docstrings der Datei.
Neu erzeugt am 22.10.2026. Bitte nach neuen Dateien ergänzen.

## cockpit

- __init__.py (4 Zeilen): CodeCockpit: barrierefreie Verwaltung von Code-Projekten.
- testdata.py (359 Zeilen): Testdaten für die Tests mit NVDA (Start mit start_testdaten.bat).
- testdata_platform.py (92 Zeilen): Testplattform für die Testdaten (nur mit start_testdaten.bat).

## cockpit/adapters

- __init__.py (1 Zeilen): Gemeinsame Grundlagen aller Adapter (Plattform, KI, Tresor, Automation, E-Mail).
- base.py (55 Zeilen): Basisklasse für alle Adapter.
- registry.py (51 Zeilen): Tabelle aller Adapter pro Art.

## cockpit/ai

- __init__.py (1 Zeilen): KI-Adapter: Ollama, OpenAI-kompatibel, später Azure OpenAI, Anthropic und Gemini.
- base.py (41 Zeilen): Schnittstelle für KI-Anbieter (Konzept 11). Vorbild ist LLMBackend aus dem Chatbot.
- models.py (67 Zeilen): Vorgeschlagene lokale Modelle nach Arbeitsspeicher (Konzept 11.1).
- ollama.py (206 Zeilen): KI-Adapter für Ollama auf diesem Rechner (Konzept 11.1). Vorbild: Chatbot und Tagebuch.
- openai_compatible.py (122 Zeilen): KI-Adapter für OpenAI-kompatible Schnittstellen (Konzept 11).
- prompt_files.py (36 Zeilen): Prompts als Textdateien (Konzept 11, Frage 14 zu Phase 8).
- recording.py (55 Zeilen): Mikrofonaufnahme für die Spracheingabe (Teilschritt 8d). Vorbild: sprache/aufnahme.py im
- streaming.py (66 Zeilen): Antworten der KI Stück für Stück lesen, mit Abbruch (Muster aus dem Chatbot).
- whisper.py (173 Zeilen): Sprach-KI: Whisper lokal mit faster-whisper (Konzept 10.15 und 11.1, Teilschritt 8d).

## cockpit/automation

- __init__.py (1 Zeilen): Automations-Adapter: keine Automation, später n8n.
- base.py (39 Zeilen): Schnittstelle für Automationsdienste wie n8n (Konzept 12). Umsetzung ab Phase 10.
- none.py (35 Zeilen): Adapter "Keine Automation": Kern und lokale Features funktionieren ohne n8n.

## cockpit/core

- __init__.py (1 Zeilen): Der Kern: Logik ohne Oberfläche. Nichts in diesem Paket importiert PySide6.
- accounts.py (225 Zeilen): Konten (Konzept 5.1): Zugänge zu Plattformen, KI, E-Mail und Automation.
- actions.py (168 Zeilen): Aktionen für die Aktionsliste (Konzept 8.3).
- activity.py (42 Zeilen): Arbeitet die KI gerade? (Wunsch des Nutzers vom 14.10.2026)
- ai_tools.py (215 Zeilen): KI-Werkzeuge (Konzept 11.1, Teilschritt 8b).
- ai_tuning.py (156 Zeilen): Die KI auf den Rechner einstellen (Wunsch des Nutzers vom 07.10.2026).
- availability.py (21 Zeilen): Ob etwas verfügbar ist, und wenn nicht, warum.
- backups.py (186 Zeilen): Sicherheitskopien vor Änderungen an Dateien (Konzept 9.7, CLAUDE.md).
- branches.py (528 Zeilen): Branches und beiseitegelegte Änderungen (Konzept 10.14, Teilschritt 5f).
- conflicts.py (148 Zeilen): Konfliktstellen einer Datei vorlesen und einzeln lösen (Wunsch des Nutzers vom 21.10.2026,
- core_actions.py (162 Zeilen): Aktionen des Kerns für die Aktionsliste.
- database.py (240 Zeilen): SQLite-Datenbank des Cockpits mit Versionsnummer und Umbau-Schritten (Migrationen).
- editor.py (128 Zeilen): Dateien und Ordner im Editor öffnen (Wunsch des Nutzers vom 21.10.2026, nach dem Vergleich mit
- error_windows.py (93 Zeilen): Fehlerfenster einer gestarteten Exe finden (Rückmeldung des Nutzers vom 02.10.2026).
- errors.py (19 Zeilen): Gemeinsame Fehlerklassen.
- exe.py (170 Zeilen): Die Exe eines Projekts (Konzept 10.4, Phase 10).
- exe_folders.py (339 Zeilen): Ordner der Exe im Ordner Release: anlegen, aufräumen, übernehmen, alte Versionen.
- exe_install.py (277 Zeilen): Gebaute Exe testen und an ihren Platz bringen, auch für Branches.
- exe_probe.py (130 Zeilen): Probelauf vor dem Exe-Bau (Wunsch des Nutzers vom 21.10.2026: Exe-Bau robuster machen).
- exe_publish.py (120 Zeilen): Versionen und Veröffentlichen der Exe (Phase 10).
- exe_python.py (365 Zeilen): Python und virtuelle Umgebung für den Bau der Exe.
- exe_report.py (199 Zeilen): Bericht bei Fehlern beim Exe-Bau (Wunsch des Nutzers vom 14.10.2026).
- exe_restart.py (143 Zeilen): Eigene Exe des Cockpits: Austausch beim Neustart.
- exe_spec.py (77 Zeilen): Die .spec-Datei für PyInstaller: schreiben, erkennen, Einstellungen ändern.
- exe_state.py (348 Zeilen): Zustand der Exe eines Projekts: Herkunft, Einstellungen zum Bauen, Zeile im Projektbaum.
- forks.py (119 Zeilen): Forks: zu fremden Projekten beitragen (Wunsch des Nutzers vom 21.10.2026, nach dem Vergleich
- git.py (326 Zeilen): Aufruf von Git (Konzept 9, Grundsatz aus ENTSCHEIDUNGEN.md: wie Git im Terminal).
- hardware.py (100 Zeilen): Arbeitsspeicher, Prozessor und Grafikkarte auslesen (Konzept 11.1). Vorbild: Chatbot.
- history.py (571 Zeilen): Verlauf und Rückgängig machen (Konzept 9.4 und 9.7, Teilschritt 5d).
- http.py (37 Zeilen): HTTP-Verbindungen für alle Adapter.
- identity.py (59 Zeilen): Git-Identität in jedem Projekt (Konzept 9.8, ENTSCHEIDUNGEN.md).
- issues.py (81 Zeilen): Issues: Zeilen für Listen, Branch-Namen und die Angaben für die KI (Wunsch des Nutzers vom
- licenses.py (76 Zeilen): Lizenzdatei eines Projekts (Wunsch des Nutzers vom 03.10.2026), ohne Qt.
- list_filter.py (96 Zeilen): Filter oben in der Projektliste und Zeichen für Offenes (Wunsch des Nutzers vom 07.10.2026).
- local_releases.py (170 Zeilen): Die Releases eines Projekts auf dem Rechner (Wunsch des Nutzers vom 06.10.2026).
- logging_setup.py (65 Zeilen): Log mit Schutz vor Geheimnissen.
- long_paths.py (51 Zeilen): Lange Pfade in Windows (Wunsch des Nutzers, 01.10.2026).
- paths.py (73 Zeilen): Ordner für Daten, Logs und Zwischenspeicher.
- project_admin.py (240 Zeilen): Projekt umbenennen und löschen (Wunsch des Nutzers vom 06.10.2026, "Projekt verwalten").
- project_collections.py (132 Zeilen): Projektsammlungen: Projekte nach Themen ordnen (Wunsch des Nutzers vom 29.09.2026).
- project_setup.py (87 Zeilen): Projekte herunterladen und wieder verbinden (Konzept 7.3 und 7.5).
- project_status.py (202 Zeilen): Stand der Projekte für die Projektliste (Konzept 8.2).
- projects.py (490 Zeilen): Projekte und ihre Ordner (Konzept 7).
- pull_requests.py (324 Zeilen): Pull Requests (Konzept 10.14, Phase 6).
- quick_guides.py (103 Zeilen): Kurzanleitungen für das Hilfefenster (Wunsch des Nutzers vom 07.10.2026).
- remote_repos.py (121 Zeilen): Repositories der Plattform-Konten für die Projektliste (ENTSCHEIDUNGEN.md, Phase 5).
- repo_admin.py (125 Zeilen): Links und Repository verwalten (Konzept 9.5, Teilschritt 5e).
- rewrite.py (221 Zeilen): Commits nachbessern, übernehmen, zusammenfassen und umsortieren (Wunsch des Nutzers vom
- safety_check.py (357 Zeilen): Sicherheitsprüfung vor dem Hochladen (Konzept 9.6). Teil des Kerns und nicht abschaltbar.
- secret.py (62 Zeilen): Hülle für Geheimnisse (Tokens, API-Schlüssel, Passwörter).
- services.py (207 Zeilen): Der Behälter, über den Features und Oberfläche an Kern-Dienste und Adapter kommen.
- settings.py (106 Zeilen): Grundeinstellungen der Installation.
- staging.py (183 Zeilen): Auswählen, was in den Commit kommt (Wunsch des Nutzers vom 21.10.2026).
- sync.py (574 Zeilen): Änderungen hochladen und holen (Konzept 9.2 und 9.3, Teilschritt 5c).
- terminal.py (174 Zeilen): Eingebautes Terminal (Konzept 9.9, Teilschritt 8a).
- text.py (46 Zeilen): Kleine Hilfen für deutsche Texte.
- trash.py (53 Zeilen): Dateien in den Papierkorb von Windows verschieben (Konzept 9.7, ENTSCHEIDUNGEN.md).
- update.py (313 Zeilen): Selbst-Aktualisierung der Exe des Cockpits (Konzept 10.5).
- upload.py (213 Zeilen): Auf GitHub hochladen (Konzept 9.1, geändert: Hinzufügen und Hochladen sind getrennt).
- vault_service.py (152 Zeilen): Der Tresor aus Sicht des Kerns: gewählte Speicherart, Namensliste und Wechsel (Konzept 5.2).
- venv_repair.py (165 Zeilen): Virtuelle Umgebung nach dem Verschieben eines Projekts (Konzept 7.5).
- worktrees.py (251 Zeilen): Ein Ordner pro Branch (Phase 10f).

## cockpit/core/features

- __init__.py (1 Zeilen): Das Feature-System (Konzept 3.2): Manifest, Register und Verwaltung.
- manager.py (300 Zeilen): Welches Feature wo aktiv ist (Konzept 3.2, 8.4 und 8.5).
- manifest.py (78 Zeilen): Beschreibung eines Features (Konzept 3.2).
- registry.py (119 Zeilen): Findet und prüft alle Features.
- settings_fields.py (180 Zeilen): Beschreibung von Einstellungsfeldern.

## cockpit/core/flows

- __init__.py (1 Zeilen): Abläufe mit Einhängepunkten (Konzept 3.3).
- engine.py (194 Zeilen): Der Ablauf-Motor (Konzept 3.3 und 9.2).
- hooks.py (20 Zeilen): Die festen Einhängepunkte der Abläufe (Konzept 3.3).
- questions.py (55 Zeilen): Rückfragen aus einem laufenden Ablauf an den Nutzer.
- step.py (31 Zeilen): Ein Schritt eines Ablaufs und sein Ergebnis.

## cockpit/email

- __init__.py (1 Zeilen): E-Mail-Adapter: später SMTP mit Anbietervorlagen und Microsoft 365.
- base.py (25 Zeilen): Schnittstelle für den E-Mail-Versand (Konzept 5.5). Umsetzung in Phase 11.

## cockpit/features

- __init__.py (4 Zeilen): Die Features. Jedes Unterpaket mit manifest.py ist ein Feature (siehe core/features/registry.py).

## cockpit/features/activity

- __init__.py (1 Zeilen): Feature "Aktivität" (Wunsch des Nutzers vom 22.10.2026).
- activity.py (233 Zeilen): Aktivität der Projekte, ohne Qt (Wunsch des Nutzers vom 22.10.2026).
- manifest.py (18 Zeilen): Feature "Aktivität" (Wunsch des Nutzers vom 22.10.2026, Plan in PLAN-NEUIGKEITEN-UND-MODULE.md).

## cockpit/features/ai_assistant

- context.py (211 Zeilen): Was die KI für einen Vorschlag bekommt (Konzept 10.1, Frage 8 zu Phase 8).
- manifest.py (25 Zeilen): Feature "KI-Assistent" (Konzept 10.1, Teilschritt 8c).
- suggest.py (93 Zeilen): Vorschläge des KI-Assistenten (Konzept 10.1). Alles blockiert, also im Hintergrund aufrufen.

## cockpit/features/ai_help

- knowledge.py (104 Zeilen): Wissen für die KI-Hilfe (Teilschritt 8e), ohne Qt.
- manifest.py (22 Zeilen): Feature "KI-Hilfe" (Konzept 10.17, Teilschritt 8e).

## cockpit/features/branches_prs

- __init__.py (1 Zeilen): Feature "Branches und Pull Requests" (Konzept 10.14, Phase 6c).
- manifest.py (24 Zeilen): Feature "Branches und Pull Requests" (Konzept 10.14, ENTSCHEIDUNGEN.md zu Phase 6).

## cockpit/features/dictation

- manifest.py (24 Zeilen): Feature "Spracheingabe" (Konzept 10.15, Teilschritt 8d).

## cockpit/features/exe_build

- ai_fix.py (422 Zeilen): Exe mit KI einrichten (Phase 10g).
- exe_branch.py (127 Zeilen): Branch für die Änderungen der KI an der Exe-Einrichtung (Wunsch des Nutzers, 01.10.2026).
- imports_check.py (98 Zeilen): Fehlende Importe finden und ergänzen, ohne KI (Rückmeldung des Nutzers vom 02.10.2026).
- manifest.py (20 Zeilen): Feature "Exe-Erstellung" (Konzept 10.4, Phase 10).
- setup_check.py (413 Zeilen): Exe-Einrichtung prüfen (Konzept 10.4). Ergebnis als Zeilen, das Ergebnis jeweils vorne.

## cockpit/features/explanations

- manifest.py (26 Zeilen): Feature "Erklärungen" (Wunsch des Nutzers vom 25.10.2026).
- texts.py (606 Zeilen): Die Texte der Erklärungen (Wunsch des Nutzers vom 25.10.2026).

## cockpit/features/news

- __init__.py (1 Zeilen): Feature "Neuigkeiten" (Wunsch des Nutzers vom 22.10.2026).
- manifest.py (19 Zeilen): Feature "Neuigkeiten" (Wunsch des Nutzers vom 22.10.2026, Plan in PLAN-NEUIGKEITEN-UND-MODULE.md).
- news.py (201 Zeilen): Neuigkeiten seit dem letzten Start, ohne Qt (Wunsch des Nutzers vom 22.10.2026).

## cockpit/features/packages

- base.py (165 Zeilen): Gemeinsame Bausteine der Paketübersicht.
- cache.py (64 Zeilen): Gespeicherte Liste der Paketübersicht (Wunsch des Nutzers vom 24.10.2026).
- catalog.py (231 Zeilen): Alle Quellen der Paketübersicht an einer Stelle: laden, prüfen, ändern.
- choco_source.py (111 Zeilen): Programme aus Chocolatey.
- cleanup.py (158 Zeilen): Aufräumen (Stufe 2 der Paketübersicht): wo Platz frei werden kann.
- manifest.py (20 Zeilen): Feature "Paketübersicht" (Wunsch des Nutzers vom 21.10.2026, Plan in PLAN-PAKETUEBERSICHT.md).
- models.py (346 Zeilen): Sprachmodelle auf dem Rechner.
- osv.py (53 Zeilen): Bekannte Sicherheitslücken in Python-Bibliotheken (Stufe 3 der Paketübersicht).
- pip_source.py (179 Zeilen): Python-Bibliotheken: das globale Python, die Umgebungen der Projekte und die für den Exe-Bau.
- project_update.py (227 Zeilen): Neuere Bibliotheken und Modelle in Projekten einsetzen (Stufe 3 der Paketübersicht).
- record.py (113 Zeilen): Was die Paketübersicht sich merkt.
- runner.py (139 Zeilen): Programme der Paketübersicht aufrufen: pip, winget, choco und ollama.
- transfer.py (94 Zeilen): Liste für einen neuen Rechner (Stufe 3 der Paketübersicht).
- usage.py (124 Zeilen): Wer benutzt was (Stufe 2 der Paketübersicht).
- web.py (61 Zeilen): Abfragen im Internet für die Paketübersicht: PyPI, Hugging Face, Ollama und OSV.
- winget_source.py (167 Zeilen): Programme aus winget.

## cockpit/features/readme

- content.py (177 Zeilen): Inhalt der README-Abschnitte (Konzept 10.2, Phase 9), ohne Qt.
- document.py (174 Zeilen): Aufbau einer README und was das Cockpit darin pflegt (Konzept 10.2, Phase 9), ohne Qt.
- manifest.py (36 Zeilen): Feature "README-Pflege" (Konzept 10.2, Phase 9).
- plan.py (235 Zeilen): README schreiben, überarbeiten und übersetzen (Konzept 10.2, Phase 9), ohne Qt.
- steps.py (169 Zeilen): Prüfung der README vor dem Hochladen (Konzept 10.2, Frage 10 zu Phase 9).

## cockpit/features/releases

- manifest.py (19 Zeilen): Feature "Releases" (Konzept 10.5 und Abschnitt 15, Punkt 14; Phase 14).
- runs.py (111 Zeilen): Releases und GitHub Actions ohne Qt (Phase 14).

## cockpit/features/terminal_explain

- explain.py (33 Zeilen): Erklärung eines fehlgeschlagenen Befehls durch die KI (Konzept 10.16).
- manifest.py (21 Zeilen): Feature "Terminal-Erklärung" (Konzept 10.16, Teilschritt 8b).

## cockpit/features/versions

- manifest.py (25 Zeilen): Feature "Versionen" (Konzept 10.3, Phase 9): Versionsnummern und Git-Tags beim Hochladen.
- steps.py (87 Zeilen): Schritte des Features Versionen im Ablauf "Änderungen hochladen" (Phase 9).
- versions.py (113 Zeilen): Versionen mit Git-Tags (Konzept 10.3, Phase 9), ohne Qt.

## cockpit/platforms

- __init__.py (1 Zeilen): Plattform-Adapter: GitHub, später GitLab und Azure DevOps.
- activity.py (88 Zeilen): Neuigkeiten und Aktivität auf einer Code-Plattform (Wunsch des Nutzers vom 22.10.2026).
- base.py (641 Zeilen): Schnittstelle für Code-Plattformen (Konzept 6.3).
- github.py (267 Zeilen): GitHub und GitHub Enterprise Server (Konzept 6).
- github_activity.py (149 Zeilen): Neuigkeiten und Aktivität auf GitHub: Issues, Kommentare, Sterne, Forks, Releases, fehlgeschlagene
- github_common.py (72 Zeilen): Gemeinsame Teile für GitHub: Adressen, Rechte bei der Anmeldung, Texte für Fehler.
- github_issues.py (88 Zeilen): Issues auf GitHub: lesen, anlegen, kommentieren, Labels und Zuständige.
- github_login.py (104 Zeilen): Anmeldung bei GitHub im Browser (Device Flow einer OAuth-App).
- github_pulls.py (149 Zeilen): Pull Requests auf GitHub: lesen, anlegen, kommentieren, Reviews, Checks, übernehmen.
- github_releases.py (125 Zeilen): Releases und GitHub Actions: anlegen, Dateien hoch- und herunterladen, Läufe und Protokolle.
- github_repos.py (216 Zeilen): Repositories auf GitHub: anlegen, ändern, löschen, Mitarbeiter, Schutz der Branches, Forks.

## cockpit/testdata_features

- __init__.py (5 Zeilen): Beispiel-Features nur für den Start mit Testdaten (ENTSCHEIDUNGEN.md, Phase 7).

## cockpit/testdata_features/beispiel_aufbau

- __init__.py (1 Zeilen): Beispiel-Feature "Beispiel Aufbau" (nur Testdaten).
- manifest.py (9 Zeilen): Beispiel Aufbau: braucht Beispiel Grundlage (nur Testdaten).

## cockpit/testdata_features/beispiel_grundlage

- __init__.py (1 Zeilen): Beispiel-Feature "Beispiel Grundlage" (nur Testdaten).
- manifest.py (22 Zeilen): Beispiel Grundlage: hat eigene Einstellungen und eine Aktion bei Code (nur Testdaten).

## cockpit/ui

- __init__.py (1 Zeilen): Die Oberfläche (PySide6).
- account_edit_dialog.py (517 Zeilen): Ein Konto anlegen oder ändern.
- accounts_dialog.py (175 Zeilen): Kontenverwaltung (Menü Konten, Konzept 5.1).
- action_conditions.py (128 Zeilen): Stand und Bedingungen hinter den Aktionen der Projektliste (Wunsch des Nutzers, 02.10.2026).
- action_list.py (88 Zeilen): Die Aktionsliste (Konzept 8.3).
- ai_dialogs.py (345 Zeilen): KI-Verwaltung (Menü KI, Konzept 11.1, Teilschritt 8b).
- ai_help_dialog.py (195 Zeilen): KI-Hilfe (Konzept 10.17, Teilschritt 8e): Hilfe, KI-Hilfe oder Umschalt+F1.
- ai_model_dialogs.py (256 Zeilen): Modell wählen und Arbeitsspeicher angeben.
- ai_speech_dialogs.py (202 Zeilen): Sprache: Spracherkennung und Vorlesen einrichten.
- ai_suggest.py (226 Zeilen): Knopf "Vorschlag der KI" (Feature KI-Assistent, Konzept 10.1, Teilschritt 8c).
- ai_tuning_ui.py (190 Zeilen): Starttest der KI und das Fenster „KI ist eingestellt auf diesen Rechner …“ (07.10.2026).
- ai_ui.py (54 Zeilen): Text-KI für eine Aufgabe vorbereiten (Konzept 11, ENTSCHEIDUNGEN.md zu Phase 8).
- announcer.py (151 Zeilen): Ansagen für den Screenreader (Muster aus Chatbot und Tagebuch).
- asker.py (61 Zeilen): Brücke für Rückfragen aus Hintergrund-Abläufen an die Oberfläche.
- backups_dialog.py (171 Zeilen): Fenster "Sicherheitskopien" im Menü Datei (Wunsch aus dem Test von 5c).
- branch_dialogs.py (611 Zeilen): Übersicht "Branches" und beiseitegelegte Änderungen (Konzept 10.14, Teilschritt 5f).
- browser_login_dialog.py (146 Zeilen): Anmeldung im Browser (Konzept 6.1, Device Flow).
- collections_flow.py (269 Zeilen): Projektsammlungen in der Projektliste (Wunsch des Nutzers vom 29.09.2026).
- common.py (207 Zeilen): Kleine Hilfen für die Oberfläche (Muster aus Chatbot und Tagebuch).
- conflict_dialogs.py (145 Zeilen): Konfliktstellen einer Datei: vorlesen und Stelle für Stelle lösen (21.10.2026).
- dictation.py (293 Zeilen): Spracheingabe in der Oberfläche (Konzept 10.15, Teilschritt 8d).
- editor_ui.py (37 Zeilen): Im Editor öffnen, aus jedem Dialog heraus (21.10.2026).
- error_dialog.py (67 Zeilen): Fehlerfenster: einfacher Text, auf Wunsch technische Details (Konzept 8.6).
- exe_ai.py (140 Zeilen): Fortschritt beim Einrichten der Exe (Phase 10g, seit dem 03.10.2026 Schritt 3 von "Exe aus dem
- exe_chat.py (173 Zeilen): Fragen an die KI nach einem Schritt beim Einrichten der Exe (Wunsch des Nutzers, 02.10.2026).
- exe_dialogs.py (508 Zeilen): Fenster zur Exe (Phase 10): Einstellungen zum Bau, der Bau selbst und das Veröffentlichen.
- exe_flow.py (721 Zeilen): Die Exe in der Oberfläche (Konzept 10.4, Phase 10).
- exe_wizard.py (330 Zeilen): Exe aus dem Code erstellen, Schritt für Schritt (Wunsch des Nutzers vom 03.10.2026).
- exe_wizard_steps.py (411 Zeilen): Die einzelnen Schritte des Exe-Assistenten.
- explanations.py (273 Zeilen): Oberfläche des Features Erklärungen (Wunsch des Nutzers vom 25.10.2026).
- features_dialogs.py (451 Zeilen): Feature-Verwaltung (Konzept 8.4 und 8.5, Phase 7).
- folder_rename_flow.py (161 Zeilen): Ordner Code und Exe in Repository und Release umbenennen (Antwort des Nutzers vom 06.10.2026).
- fork_flow.py (124 Zeilen): Forks in der Oberfläche (Wunsch des Nutzers vom 21.10.2026, siehe core/forks.py).
- form_builder.py (168 Zeilen): Baut aus Einstellungsfeldern (core/features/settings_fields.py) ein barrierefreies Formular.
- help_window.py (183 Zeilen): Hilfefenster mit Kurzanleitungen (Wunsch des Nutzers vom 07.10.2026). F1 oder Menü Hilfe.
- history_dialogs.py (194 Zeilen): Fenster für Verlauf und Rückgängig machen (Konzept 9.4 und 9.7, Teilschritt 5d).
- history_edit_dialogs.py (518 Zeilen): Eine Version ansehen und den Verlauf ändern: umsortieren, nachbessern, verwerfen, hochladen.
- identity_dialog.py (109 Zeilen): Fenster "Git-Identität" nach dem Anlegen eines Plattform-Kontos (Wunsch des Nutzers, 28.09.2026).
- issue_dialogs.py (430 Zeilen): Issues lesen, anlegen, kommentieren, schließen, mit Labels und Zuweisen (Wunsch des Nutzers vom
- issue_flow.py (93 Zeilen): Issues in der Oberfläche (21.10.2026): im Hintergrund die offenen Issues, die Labels und die
- license_flow.py (157 Zeilen): Lizenz eines Projekts in der Oberfläche (Wunsch des Nutzers vom 03.10.2026).
- look.py (92 Zeilen): Aussehen für das Auge (PLAN-OPTIK.md, Schritte 4, 5 und 7, 22.10.2026).
- main_window.py (224 Zeilen): Hauptfenster: Menüleiste, Projektliste, Aktionsliste und Statuszeile.
- menus.py (51 Zeilen): Barrierefreie Menüs (zusammengeführt aus Chatbot und Tagebuch).
- messages_dialog.py (33 Zeilen): Liste der letzten Meldungen, neueste oben (Strg+Umschalt+L).
- news_dialogs.py (212 Zeilen): Fenster "Neuigkeiten" und "Aktivität" (Wunsch des Nutzers vom 22.10.2026).
- news_flow.py (116 Zeilen): Menü Neuigkeiten und die Ansage nach dem Start (Wunsch des Nutzers vom 22.10.2026).
- package_dialogs.py (807 Zeilen): Fenster der Paketübersicht (Wunsch des Nutzers vom 21.10.2026, PLAN-PAKETUEBERSICHT.md).
- package_flow.py (420 Zeilen): Menü Pakete und die Abläufe der Paketübersicht (Wunsch des Nutzers vom 21.10.2026).
- password_dialogs.py (116 Zeilen): Dialoge für das Master-Passwort der Tresordatei (Konzept 5.2).
- project_actions.py (276 Zeilen): Aktionen rund um Projekte, die Dialoge oder Hintergrund-Arbeit brauchen (Phase 5a).
- project_add_actions.py (243 Zeilen): Projekt vom Rechner hinzufügen: Aufbau prüfen, Ordner umstellen, danach hochladen anbieten.
- project_git_actions.py (326 Zeilen): Git-Aktionen auf Main-Branch und Branch: hochladen, holen, Verlauf, Branches, Beiseitelegen.
- project_labels.py (210 Zeilen): Texte der Projektliste: Beschriftungen, Filter und Kinder eines Eintrags.
- project_list.py (644 Zeilen): Die Projektliste (Konzept 8.2, umgesetzt als Liste statt Baum, siehe ENTSCHEIDUNGEN.md).
- project_list_delegate.py (51 Zeilen): Zeichner der Projektliste, nur für das Auge (PLAN-OPTIK.md, Schritte 1 und 3, 22.10.2026).
- project_manage.py (243 Zeilen): Projekt verwalten (Wunsch des Nutzers vom 06.10.2026).
- project_manage_actions.py (200 Zeilen): Projekt verwalten: neu einlesen, Filter, Features, Links, entfernen, neuer Ort, Umgebung.
- project_remote_actions.py (332 Zeilen): Projekt und Plattform: Repository anlegen, herunterladen, verbinden, löschen, ausblenden.
- proposal_dialog.py (76 Zeilen): Vorschlag zum Lesen, Übernehmen, Bearbeiten oder Überspringen (Rückmeldung vom 07.10.2026).
- pull_request_dialogs.py (479 Zeilen): Pull Requests ansehen, erstellen und kommentieren (Konzept 10.14, Teilschritt 6a).
- pull_request_flow.py (218 Zeilen): Pull Requests in der Oberfläche (Teilschritt 6a).
- pull_request_forms.py (292 Zeilen): Pull Request anlegen, kommentieren, prüfen und übernehmen.
- quick_nav.py (209 Zeilen): Schnellnavigation, Befehlssuche und Tastenhinweise (Wunsch des Nutzers vom 07.10.2026).
- readme_dialogs.py (352 Zeilen): Dialoge für die README: Text, Schreiben, Ändern, Übersetzen, Sprachen.
- readme_flow.py (190 Zeilen): README-Pflege in der Oberfläche (Konzept 10.2, Phase 9).
- release_rows.py (267 Zeilen): Aktionen der Zeile Releases und der Release-Zeilen (Wunsch des Nutzers vom 06.10.2026).
- releases_flow.py (499 Zeilen): Releases und GitHub Actions in der Oberfläche (Phase 14).
- repo_delete.py (162 Zeilen): Repository löschen: Name zur Bestätigung eintippen, dann löschen.
- repo_dialog_parts.py (89 Zeilen): Bausteine der Repository-Dialoge: Hintergrundarbeit und Knopfzeile.
- repo_dialogs.py (313 Zeilen): Links, Repository verwalten und Mitarbeiter (Konzept 9.5, Teilschritt 5e).
- repo_people_dialogs.py (278 Zeilen): Mitarbeiter einladen und verwalten, Schutz der Branches.
- row_delegate.py (112 Zeilen): Zeilen in Listen mit zwei Textebenen, nur für das Auge (PLAN-OPTIK.md, Schritt 3).
- settings_dialog.py (50 Zeilen): Dialog Grundeinstellungen (Menü Einstellungen).
- setup_pages.py (662 Zeilen): Die Seiten des Einrichtungs-Assistenten.
- setup_wizard.py (143 Zeilen): Einrichtungsassistent beim ersten Start (Konzept 8.7, ohne Profile).
- sounds.py (297 Zeilen): Töne beim Hoch- und Herunterladen (Wunsch des Nutzers vom 07.10.2026) und während die KI
- sounds_dialog.py (68 Zeilen): Fenster "Signaltöne" im Menü Einstellungen (Wunsch des Nutzers vom 24.10.2026).
- stash_dialogs.py (163 Zeilen): Beiseitegelegte Änderungen und Name für einen neuen Branch.
- state_panel.py (57 Zeilen): Bereich "Stand" unter den Aktionen, nur für das Auge (PLAN-OPTIK.md, Schritt 2, 22.10.2026).
- sync_dialogs.py (497 Zeilen): Fenster für Änderungen hochladen und holen (Konzept 9.2 und 9.3).
- sync_flow.py (446 Zeilen): Änderungen hochladen und holen in der Oberfläche (Konzept 9.2 und 9.3, Teilschritt 5c).
- tasks.py (95 Zeilen): Hintergrund-Aufgaben (Muster aus Chatbot und Tagebuch). Die Oberfläche blockiert nie.
- terminal_dialog.py (331 Zeilen): Fenster "Terminal" (Konzept 9.9, Teilschritt 8a).
- text_dialog.py (59 Zeilen): Fenster, das einen Text als Liste zeigt: eine Zeile pro Eintrag.
- update_ui.py (221 Zeilen): Updates der Exe des Cockpits: Prüfung bei jedem Start, Rückfrage, Austausch.
- upload_dialogs.py (305 Zeilen): Fenster für das erste Hochladen (Konzept 9.1 und 9.6).
- upload_flow.py (216 Zeilen): Ablauf "Auf GitHub hochladen" in der Oberfläche (Konzept 9.1).
- vault_settings_dialog.py (109 Zeilen): Dialog Tresor-Einstellungen (Menü Konten, Konzept 13).
- vault_ui.py (89 Zeilen): Tresor in der Oberfläche: entsperren bei Bedarf und Speicherart wechseln (Konzept 5.2).
- videos.py (31 Zeilen): Erklärvideos im Ordner erklärvideos (Wunsch des Nutzers, 29.09.2026).
- window_actions.py (198 Zeilen): Aktionsliste des Hauptfensters: Kontext, Ausführen, Kontextmenü, Fokus.
- window_menus.py (301 Zeilen): Menüleiste und Tastenkürzel des Hauptfensters, dazu die Fenster, die die Menüs öffnen.
- window_status.py (228 Zeilen): Stand der Projekte im Hauptfenster: neu einlesen, Git-Stand und Stand auf der Plattform holen.
- window_vault.py (74 Zeilen): Tresor im Hauptfenster: sperren, entsperren, automatisch sperren, Konten.
- worktree_flow.py (324 Zeilen): Ein Ordner pro Branch in der Oberfläche (Phase 10f).

## cockpit/vault

- __init__.py (1 Zeilen): Tresor-Adapter: Windows-Anmeldeinformationsverwaltung und verschlüsselte Tresordatei.
- base.py (48 Zeilen): Schnittstelle für den Tresor (Konzept 5.2). Die echten Adapter kommen in Phase 3.
- crypto.py (52 Zeilen): Verschlüsselung für Tresordatei und Sicherung (Konzept 5.2, Verfahren aus dem Tagebuch).
- vault_file.py (166 Zeilen): Verschlüsselte Tresordatei mit Master-Passwort (Konzept 5.2).
- windows.py (75 Zeilen): Tresor in der Windows-Anmeldeinformationsverwaltung (Konzept 5.2), über die Bibliothek keyring.
