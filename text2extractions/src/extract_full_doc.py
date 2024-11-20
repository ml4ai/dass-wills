import os, json
from pydantic import BaseModel, validator
from typing import List, Dict, Optional
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

full_prompt = """You are given the text of a legal will and testament. Extract information about the will and its components using the structured JSON format provided. Each field is mandatory, and the output should be structured precisely according to the schema. Keep the original text when extracting for the ease of retrieving the source of the information.

### Requirements:
1. **Testator’s name**: The name of the person who wrote and signed the will.
2. **Date of Will**: The date the will was created.
3. **Entities**: Include unique IDs (`e1`, `e2`, etc.) for the following entities:
   - **Testator**: The person who wrote and signed the will
   - **Executor**: The individual appointed to execute the will's instructions 
   - **Assets**: Items or properties owned by the testator
   - **Beneficiaries**: Individuals or entities designated to receive assets or properties
   - **Conditions**: Conditions or shares relevant to bequest event, such as "If beneficiary predeceases testator, transfer to X" or "50%", "1/6", "equally", "per stirpes", etc.
4. **Events**: Include unique IDs (`v1`, `v2`, etc.) for the following events:
   - **Bequest Events**: Event in which a testator bequeaths his/her assets to beneficiaries. Do not group bequests that include different beneficiaries and assets into one event. Treat them as separate bequest events.
5. Use IDs to maintain clarity. Each entity should be assigned a unique ID (e.g., `e1`, `e2`) and referenced in events using these IDs.
"""


class Testator(BaseModel):
    id: str
    name: str
    state_of_residence: Optional[str] = None
    @validator('state_of_residence', pre=True, always=True)
    def replace_not_specified_with_none(cls, value):
        if value == "Not specified":
            return None
        return value

class Executor(BaseModel):
    id: str
    name: str
    relationship_to_testator: Optional[str] = None
    waived_bond: bool
    @validator('relationship_to_testator', pre=True, always=True)
    def replace_not_specified_with_none(cls, value):
        if value == "Not specified":
            return None
        return value

class Asset(BaseModel):
    id: str
    description: str


class Beneficiary(BaseModel):
    id: str
    name: str
    relationship_to_testator: Optional[str] = None
    @validator('relationship_to_testator', pre=True, always=True)
    def replace_not_specified_with_none(cls, value):
        if value == "Not specified":
            return None
        return value

class Condition(BaseModel):
    id: str
    text: str  # Conditions like "If beneficiary predeceases testator, transfer to X" or shares like "50%", "1/6", etc.

class BequestEvent(BaseModel):
    id: str
    type: str  # Should be "Bequest"
    Testator: str
    Executor: List[str]
    Beneficiary: List[str]  # References the IDs of Beneficiaries
    Asset: List[str]        # References the IDs of Assets
    Condition: Optional[List[str]] = None  # References the IDs of conditions relevant to this bequest event


class Entities(BaseModel):
    testator: Testator
    executor: List[Executor]
    beneficiary: List[Beneficiary]
    asset: List[Asset]
    condition: List[Condition]


class Extractions(BaseModel):
    entities: List[Entities]
    events: List[BequestEvent]


class Will(BaseModel):
    testator_name: str
    date_of_will: Optional[str] = None
    extractions: Extractions
    @validator('date_of_will', pre=True, always=True)
    def replace_not_specified_with_none(cls, value):
        if value == "Not specified":
            return None
        return value


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def extract_from_full_doc(prompt, target_text, client):
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": target_text},
        ],
        response_format=Will,
        temperature=0,
        max_tokens=16384,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    extraction = completion.choices[0].message.parsed
    return extraction


def export_to_json(json_object, file_path):
    with open(file_path, 'w') as json_file:
        json_file.write(json_object.json(indent=4))


def read_and_tokenize(file_path):
    try:
        # Read the content of the file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        # Tokenize the text into sentences
        sentences = sent_tokenize(text)
        return sentences
    except FileNotFoundError:
        print(f"The file '{file_path}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


def main(prompt):
    # The below paths should be adjusted to reflect the actual paths to the inputs and outputs
    input_dir = "/Users/alicekwak/repos/dass-wills/text2extractions/input/full_text_ID"
    output_dir = "/Users/alicekwak/repos/dass-wills/text2extractions/output/full_text_ID"

    os.makedirs(output_dir, exist_ok=True)

    # prompt the user for their api key
    key = input("Please enter your openai api key: ")
    client = OpenAI(api_key=key)

    # Process each .txt file in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            input_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + '.json'
            output_path = os.path.join(output_dir, output_filename)

            # Read and tokenize input file
            with open(input_path, 'r', encoding='utf-8') as file:
                target_text = file.read()

            extraction = extract_from_full_doc(prompt, target_text, client)
            export_to_json(extraction, output_path)
            print(f"Extraction completed for {filename}")


if __name__ == "__main__":
    main(full_prompt)
