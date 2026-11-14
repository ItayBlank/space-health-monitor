"""Download the official English Vosk model once; subsequent speech is offline."""
import argparse
from pathlib import Path
import sys
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hal2030.downlink import DownlinkService

MODEL = 'vosk-model-small-en-us-0.15'
URL = f'https://alphacephei.com/vosk/models/{MODEL}.zip'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path)
    args = parser.parse_args()
    target = args.destination or DownlinkService().output_dir.parent / 'voice-model'
    target.mkdir(parents=True, exist_ok=True)
    if (target / MODEL / 'am/final.mdl').exists():
        print(f'Model already present: {target / MODEL}')
        return
    archive = target / (MODEL + '.zip')
    print(f'Downloading {URL}')
    urllib.request.urlretrieve(URL, archive)
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
