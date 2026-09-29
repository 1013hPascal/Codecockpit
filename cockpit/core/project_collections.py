"""Projektsammlungen: Projekte nach Themen ordnen (Wunsch des Nutzers vom 29.09.2026).

Eine Sammlung hat nur einen Namen. Ein Projekt steht in höchstens einer Sammlung. Wer es einer
anderen Sammlung zuordnet, nimmt es aus der alten heraus. Wird eine Sammlung aufgelöst, stehen
ihre Projekte wieder einzeln in der Projektliste. Ordner und Dateien bleiben dabei unverändert,
die Zuordnung steht nur in der Datenbank.
"""
from __future__ import annotations

from dataclasses import dataclass

from cockpit.core.database import Database
from cockpit.core.errors import CockpitError

PREFIX = "Sammlung"


@dataclass(frozen=True)
class Collection:
    id: int
    name: str

    @property
    def title(self) -> str:
        """Zum Beispiel "Sammlung Webseiten"."""
        return f"{PREFIX} {self.name}"


def clean_name(name: str) -> str:
    """Leerzeichen am Rand weg. Wer "Sammlung Web" eingibt, meint den Namen "Web"."""
    name = " ".join(name.split())
    if name.lower().startswith(PREFIX.lower() + " "):
        name = name[len(PREFIX) + 1:].strip()
    return name


class CollectionStore:
    def __init__(self, database: Database) -> None:
        self.database = database

    def all(self) -> list[Collection]:
        """Alle Sammlungen, nach Namen sortiert."""
        rows = self.database.query("SELECT id, name FROM collections")
        return sorted((Collection(r["id"], r["name"]) for r in rows),
                      key=lambda c: c.name.lower())

    def get(self, collection_id: int) -> Collection | None:
        row = self.database.query_one("SELECT id, name FROM collections WHERE id = ?",
                                      (collection_id,))
        return Collection(row["id"], row["name"]) if row else None

    def _check_name(self, name: str, own_id: int | None = None) -> str:
        name = clean_name(name)
        if not name:
            raise CockpitError("Bitte geben Sie einen Namen ein.")
        if any(c.name.lower() == name.lower() and c.id != own_id for c in self.all()):
            raise CockpitError(f"Die Sammlung {name} gibt es schon. "
                               "Bitte wählen Sie einen anderen Namen.")
        return name

    def create(self, name: str) -> Collection:
        name = self._check_name(name)
        cursor = self.database.execute("INSERT INTO collections (name) VALUES (?)", (name,))
        return Collection(cursor.lastrowid, name)

    def rename(self, collection_id: int, name: str) -> Collection:
        name = self._check_name(name, collection_id)
        self.database.execute("UPDATE collections SET name = ? WHERE id = ?",
                              (name, collection_id))
        return Collection(collection_id, name)

    def dissolve(self, collection_id: int) -> None:
        """Sammlung löschen. Die Projekte bleiben, nur ohne Sammlung."""
        with self.database.transaction() as conn:
            conn.execute("DELETE FROM collection_members WHERE collection_id = ?",
                         (collection_id,))
            conn.execute("DELETE FROM collections WHERE id = ?", (collection_id,))

    def membership(self) -> dict[int, int]:
        """Projekt -> Sammlung, nur für Projekte in einer Sammlung."""
        rows = self.database.query("SELECT project_id, collection_id FROM collection_members")
        return {r["project_id"]: r["collection_id"] for r in rows}

    def members(self, collection_id: int) -> set[int]:
        return {p for p, c in self.membership().items() if c == collection_id}

    def set_members(self, collection_id: int, project_ids: set[int]) -> None:
        """Genau diese Projekte in die Sammlung. Sie verlassen dabei ihre alte Sammlung.
        Projekte, die nicht mehr markiert sind, stehen danach ohne Sammlung da."""
        with self.database.transaction() as conn:
            conn.execute("DELETE FROM collection_members WHERE collection_id = ?",
                         (collection_id,))
            for project_id in sorted(project_ids):
                conn.execute("INSERT OR REPLACE INTO collection_members "
                             "(project_id, collection_id) VALUES (?, ?)",
                             (project_id, collection_id))
