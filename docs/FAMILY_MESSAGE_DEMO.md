# Family message demo

Run `python -m uvicorn server:app --host 127.0.0.1 --port 8000` and open `http://127.0.0.1:8000`. Go to **HAL → Family Archive → Family message demo**. The page opens with the 4.4-second Mars reconstruction. Expand **Compare the original and see what was sent** for the source video, low-bitrate encode, and payload download. **Try the shorter example** shows a 1.3-second take by the same CREMA-D actor.

Each transmitted ZIP contains `message.json` (version, frame rate, frame count), `motion.npy` (76 float32 values per frame), and `audio.ogg` (mono Opus at a 24 kbps target). The browser plays previews. The offline CLI renders each ZIP using the same preloaded portrait, with speech and motion on one timeline.

## Offline CLI

Initial setup requires network access. Use Windows PowerShell with Python 3.13, Git, curl, and an FFmpeg build with libx264 and libopus on PATH. Run from the repository checkout:

```powershell
New-Item -ItemType Directory -Force runtime/family-message | Out-Null
git clone https://github.com/KlingAIResearch/LivePortrait.git runtime/family-message/LivePortrait
git -C runtime/family-message/LivePortrait checkout 9b294b3d0536135442ea73cb01e6cb3ca7029dd3
python -m venv runtime/family-message/.venv
.\runtime\family-message\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\runtime\family-message\.venv\Scripts\python.exe -m pip install numpy scipy opencv-python pyyaml rich
$weights = 'runtime/family-message/LivePortrait/pretrained_weights/liveportrait'
$files = @(
  'base_models/appearance_feature_extractor.pth',
  'base_models/motion_extractor.pth',
  'base_models/warping_module.pth',
  'base_models/spade_generator.pth',
  'retargeting_models/stitching_retargeting_module.pth'
)
foreach ($file in $files) {
  $dest = Join-Path $weights $file
  New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
  curl.exe -fL --retry 2 "https://huggingface.co/KlingTeam/LivePortrait/resolve/main/liveportrait/$file" -o $dest
  if ($LASTEXITCODE -ne 0) { throw "Could not download $file" }
}
```

After installing the runtime, render either shipped ZIP offline:

```powershell
$python = '.\runtime\family-message\.venv\Scripts\python.exe'
$model = 'runtime/family-message/LivePortrait'
$demo = 'static/family-media'
foreach ($name in 'one','two') {
  & $python tools/family_liveportrait.py --liveportrait $model render "$demo/$name.zip" "$demo/portrait.png" "runtime/family-message/$name-rendered.mp4" --paste-back 242:242:86:16
  if ($LASTEXITCODE -ne 0) { throw "Rendering failed for $name" }
}
```

To regenerate the payloads, first extract an eyes-open, closed-mouth calibration image from the untrimmed source. This frame comes from the original recording session and is distinct from the portrait. The sender uses it before computing motion. The receiver needs only the ZIP, portrait, and preinstalled runtime.

```powershell
$assets = 'runtime/family-message'
$revision = '1658cd342dff90010aa843eaeebd53610a08b1dc'
$source = '1001_DFA_NEU_XX.flv'
curl.exe -fL "https://media.githubusercontent.com/media/CheyneyComputerScience/CREMA-D/$revision/VideoFlash/$source" -o "$assets/$source"
if ($LASTEXITCODE -ne 0) { throw 'Could not download the calibration take' }
ffmpeg -y -i "$assets/$source" -vf 'crop=242:242:86:16,scale=256:256' -frames:v 1 "$assets/neutral.png"
if ($LASTEXITCODE -ne 0) { throw 'Could not extract the calibration image' }
$fps = @{ one = 20; two = 15 }
foreach ($name in 'one','two') {
  & $python tools/family_liveportrait.py --liveportrait $model pack "$demo/$name-reference.mp4" "$assets/$name.zip" --fps $fps[$name] --crop 242:242:86:16 --calibration-image "$assets/neutral.png" --baseline "$assets/$name-baseline.mp4"
  if ($LASTEXITCODE -ne 0) { throw "Packing failed for $name" }
}
```

For new footage, choose a tightly framed, front-facing subject with a relaxed, eyes-open expression before speech. Select that frame explicitly when the clip starts mid-blink or mid-speech. With no calibration image, the CLI uses the first decoded frame. Messages can be up to 30 seconds long.

## Measured payloads

| Example | Render duration | Frame rate | Reference MP4 | Low-bitrate MP4 | Message ZIP | Reduction vs. low-bitrate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Single take | 1.3 s | 20 fps | 102,603 B | 14,089 B | 11,821 B | 16.1% |
| Edited reel | 4.4 s | 15 fps | 309,577 B | 48,437 B | 32,950 B | 32.0% |

These are complete file sizes. Within each row the 256 × 256 H.264 baseline uses the same crop, frame rate, and Opus packets as the corresponding ZIP. H.264 targets and is capped at 64 kbps. The receiver crops the face from the shared still, renders it at LivePortrait’s native resolution, and blends it back into the 480 × 360 still with a feathered edge. The body and background come from the still. The renderer muxes AAC encoded from the received speech.

The shared portrait is 112,941 B and the five checkpoints total 522,320,239 B. These are one-time inputs and excluded from the per-message reduction. The portrait costs more than the combined savings on these two messages. The clips contain acted speech with a fixed camera and background. Visual fidelity differs, and CPU rendering happens before playback. The 4.4-second reel took 579 seconds to render and encode on the test Intel Core i5-1135G7 with four PyTorch threads, after model load.

## Asset provenance

Contains recordings from [CREMA-D by Cao et al.](https://github.com/CheyneyComputerScience/CREMA-D) at Git revision `1658cd342dff90010aa843eaeebd53610a08b1dc`. The authors release the database under [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) and individual recordings under [DbCL 1.0](https://opendatacommons.org/licenses/dbcl/1-0/). Both examples preserve the actor’s original spoken audio. See [the source registry](../data/sources.json) for input and output hashes.

- The shared portrait is the full first frame of `1001_IEO_NEU_XX.flv`. The receiver derives the existing face crop with `crop=242:242:86:16,scale=256:256`. The sender calibrates from the same crop of the first frame of `1001_DFA_NEU_XX.flv`.
- The single take trims `1001_DFA_NEU_XX.flv` to 0.24–1.54 seconds and encodes it as H.264/AAC before motion extraction.
- The reel joins `1001_MTI_NEU_XX.flv` (0.20–1.90 s), `1001_DFA_NEU_XX.flv` (0.24–1.54 s), and `1001_IOM_NEU_XX.flv` (0.49–1.79 s) with straight cuts and no changes to the spoken words. The edited reference is H.264/AAC at 20 fps and its payload and baseline use 15 fps.
