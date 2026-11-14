"""Exercise frozen speech dependencies and model discovery without a microphone."""
import json
from pathlib import Path


def verify_voice_model(output: Path):
    """Load the automatically detected model and decode silence; raise on failure.

    Writes a receipt only after success. No recording device is opened.
    """
    import sounddevice  # Verify the bundled PortAudio library can be imported.
    from vosk import Model, KaldiRecognizer
    from hal2030.downlink import DownlinkService
    from hal2030.voice_model import default_model_path
    from hal2030.vision_voice import COMMANDS

    path = default_model_path(DownlinkService().output_dir.parent)
    model = Model(str(path))
    recognizer = KaldiRecognizer(model, 16000, json.dumps(COMMANDS + ['[unk]']))
    recognizer.AcceptWaveform(bytes(32000))
    result = json.loads(recognizer.FinalResult())
    if result.get('text'):
        raise ValueError('Unexpected recognition from silence')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'model_path': str(path), 'loaded': True,
                                 'silence_decoded': True}), encoding='utf-8')
