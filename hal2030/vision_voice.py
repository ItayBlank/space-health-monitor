"""Optional offline speech input and slow Qt narration for the vision dialog.

Microphone input is session-local, never persisted or transmitted. Recognition
runs on a daemon worker; Qt signals carry finalized commands to the GUI thread.
"""
from __future__ import annotations

import json
from pathlib import Path
import queue
import threading

from PySide6.QtCore import QObject, QLocale, QTimer, Signal
from PySide6.QtTextToSpeech import QTextToSpeech

COMMANDS = ['up', 'down', 'left', 'right', 'continue', 'repeat', 'back', 'pause', 'resume', 'unable']


class _Events(QObject):
    result = Signal(int, str)
    status = Signal(str)
    ready = Signal()
    failed = Signal(str)


class VoiceGuide(QObject):
    """Speak visible instructions and accept only finalized offline commands.

    start requires a locally installed Vosk model and sounddevice. Failures are
    emitted as readable status; buttons remain usable. stop releases microphone.
    """
    command = Signal(str)
    status = Signal(str)
    mode_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tts = QTextToSpeech(self)
        self.tts.setLocale(QLocale('en_US'))
        self.tts.setRate(-0.35)
        self.tts.stateChanged.connect(self._tts_state)
        self.events = _Events()
        self.events.result.connect(self._recognized)
        self.events.status.connect(self.status.emit)
        self.events.ready.connect(self._ready)
        self.events.failed.connect(self._failed)
        self.narration = True
        self.active = False
        self.closed = False
        self.listening = False
        self.generation = 0
        self.worker = None
        self.cancel = threading.Event()
        self.last_text = ''
        self.speaking = False
        self.input_enabled = True
        self.loading = False
        self.error_message = ''

    def publish_mode(self):
        """Emit the current input/output state for the persistent voice indicator."""
        mode = ('speaking' if self.speaking else 'loading' if self.loading else
                'listening' if self.listening else 'waiting' if self.active else
                'error' if self.error_message else 'off')
        self.mode_changed.emit(mode)

    def start(self, model_path: str):
        """Start local microphone recognition once; model loading is nonblocking."""
        if self.worker and self.worker.is_alive():
            return
        self.cancel = threading.Event()
        self.loading = True
        self.error_message = ''
        self.publish_mode()
        self.status.emit('Loading offline speech model…')
        self.worker = threading.Thread(target=self._run, args=(model_path, self.cancel), daemon=True)
        self.worker.start()

    def _run(self, model_path, cancel):
        try:
            import sounddevice as sd
            from vosk import Model, KaldiRecognizer
            if not Path(model_path).is_dir():
                raise ValueError('Select the extracted Vosk model folder first.')
            model = Model(str(model_path))
            recognizer = KaldiRecognizer(model, 16000, json.dumps(COMMANDS + ['[unk]']))
            audio = queue.Queue(maxsize=16)

            def callback(data, frames, time_info, status):
                if status or not self.listening or cancel.is_set():
                    return
                try:
                    audio.put_nowait((self.generation, bytes(data)))
                except queue.Full:
                    pass

            if cancel.is_set():
                return
            with sd.RawInputStream(samplerate=16000, blocksize=1600, dtype='int16',
                                   channels=1, callback=callback):
                self.events.ready.emit()
                last_generation = -1
                while not cancel.is_set():
                    try:
                        generation, data = audio.get(timeout=.1)
                    except queue.Empty:
                        continue
                    if generation != self.generation or not self.listening:
                        continue
                    if generation != last_generation:
                        recognizer.Reset()
                        last_generation = generation
                    if recognizer.AcceptWaveform(data):
                        text = json.loads(recognizer.Result()).get('text', '').strip()
                        if text in COMMANDS:
                            self.events.result.emit(generation, text)
                        elif text:
                            self.events.status.emit('Speech not recognized. Repeat your answer; nothing was scored.')
        except Exception as error:
            if not cancel.is_set():
                self.events.failed.emit(f'Voice input unavailable: {error}. Use buttons or keyboard.')
        finally:
            self.active = False

    def _failed(self, message):
        self.active = False
        self.loading = False
        self.error_message = message
        self.listening = False
        self.generation += 1
        self.status.emit(message)
        self.publish_mode()

    def _ready(self):
        if self.closed:
            return
        self.active = True
        self.loading = False
        self.publish_mode()
        if not self.speaking:
            self._arm(self.generation)

    def _recognized(self, generation, text):
        if not self.closed and self.listening and generation == self.generation:
            self.listening = False
            self.generation += 1
            self.publish_mode()
            self.command.emit(text)

    def say(self, text):
        """Narrate one instruction; suppress recognition until narration and echo delay end."""
        if self.closed:
            return
        self.last_text = text
        self.listening = False
        self.generation += 1
        self.speaking = True
        self.tts.stop()
        if self.narration and self.tts.state() != QTextToSpeech.State.Error:
            self.status.emit('Speaking… microphone commands are suspended.')
            self.tts.say(text)
        else:
            self.speaking = False
            self.status.emit('Text guidance active. Voice narration unavailable or muted.')
            token = self.generation
            QTimer.singleShot(700, lambda: self._arm(token))
        self.publish_mode()

    def _tts_state(self, state):
        if self.closed:
            return
        if state in (QTextToSpeech.State.Ready, QTextToSpeech.State.Error):
            self.speaking = False
            if state == QTextToSpeech.State.Error:
                self.status.emit('Narration unavailable. Follow the visible text.')
            token = self.generation
            QTimer.singleShot(700, lambda: self._arm(token))
        elif state == QTextToSpeech.State.Speaking:
            self.speaking = True
            self.listening = False
        self.publish_mode()

    def _arm(self, token):
        if self.closed or token != self.generation or self.speaking or not self.input_enabled:
            return
        self.listening = self.active
        self.publish_mode()
        self.status.emit('Listening — say your answer or continue.' if self.active else
                         self.error_message or 'Microphone off — buttons and keyboard remain available.')

    def stop(self):
        """Disable commands immediately and signal the worker to release its audio stream."""
        self.closed = True
        self.listening = False
        self.generation += 1
        self.cancel.set()
        self.tts.stop()
        self.active = False
        self.loading = False
        self.speaking = False
        self.publish_mode()
