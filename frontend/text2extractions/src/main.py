import os, json
from pydantic import BaseModel
from typing import List, Dict, Optional
from openai import OpenAI
import argparse
import os
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

full_prompt = """You are given the text of a legal will and testament. Extract information about the will and its components using the structured JSON format provided. Each field is mandatory, and the output should be structured precisely according to the schema. When extracting information, keep the original texts for the ease of retrieving provenance whenever possible. When there's no good information to be extracted, return None value.

### Requirements:
1. **Testator’s name**: The name of the person who wrote and signed the will.
2. **Date of Will**: The date the will was created.
3. **Entities**: Include unique IDs (`e1`, `e2`, etc.) for the following entities. If an entity's role and name are identical, assign only one ID and ensure it is not repeated. (See Note1 and Note2 below in the example given):
   - **Testator**: The person who wrote and signed the will
   - **Executor**: The individual appointed to execute the will's instructions 
   - **Assets**: Items or properties owned by the testator.
   - **Beneficiaries**: Individuals or entities designated to receive assets or properties.
   - **Conditions**: Extract all conditions relevant to the bequest event. Key conditions to extract include:
    1. Asset Division: Specify how assets are to be distributed, such as terms like `per stirpes`, `equally`, or specific proportions (e.g., `5%`, `one half`). Avoid referencing the assets themselves; focus exclusively on the proportions and distribution terms. For instance, if the text states five (5) percent of my net estate, include five (5) percent under Conditions and categorize my net estate under Assets (See Note3, Note4, Note5 below in the example given).
    2. Contingency Provisions: Capture if-then scenarios, such as `if a beneficiary is deceased, their share is allocated to another person`.
    3. Age-Related Provisions: Identify conditions tied to a beneficiary's age, such as `if a beneficiary is a minor, a guardian/trustee will be appointed`.
    4. Additional Clauses: Note any other stipulations affecting the distribution or management of assets.
4. **Events**: Include unique IDs (`v1`, `v2`, etc.) for the following events:
   - **Bequests**: Events in which a testator bequeaths his/her assets to beneficiaries. Testator, Assets, and Beneficiaries are REQUIRED at all times.
5. Use IDs to maintain clarity. Each entity should be assigned a unique ID (e.g., `e1`, `e2`) and referenced in events using these IDs.

Here's an example:

# Will text: Last Will and Testament of [Person-1] I, [Person-1], do make, publish and declare this to be my Last Will and Testament, hereby revoking all wills and codicils heretofore made by me. I. BEQUEST OF TANGIBLE PERSONAL PROPERTY I bequeath to my wife, [Person-2], in fee, all clothing, household goods, personal effects, and all other tangible personal property, not otherwise specifically bequeathed, owned by me at the time of my death. II. DEVISES I hereby devise my farm located in Ripley, Tennessee, consisting of approximately 58-60 acres, to my wife, [Person-2], in fee, if she should be living at the time of my death. If my wife should not be living at my death, then in such event, I devise my said farm to my daughter, [Person-3]. It is my hope and desire that this property remain in my family and not be sold. III. SPECIFIC BEQUEST I hereby will and bequeath five (5) percent of my net estate to [Organization-1] at Arp, Tennessee. IV. RESIDUARY ESTATE All the rest, residue and remainder of the property which I may own at the time of my death, real, personal, and mixed, tangible and intangible, of whatsoever nature and wheresoever situated, including all property which I may acquire or become entitled to after the execution of this will, including all lapsed legacies and devises, and all life insurance payable to my estate, bequeath and devise in fee to my wife, [Person-2]. If my said wife, [Person-2], should not survive me, then I bequeath and devise the remainder of said property in my estate in fee and in equal shares to my two daughters, [Person-3] and [Person-4]. If either of my said daughters should not be living at my death, then and in such event I bequeath and devise the interest which my deceased daughter would have received, per stirpes, and in fee, unto her issue who shall be living at my death. V. APPOINTMENT OF EXECUTOR I appoint my wife, [Person-2], as the Executrix of this my Last Will and Testament. (All references to Executor apply equally to Executrix). If and in the event she should fail or cease to serve in said capacity, then I appoint my daughter, [Person-3], to serve as said Executrix of my estate; I direct that no bond nor security be required of either of the above named fiduciaries for the faithful performance of their duties. IN WITNESS WHEREOF, I have hereunto set my hand this 14th day of March, 1990, and do publish and declare this as my Last Will and Testament in the presence of each and all of the subscribing witnesses whom I have requested to act as such by signing their names as attesting witnesses in my presence and in the presence of each other and by signing the Affidavit below pursuant to the provisions of T.C.A. §32-2-110.

# Expected output (`%%` Marks a place where you should focus):
{
    "testator_name": "[Person-1]",
    "date_of_will": "14th day of March, 1990",
    "extractions": {
        "entities": [
            {
                "testator": {
                    "id": "e1",
                    "name": "[Person-1]"
                },
                "executor": [
                    {
                        "id": "e2",
                        "name": "[Person-2]"
                    },
                    {
                        "id": "e3",
                        "name": "[Person-3]"
                    }
                ],
                "beneficiary": [
                    {
                        "id": "e4",
                        "name": "[Person-2]" %% Note1: See that [Person-2] is only extracted once and assigned a single ID, even though it appears multiple times in the will text. Follow this convention when you do the task.
                    },
                    {
                        "id": "e5",
                        "name": "[Person-3]" %% Note2: See that [Person-3] is only extracted once and assigned a single ID, even though it appears multiple times in the will text. Follow this convention when you do the task.
                    },
                    {
                        "id": "e6",
                        "name": "[Organization-1]"
                    },
                    {
                        "id": "e7",
                        "name": "[Person-4]"
                    },
                    {
                        "id": "e8",
                        "name": "[Person-3] or [Person-4]'s issue who shall be living at [Person-1]'s death"
                    },
                ],
                "asset": [
                    {
                        "id": "e9",
                        "description": "all clothing, household goods, personal effects, and all other tangible personal property, not otherwise specifically bequeathed, owned by me at the time of my death"
                    },
                    {
                        "id": "e10",
                        "description": "farm located in Ripley, Tennessee, consisting of approximately 58-60 acres"
                    },
                    {
                        "id": "e11",
                        "description": "[Person-1]'s net estate" %% Note3: net estate is included as an asset.
                    },
                    {
                        "id": "e12",
                        "description": "All the rest, residue and remainder of the property"
                    }
                ],
                "condition": [
                    {
                        "id": "e13",
                        "text": "if [Person-2] should be living at the time of [Person-1]'s death"
                    },
                    {
                        "id": "e14",
                        "text": "If [Person-2] should not be living at [Person-1]'s death"
                    },
                    {
                        "id": "e15",
                        "text": "five (5) percent" %% Note4: See that ONLY `five (5) percent` is marked as a condition here, NOT the entire phrase `five (5) percent of my net estate`.
                    },
                    {
                        "id": "e16",
                        "text": "If [Person-2] should not survive [Person-1]"
                    },
                    {
                        "id": "e17",
                        "text": "in equal shares"
                    },
                    {
                        "id": "e18",
                        "text": "If either of [Person-3] and [Person-4] should not be living at [Person-1]'s death"
                    },
                    {
                        "id": "e19",
                        "text": "per stirpes"
                    }
                ]
            }
        ],
        "events": [
            {
                "id": "v1",
                "type": "Bequest",
                "Testator": "e1",
                "Executor": [
                    "e2"
                ],
                "Beneficiary": [
                    "e4"
                ],
                "Asset": [
                    "e9"
                ],
                "Condition": []
            },
            {
                "id": "v2",
                "type": "Bequest",
                "Testator": "e1",
                "Executor": [
                    "e2"
                ],
                "Beneficiary": [
                    "e4"
                ],
                "Asset": [
                    "e10"
                ],
                "Condition": [
                    "e13"
                ]
            },
            {
                "id": "v3",
                "type": "Bequest",
                "Testator": "e1",
                "Executor": [
                    "e2"
                ],
                "Beneficiary": [
                    "e5"
                ],
                "Asset": [
                    "e10"
                ],
                "Condition": [
                    "e14"
                ]
            },
            {
                "id": "v4", %% Note5: See how this bequest event is constructed; net estate and five (5) percent are included as an asset and a condition here.
                "type": "Bequest",
                "Testator": "e1",
                "Executor": [
                    "e2"
                ],
                "Beneficiary": [
                    "e6"
                ],
                "Asset": [
                    "e11"
                ],
                "Condition": [
                    "e15"
                ]
            },
            {
                "id": "v5",
                "type": "Bequest",
                "Testator": "e1",
                "Executor": [
                    "e2"
                ],
                "Beneficiary": [
                    "e4"
                ],
                "Asset": [
                    "e12"
                ],
                "Condition": []
            },
            {
                "id": "v6",
                "type": "Bequest",
                "Testator": "e1",
                "Executor": [
                    "e2"
                ],
                "Beneficiary": [
                    "e5",
                    "e7"
                ],
                "Asset": [
                    "e12"
                ],
                "Condition": [
                    "e16",
                    "e17"
                ]
            },
            {
                "id": "v7",
                "type": "Bequest",
                "Testator": "e1",
                "Executor": [
                    "e2"
                ],
                "Beneficiary": [
                    "e8"
                ],
                "Asset": [
                    "e12"
                ],
                "Condition": [
                    "e18",
                    "e19"
                ]
            }
        ]
    }
}
"""


class Testator(BaseModel):
    id: str
    name: str


class Executor(BaseModel):
    id: str
    name: str


class Asset(BaseModel):
    id: str
    description: str


class Beneficiary(BaseModel):
    id: str
    name: str


class Condition(BaseModel):
    id: str
    text: str  # Conditions like "If beneficiary predeceases testator, transfer to X" or shares like "50%", "1/6", etc.


class BequestEvent(BaseModel):
    id: str
    type: str  # Should be "Bequest"
    Testator: str
    Executor: List[str]
    Beneficiary: List[str]  # References the ID of a Beneficiary
    Asset: List[str]        # References the ID of an Asset
    Condition: Optional[List[str]] = None  # References the ID of condition relevant to this bequest event


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
    date_of_will: str
    extractions: Extractions


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
    # Argument parsing with short and long flags
    parser = argparse.ArgumentParser(description="Extract data from .txt files and output JSON.")
    parser.add_argument("-i", "--input_dir", required=True, type=str, help="Path to the input directory containing .txt files")
    parser.add_argument("-o", "--output_dir", required=True, type=str, help="Path to the output directory for .json files")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)

    # Fetch the API key from the environment variable
    env_var_key = 'OPENAI_API_KEY'
    api_key = os.getenv(env_var_key)
    if not api_key:
        raise EnvironmentError(f"{env_var_key} not found in environment variables.")
    
    client = OpenAI(api_key=api_key)

    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            input_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + '.json'
            output_path = os.path.join(output_dir, output_filename)

            with open(input_path, 'r', encoding='utf-8') as file:
                target_text = file.read()

            extraction = extract_from_full_doc(prompt, target_text, client)
            export_to_json(extraction, output_path)
            print(f"Extraction completed for {filename}")

if __name__ == "__main__":
    main(full_prompt)
