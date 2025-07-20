import os, json, re
from pydantic import BaseModel
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


class AssetDistribution(BaseModel):
    beneficiaries: Dict[str, float]  # e.g., {"Person-2": 1.0}
    rules_id: List[int]              # e.g., [5, 1]
    rules_applied_text: List[str]    # e.g., ["If person(s) not alive...", "Equal Allocation"]


class WillSummary(BaseModel):
    __root__: Dict[str, AssetDistribution]  # key = asset name (e.g., "My House")

    class Config:
        schema_extra = {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "beneficiaries": {
                        "type": "object",
                        "additionalProperties": {"type": "number"}
                    },
                    "rules_id": {
                        "type": "array",
                        "items": {"type": "integer"}
                    },
                    "rules_applied_text": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["beneficiaries", "rules_id", "rules_applied_text"]
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


def export_to_json(json_object, file_path):
    with open(file_path, 'w') as json_file:
        json_file.write(json_object.json(indent=4))


def read_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Could not read file {filepath}: {e}")
        return ""


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

    return WillSummary.parse_raw(selected)


def main(prompt, target_text):
    # The below paths should be adjusted to reflect the actual paths to the inputs, oracles, and outputs
    input_dir = "../input"
    oracle_dir = "../people_db.json"
    sample_will_dir = "../dass-wills/baseline/resources/sample_will.txt"
    example_oracle_dir = "../dass-wills/baseline/resources/example_oracle.json"
    expected_output_dir = "../example_expected_output.json"
    output_dir = "../output"

    os.makedirs(output_dir, exist_ok=True)

    # Load supporting files
    sample_will = read_file(sample_will_dir)
    example_oracle = read_file(example_oracle_dir)
    expected_output = read_file(expected_output_dir)
    example_oracle_clean = json.dumps(example_oracle, indent=2).replace("{", "{{").replace("}", "}}")
    expected_output_clean = json.dumps(expected_output, indent=2).replace("{", "{{").replace("}", "}}")
    oracle = read_file(oracle_dir)
    oracle_clean = json.dumps(oracle, indent=2).replace("{", "{{").replace("}", "}}")

    # Fetch the API key from the environment variable
    key = 'OPEN_AI_KEY'
    client = OpenAI(api_key=key)

    # Process each .txt file in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            input_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + '.json'
            output_path = os.path.join(output_dir, output_filename)

            # Read and tokenize input file
            with open(input_path, 'r', encoding='utf-8') as file:
                will_text = file.read()

            prompt = prompt.format(
                sample_will=sample_will,
                example_oracle=oracle_clean,
                expected_output=expected_output_clean,
            )

            target_text = target_text.format(
                will_text=will_text,
                oracle=oracle_clean,
            )

            # without self-consistency
            # extraction = summary_generation(prompt, target_text, client)

            # with self-consistency
            most_common = self_consistent_summary(prompt, target_text, client)
            export_to_json(most_common, output_path)
            print(f"Summary generation completed for {filename}")


if __name__ == "__main__":
    main(step_by_step_prompt, target_input)
