"""Tamara: a voice assistant for your Mac. Say "Tamara" to wake her up."""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ACTIVE_SECONDS = 30  # after she answers, you can keep talking without saying "Tamara" again
YES = re.compile(r"\b(yes|yeah|yep|yup|sure|go ahead|do it|please do|okay|ok|confirm|proceed)\b", re.I)
SLEEP = re.compile(r"\b(goodbye|good bye|go to sleep|that's all|that is all|stop listening)\b", re.I)
CANCEL = re.compile(r"^\W*(never ?mind|cancel|stop|forget it)\W*$", re.I)


def load_env():
    path = os.path.join(HERE, ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                if value.strip():
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    load_env()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("No API key found. Open the .env file in this folder and paste your Anthropic API key.")
        sys.exit(1)

    from brain import Brain
    from voice import Ears, Mouth, find_wake_word

    mouth, ears = Mouth(), Ears()

    def confirm(question):
        mouth.say(question)
        answer = ears.transcribe(ears.listen(wait_seconds=8, max_seconds=6))
        print(f"You: {answer}")
        return bool(YES.search(answer))

    brain = Brain(mouth.say, confirm)
    mouth.say("Hello, I'm Tamara. How are you? Say my name whenever you need me.")
    print("\nListening... (press Ctrl+C to quit)\n")

    active_until = 0.0
    while True:
        awake = time.time() < active_until
        audio = ears.listen(wait_seconds=None, max_seconds=30 if awake else 8)
        text = ears.transcribe(audio)
        if not text:
            continue

        command = text
        if not awake:
            command = find_wake_word(text)
            if command is None:
                continue  # not talking to Tamara
            if not command:
                mouth.say("Yes? What would you like me to do?")
                active_until = time.time() + ACTIVE_SECONDS
                continue

        print(f"You: {command}")
        if CANCEL.match(command):
            mouth.say("Okay.")
            continue
        if SLEEP.search(command):
            mouth.say("Goodbye. Say my name if you need me.")
            active_until = 0.0
            continue
        try:
            brain.respond(command)
        except Exception as err:
            print(f"[error] {err}")
            mouth.say("Sorry, I had trouble thinking that through. Please check the window for details.")
        active_until = time.time() + ACTIVE_SECONDS


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTamara stopped.")
