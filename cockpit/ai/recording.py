"""Mikrofonaufnahme für die Spracheingabe (Teilschritt 8d). Vorbild: sprache/aufnahme.py im
Tagebuch.

Die Aufnahme bleibt nur im Arbeitsspeicher, bis die Umwandlung in Text fertig ist. Sie wird nie
auf die Festplatte geschrieben.
"""
from __future__ import annotations

from cockpit.core.errors import CockpitError

SAMPLE_RATE = 16000                    # Hz, was faster-whisper erwartet


class Recording:
    """Nimmt vom Standardmikrofon auf, bis stop() kommt oder max_seconds erreicht sind."""

    def __init__(self, max_seconds: int) -> None:
        self.max_frames = max_seconds * SAMPLE_RATE
        self.blocks: list = []
        self.frames = 0
        self.full = False
        self.stream = None

    def start(self) -> None:
        try:
            import sounddevice
            self.stream = sounddevice.InputStream(samplerate=SAMPLE_RATE, channels=1,
                                                  dtype="float32", callback=self._callback)
            self.stream.start()
        except Exception as exc:              # kein Mikrofon, Treiber, Datenschutz von Windows
            self.stream = None
            raise CockpitError("Es ist kein Mikrofon verfügbar. Bitte prüfen Sie, ob eines "
                               "angeschlossen ist und ob Windows Apps den Zugriff auf das "
                               "Mikrofon erlaubt.", repr(exc)) from None

    def _callback(self, data, frames, time_info, status) -> None:
        if self.full:
            return
        self.blocks.append(data[:, 0].copy())
        self.frames += frames
        if self.frames >= self.max_frames:
            self.full = True

    def stop(self):
        """Aufnahme beenden, gibt sie als numpy-Array zurück (leer, wenn nichts kam)."""
        import numpy
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            finally:
                self.stream = None
        if not self.blocks:
            return numpy.zeros(0, dtype=numpy.float32)
        return numpy.concatenate(self.blocks)[: self.max_frames]
