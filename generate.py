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
BASELINE_ENGINE  = "generative"     # use the Generative engine
BASELINE_VOICE   = "Danielle"       # fallback if discovery fails
OUTPUT_FORMAT    = "mp3"            # "mp3" | "ogg_vorbis" | "pcm"
SAMPLE_RATE      = "24000"
OUTPUT_BASE_DIR  = "out_vm"         # base folder for all recordings

# Long-form limits (conservative default)
GEN_LIMIT    = 1500
SSML_HEADROOM = 0.85

# Inputs
TEXT_INPUT = (
    """
    One day, a rich merchant came to Birbal. He said to Birbal, “I have seven servants in my
    house. One of them has stolen my bag of precious pearls. Please find out the thief.”
    So Birbal went to the rich man’s house. He called all the seven servants in a room. He gave a
    stick to each one of them. Then he said, “These are magic sticks. Just now all these sticks are
    equal in length. Keep them with you and return tomorrow. If there is a thief in the house,
    his stick will grow an inch longer by tomorrow.”
    The servant who had stolen the bag of pearls was scared. He thought, “If I cut a piece of one
    inch from my stick, I won’t be caught.” So he cut the stick and made it shorter by one inch.
    The next day Birbal collected the sticks from the servants. He found that one servant’s stick
    was short by an inch. Birbal pointed his finger at him and said, “Here is the thief.” The
    servant confessed to his crime. He returned the bag of pearls. He was sent to jail.
    """
)

SSML_INPUT = """<speak>
  <!-- Minimal SSML; richer SSML may not be supported by generative engine -->
  <p>One day, a rich merchant came to Birbal. He said to Birbal, I have seven servants in my house.</p>
  <p>One of them has stolen my bag of precious pearls. Please find out the thief.</p>
  <p>So Birbal went to the rich man’s house. He called all the seven servants in a room. He gave a stick to each one of them.</p>
  <p>Then he said, These are magic sticks. Just now all these sticks are equal in length. Keep them with you and return tomorrow.</p>
  <p>If there is a thief in the house, his stick will grow an inch longer by tomorrow.</p>
  <p>The servant who had stolen the bag of pearls was scared. He thought, If I cut a piece of one inch from my stick, I won’t be caught.</p>
  <p>So he cut the stick and made it shorter by one inch. The next day Birbal collected the sticks from the servants.</p>
  <p>He found that one servant’s stick was short by an inch. Birbal pointed his finger at him and said, Here is the thief.</p>
  <p>The servant confessed to his crime. He returned the bag of pearls. He was sent to jail.</p>
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

def sanitize_ssml_minimal(ssml_text: str) -> str:
    # Keep only speak/p/s/break and clamp breaks
    t = ssml_text
    t = re.sub(r"<!--.*?-->", "", t, flags=re.DOTALL)
    t = re.sub(r"<(?!/?(speak|p|s|break)\b)[^>]+>", "", t, flags=re.IGNORECASE)
    def _normalize_break(m):
        try:
            ms = max(100, min(int(m.group(1)), 400))
        except Exception:
            ms = 200
        return f'<break time="{ms}ms"/>'
    t = re.sub(r'<break[^>]*time="(\d+)ms"[^>]*/>', _normalize_break, t)
    inner = re.sub(r"^\s*<\s*speak\s*>", "", t.strip(), flags=re.IGNORECASE)
    inner = re.sub(r"<\s*/\s*speak\s*>\s*$", "", inner, flags=re.IGNORECASE)
    return f"<speak>{inner}</speak>"

def strip_all_tags(ssml_text: str) -> str:
    # Convert SSML to plain text for engines that reject SSML entirely
    t = re.sub(r"<[^>]+>", " ", ssml_text)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _limit(engine: str, text_type: str) -> int:
    base = GEN_LIMIT
    return int(base * (SSML_HEADROOM if text_type == "ssml" else 1.0))

def split_ssml_safe(ssml_text: str, engine: str):
    lim = _limit(engine, "ssml")
    cleaned = ssml_text.strip()
    if len(cleaned) <= lim:
        return [cleaned]
    parts = re.split(r"(?<=</p>)\s*", cleaned)
    chunks, buf = [], ""
    for part in parts:
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
    return chunks or [cleaned]

def split_plain_text(text: str, engine: str):
    lim = _limit(engine, "text")
    parts = []
    sentences = re.split(r'(?<=[\.!\?])\s+', text.strip())
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
        ssml = sanitize_ssml_minimal(text)
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
            msg = str(e)
            # If generative rejects SSML entirely, try stripping to text while keeping generative
            if text_type == "ssml" and engine == "generative":
                try:
                    stripped = strip_all_tags(seg)
                    resp = pc.synthesize_speech(
                        Text=stripped, TextType="text", VoiceId=voice, Engine="generative",
                        OutputFormat=output_format, SampleRate=sample_rate
                    )
                except (BotoCoreError, ClientError):
                    raise RuntimeError(f"Generative engine rejected SSML and text fallback for {voice} seg#{idx}: {e}")
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

def select_generative_voice():
    """
    Choose a voice that supports the Generative engine.
    Prefer Indian voices if available (Kajal, Raveena, Aditi), otherwise pick common generative voices (Danielle, Matthew, Ruth).
    """
    try:
        all_voices = list_voices()
        gen_voices = [v for v in all_voices if "generative" in (v.get("SupportedEngines") or [])]
        if not gen_voices:
            return BASELINE_VOICE, BASELINE_ENGINE

        preferred_indian = ["Kajal", "Raveena", "Aditi"]
        for vid in preferred_indian:
            for v in gen_voices:
                if v.get("Id") == vid:
                    return vid, "generative"

        preferred_common = ["Danielle", "Matthew", "Ruth", "Amy", "Gregory"]
        for vid in preferred_common:
            for v in gen_voices:
                if v.get("Id") == vid:
                    return vid, "generative"

        # Fallback to the first available generative voice
        return gen_voices[0].get("Id"), "generative"
    except Exception:
        return BASELINE_VOICE, BASELINE_ENGINE

def main():
    _assert_aws_creds()
    ensure_dirs(os.path.join(OUTPUT_BASE_DIR, "baseline"))

    selected_voice, selected_engine = select_generative_voice()
    print(f"Using voice: {selected_voice} | Engine: {selected_engine}")

    baseline_text_path = os.path.join(OUTPUT_BASE_DIR, "baseline", f"plain_{selected_voice}_{selected_engine}.{OUTPUT_FORMAT}")
    baseline_ssml_path = os.path.join(OUTPUT_BASE_DIR, "baseline", f"ssml_{selected_voice}_{selected_engine}.{OUTPUT_FORMAT}")

    synthesize(TEXT_INPUT, text_type="text", voice=selected_voice,
               engine=selected_engine, outpath=baseline_text_path)
    synthesize(SSML_INPUT,  text_type="ssml", voice=selected_voice,
               engine=selected_engine, outpath=baseline_ssml_path)

    print(f"\nBaseline files written:\n  {baseline_text_path}\n  {baseline_ssml_path}\n")

if __name__ == "__main__":
    main()

