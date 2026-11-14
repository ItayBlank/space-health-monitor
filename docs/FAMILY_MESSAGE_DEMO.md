# Family message demo

Run `python -m uvicorn server:app --host 127.0.0.1 --port 8000` and open `http://127.0.0.1:8000`. Go to **HAL → Family Archive → Family message demo**. For each fictional message, play the Earth reference, the low-bitrate video, and the preview rendered on the receiver. Download either message ZIP and the shared portrait from the page to repeat the reconstruction locally.

The browser displays pre-rendered clips. The actual offline sender and receiver are the `pack` and `render` commands below. The simulated Earth–Mars link carries only a ZIP with `message.json` (version, frame rate, frame count), `motion.npy` (76 float32 values per frame), and `audio.ogg` (mono Opus at a 24 kbps target). The receiver uses the same fixed portrait for both ZIPs. It performs LivePortrait inference locally and writes an MP4 with the supplied speech and motion on one timeline. It requires no source clip. Its dependencies and model weights are installed once.

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

After setup, the following commands run offline. Use either shipped ZIP or encode both from the synthetic references:

```powershell
$python = '.\runtime\family-message\.venv\Scripts\python.exe'
$tool = 'tools/family_liveportrait.py'
$demo = 'static/family-media'
foreach ($name in 'one','two') {
  & $python $tool --liveportrait runtime/family-message/LivePortrait pack "$demo/$name-reference.mp4" "runtime/family-message/$name.zip" --fps 5 --crop 320:320:160:55 --baseline "runtime/family-message/$name-baseline.mp4"
  if ($LASTEXITCODE -ne 0) { throw "Packing failed for $name" }
}
```

Put only the ZIPs and `portrait.png` in a receiver input folder. The receiver also needs the script, the preinstalled runtime, and the model. Run the receiver twice with the same portrait:

```powershell
New-Item -ItemType Directory -Force runtime/family-message/receiver-input | Out-Null
Copy-Item "$demo/one.zip","$demo/two.zip","$demo/portrait.png" runtime/family-message/receiver-input
foreach ($name in 'one','two') {
  & $python $tool --liveportrait runtime/family-message/LivePortrait render "runtime/family-message/receiver-input/$name.zip" runtime/family-message/receiver-input/portrait.png "runtime/family-message/$name-rendered.mp4"
  if ($LASTEXITCODE -ne 0) { throw "Rendering failed for $name" }
}
```

To test messages you packed, replace the two shipped ZIPs in the receiver input folder with your generated ZIPs.

For a new clip, use a tightly framed, front-facing subject with a neutral pose in the first frame. The sender uses the first frame to normalize the motion it extracts. The decoder supports clips up to 30 seconds.

## Measured payloads

| Message | Duration | Reference MP4 | Low-bitrate MP4 | Message ZIP | Reduction vs. low-bitrate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dinner is ready | 3.0 s | 56,363 B | 22,410 B | 11,188 B | 50.1% |
| The basil bloomed | 2.8 s | 53,309 B | 20,899 B | 10,293 B | 50.7% |

These are complete file sizes. The 256 × 256 H.264 baseline uses the same crop and 5 fps timeline used for motion extraction. Video targets 64 kbps with a 64 kbps cap. The sender copies the same Opus stream into the baseline. The 512 × 512 reconstruction uses LivePortrait’s native output and muxes AAC encoded from the received Opus. The portrait (17,721 B) and five checkpoints (522,320,239 B) are one-time inputs. Against the baseline, the two messages save 21,828 B in total. Including just the shared portrait, the saving is 4,107 B. With the model already installed, the portrait cost is recovered by the second message on these examples.

This measures transfer size for two short, low-motion synthetic clips. Visual fidelity differs between the baseline and reconstruction. Rendering and encoding took about two minutes per clip on an Intel Core i5-1135G7 with four PyTorch threads, after checkpoint load. Playback uses the resulting video file. These clips do not establish real-time performance or spacecraft compute requirements.

## Synthetic asset provenance

The two exact spoken lines are “Dinner is ready. We saved you a seat.” and “The basil bloomed. See you soon.” Both WAV sources were generated with Windows `System.Speech` at rate 2, 24 kHz 16-bit PCM mono. Run `tools/build_family_demo.py` with each WAV and a separate scratch output directory to generate the illustrated Earth reference, then run `pack` above. The shared portrait is the first frame of the first synthetic reference, cropped with `crop=320:320:160:55,scale=256:256`. The second reference is used only by its sender. Exact output bytes can vary by installed voice and encoders.
