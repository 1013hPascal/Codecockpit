# Branches und Pull Requests

Mit diesem Feature kommen Ihre Änderungen nicht mehr direkt in main.

Stattdessen fragt „Änderungen hochladen“ auf main, in welchen Branch hochgeladen wird. Der Name wird aus Ihrer Nachricht vorgeschlagen, zum Beispiel „suche-in-pdfs“.

Nach dem Hochladen bietet das Cockpit an, einen Pull Request zu erstellen. Andere können ihn dann prüfen, bevor er in main kommt.

In Firmen ist main oft geschützt. Dann ist dieser Weg ohnehin nötig.

Sie schalten das Feature bei Code mit „Hochladen über Pull Requests einschalten“ ein und mit „Hochladen über Pull Requests ausschalten“ wieder aus.

Die Einstellung steht in der Datei cockpit.toml im Ordner Code. Diese Datei gehört zum Projekt und wird mit hochgeladen.
