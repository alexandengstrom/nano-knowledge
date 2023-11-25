import openai
import os
import requests
import json
import random
import argparse

VOICE_ID = "sqq5kZVzLDloiGWHUxAV"
MODEL = "gpt-4-1106-preview"


def read_file(file_path):
    """Reads content from a file."""
    with open(file_path, "r") as file:
        return file.read()


def append_to_file(file_path, text):
    """Appends text to a file."""
    with open(file_path, "a") as file:
        file.write(f"{text}\n")


def get_api_key(api_name):
    """Retrieves API key from a file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(base_dir, f"../api_keys/{api_name}")
    with open(key_path, "r") as file:
        return file.read().strip()


def setup_openai_api():
    """Sets up OpenAI API key."""
    openai.api_key = get_api_key("openai")


def query_openai_gpt(message_history):
    """Queries OpenAI GPT for a podcast script."""
    try:
        completion = openai.ChatCompletion.create(
            model=MODEL,
            response_format={"type": "json_object"},
            messages=message_history,
            max_tokens=3600)
        response = completion['choices'][0]['message']['content']
        content = json.loads(response)
        assert all(k in content for k in ("title", "description", "content"))
    except (json.JSONDecodeError, AssertionError):
        print("Invalid JSON format")
        exit()

    print(f"Script Length: {len(content['content'].split())} words")
    return content


def request_text_to_speech(content, voice_id):
    """Requests ElevenLabs API to convert text to speech."""
    api_key = get_api_key("elevenlabs")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key}
    data = {
        'text': content,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {'stability': 0, 'similarity_boost': 0, 'style': 0.5, 'use_speaker_boost': False}
    }

    return requests.post(url, headers=headers, data=json.dumps(data))


def handle_audio_response(response, season, episode):
    """Handles the response from the text-to-speech request."""
    if response.status_code == 200:
        audio_data = response.content
        filename = f"season{season}_episode{episode}.wav"
        with open(filename, "wb") as file:
            file.write(audio_data)
            print(f"Saved audio file: {filename}")
    else:
        print(f"Error: {response.status_code}")


def create_podcast_episode(season, episode):
    """Creates a single podcast episode."""
    used_topics = read_file("topics_used.txt")
    random.shuffle(used_topics)
    used_topics_str = ", ".join(s.strip() for s in subjects)

    subjects = read_file("subjects.txt").split("\n")
    random.shuffle(subjects)
    subjects_str = ", ".join(s.strip() for s in subjects)

    message_history = [
        {"role": "user", "content": read_file("prompt.txt")},
        {"role": "user", "content": f"This is topics that has already been used in the podcast so do not create a duplicate: {used_topics_str}"},
        {"role": "user", "content": f"You can choose a random fact in one of those subjects: {subjects_str}"}
    ]

    content = query_openai_gpt(message_history)
    response = request_text_to_speech(content["content"], VOICE_ID)
    handle_audio_response(response, season, episode)
    append_to_file("topics_used.txt", content["title"])


def create_podcast_season(season, episode_count):
    """Creates a full season of podcast episodes."""
    for episode in range(1, episode_count + 1):
        create_podcast_episode(season, episode)


def parse_arguments():
    """Parses command line arguments for the script."""
    parser = argparse.ArgumentParser(
        description='Automated Podcast Creation Script')
    parser.add_argument(
        '--season',
        type=int,
        help='Season number for the podcast'
    )
    parser.add_argument(
        '--episodes',
        type=int,
        default=1,
        help='Number of episodes to create for the season (default is 1)'
    )

    return parser.parse_args()


def main():
    """Main function to run the podcast creation script."""
    args = parse_arguments()

    season = args.season
    number_of_episodes = args.episodes

    print(f"Creating Season {season} with {number_of_episodes} episodes.")
    create_podcast_season(season, number_of_episodes)
    print("Podcast creation complete.")


if __name__ == "__main__":
    setup_openai_api()
    main()
