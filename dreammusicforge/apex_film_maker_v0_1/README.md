# APEX Film Maker Studio · v0.1 (2026-10-10)

**Status: working local-first production preproduction + draft assembly MVP. Not an autonomous video generator or independently verified release system.**

## Open the studio

- Quick desktop demo: open `index.html` in a modern browser.
- Recommended: run `python server.py` and browse to `http://127.0.0.1:8765/index.html`.
- On iPhone: this is a responsive web app, but the Python host runs on a computer. To view it on the same trusted Wi-Fi, run `python server.py --host 0.0.0.0` on the computer, and visit `http://COMPUTER-LAN-IP:8765/` from Safari. Do **not** expose this HTTP server to the internet.

Browser studio features: create multiple projects; four narrative engine templates; editable story/identity/world/audio bibles; nine-scene structured drafts; physical state and boundary contracts; Kling-budget-aware (~1,900-character) prompts; speaker-specific dialogue; attach and persist scene videos in browser IndexedDB; sequential **rough** previews; human-checkable quality ledger; fail-closed release status; production Markdown, portable JSON and clip-manifest exports; validated JSON import.

Project details persist only in browser localStorage. Imported projects reset scene footage and QA attestations to unverified. Edits to canonical project intent invalidate all previous scene attestations; changes to one scene invalidate that scene’s QA and the master sign-off. Uploaded clips persist only in browser IndexedDB: **back up the original videos separately**. Browser storage may be cleared by the browser or operating system. Exported JSON deliberately does not include video binaries, images or privacy-sensitive credentials.

## Assemble a draft master from your generated videos

Requirements: Python 3.10+ and `ffmpeg` / `ffprobe` on `PATH` (only the assembly utility requires them).

1. In **Delivery**, export the project JSON and clip manifest.
2. Copy each rendered scene to one folder as `scene_01.mp4`, `scene_02.mp4`, etc. Match exactly the planned scene order and scene lengths.
3. Optionally create a full-length, continuous master soundtrack (strongly preferred).
4. Run:

```bash
python stitch.py --project "my-film.apex-project.json" --clips ./clips --out master_draft.mp4
# Better audio continuity:
python stitch.py --project "my-film.apex-project.json" --clips ./clips --audio master_audio.wav --out master_draft.mp4
```

The utility validates file existence, required streams, minimum clip lengths, planned runtime, source hashes, and final observed video duration/resolution. It normalizes clips to H.264/AAC, 30 fps and target aspect while avoiding repeated final-generation encodes. It outputs `master_draft.mp4` and `master_draft.receipt.json`. It will reject footage that is too short rather than invent/freeze missing frames.

**Draft limitations:** No automatic lip-sync analysis, face verification, semantic inspection, auditory coherence testing, rights clearance or YouTube metrics. Plain clip concatenation is used (hard cuts; no invented transitions). Clip audio boundaries may jump unless you supply one continuous master audio file. No quality score is invented. This is not an automatic publish pipeline.

## Integration contract

APEX owns intention and canonical identity/state. Providers (Runway/Kling/HeyGen/etc.) render media. Capture actual assets, inspect them, target repairs; do not promote unverified claims to canonical truth.

`INTENT → CANONICAL STORY / IDENTITY / WORLD → SCENE & BOUNDARY CONTRACTS → GENERATOR PROMPTS → ACTUAL CLIPS → MANUAL EVIDENCE LEDGER → ASSEMBLED DRAFT → HUMAN MASTER REVIEW → EXTERNAL RELEASE APPROVAL`

This incremental release inherits `dreammusicforge/CONTINUOUS_VIDEO_CANON.md` in `langeneggerotto-creator/apex-ocode`. Long film continuity may use true continuity, concealed continuity, motivated transitions or editorial cuts; none should be mislabeled. One continuous master-audio timeline is preferred. Prompt compilation honors the ~1,900-character working ceiling for Kling workflows.

## Evidence boundaries

| Capability | v0.1 status |
| --- | --- |
| Browser studio, local project persistence, narrative scaffolds, prompt compilation | Implemented / local tests |
| Browser video attachment/rough preview | Implemented / manual functional tests |
| FFmpeg assembly and machine receipt | Implemented / integration tests |
| Live Runway/Kling/HeyGen provider dispatch | **Not implemented** |
| Automated footage inspection & targeted repair | **Not implemented** |
| Hosted accounts, team collaboration, cloud backup, publishing | **Not implemented** |
| Automatic verified high retention, virality or error-free film | Not measurable/guaranteed |

## Run tests

```bash
python -m unittest discover -s tests -v
```

See `CHATGPT_WORKFLOW.md` for how to use this studio together with ChatGPT.