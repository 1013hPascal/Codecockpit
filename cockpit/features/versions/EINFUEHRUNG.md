# Versionen

Mit diesem Feature bekommt Ihr Projekt Versionsnummern wie 1.4.0.

Beim Hochladen fragt das Cockpit nach dem Commit: Ist das eine neue Version? Zur Wahl stehen „Keine neue Version“, „Kleine Korrektur“, „Neue Funktion“ und „Große Änderung“. Vorgabe ist „Keine neue Version“. Bei jeder Wahl steht die neue Nummer dabei, zum Beispiel „Neue Funktion, Version 1.4.0“.

Die Version kommt als Tag an den Commit, zum Beispiel v1.4.0, und wird mit hochgeladen. Im Verlauf steht sie bei ihrem Commit.

Steht die Nummer auch im Code, zum Beispiel __version__ = "1.3.2", ändert das Cockpit sie mit, im selben Commit. Welche Datei das ist, findet es selbst. Sie können sie auch in den Einstellungen des Features angeben.

„Exe veröffentlichen“ schlägt dann die zuletzt gesetzte Version vor.
