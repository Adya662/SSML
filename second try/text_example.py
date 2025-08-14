import boto3
import os
def _assert_aws_creds():
  try:
    import boto3
    s = boto3.Session() # respects AWS_PROFILE/AWS_SDK_LOAD_CONFIG
    if s.get_credentials() is None:
      raise RuntimeError(
        "No AWS credentials available. With SSO, run:\n"
        " aws sso login --profile <your-profile>\n"
        "and export AWS_PROFILE and AWS_SDK_LOAD_CONFIG before running this script."
      )
  except Exception as e:
    raise
# If you want to hard-pin the SSO profile from code (optional):
os.environ.setdefault("AWS_PROFILE", "Power-root")
os.environ.setdefault("AWS_SDK_LOAD_CONFIG", "1")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-south-1")

_assert_aws_creds()
polly = boto3.client("polly", region_name="us-east-1")
ssml = """
Given the severity of this situation and the fact that this is clearly our fulfillment error, I'm expediting your replacement through our express delivery service, and I'm pleased to inform you that this will be much faster than our standard delivery times. Here's the timeline I can guarantee for your replacement: Since this is being processed as a priority case, I'm arranging for your replacement dress to be dispatched today itself if we can get it processed within the next few hours, or definitely by tomorrow morning at the latest. With our express delivery service, which I'm providing to you at no additional cost as compensation for the inconvenience, you should receive your correct red dress within 2-3 business days maximum. More specifically, if the dress ships today, you should receive it by August 15th or 16th at the latest. If it ships tomorrow morning, you'll receive it by August 16th or 17th. This is significantly faster than our standard 5-7 day delivery window, and again, the express shipping charges are completely waived for you. I'm also ensuring that you receive proactive tracking updates throughout the process. You'll get SMS notifications when the replacement order is created, when it's dispatched, when it's out for delivery, and when it's delivered. You'll also receive email updates with detailed tracking information and the photographic verification I mentioned earlier. Additionally, I'm arranging for the return pickup of the incorrect blue dress to happen after you receive your replacement. This way, if there are any unforeseen issues with the replacement (though I'm confident there won't be), you'll still have the blue dress as a backup until everything is completely resolved to your satisfaction. Our delivery executive will also be given special instructions about your case, so they'll handle your package with extra care and will be available to address any immediate concerns you might have upon delivery.
"""
resp = polly.synthesize_speech(
    Text=ssml,
    TextType="text",          # using plain text here
    VoiceId="Joanna",         # try other voices like "Matthew", "Amy"
    Engine="standard",          # optional: "standard" or "neural" (voice-dependent)
    OutputFormat="mp3"
)
# Save the audio stream
with open("polly-text.mp3", "wb") as f:
    f.write(resp["AudioStream"].read())
print("Saved to polly-text.mp3")











