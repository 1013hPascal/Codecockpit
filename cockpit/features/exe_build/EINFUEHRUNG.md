# Exe-Erstellung

Mit diesem Feature baut das Cockpit aus Ihrem Python-Code eine Exe. Andere können Ihr Programm dann starten, ohne Python zu installieren.

Dafür braucht das Cockpit Python auf Ihrem Rechner. Fehlt es, steht im Menü Hilfe die Anleitung „Python installieren“.

Beim ersten Bauen fragt das Cockpit nach der Startdatei, dem Namen der Exe und der Bauart. Daraus entsteht eine Datei mit der Endung .spec im Ordner Code. Sie wird mit hochgeladen und bei jedem weiteren Bau wiederverwendet.

Das Cockpit legt im Ordner Code eine eigene virtuelle Umgebung an und installiert dort Ihre Bibliotheken und PyInstaller. Beim ersten Mal dauert das einige Minuten.

Die neue Exe wird zuerst getestet. Nur wenn der Test klappt, ersetzt sie die bisherige. Die bisherige kommt vorher in die Sicherheitskopien.

Mit „Exe veröffentlichen …“ legen Sie auf GitHub ein Release mit Versionsnummer an. Die Exe hängt dort als Download.

Mehr steht in der Anleitung „Wie funktioniert die Exe?“ im Menü Hilfe.
