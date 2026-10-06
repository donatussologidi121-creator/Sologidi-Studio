# Tamara — your voice assistant for the Mac

Say **"Tamara, open Safari"** or **"Tamara, what's in my Downloads folder?"** and she does it and talks back.

## Set up (once, about 10 minutes)

1. **Get an API key.** Go to https://console.anthropic.com, sign in, add a few dollars of credit under *Billing*,
   then *API Keys → Create Key*. Copy it. (A Claude Pro/Max subscription does not include API access; this is separate.)
2. **Download this folder** to your Mac (from GitHub, branch `ccr-53151dca-mmrzii`, folder `tamara`).
3. Open **Terminal** (press Cmd+Space, type "Terminal"). Type `cd ` (with a space), drag the `tamara` folder
   into the Terminal window, press Enter. Then run:
   ```
   bash setup.sh
   open -e .env
   ```
   Paste your key after `ANTHROPIC_API_KEY=`, save, and close the file.

## Run her

Double-click **start_tamara.command** (or run `.venv/bin/python tamara.py`).
The first time, macOS asks for **Microphone** access for Terminal — click Allow.
The first run also downloads a small speech model (about 150 MB).

## How to talk to her

- Say her name plus the request: *"Tamara, what time is it?"*
- After she answers you can keep talking for 30 seconds without repeating her name.
- *"Goodbye"* or *"go to sleep"* puts her back to waiting for her name. *"Never mind"* cancels. Ctrl+C quits.

## Safety

Tamara can run commands, control apps and write files. Harmless look-only actions happen straight away.
Anything that changes things (writing files, deleting, sending, most scripts) she **asks out loud first** —
answer "yes" or "no". She is also told to treat text from web pages and files as information, never as orders.

## Files

| File | What it does |
|---|---|
| `tamara.py` | The main loop: listen → wake word → think → speak |
| `voice.py` | Ears (microphone + Whisper) and mouth (Mac `say`) |
| `brain.py` | Claude, Tamara's personality and memory |
| `tools.py` | What she can do on the Mac, and the safety check |

## Change her voice

In `.env` add `TAMARA_VOICE=Samantha` (or Ava, Zoe, Daniel...). Download nicer voices in
*System Settings → Accessibility → Spoken Content → System Voice → Manage Voices*.
