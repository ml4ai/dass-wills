from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

def create_cr_prompt(current_extraction, prev_extractions):
    prompt = """%Instruction: Please carefully read the following passages. For each passage, you must identify which entity set, if any, the given entity set refers to. An entity set consists of a unique identifier ('id'), a type, and specific text references within the passage. If the given entity set does not correspond to any antecedent entity set, please select "no antecedent." When determining the antecedent, only consider the entity sets that refer to the exact same real-world entity as the co-referring sets. If one entity set includes another entity set, regard the two entity sets as not referring to the same real world entity (as the former entity set is larger than the latter entity set).

%Note about the special tokens: Please note that any words that contain square brackets ("[" and "]") are special tokens used for anonymization. For example, [Person-1] and [Address-1] are special tokens representing a person's name and address. If the number within the token differs, it means that the tokens represent different entities. For example, [Person-1] and [Person-2] are special tokens representing two different persons.

%Output format: You should only produce a number (e.g., 0, 1, 2, etc.) as an output. If the given entity does not have any antecedant, do not say "no antecedant" but choose among the choices and output the correct choice number (e.g., 3, if 3 is the choice that states "no antecedant")

%Taxonomy:

- Beneficiary: a person or entity (e.g., organization) that receives something from a will
- Executor: a person who executes a will (=personal representative)
- Will: a legal document containing a person’s wishes regarding the disposal of one’s asset after death
- Asset: any money, personal property, or real estate owned by a testator\n\n"""
    prompt += "%Context: \n\n" + prev_extractions["full_text"] + "\n\n"
    prompt += "%Given Entity Set: " + str(current_extraction) + "\n\n"
    prompt += "%Choices:\n\n"
    no_coreference_resolution = ["Testator", "Condition", "Time"]
    entity_extractions = prev_extractions["extractions"]["entities"]
    choices = []
    for entity in entity_extractions:
        if entity['type'] == current_extraction['type'] and entity['type'] not in no_coreference_resolution:
            choices.append(entity)
    if len(choices) > 0:
        n = 0
        while n < len(choices):
            prompt += str(n+1) + ". " + str(choices[n]) + "\n\n"
            n += 1
        prompt += str(len(choices)+1) + ". no antecedent\n\n%Question: What does the given entity set refers to? Just give me the number ONLY and NEVER return anything else."
    return choices, prompt


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def coreference_resolution(prompt, client):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=4096,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].message.content


def main(current_extraction, prev_extractions, client):
    choices, prompt = create_cr_prompt(current_extraction, prev_extractions)
    if prompt:
        response = coreference_resolution(prompt, client)
        if response and int(response) < len(choices):
            resolved = choices[int(response)]
            return resolved
