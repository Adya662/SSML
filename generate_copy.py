#!/usr/bin/env python3
# pip install boto3
import os, re
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# ================== CONFIG (edit these) ==================
os.environ.setdefault("AWS_PROFILE", "Power-root")
os.environ.setdefault("AWS_SDK_LOAD_CONFIG", "1")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-south-1")

POLLY_REGION     = "us-east-1"      # voices/engines vary by region
BASELINE_ENGINE  = "neural"         # "neural" or "standard"
BASELINE_VOICE   = "Joanna"         # e.g., "Matthew", "Amy", "Aria" (region-dependent)
OUTPUT_FORMAT    = "mp3"            # "mp3" | "ogg_vorbis" | "pcm"
SAMPLE_RATE      = "24000"
GRID_LANGUAGE_CODE = "en-US"        # None for all languages
DO_GRID            = False          # try all voice/engine combos
OUTPUT_BASE_DIR    = "out_ang"      # base folder for all recordings
PRESERVE_RICH_SSML = True           # if True, use Standard engine for SSML to keep amazon:* and pitch/volume effects

# Long-form limits (room for safety)
NEURAL_LIMIT  = 1500
STANDARD_LIMIT= 3000
SSML_HEADROOM = 0.85  # tags add chars; use less than hard limit

TEXT_INPUT = (
    """
    are you really kidding me? It doesn't make sense? Like bro what even is it. 
    """
)

SSML_INPUT = """<speak>
  <s>
    <prosody pitch="+12%" rate="fast" volume="loud">Are you <emphasis level="strong">really</emphasis> kidding me?</prosody>
  </s>
  <s>
    <amazon:breath duration="short" volume="soft"/>
    <prosody pitch="+8%" rate="medium">It <emphasis level="moderate">doesn't</emphasis> make sense?</prosody>
  </s>
  <s>
    <prosody rate="fast">Like, bro, <break time="500ms"/> what even is it.</prosody>
  </s>
</speak>"""

# ================== RUNTIME ==================
def _assert_aws_creds():
    s = boto3.Session()
    if s.get_credentials() is None:
        raise RuntimeError(
            "No AWS credentials available. With SSO, run:\n"
            "  aws sso login --profile <your-profile>\n"
            "and export AWS_PROFILE and AWS_SDK_LOAD_CONFIG before running this script."
        )

def polly_client():
    return boto3.client("polly", region_name=POLLY_REGION)

def ensure_dirs(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)

def sanitize_ssml_for_neural(ssml_text: str) -> str:
    t = ssml_text
    # Remove comments
    t = re.sub(r"<!--.*?-->", "", t, flags=re.DOTALL)
    # Strip all amazon:* tags but keep inner contents
    t = re.sub(r"</?amazon:[^>]+>", "", t)
    # Remove <mark .../>
    t = re.sub(r"<mark[^>]*/>", "", t)
    # Replace <phoneme ...>inner</phoneme> with inner
    t = re.sub(r"<phoneme[^>]*>(.*?)</phoneme>", r"\1", t, flags=re.DOTALL)
    # Drop pitch/volume in prosody; keep rate
    def _strip_prosody_attrs(m):
        attrs = m.group(1)
        attrs = re.sub(r'\s+pitch="[^"]*"', "", attrs)
        attrs = re.sub(r'\s+volume="[^"]*"', "", attrs)
        return f"<prosody{attrs}>"
    t = re.sub(r"<prosody([^>]*)>", _strip_prosody_attrs, t)
    # Clamp breaks (100–400ms)
    def _clamp_break(m):
        try:
            ms = max(100, min(int(m.group(1)), 400))
        except Exception:
            ms = 200
        return f'<break time="{ms}ms"/>'
    t = re.sub(r'<break\s+time="(\d+)ms"\s*/>', _clamp_break, t)
    return t

def sanitize_ssml_for_neural_minimal(ssml_text: str) -> str:
    """
    Aggressive sanitization: keep only <speak>, <p>, <s>, and <break time="Nms"/>.
    Strip all other tags and attributes to maximize Neural compatibility.
    """
    t = ssml_text
    # Remove comments and amazon:* wrappers
    t = re.sub(r"<!--.*?-->", "", t, flags=re.DOTALL)
    t = re.sub(r"</?amazon:[^>]+>", "", t)
    # Remove phoneme entirely keeping inner text
    t = re.sub(r"<phoneme[^>]*>(.*?)</phoneme>", r"\1", t, flags=re.DOTALL)
    # Remove all prosody, emphasis, say-as and any other tags except speak/p/s/break
    t = re.sub(r"</?(prosody|emphasis|say-as|sub|mark|audio|lang|w|voice)[^>]*>", "", t, flags=re.IGNORECASE)
    # Normalize break tags, remove attributes except time and clamp
    def _normalize_break(m):
        try:
            ms = max(100, min(int(m.group(1)), 400))
        except Exception:
            ms = 200
        return f'<break time="{ms}ms"/>'
    t = re.sub(r'<break[^>]*time="(\d+)ms"[^>]*/>', _normalize_break, t)
    # Remove any other tags than speak/p/s/break
    t = re.sub(r"<(?!/?(speak|p|s|break)\b)[^>]+>", "", t, flags=re.IGNORECASE)
    # Ensure speak wrapper
    inner = re.sub(r"^\s*<\s*speak\s*>", "", t.strip(), flags=re.IGNORECASE)
    inner = re.sub(r"<\s*/\s*speak\s*>\s*$", "", inner, flags=re.IGNORECASE)
    return f"<speak>{inner}</speak>"

def _limit(engine: str, text_type: str) -> int:
    base = NEURAL_LIMIT if engine == "neural" else STANDARD_LIMIT
    return int(base * (SSML_HEADROOM if text_type == "ssml" else 1.0))

def split_ssml_safe(ssml_text: str, engine: str):
    """
    Split SSML only on </p> boundaries to keep tags balanced.
    Wrap each part in <speak>…</speak> if not already wrapped.
    """
    lim = _limit(engine, "ssml")
    cleaned = ssml_text.strip()

    # If small enough, use as-is
    if len(cleaned) <= lim:
        return [cleaned]

    # Split on </p> boundaries (keep the closing tag)
    parts = re.split(r"(?<=</p>)\s*", cleaned)
    chunks, buf = [], ""
    for part in parts:
        # Ensure each piece is self-contained without outer <speak>, so we can wrap it
        part_inner = re.sub(r"^\s*<\s*speak\s*>", "", part.strip(), flags=re.IGNORECASE)
        part_inner = re.sub(r"<\s*/\s*speak\s*>\s*$", "", part_inner, flags=re.IGNORECASE)
        candidate = (buf + part_inner)
        if len(candidate) <= lim:
            buf = candidate
        else:
            if buf:
                chunks.append(f"<speak>{buf}</speak>")
            buf = part_inner
    if buf:
        chunks.append(f"<speak>{buf}</speak>")

    # Fallback: if we somehow produced nothing, return original (Polly will throw a length error)
    return chunks or [cleaned]

def split_plain_text(text: str, engine: str):
    lim = _limit(engine, "text")
    parts = []
    sentences = re.split(r'(?<=[\.\!\?])\s+', text.strip())
    buf = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        candidate = (buf + " " + s).strip() if buf else s
        if len(candidate) <= lim:
            buf = candidate
        else:
            if buf: parts.append(buf)
            # If a single sentence is longer than limit, split on commas/spaces
            if len(s) > lim:
                chunks = re.split(r'(,|\s)', s)
                sub = ""
                for c in chunks:
                    nxt = (sub + c)
                    if len(nxt) > lim and sub:
                        parts.append(sub)
                        sub = c
                    else:
                        sub = nxt
                if sub: parts.append(sub)
                buf = ""
            else:
                buf = s
    if buf: parts.append(buf)
    return parts

def synthesize(text, *, text_type, voice, engine, outpath, output_format=OUTPUT_FORMAT, sample_rate=SAMPLE_RATE):
    pc = polly_client()

    # Prepare segments
    if text_type == "ssml":
        ssml = text
        if engine == "neural":
            ssml = sanitize_ssml_for_neural(ssml)
            # If still too long, split by paragraphs safely
            segments = split_ssml_safe(ssml, engine)
        else:
            # Standard supports more SSML features; still split safely if needed
            segments = split_ssml_safe(ssml, engine)
    else:
        segments = split_plain_text(text, engine)

    audio_bytes = b""
    for idx, seg in enumerate(segments, 1):
        try:
            resp = pc.synthesize_speech(
                Text=seg,
                TextType=text_type,
                VoiceId=voice,
                Engine=engine,
                OutputFormat=output_format,
                SampleRate=sample_rate
            )
        except (BotoCoreError, ClientError) as e:
            # If neural SSML fails due to unsupported neural features, try minimal sanitize on neural,
            # then try standard, and finally fall back to another Indian voice that supports the engine.
            msg = str(e)
            if text_type == "ssml" and engine == "neural" and ("InvalidSsmlException" in msg or "Unsupported Neural" in msg):
                minimally_sanitized = sanitize_ssml_for_neural_minimal(seg)
                try:
                    resp = pc.synthesize_speech(
                        Text=minimally_sanitized, TextType=text_type, VoiceId=voice, Engine="neural",
                        OutputFormat=output_format, SampleRate=sample_rate
                    )
                except (BotoCoreError, ClientError):
                    try:
                        resp = pc.synthesize_speech(
                            Text=seg, TextType=text_type, VoiceId=voice, Engine="standard",
                            OutputFormat=output_format, SampleRate=sample_rate
                        )
                    except (BotoCoreError, ClientError):
                        fallback_voice, fallback_engine = select_indian_voice(preferred_engine="standard")
                        resp = pc.synthesize_speech(
                            Text=minimally_sanitized, TextType=text_type, VoiceId=fallback_voice, Engine=fallback_engine,
                            OutputFormat=output_format, SampleRate=sample_rate
                        )
            else:
                raise RuntimeError(f"synthesize_speech failed for {voice} ({engine}) seg#{idx}: {e}")

        stream = resp.get("AudioStream")
        if not stream:
            raise RuntimeError("No AudioStream in response.")
        audio_bytes += stream.read()

    with open(outpath, "wb") as f:
        f.write(audio_bytes)
    print(f"Saved: {outpath}")

def list_voices(language_code=None):
    pc = polly_client()
    voices = []
    paginator = pc.get_paginator("describe_voices")
    kwargs = {}
    if language_code:
        kwargs["LanguageCode"] = language_code
    for page in paginator.paginate(**kwargs):
        voices.extend(page.get("Voices", []))
    return voices

def select_indian_voice(preferred_engine: str = BASELINE_ENGINE):
    """
    Prefer Indian voices in this order: Kajal, Raveena, Aditi.
    Choose the preferred engine if supported, otherwise fall back to any supported engine.
    """
    try:
        indian_voices = []
        # Try Indian English and Hindi voices
        for lang_code in ("en-IN", "hi-IN"):
            indian_voices.extend(list_voices(language_code=lang_code))
        # If API does not filter or returns empty, fall back to all voices
        if not indian_voices:
            indian_voices = list_voices()

        preferred_voice_ids = ["Kajal", "Raveena", "Aditi"]

        # Try preferred list first
        for voice_id in preferred_voice_ids:
            for v in indian_voices:
                if v.get("Id") == voice_id:
                    engines = v.get("SupportedEngines") or []
                    if preferred_engine in engines:
                        return voice_id, preferred_engine
                    if engines:
                        return voice_id, engines[0]

        # Otherwise, pick any Indian voice
        for v in indian_voices:
            engines = v.get("SupportedEngines") or []
            if not engines:
                continue
            engine = preferred_engine if preferred_engine in engines else engines[0]
            return v.get("Id"), engine
    except Exception:
        pass

    # Fallback to configured baseline if discovery fails
    return BASELINE_VOICE, BASELINE_ENGINE

def grid_synthesize(text, ssml, *, language_code=GRID_LANGUAGE_CODE, outdir=None):
    outdir = outdir or os.path.join(OUTPUT_BASE_DIR, "grid")
    ensure_dirs(outdir)
    voices = list_voices(language_code=language_code) or list_voices()
    combos = [(v["Id"], eng) for v in voices for eng in (v.get("SupportedEngines") or [])]
    print(f"Voices discovered: {len(voices)} | Engine combos: {len(combos)}")

    for vid, eng in combos:
        voice_dir = os.path.join(outdir, eng, vid)
        ensure_dirs(voice_dir)
        try:
            synthesize(text, text_type="text", voice=vid, engine=eng,
                       outpath=os.path.join(voice_dir, f"text_{vid}_{eng}.{OUTPUT_FORMAT}"))
        except Exception as e:
            print(f"[SKIP text] {vid}/{eng}: {e}")
        try:
            synthesize(ssml, text_type="ssml", voice=vid, engine=eng,
                       outpath=os.path.join(voice_dir, f"ssml_gpt_{vid}_{eng}.{OUTPUT_FORMAT}"))
        except Exception as e:
            print(f"[SKIP ssml] {vid}/{eng}: {e}")

def main():
    _assert_aws_creds()
    ensure_dirs(os.path.join(OUTPUT_BASE_DIR, "baseline"))

    # Select an Indian voice automatically (prefers Kajal, then Raveena, then Aditi)
    selected_voice, selected_engine = select_indian_voice(preferred_engine=BASELINE_ENGINE)
    print(f"Using voice: {selected_voice} | Engine: {selected_engine}")

    # Baseline: two files (plain + SSML) for the selected voice/engine
    baseline_text_path = os.path.join(OUTPUT_BASE_DIR, "baseline", f"plain_{selected_voice}_{selected_engine}.{OUTPUT_FORMAT}")
    synthesize(TEXT_INPUT, text_type="text", voice=selected_voice,
               engine=selected_engine, outpath=baseline_text_path)

    ssml_engine = "standard" if PRESERVE_RICH_SSML else selected_engine
    try:
        baseline_ssml_path = os.path.join(OUTPUT_BASE_DIR, "baseline", f"ssml_gpt_{selected_voice}_{ssml_engine}.{OUTPUT_FORMAT}")
        synthesize(SSML_INPUT,  text_type="ssml", voice=selected_voice,
                   engine=ssml_engine, outpath=baseline_ssml_path)
    except Exception as e:
        # Fallback: if chosen engine (likely standard) is unsupported, try neural with sanitization
        print(f"[Fallback] SSML synthesis failed with {ssml_engine} for {selected_voice}: {e}. Retrying with neural…")
        ssml_engine = "neural"
        baseline_ssml_path = os.path.join(OUTPUT_BASE_DIR, "baseline", f"ssml_gpt_{selected_voice}_{ssml_engine}.{OUTPUT_FORMAT}")
        synthesize(SSML_INPUT,  text_type="ssml", voice=selected_voice,
                   engine=ssml_engine, outpath=baseline_ssml_path)

    print(f"\nBaseline files written:\n  {baseline_text_path}\n  {baseline_ssml_path}\n")

    if DO_GRID:
        print("Running full grid (this may create MANY files and incur costs)…")
        grid_synthesize(TEXT_INPUT, SSML_INPUT, language_code=GRID_LANGUAGE_CODE)

if __name__ == "__main__":
    main()