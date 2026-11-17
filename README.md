# Free Shorts Automation

A free, GitHub Actions-based Korean Shorts renderer.

## What it does
- Reads `cards.json`
- Generates Korean narration with MeloTTS (CPU)
- Creates 1080x1920 scene cards from supplied images (or a neutral fallback)
- Renders an H.264/AAC MP4 with FFmpeg
- Uploads the MP4 as a GitHub Actions artifact

## Important privacy note
This repository is currently public. Do not add private scripts, patient/customer information, private images, voice recordings, API keys, or unreleased content here. For real production assets, first create/use a private repository and copy this pipeline there. GitHub Free includes 2,000 Actions minutes/month for private repositories; public repository standard runners are free, subject to GitHub policy.

## Input format
Copy `cards.example.json` to `cards.json`. Each scene needs:
- `narration`: spoken Korean sentence(s)
- `caption`: short on-screen Korean caption
- `image`: optional relative image path such as `assets/scene_01.png`

Keep 3–6 scenes for a short video. Add only images you own or are licensed to use commercially.

## Run
1. Add `cards.json` and your images to the repository (only after using a private repository for non-public content).
2. Open **Actions → Render Korean Short → Run workflow**.
3. Download the `shorts-video` artifact from the completed run.

The first run installs MeloTTS and downloads its model, so it can take longer. The rendered MP4 is 1080x1920, H.264/AAC, 30 fps.

## Current scope
This repository automates video rendering. Social publishing is not enabled here: YouTube publishing can be handled through the connected vidIQ account after review and approval. Instagram and TikTok require their own account/app authorization and platform policy checks.

## License notes
MeloTTS Korean model card: MIT. Third-party packages and media retain their own licenses. This project does not grant rights to uploaded images, music, or other media.
