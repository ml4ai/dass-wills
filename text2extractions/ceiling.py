# This code is for evaluation purpose only
import os
import csv
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

def create_full_prompt(preds, example_list):
  first_part = """Your task is to extract all instances of the following entities and events (including pronouns) from the will texts and output the extraction in JSON format.

  %%entities: Testator, Beneficiary, Witness, State, County, Asset, Bond, Executor, Date, Time, Trustee, Will, Codicil, Debt, Expense, Tax, Duty, Right, Condition, Guardian, Trust, Conservator, Affidavit, NotaryPublic, NonBeneficiary
  %events: WillCreation, SignWill, Attestation, Revocation, Codicil, Bequest, Nomination, Disqualification, Renunciation, Death, Probate, Direction, Authorization, Excuse, Give, Notarization, NonProbateInstrumentCreation, Birth, Residual, Removal

  Here’s some examples of expected outputs in the desired format.

  {
  """
  second_part = "\n}"
  examples_to_use = []
  n = 0
  while n < 9:
    if preds[n] == 1:
      examples_to_use.append(example_list[n])
    n += 1
  if len(examples_to_use) == 0:
    examples_to_use.append(example_list[9])
  prompt_examples = ',\n'.join(examples_to_use)
  full_prompt = first_part + prompt_examples + second_part
  return full_prompt

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def extract_information(prompt, target_text, client):
  
  response = client.chat.completions.create(
    model='gpt-4-1106-preview',
    response_format={
      'type': 'json_object',
    },
    messages=[
      {
        "role": "system",
        "content": prompt
      },
      {
        "role": "user",
        "content": target_text
      }
    ],
    temperature=1,
    max_tokens=4096,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
  )
  return response

def main(input_file):
  # prompt the user for their openai api key
  key = input("Please enter your openai api key: ")
  client = OpenAI(api_key=key)

  text_list = []
  pred_list = []
  with open(input_file, 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader, None)
    for row in csvreader:
      text_list.append(row[0])
      preds = [eval(i) for i in row[1:]]
      pred_list.append(preds)

  # check if the length of preds_list and text_list are equal
  assert len(preds) == len(text_list)

  # get the prompt examples
  example_csv = "prompt_examples.csv"
  example_list = []
  with open(example_csv, 'r') as csvfile:
      csvreader = csv.reader(csvfile)
      for row in csvreader:
        example_list.append(row[1])

  # using predictions, create prompts and extract information
  extracted_info = []
  n = 0
  while n < len(text_list):
    print("processing " + str(n+1) + "th sentence!")
    try:
      prompt = create_full_prompt(preds[n], example_list)
      response = extract_information(prompt, text_list[n], client)
      extracted_info.append(response.choices[0].message.content)
      n += 1
    except:
      print("something went wrong while processing " + str(n) + "th text!")
      return extracted_info
  return extracted_info