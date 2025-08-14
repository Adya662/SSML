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
DO_GRID            = True           # try all voice/engine combos

# Long-form limits (room for safety)
NEURAL_LIMIT  = 1500
STANDARD_LIMIT= 3000
SSML_HEADROOM = 0.85  # tags add chars; use less than hard limit

TEXT_INPUT = (
    "Given the severity of this situation and the fact that this is clearly our fulfillment error, "
    "I'm expediting your replacement through our express delivery service, and I'm pleased to inform you "
    "that this will be much faster than our standard delivery times. Here's the timeline I can guarantee for your replacement: "
    "Since this is being processed as a priority case, I'm arranging for your replacement dress to be dispatched today itself if we can get it processed within the next few hours, "
    "or definitely by tomorrow morning at the latest. With our express delivery service, which I'm providing to you at no additional cost as compensation for the inconvenience, "
    "you should receive your correct red dress within 2-3 business days maximum. More specifically, if the dress ships today, you should receive it by August 15th or 16th at the latest. "
    "If it ships tomorrow morning, you'll receive it by August 16th or 17th. This is significantly faster than our standard 5-7 day delivery window, and again, the express shipping charges are completely waived for you. "
    "I'm also ensuring that you receive proactive tracking updates throughout the process. You'll get SMS notifications when the replacement order is created, when it's dispatched, when it's out for delivery, and when it's delivered. "
    "You'll also receive email updates with detailed tracking information and the photographic verification I mentioned earlier. Additionally, I'm arranging for the return pickup of the incorrect blue dress to happen after you receive your replacement. "
    "This way, if there are any unforeseen issues with the replacement (though I'm confident there won't be), you'll still have the blue dress as a backup until everything is completely resolved to your satisfaction. "
    "Our delivery executive will also be given special instructions about your case, so they'll handle your package with extra care and will be available to address any immediate concerns you might have upon delivery."
)

SSML_INPUT = """<speak>
  <amazon:effect name="drc">
    <amazon:auto-breaths volume="low" frequency="low" duration="short">
      <amazon:domain name="conversational">
        <amazon:effect phonation="soft">
          <amazon:effect vocal-tract-length="-5%">
            <!-- p1 -->
            <p><s>
              <prosody rate="slow" pitch="-1st" volume="medium">Given the severity of this situation</prosody>
              <break time="250ms"/>
              <prosody rate="slow" pitch="-1st">and the fact that this is clearly our <phoneme alphabet="ipa" ph="fʊlˈfɪlmənt">fulfillment</phoneme> error,</prosody>
              <break time="250ms"/>
              <prosody rate="medium" pitch="-1st">I'm expediting your replacement through our express delivery service, and I'm pleased to inform you that this will be much faster than our standard delivery times.</prosody>
            </s></p>
            <!-- p2 -->
            <p><s><prosody rate="slow" pitch="-1st">Here's the timeline I can guarantee for your replacement:</prosody></s></p>
            <!-- p3 -->
            <p><s>
              <prosody rate="medium" pitch="-1st">Since this is being processed as a priority case, I'm arranging for your replacement dress to be <phoneme alphabet="ipa" ph="dɪˈspætʃt">dispatched</phoneme> today itself if we can get it processed within the next few hours,</prosody>
              <break time="150ms"/>
              <prosody rate="slow" pitch="-2st">or definitely by tomorrow morning at the latest.</prosody>
            </s></p>
            <!-- p4 -->
            <p><s>
              <prosody rate="slow" pitch="-1st">With our express delivery service, which I'm providing to you at no additional cost as compensation for the inconvenience,</prosody>
              <break time="150ms"/>
              <prosody rate="medium" pitch="-1st">you should receive your correct red <phoneme alphabet="ipa" ph="drɛs">dress</phoneme> within <sub alias="two to three">2–3</sub> business days maximum.</prosody>
            </s></p>
            <!-- p5 -->
            <p><s>
              <prosody rate="medium" pitch="-1st">More specifically, if the dress ships today, you should receive it by August <say-as interpret-as="ordinal">15</say-as> or <say-as interpret-as="ordinal">16</say-as> at the latest.</prosody>
              <break time="120ms"/>
              <prosody rate="medium" pitch="-1st">If it ships tomorrow morning, you'll receive it by August <say-as interpret-as="ordinal">16</say-as> or <say-as interpret-as="ordinal">17</say-as>.</prosody>
            </s></p>
            <!-- p6 -->
            <p><s>
              <prosody rate="medium" pitch="-1st">This is significantly faster than our <sub alias="five to seven">5–7</sub> day delivery window, and again, the express shipping charges are completely waived for you.</prosody>
            </s></p>
            <!-- p7 -->
            <p><s>
              <prosody rate="slow" pitch="-1st">I'm also ensuring that you receive proactive tracking updates throughout the process.</prosody>
              <break time="100ms"/>
              <prosody rate="medium" pitch="-1st">You'll get <sub alias="S M S">SMS</sub> notifications when the replacement order is created, when it's dispatched, when it's out for delivery, and when it's delivered.</prosody>
              <break time="100ms"/>
              <prosody rate="medium" pitch="-1st">You'll also receive email updates with detailed tracking information and the photographic verification I mentioned earlier.</prosody>
            </s></p>
            <!-- p8 -->
            <p><s>
              <prosody rate="slow" pitch="-1st">Additionally, I'm arranging for the return pickup of the incorrect blue <phoneme alphabet="ipa" ph="drɛs">dress</phoneme> to happen after you receive your replacement.</prosody>
              <break time="100ms"/>
              <prosody rate="medium" pitch="-1st">This way, if there are any unforeseen issues with the replacement</prosody>
              <amazon:effect name="whispered">(though I'm confident there won't be)</amazon:effect>
              <prosody rate="medium" pitch="-1st">, you'll still have the blue dress as a backup until everything is completely resolved to your satisfaction.</prosody>
            </s></p>
            <!-- p9 -->
            <p><s>
              <prosody rate="slow" pitch="-1st">Our delivery executive will also be given special instructions about your case, so they'll handle your package with extra care and will be available to address any immediate concerns you might have upon delivery.</prosody>
            </s></p>

            <mark name="end_of_message"/>
          </amazon:effect>
        </amazon:effect>
      </amazon:domain>
    </amazon:auto-breaths>
  </amazon:effect>
</speak>
"""

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
            # If neural SSML still fails due to unsupported features, retry with standard
            msg = str(e)
            if text_type == "ssml" and engine == "neural" and ("InvalidSsmlException" in msg or "Unsupported Neural" in msg):
                resp = pc.synthesize_speech(
                    Text=seg, TextType=text_type, VoiceId=voice, Engine="standard",
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

def grid_synthesize(text, ssml, *, language_code=GRID_LANGUAGE_CODE, outdir="out/grid"):
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
                       outpath=os.path.join(voice_dir, f"ssml_{vid}_{eng}.{OUTPUT_FORMAT}"))
        except Exception as e:
            print(f"[SKIP ssml] {vid}/{eng}: {e}")

def main():
    _assert_aws_creds()
    ensure_dirs("out/baseline")

    # Baseline: two files (plain + SSML) for the chosen voice/engine
    baseline_text_path = f"out/baseline/plain_{BASELINE_VOICE}_{BASELINE_ENGINE}.{OUTPUT_FORMAT}"
    baseline_ssml_path = f"out/baseline/ssml_{BASELINE_VOICE}_{BASELINE_ENGINE}.{OUTPUT_FORMAT}"
    synthesize(TEXT_INPUT, text_type="text", voice=BASELINE_VOICE,
               engine=BASELINE_ENGINE, outpath=baseline_text_path)
    synthesize(SSML_INPUT,  text_type="ssml", voice=BASELINE_VOICE,
               engine=BASELINE_ENGINE, outpath=baseline_ssml_path)
    print(f"\nBaseline files written:\n  {baseline_text_path}\n  {baseline_ssml_path}\n")

    if DO_GRID:
        print("Running full grid (this may create MANY files and incur costs)…")
        grid_synthesize(TEXT_INPUT, SSML_INPUT, language_code=GRID_LANGUAGE_CODE)

if __name__ == "__main__":
    main()