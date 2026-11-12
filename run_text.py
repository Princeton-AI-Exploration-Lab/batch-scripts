"""Send every row of a CSV file to a local Unsloth model and save the answers.

Each row is sent as lines of "column title: value", one line per column.

How to run:   python run_text.py
Settings:     config.toml
System prompt: system_prompt.txt
"""

import csv
import json
import os
import time
import tomllib
import urllib.request

LOG_FILE = "run_log.txt"

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


def ask_model(user_message):
    """Send one message to the model and return its answer and its thinking."""
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


# Read all the input rows.
with open(config["input_file"], newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    columns = reader.fieldnames
    rows = list(reader)

# For a quick demo, only keep the first few rows (0 means keep them all).
max_rows = config.get("max_rows", 0)
if max_rows:
    rows = rows[:max_rows]

write_log(f"=== run_text.py started. {len(rows)} rows. model={config['model']} parameters={config['parameters']}")

# Ask the model about each row. Each answer is saved straight away,
# so nothing is lost if the run stops part way through.
with open(config["output_file"], "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=columns + ["response", "thinking"])
    writer.writeheader()

    for number, row in enumerate(rows, start=1):
        print(f"Row {number} of {len(rows)}...")
        write_log(f"Row {number}: sending")
        try:
            # Turn the row into lines of "column title: value".
            message = "\n".join(f"{title}: {value}" for title, value in row.items())
            row["response"], row["thinking"] = ask_model(message)
            if not row["response"]:
                print("   No answer came back. See", LOG_FILE)
        except Exception as error:
            # If the server sent an explanation with the error, keep that too.
            details = error.read().decode("utf-8") if hasattr(error, "read") else ""
            row["response"] = f"ERROR: {error} {details}"
            print("  ", row["response"])
            write_log(f"Row {number}: {row['response']}")
        writer.writerow(row)
        f.flush()

print("Done. Answers saved to", config["output_file"])
