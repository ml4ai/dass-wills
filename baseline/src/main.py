import os, json, re
import tiktoken
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Optional
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff
from collections import Counter


# Various prompts
basic_prompt = """
You are given a will. Your task is to extract a structured summary of the distribution of assets. For each asset, provide the following information:

- The name(s) of the beneficiary or beneficiaries
- The percentage share (between 0 and 1) allocated to each beneficiary
- The reasoning behind each extraction or inference

For the reasoning, include both a human-readable explanation (`rules_applied_text`) and the associated rule number(s) (`rules_id`).

** Inheritance Logic Rules:
0: "Allocation Per stirpes"
1: "Equal Allocation"
3: "Allocating a certain proportion to each person"
5: "If a person(s) is not alive, transfer assets to another person(s)"
6: "If nobody is alive to bequeath, transfer assets as per state law"
11: "Execute the directive if someone is of appropriate age."

You will also be provided with an oracle, which is a structured reference containing background information relevant to the will. The oracle includes:

- A list of individuals (e.g., family members, named persons), with metadata such as whether they are alive at the time of the testator's death
- A list of assets associated with the testator

Note that the oracle does not explicitly label who the testator or beneficiaries are. You must infer this by comparing names mentioned in the will to the entries in the oracle. Use this oracle to verify and support details such as survivorship status, relationships, and the existence of specific assets.

** Additional Instructions:
- If a percentage is not explicitly stated, infer it only if clearly implied by the text.
- If any part of the document is ambiguous or unclear, do not guess. Simply return "unclear" for that field.
- Follow the format and level of detail shown in the example provided below.
- Do not include any additional explanation or reasoning beyond the fields "rules_id" and "rules_applied_text".

** Example:
- Will text: {sample_will}

- Oracle: 
{example_oracle}

- Expected output:
{expected_output}
"""

concise_prompt = """
Your task is to extract a structured summary of the distribution of assets from a will. For each asset, list the beneficiary names, their share of inheritance, and the reasoning behind each extraction or inference. Only infer shares if clearly implied. If any detail is ambiguous or unclear, return “unclear” for that field. See the example below for expected content and format. In the reasoning, include which inheritance logic rules apply by listing both the explanation (`rules_applied_text`) and the rule number(s) (`rules_id`). The rules are:

0: "Allocation Per stirpes"
1: "Equal Allocation"
3: "Allocating a certain proportion to each person"
5: "If a person(s) is not alive, transfer assets to another person(s)"
6: "If nobody is alive to bequeath, transfer assets as per state law"
11: "Execute the directive if someone is of appropriate age."

You will also be provided with an oracle – a structured reference listing individuals (with details such as whether they are alive at the time of the testator’s death) and the testator’s assets. The oracle does not explicitly identify the testator or beneficiaries; you must infer this by matching names from the will to entries in the oracle. Use the oracle to support inferences about survivorship, relationships, and asset ownership.

See the example below for expected content and format.

** Example:
- Will text: {sample_will}

- Oracle: 
{example_oracle}

- Expected output:
{expected_output}
"""


step_by_step_prompt = """

1. Read the provided will carefully to understand the distribution of assets.
2. Identify all beneficiaries and assets mentioned in the document. Determine which individuals are entitled to which assets.
3. For each asset, extract the following information:
- The name(s) of the beneficiary or beneficiaries
- The percentage share (between 0 and 1) allocated to each beneficiary
- The specific assets they are entitled to
- The reasoning behind each extraction or inference
4. Use the provided oracle to support your analysis. It lists individuals (with metadata such as whether they are alive at the time of the testator’s death) and the testator’s assets. The oracle does not explicitly label the testator or beneficiaries – identify them by matching names from the will to oracle entries. Use this information to verify survivorship, relationships, and asset ownership.
5. In the reasoning, specify which inheritance rules apply. Include:
- A brief explanation (`rules_applied_text`)
- The corresponding rule number(s) (`rules_id`)
6. If the share is not explicitly stated, infer it only if clearly implied in the language of the will.
7. If any information is ambiguous or unclear, do not make assumptions. Instead, return “unclear” for that field.
8. Format your output according to the example provided, matching both structure and level of detail.

** Inheritance Rules:
0: "Allocation Per stirpes"
1: "Equal Allocation"
3: "Allocating a certain proportion to each person"
5: "If a person(s) is not alive, transfer assets to another person(s)"
6: "If nobody is alive to bequeath, transfer assets as per state law"
11: "Execute the directive if someone is of appropriate age."

** Example:
- Will text: {sample_will}

- Oracle: 
{example_oracle}

- Expected output:
{expected_output}
"""


target_input = """
- Will text: {will_text}

- Oracle: 
{oracle}
"""


class BeneficiaryDetail(BaseModel):
    share: float
    rules_applied_text: List[str]
    rules_id: List[int]


class AssetDistribution(BaseModel):
    beneficiaries: Dict[str, BeneficiaryDetail]


class WillSummary(BaseModel):
    __root__: Dict[str, AssetDistribution]

    class Config:
        schema_extra = {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "beneficiaries": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "share": {"type": "number"},
                                "rules_applied_text": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "rules_id": {
                                    "type": "array",
                                    "items": {"type": "integer"}
                                }
                            },
                            "required": ["share", "rules_applied_text", "rules_id"]
                        }
                    }
                },
                "required": ["beneficiaries"]
            }
        }


def extract_json_block(text: str) -> str:
    # Remove Markdown backticks or wrap blocks
    code_block_match = re.search(r"```json(.*?)```", text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()
    return text.strip()


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def summary_generation(prompt, target_text, client):
    completion = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": target_text},
        ],
        temperature=0.7,
        max_tokens=16384,
        top_p=0.9,
        frequency_penalty=0,
        presence_penalty=0
    )
    output_text = completion.choices[0].message.content
    json_str = extract_json_block(output_text)
    return json_str


def export_to_json(json_object, output_path):
    with open(output_path, "w") as json_file:
        if json_object is None:
            print("Warning: json_object is None. Saving empty JSON.")
            json_file.write("{}")
        else:
            json_file.write(json_object.json(indent=4))


def read_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Could not read file {filepath}: {e}")
        return ""


def sanitize_shares(will_json):
    for asset_name, asset in will_json.items():
        beneficiaries = asset.get("beneficiaries", {})
        if not isinstance(beneficiaries, dict):
            print(f"Fixing non-dict beneficiaries for asset: {asset_name} -> {beneficiaries}")
            asset["beneficiaries"] = {}
            continue
        for ben_name, ben in beneficiaries.items():
            share = ben.get("share")
            try:
                ben["share"] = float(share)
            except (TypeError, ValueError):
                print(f"Skipping non-numeric share value: {share} (asset: {asset_name}, beneficiary: {ben_name})")
                ben["share"] = None  # or 0.0
    return will_json


def self_consistent_summary(prompt, target_text, client, iterations=10, tie_breaking='first'):
    outputs = [summary_generation(prompt, target_text, client) for _ in range(iterations)]
    count = Counter(outputs)
    most_common = count.most_common()

    max_count = most_common[0][1]
    top_candidates = [s for s, c in most_common if c == max_count]

    # Choose from candidates
    if len(top_candidates) == 1:
        selected = top_candidates[0]
    elif tie_breaking == 'first':
        selected = next(output for output in outputs if output in top_candidates)
    elif tie_breaking == 'longest':
        selected = max(top_candidates, key=len)
    elif tie_breaking == 'shortest':
        selected = min(top_candidates, key=len)
    else:
        raise ValueError(f"Unknown tie_breaking strategy: {tie_breaking}")

    try:
        parsed = json.loads(selected)
        parsed = sanitize_shares(parsed)
        return WillSummary.parse_obj(parsed)

    except (json.JSONDecodeError, ValueError, ValidationError) as e:
        print(f"Warning: Failed to parse WillSummary: {e}")
        return None

def count_tokens(text, model="gpt-4o"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def main(prompt, target_text):
    base_dir = "/Users/alicekwak/repos/dass-wills/baseline"
    input_root = os.path.join(base_dir, "test")
    sample_will_path = os.path.join(base_dir, "resources/sample_will.txt")
    example_oracle_path = os.path.join(base_dir, "resources/example_oracle.json")
    expected_output_path = os.path.join(base_dir, "resources/example_expected_output.json")

    # Load static files
    sample_will = read_file(sample_will_path)
    example_oracle = read_file(example_oracle_path)
    expected_output = read_file(expected_output_path)
    example_oracle_clean = json.dumps(example_oracle, indent=2).replace("{", "{{").replace("}", "}}")
    expected_output_clean = json.dumps(expected_output, indent=2).replace("{", "{{").replace("}", "}}")

    # Fetch the API key from the environment variable
    key = 'API key'
    client = OpenAI(api_key=key)

    # Process each subdirectory in input_root
    for subdir in os.listdir(input_root):
        subdir_path = os.path.join(input_root, subdir)
        print(subdir_path)
        if not os.path.isdir(subdir_path):
            continue

        will_path = os.path.join(subdir_path, "will.txt")
        oracle_path = os.path.join(subdir_path, "concise_people_db.json")
        output_path = os.path.join(subdir_path, "concise_oracle_revised_baseline.json")

        # Ensure required files exist
        if not (os.path.exists(will_path) and os.path.exists(oracle_path)):
            print(f"Skipping {subdir}: missing will.txt or people_db.json")
            continue

        # Read input files
        with open(will_path, 'r', encoding='utf-8') as f:
            will_text = f.read()

        with open(oracle_path, 'r', encoding='utf-8') as f:
            oracle = json.load(f)
        oracle_clean = json.dumps(oracle, indent=2).replace("{", "{{").replace("}", "}}")

        # Format prompt and target
        prompt_formatted = prompt.format(
            sample_will=sample_will,
            example_oracle=example_oracle_clean,
            expected_output=expected_output_clean,
        )

        target_text_formatted = target_text.format(
            will_text=will_text,
            oracle=oracle_clean,
        )

        word_count = len(target_text_formatted.split())
        token_count = count_tokens(target_text_formatted, model="gpt-4o")
        print(f"Word count: {word_count}")
        print(f"Token count: {token_count}")

        # Run model inference
        # most_common = self_consistent_summary(prompt_formatted, target_text_formatted, client)

        # Save output
        # export_to_json(most_common, output_path)
        # print(f"Saved output for {subdir} at {output_path}")


if __name__ == "__main__":
    main(basic_prompt, target_input)
