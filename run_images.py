"""Send every image in a folder to a local Unsloth model and save the answers.

How to run:   python run_images.py
Settings:     config.toml
System prompt: system_prompt.txt

The loaded model must be one that can read images (a "vision" model).
"""

import base64
import csv
import json
import mimetypes
import os
import time
import tomllib
import urllib.request

LOG_FILE = "run_log.txt"

IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".webp")

# Work from the folder this script lives in, so the file names in config.toml are found.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("config.toml", "rb") as f:
    config = tomllib.load(f)

with open(config["system_prompt_file"], encoding="utf-8") as f:
    system_prompt = f.read().strip()


def write_log(text):
    """Add one line, with the date and time, to the log file."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "  " + text + "\n")


def ask_model(image_path):
    """Send one image (plus the image_prompt) to the model and return its answer and its thinking."""
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("ascii")
    image_type = mimetypes.guess_type(image_path)[0]

    user_message = [
        {"type": "text", "text": config["image_prompt"]},
        {"type": "image_url", "image_url": {"url": f"data:{image_type};base64,{image_data}"}},
    ]
    messages = [{"role": "user", "content": user_message}]
    if system_prompt:
        messages.insert(0, {"role": "system", "content": system_prompt})

    body = {"model": config["model"], "messages": messages, **config["parameters"]}

    headers = {"Content-Type": "application/json"}
    if config["api_key"]:
        headers["Authorization"] = "Bearer " + config["api_key"]

    request = urllib.request.Request(
        config["base_url"] + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
    )
    start = time.time()
    with urllib.request.urlopen(request, timeout=600) as reply:
        raw_reply = reply.read().decode("utf-8")
    # Keep the model's full, untouched reply in the log for diagnostics.
    write_log(f"Reply after {time.time() - start:.0f} seconds: {raw_reply}")

    message = json.loads(raw_reply)["choices"][0]["message"]
    # "reasoning_content" is the model's thinking. It is empty when thinking is off.
    return message.get("content") or "", message.get("reasoning_content") or ""


# Find all the images, in alphabetical order.
folder = config["image_folder"]
images = sorted(name for name in os.listdir(folder) if name.lower().endswith(IMAGE_TYPES))

# For a quick demo, only keep the first few images (0 means keep them all).
max_rows = config.get("max_rows", 0)
if max_rows:
    images = images[:max_rows]

write_log(f"=== run_images.py started. {len(images)} images. model={config['model']} parameters={config['parameters']}")

# Ask the model about each image. Each answer is saved straight away,
# so nothing is lost if the run stops part way through.
with open(config["output_file"], "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["image", "response", "thinking"])

    for number, name in enumerate(images, start=1):
        print(f"Image {number} of {len(images)}: {name}")
        write_log(f"Image {number} ({name}): sending")
        try:
            response, thinking = ask_model(os.path.join(folder, name))
            if not response:
                print("   No answer came back. See", LOG_FILE)
        except Exception as error:
            # If the server sent an explanation with the error, keep that too.
            details = error.read().decode("utf-8") if hasattr(error, "read") else ""
            response, thinking = f"ERROR: {error} {details}", ""
            print("  ", response)
            write_log(f"Image {number} ({name}): {response}")
        writer.writerow([name, response, thinking])
        f.flush()

print("Done. Answers saved to", config["output_file"])
