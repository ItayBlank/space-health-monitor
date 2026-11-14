"""Download the official English Vosk model once; subsequent speech is offline."""
import argparse
import hashlib
from pathlib import Path
import sys
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hal2030.downlink import DownlinkService

from hal2030.voice_model import MODEL_NAME as MODEL, MODEL_URL as URL, MODEL_SHA256, model_present


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path)
    args = parser.parse_args()
    target = args.destination or DownlinkService().output_dir.parent / 'voice-model'
    target.mkdir(parents=True, exist_ok=True)
    if model_present(target / MODEL):
        print(f'Model already present: {target / MODEL}')
        return
    archive = target / (MODEL + '.zip')
    print(f'Downloading {URL}')
    urllib.request.urlretrieve(URL, archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != MODEL_SHA256:
        archive.unlink()
        raise ValueError('Model download checksum mismatch')
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            resolved = (target / info.filename).resolve()
            if not resolved.is_relative_to(target.resolve()) or Path(info.filename).parts[0] != MODEL:
                raise ValueError('Unexpected path in model archive')
        bundle.extractall(target)
    archive.unlink()
    print(f'Ready: {target / MODEL}')


if __name__ == '__main__':
    main()
