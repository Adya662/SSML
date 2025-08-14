# Amazon Polly Output Catalogue

This folder contains generated audio samples from **Amazon Polly** using different voices, engines, and input styles (plain text vs SSML).
It serves as a catalogue to compare how each configuration sounds, so you can choose the best for your use case.

---

## 📂 Folder Structure

### 1. `baseline/`
A small **control sample** to confirm Polly is working before generating every possible voice.

- **plain_<Voice>_<Engine>.mp3**
  Plain text narration (`TEXT_INPUT`), no SSML tags.
- **ssml_<Voice>_<Engine>.mp3**
  SSML narration (`SSML_INPUT`) with prosody, emphasis, pauses, etc.

Example:

baseline/
plain_Joanna_neural.mp3   ← Joanna voice, Neural engine, plain text
ssml_Joanna_neural.mp3    ← Joanna voice, Neural engine, SSML-enhanced

---

### 2. `grid/`
The **full sweep**: all available voices + engines for the chosen language code (`GRID_LANGUAGE_CODE` in script).
Each voice/engine pair has both a plain text and SSML version.

Structure:

grid/
neural/
Joanna/
text_Joanna_neural.mp3   ← Plain text
ssml_Joanna_neural.mp3   ← SSML
Matthew/
text_Matthew_neural.mp3
ssml_Matthew_neural.mp3
standard/
Brian/
text_Brian_standard.mp3
ssml_Brian_standard.mp3

File naming convention:

text_.mp3   → Plain text version
ssml_.mp3   → SSML version

---

### 3. Special Category Folders (optional / extra)

Depending on Polly features and test runs, you may also see:

- `generative/` – Files generated with Polly's generative preview voices (if available in your AWS region).
- `long-form/` – Files from Polly's long-form TTS mode for very long scripts.
- `neural/` – Direct output of neural engine runs (similar to `grid/neural`).
- `standard/` – Direct output of standard engine runs (similar to `grid/standard`).

These may have been created from separate test runs or manual organisation.

---

## 🔍 How to Use This Catalogue

1. Start with `baseline/`
   Listen to both plain and SSML for your chosen voice/engine to confirm SSML formatting and that AWS Polly is working.

2. Explore `grid/`
   Browse by engine (`neural` for more natural tone, `standard` for wider SSML support).
   Compare plain text vs SSML in the same voice to hear the effect of prosody and emphasis.

3. Check special folders (if present)
   - `generative/` → Try Polly's experimental AI voices.
   - `long-form/` → For audiobooks, long scripts, or consistent delivery over minutes.
   - `neural/` and `standard/` → Alternative organisation if you want to focus on one engine type.

---

## ℹ️ Terminology

- Voice: Named persona in Polly (e.g., Joanna, Matthew, Amy).
- Engine:
  - `standard` – Classic TTS engine. Supports most SSML tags.
  - `neural` – Higher-quality, natural-sounding speech. Some SSML tags (especially Amazon-specific ones) are not supported.
  - `generative` (if available) – New AI-based voices with more expressiveness.
- SSML: Speech Synthesis Markup Language. Controls speech rate, pitch, pauses, emphasis, and more.
- Plain Text: Raw text without SSML formatting.

---

## 📊 Tips for Comparing Voices

- Listen to plain text first to get a baseline of the voice quality.
- Then listen to SSML version of the same voice/engine to hear how well it responds to prosody and emphasis.
- Neural voices are often smoother, but may ignore unsupported SSML tags.
- Standard voices have wider SSML compatibility but can sound less natural.

---

## 📝 Script Config Recap

From the script’s top-level variables:

- `BASELINE_VOICE` – Voice used in the baseline folder.
- `BASELINE_ENGINE` – Engine used in the baseline folder.
- `GRID_LANGUAGE_CODE` – Language for the grid search (e.g., `en-US`).
- `DO_GRID` – Whether to run the full grid output.

---

## 📜 Catalogue

### baseline/
- baseline/plain_Joanna_neural.mp3
- baseline/ssml_Joanna_neural.mp3

### grid/neural/
- grid/neural/Danielle/text_Danielle_neural.mp3
- grid/neural/Danielle/ssml_Danielle_neural.mp3
- grid/neural/Gregory/text_Gregory_neural.mp3
- grid/neural/Gregory/ssml_Gregory_neural.mp3
- grid/neural/Ivy/text_Ivy_neural.mp3
- grid/neural/Ivy/ssml_Ivy_neural.mp3
- grid/neural/Joanna/text_Joanna_neural.mp3
- grid/neural/Joanna/ssml_Joanna_neural.mp3
- grid/neural/Joey/text_Joey_neural.mp3
- grid/neural/Joey/ssml_Joey_neural.mp3
- grid/neural/Justin/text_Justin_neural.mp3
- grid/neural/Justin/ssml_Justin_neural.mp3
- grid/neural/Kendra/text_Kendra_neural.mp3
- grid/neural/Kendra/ssml_Kendra_neural.mp3
- grid/neural/Kevin/text_Kevin_neural.mp3
- grid/neural/Kevin/ssml_Kevin_neural.mp3
- grid/neural/Kimberly/text_Kimberly_neural.mp3
- grid/neural/Kimberly/ssml_Kimberly_neural.mp3
- grid/neural/Matthew/text_Matthew_neural.mp3
- grid/neural/Matthew/ssml_Matthew_neural.mp3
- grid/neural/Ruth/text_Ruth_neural.mp3
- grid/neural/Ruth/ssml_Ruth_neural.mp3
- grid/neural/Salli/text_Salli_neural.mp3
- grid/neural/Salli/ssml_Salli_neural.mp3
- grid/neural/Stephen/text_Stephen_neural.mp3
- grid/neural/Stephen/ssml_Stephen_neural.mp3

### grid/standard/
- grid/standard/Ivy/text_Ivy_standard.mp3
- grid/standard/Joanna/text_Joanna_standard.mp3
- grid/standard/Joey/text_Joey_standard.mp3
- grid/standard/Justin/text_Justin_standard.mp3
- grid/standard/Kendra/text_Kendra_standard.mp3
- grid/standard/Kimberly/text_Kimberly_standard.mp3
- grid/standard/Matthew/text_Matthew_standard.mp3
- grid/standard/Salli/text_Salli_standard.mp3

### grid/generative/
- grid/generative/Danielle/text_Danielle_generative.mp3
- grid/generative/Joanna/text_Joanna_generative.mp3
- grid/generative/Matthew/text_Matthew_generative.mp3
- grid/generative/Ruth/text_Ruth_generative.mp3
- grid/generative/Stephen/text_Stephen_generative.mp3

### grid/long-form/
- grid/long-form/Danielle/text_Danielle_long-form.mp3
- grid/long-form/Gregory/text_Gregory_long-form.mp3
- grid/long-form/Patrick/text_Patrick_long-form.mp3
- grid/long-form/Ruth/text_Ruth_long-form.mp3