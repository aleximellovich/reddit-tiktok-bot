import os
import praw
import redis
from google.cloud import texttospeech


def authenticate_reddit():
    client_id = os.environ['REDDIT_CLIENT_ID']
    client_secret = os.environ['REDDIT_CLIENT_SECRET']
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent="PyEng Bot 0.1"
    )
    return reddit


def get_content(subreddit, reddit):

    reddit_subreddit = reddit.subreddit(subreddit)

    limit = 20

    hot_submissions = list(reddit_subreddit.hot(limit=limit))
    hot_submissions.sort(key=lambda x: x.score, reverse=True)

    content = {}
    r = redis.Redis(host='localhost', port=6379)
    for submission in hot_submissions:
        current_submission_id_list = r.json().get(subreddit)
        if current_submission_id_list is None:
            current_submission_id_list = list()

        if submission.id not in current_submission_id_list:
            current_submission_id_list.append(submission.id)
            r.json().set(subreddit, '$', current_submission_id_list)
            content["subreddit"] = subreddit
            content["title"] = submission.title
            if subreddit == 'askreddit':
                content["body"] = get_comments(submission, 20)
            else:
                content["body"] = submission.selftext

            return content


def create_audio(text):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    return response.audio_content


def get_audio_temp(text):
    """
    Synthesizes long input, writing the resulting audio to `output_gcs_uri`.

    Example usage: synthesize_long_audio('12345', 'us-central1', 'gs://{BUCKET_NAME}/{OUTPUT_FILE_NAME}.wav')

    """
    # TODO(developer): Uncomment and set the following variables
    project_id = os.environ['PROJECT_ID']
    location = 'global'
    output_gcs_uri = 'gs://texttospeech-audio/audio.wav'

    client = texttospeech.TextToSpeechLongAudioSynthesizeClient()

    input = texttospeech.SynthesisInput(
        text=text
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", name="en-US-Standard-A"
    )

    parent = f"projects/{project_id}/locations/{location}"

    request = texttospeech.SynthesizeLongAudioRequest(
        parent=parent,
        input=input,
        audio_config=audio_config,
        voice=voice,
        output_gcs_uri=output_gcs_uri
    )

    operation = client.synthesize_long_audio(request=request)
    # Set a deadline for your LRO to finish. 300 seconds is reasonable, but can be adjusted depending on the length of the input.
    # If the operation times out, that likely means there was an error. In that case, inspect the error, and try again.
    result = operation.result(timeout=300)
    print(
        "\nFinished processing, check your GCS bucket to find your audio file! Printing what should be an empty result: ",
        result,
    )


def get_comments(submission, limit):
    submission.comment_sort = "top"
    comments = submission.comments.list()
    content_body = ""
    for i, comment in enumerate(comments):
        if i >= limit:
            break
        formatted_comment = comment.body.replace('\n', "")
        content_body += f"{formatted_comment}\n\n\n"

    return content_body


def print_submissions(submissions):
    for i, submission in enumerate(submissions):
        print(f"{i}:\t{submission.title}\n")
        print(f"Score:\t{submission.score}")


def print_content(content):
    subreddit = content["subreddit"]
    title = content["title"]
    body = content["body"]

    print(f"Subreddit: {subreddit}\nTitle: {title}\n Content: {body}")