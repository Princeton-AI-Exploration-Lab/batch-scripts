BATCH QUERIES TO A LOCAL UNSLOTH MODEL
======================================

What you need
-------------
- Python 3.11 or newer. Nothing else to install.
- Unsloth running on your computer with a model loaded.

Files
-----
config.toml        Your settings. Edit this.
system_prompt.txt  Your system prompt. Edit this.
inputs.csv         Example input file. Replace with your own.
run_text.py        Sends each row of your CSV to the model.
run_images.py      Sends each image in a folder to the model.

Steps
-----
1. Start Unsloth and load your model.
2. Check that base_url in config.toml matches the address Unsloth shows you.
   Leave api_key empty unless your setup needs a key.
3. Write your system prompt in system_prompt.txt.
4. Set your hyperparameters in the [parameters] part of config.toml.
   Thinking mode is the enable_thinking line there: true or false.
5. Text task:  put your CSV in this folder. Set input_file in config.toml.
               Every column of each row is sent to the model, written as
               "column title: value", one line per column.
   Image task: put your images in a folder called "images" in this folder.
               Set image_prompt in config.toml.
6. Optional: for a quick test, set max_rows in config.toml to a small
   number like 3. Set it back to 0 to run everything.
7. Open a terminal in this folder and run ONE of these:
       python run_text.py
       python run_images.py
8. Open results.csv in Excel or Google Sheets.

Good to know
------------
- results.csv has a "response" column (the answer) and a "thinking" column
  (the model's reasoning, when thinking mode is on).
- Each run REPLACES results.csv. Rename the old one first, or change
  output_file in config.toml, if you want to keep it.
- If a row fails, its response cell starts with "ERROR:" and the run
  carries on with the next row.
- "HTTP Error 401" means Unsloth wants an API key. Make one in Unsloth
  under Settings -> API and paste it into api_key in config.toml.
- "Connection refused" means Unsloth is not running, or the port number
  in base_url is wrong.
- The image script needs a model that can read images.
