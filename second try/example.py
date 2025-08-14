import boto3
import os

def _assert_aws_creds():
  try:
    s = boto3.Session()
    if s.get_credentials() is None:
      raise RuntimeError("No AWS credentials available. Run: aws sso login --profile <your-profile>")
  except Exception as e:
    raise

os.environ.setdefault("AWS_PROFILE", "Power-root")
os.environ.setdefault("AWS_SDK_LOAD_CONFIG", "1")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-south-1")

_assert_aws_creds()
polly = boto3.client("polly", region_name="us-east-1")

customer_service_text = """Given the severity of this situation and the fact that this is clearly our fulfillment error, I'm expediting your replacement through our express delivery service, and I'm pleased to inform you that this will be much faster than our standard delivery times. Here's the timeline I can guarantee for your replacement: Since this is being processed as a priority case, I'm arranging for your replacement dress to be dispatched today itself if we can get it processed within the next few hours, or definitely by tomorrow morning at the latest. With our express delivery service, which I'm providing to you at no additional cost as compensation for the inconvenience, you should receive your correct red dress within 2-3 business days maximum. More specifically, if the dress ships today, you should receive it by August 15th or 16th at the latest. If it ships tomorrow morning, you'll receive it by August 16th or 17th. This is significantly faster than our standard 5-7 day delivery window, and again, the express shipping charges are completely waived for you. I'm also ensuring that you receive proactive tracking updates throughout the process. You'll get SMS notifications when the replacement order is created, when it's dispatched, when it's out for delivery, and when it's delivered. You'll also receive email updates with detailed tracking information and the photographic verification I mentioned earlier. Additionally, I'm arranging for the return pickup of the incorrect blue dress to happen after you receive your replacement. This way, if there are any unforeseen issues with the replacement (though I'm confident there won't be), you'll still have the blue dress as a backup until everything is completely resolved to your satisfaction. Our delivery executive will also be given special instructions about your case, so they'll handle your package with extra care and will be available to address any immediate concerns you might have upon delivery."""

def synthesize(text, voice_id, engine, output_file, text_type="text"):
  try:
    resp = polly.synthesize_speech(
      Text=text,
      TextType=text_type,
      VoiceId=voice_id,
      Engine=engine,
      OutputFormat="mp3"
    )
    with open(output_file, "wb") as f:
      f.write(resp["AudioStream"].read())
    print(f"✅ {output_file}")
    return True
  except Exception as e:
    msg = str(e)
    # Fallback: if neural SSML is unsupported, retry as plain text
    if text_type == "ssml" and engine == "neural" and "InvalidSsmlException" in msg:
      try:
        resp = polly.synthesize_speech(
          Text=customer_service_text,
          TextType="text",
          VoiceId=voice_id,
          Engine=engine,
          OutputFormat="mp3"
        )
        with open(output_file, "wb") as f:
          f.write(resp["AudioStream"].read())
        print(f"✅ {output_file}")
        return True
      except Exception as e2:
        print(f"❌ {output_file}: {str(e2)}")
        return False
    else:
      print(f"❌ {output_file}: {msg}")
      return False

# SSML versions
standard_ssml = f"""<speak>
<prosody rate="fast">
<emphasis level="strong">Given the severity of this situation</emphasis> and the fact that 
<emphasis level="moderate">this is clearly our fulfillment error</emphasis>, 
<break time="0.5s"/>
I'm <prosody rate="fast" volume="loud">expediting your replacement</prosody> through our express delivery service, 
<break time="0.3s"/>
and I'm <prosody pitch="high" volume="medium">pleased to inform you</prosody> that this will be 
<emphasis level="strong">much faster</emphasis> than our standard delivery times.
<break time="300ms"/>
Here's the timeline I can <emphasis level="strong">guarantee</emphasis> for your replacement:
<break time="200ms"/>
Since this is being processed as a <emphasis level="strong">priority case</emphasis>, 
I'm arranging for your replacement dress to be <prosody rate="slow" volume="loud">dispatched today itself</prosody> 
if we can get it processed within the next few hours, 
<break time="150ms"/>
or <emphasis level="moderate">definitely by tomorrow morning at the latest</emphasis>.
<break time="300ms"/>
With our express delivery service, which I'm providing to you at 
<emphasis level="strong">no additional cost</emphasis> as compensation for the inconvenience, 
you should receive your correct red dress within <prosody pitch="high">2-3 business days maximum</prosody>.
<break time="200ms"/>
<prosody rate="slow" volume="medium">More specifically</prosody>, 
if the dress ships today, you should receive it by <say-as interpret-as="date" format="md">August 15th</say-as> 
or <say-as interpret-as="date" format="md">16th</say-as> at the latest.
<break time="150ms"/>
If it ships tomorrow morning, you'll receive it by <say-as interpret-as="date" format="md">August 16th</say-as> 
or <say-as interpret-as="date" format="md">17th</say-as>.
<break time="300ms"/>
This is <emphasis level="strong">significantly faster</emphasis> than our standard 5-7 day delivery window, 
<break time="0.3s"/>
and again, the express shipping charges are <emphasis level="strong">completely waived for you</emphasis>.
<break time="300ms"/>
I'm also ensuring that you receive <prosody pitch="high" volume="medium">proactive tracking updates</prosody> 
throughout the process. You'll get <sub alias="S M S">SMS</sub> notifications when the replacement order is created, 
when it's dispatched, when it's out for delivery, and when it's delivered.
<break time="200ms"/>
Additionally, I'm arranging for the return pickup of the incorrect blue dress to happen 
<emphasis level="moderate">after you receive your replacement</emphasis>.
<break time="200ms"/>
This way, if there are any unforeseen issues with the replacement 
<prosody rate="slow" volume="soft">(though I'm confident there won't be)</prosody>, 
you'll still have the blue dress as a backup until everything is 
<emphasis level="strong">completely resolved to your satisfaction</emphasis>.
<break time="0.8s"/>
Our delivery executive will also be given <emphasis level="strong">special instructions</emphasis> about your case, 
so they'll handle your package with <prosody pitch="high">extra care</prosody> and will be available to address 
any immediate concerns you might have upon delivery.
</prosody>
</speak>"""

neural_ssml = f"""<speak>
{customer_service_text}
</speak>"""

longform_ssml = f"""<speak>
<prosody rate="medium" volume="medium">
Given the severity of this situation and the fact that this is clearly our fulfillment error, 
I'm <emphasis level="strong">expediting your replacement</emphasis> through our express delivery service, 
<break time="0.5s"/>
and I'm pleased to inform you that this will be much faster than our standard delivery times.
<break time="1s"/>
Here's the timeline I can guarantee for your replacement: 
<break time="0.3s"/>
Since this is being processed as a priority case, I'm arranging for your replacement dress to be 
<prosody rate="slow">dispatched today itself</prosody> if we can get it processed within the next few hours, 
or definitely by tomorrow morning at the latest.
<break time="0.8s"/>
<prosody volume="loud">With our express delivery service</prosody>, which I'm providing to you at no additional cost 
as compensation for the inconvenience, you should receive your correct red dress within 2-3 business days maximum.
<break time="0.5s"/>
More specifically, if the dress ships today, you should receive it by August 15th or 16th at the latest. 
If it ships tomorrow morning, you'll receive it by August 16th or 17th.
<break time="0.5s"/>
This is significantly faster than our standard 5-7 day delivery window, 
and again, the express shipping charges are completely waived for you.
<break time="1s"/>
I'm also ensuring that you receive proactive tracking updates throughout the process. 
You'll get SMS notifications when the replacement order is created, when it's dispatched, 
when it's out for delivery, and when it's delivered.
<break time="0.5s"/>
Additionally, I'm arranging for the return pickup of the incorrect blue dress to happen 
after you receive your replacement. This way, if there are any unforeseen issues with the replacement, 
you'll still have the blue dress as a backup until everything is completely resolved to your satisfaction.
<break time="0.8s"/>
<emphasis level="strong">Our delivery executive will also be given special instructions about your case</emphasis>, 
so they'll handle your package with extra care and will be available to address any immediate concerns 
you might have upon delivery.
</prosody>
</speak>"""

generative_ssml = f"""<speak>
<prosody rate="medium">{customer_service_text}</prosody>
</speak>"""

dramatic_ssml = f"""<speak>
<amazon:domain name="conversational">
<prosody rate="slow" volume="x-loud" pitch="low">
<emphasis level="strong">Given the severity of this situation</emphasis> 
<break time="1s"/>
and the fact that <amazon:effect name="whispered">this is clearly our fulfillment error</amazon:effect>, 
<break time="2s"/>
I'm <prosody rate="x-fast" volume="x-loud" pitch="high">EXPEDITING your replacement</prosody> 
through our express delivery service.
<break time="1.5s"/>
</prosody>
<amazon:effect name="drc">
<prosody rate="medium" volume="loud">
And I'm <emphasis level="strong">PLEASED</emphasis> to inform you that this will be 
<prosody rate="slow" pitch="high">MUCH faster</prosody> than our standard delivery times.
</prosody>
</amazon:effect>
<break time="2s"/>
<prosody rate="x-slow" volume="x-loud" pitch="x-low">
Here's the timeline I can <emphasis level="strong">GUARANTEE</emphasis> for your replacement:
</prosody>
<break time="1.5s"/>
<amazon:effect name="whispered">
<prosody rate="slow">
Since this is being processed as a priority case, I'm arranging for your replacement dress 
to be dispatched today itself if we can get it processed within the next few hours, 
or definitely by tomorrow morning at the latest.
</prosody>
</amazon:effect>
<break time="2s"/>
<amazon:domain name="news">
<prosody rate="fast" volume="x-loud">
With our express delivery service, which I'm providing to you at 
<emphasis level="strong">NO ADDITIONAL COST</emphasis> as compensation for the inconvenience, 
you should receive your correct red dress within 
<prosody rate="x-slow" pitch="high">TWO to THREE business days MAXIMUM</prosody>.
</prosody>
</amazon:domain>
<break time="2s"/>
<amazon:effect name="whispered">
<prosody rate="x-slow" volume="soft">
More specifically, if the dress ships today, you should receive it by 
<say-as interpret-as="date" format="md">August 15th</say-as> or 
<say-as interpret-as="date" format="md">16th</say-as> at the latest.
</prosody>
</amazon:effect>
<break time="1s"/>
<prosody rate="fast" volume="x-loud" pitch="high">
If it ships tomorrow morning, you'll receive it by 
<say-as interpret-as="date" format="md">August 16th</say-as> or 
<say-as interpret-as="date" format="md">17th</say-as>.
</prosody>
<break time="2s"/>
<amazon:effect name="drc">
<prosody rate="medium" volume="x-loud">
This is <emphasis level="strong">SIGNIFICANTLY FASTER</emphasis> than our standard 5-7 day delivery window, 
<break time="1s"/>
and again, the express shipping charges are <prosody rate="slow" pitch="high">COMPLETELY WAIVED FOR YOU</prosody>.
</prosody>
</amazon:effect>
<break time="2s"/>
<amazon:domain name="conversational">
<prosody rate="slow" volume="medium">
I'm also ensuring that you receive proactive tracking updates throughout the process. 
You'll get <acronym>SMS</acronym> notifications when the replacement order is created, 
when it's dispatched, when it's out for delivery, and when it's delivered.
</prosody>
</amazon:domain>
<break time="1.5s"/>
<amazon:effect name="whispered">
<prosody rate="x-slow" volume="x-soft">
Additionally, I'm arranging for the return pickup of the incorrect blue dress 
to happen after you receive your replacement. This way, if there are any unforeseen issues 
with the replacement, you'll still have the blue dress as a backup until everything is 
completely resolved to your satisfaction.
</prosody>
</amazon:effect>
<break time="2s"/>
<prosody rate="fast" volume="x-loud" pitch="high">
Our delivery executive will also be given <emphasis level="strong">SPECIAL INSTRUCTIONS</emphasis> 
about your case, so they'll handle your package with 
<prosody rate="slow" pitch="high">EXTRA CARE</prosody> 
and will be available to address any immediate concerns you might have upon delivery.
</prosody>
</amazon:domain>
</speak>"""

breathing_ssml = f"""<speak>
<amazon:breath duration="medium" volume="x-loud"/>
<prosody rate="medium" volume="medium">
Given the severity of this situation 
<amazon:breath duration="short" volume="medium"/>
and the fact that this is clearly our fulfillment error, 
<amazon:breath duration="long" volume="soft"/>
I'm expediting your replacement through our express delivery service,
<amazon:breath duration="medium" volume="medium"/>
and I'm pleased to inform you that this will be much faster than our standard delivery times.
</prosody>
<amazon:breath duration="long" volume="loud"/>
<prosody rate="slow" volume="loud">
Here's the timeline I can guarantee for your replacement:
<amazon:breath duration="short" volume="medium"/>
Since this is being processed as a priority case,
<amazon:breath duration="medium" volume="soft"/>
I'm arranging for your replacement dress to be dispatched today itself 
if we can get it processed within the next few hours,
<amazon:breath duration="long" volume="medium"/>
or definitely by tomorrow morning at the latest.
</prosody>
<amazon:breath duration="long" volume="loud"/>
<prosody rate="medium" volume="medium">
With our express delivery service,
<amazon:breath duration="short" volume="soft"/>
which I'm providing to you at no additional cost as compensation for the inconvenience,
<amazon:breath duration="medium" volume="medium"/>
you should receive your correct red dress within 2-3 business days maximum.
</prosody>
<amazon:breath duration="long" volume="medium"/>
<prosody rate="slow">
More specifically,
<amazon:breath duration="short" volume="soft"/>
if the dress ships today, you should receive it by August 15th or 16th at the latest.
<amazon:breath duration="medium" volume="medium"/>
If it ships tomorrow morning, you'll receive it by August 16th or 17th.
</prosody>
<amazon:breath duration="long" volume="loud"/>
<prosody rate="medium" volume="loud">
This is significantly faster than our standard 5-7 day delivery window,
<amazon:breath duration="short" volume="soft"/>
and again, the express shipping charges are completely waived for you.
</prosody>
<amazon:breath duration="long" volume="medium"/>
<prosody rate="medium">
I'm also ensuring that you receive proactive tracking updates throughout the process.
<amazon:breath duration="short" volume="soft"/>
You'll get SMS notifications when the replacement order is created,
<amazon:breath duration="short" volume="soft"/>
when it's dispatched,
<amazon:breath duration="short" volume="soft"/>
when it's out for delivery,
<amazon:breath duration="short" volume="soft"/>
and when it's delivered.
</prosody>
<amazon:breath duration="medium" volume="medium"/>
<prosody rate="slow">
Additionally, I'm arranging for the return pickup of the incorrect blue dress 
to happen after you receive your replacement.
<amazon:breath duration="long" volume="soft"/>
This way, if there are any unforeseen issues with the replacement,
<amazon:breath duration="medium" volume="medium"/>
you'll still have the blue dress as a backup until everything is 
completely resolved to your satisfaction.
</prosody>
<amazon:breath duration="long" volume="loud"/>
<prosody rate="medium" volume="loud">
Our delivery executive will also be given special instructions about your case,
<amazon:breath duration="short" volume="soft"/>
so they'll handle your package with extra care and will be available to address 
any immediate concerns you might have upon delivery.
</prosody>
<amazon:breath duration="medium" volume="medium"/>
</speak>"""

configs = [
  (standard_ssml, 'Aditi', 'standard', 'ssml-standard-aditi.mp3', 'ssml'),
  (neural_ssml, 'Kajal', 'neural', 'ssml-neural-kajal.mp3', 'ssml'),
  (generative_ssml, 'Ruth', 'generative', 'ssml-generative-ruth.mp3', 'ssml'),
  (customer_service_text, 'Aditi', 'standard', 'plain-standard-aditi.mp3', 'text'),
  (customer_service_text, 'Kajal', 'neural', 'plain-neural-kajal.mp3', 'text'),
  (customer_service_text, 'Ruth', 'generative', 'plain-generative-ruth.mp3', 'text'),
  (breathing_ssml, 'Aditi', 'standard', 'breathing-natural-aditi.mp3', 'ssml'),
]

def main():
    for text, voice_id, engine, output_file, text_type in configs:
        synthesize(text, voice_id, engine, output_file, text_type)

if __name__ == "__main__":
    main()