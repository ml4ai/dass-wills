import os
import csv
from setfit import SetFitModel
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

def create_full_prompt(example_list):
  first_part = """Your task is to extract all instances of the following entities and events (including pronouns) from the will texts and output the extraction in JSON format.

  %%entities: Testator, Beneficiary, Witness, State, County, Asset, Bond, Executor, Date, Time, Trustee, Will, Codicil, Debt, Expense, Tax, Duty, Right, Condition, Guardian, Trust, Conservator, Affidavit, NotaryPublic, NonBeneficiary

  %%events: WillCreation, SignWill, Attestation, Revocation, Codicil, Bequest, Nomination, Disqualification, Renunciation, Death, Probate, Direction, Authorization, Excuse, Give, Notarization, NonProbateInstrumentCreation, Birth, Residual, Removal

  Here’s some examples of expected outputs in the desired format.

  {
  """
  second_part = "\n}"
  prompt_examples = ',\n'.join(example_list)

  full_prompt = first_part + prompt_examples + second_part

  return full_prompt

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def extract_information(full_prompt, will_text, client):
  response = client.chat.completions.create(
    model="gpt-4-1106-preview",
    response_format={
      'type': 'json_object',
    },
    messages=[
      {
        "role": "system",
        "content": full_prompt
      },
      {
        "role": "user",
        "content": will_text
      }
    ],
    temperature=1,
    max_tokens=4096,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
  )
  return response

def main(text_list):

  # prompt the user for their openai api key
  key = input("Please enter your openai api key: ")
  client = OpenAI(api_key=key)

  # open given csv and create a list out of it
  example_csv = "./docs/prompt_examples.csv"
  example_list = []
  with open(example_csv, 'r') as csvfile:
      csvreader = csv.reader(csvfile)
      for row in csvreader:
        example_list.append(row[1])

  full_prompt = create_full_prompt(example_list)

  # extract information from the will texts
  extracted_info = []
  n = 0
  while n < len(text_list):
    print("processing " + str(n+1) + "th sentence!")
    try:
      response = extract_information(full_prompt, text_list[n], client)
      extracted_info.append(response.choices[0].message.content)
      n += 1
    except:
      print("something went wrong while processing " + str(n) + "th text!")
      return extracted_info
  return extracted_info