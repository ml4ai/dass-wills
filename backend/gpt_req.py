from openai import OpenAI
from pydantic import BaseModel
from collections import Counter

## Defining Output Objects

class RuleID (BaseModel):
    id: int

class Boolean (BaseModel):
    ans: bool

class Division(BaseModel):
    person_name: str
    asset_name: str
    share: float

class RuleOutputDivision(BaseModel):
    division: list[Division]

class AgeRequirement(BaseModel):
    person_name: str
    minimum_age: int

class RuleOutput5(BaseModel):
    division: list[Division]
    unalive_people: list[str]

class RuleOutput11(BaseModel):
    division: list[Division]
    age_reqs: list[AgeRequirement]

class RuleOutputDivision(BaseModel):
    division: list[Division]
    

rules_text_full_response="""Rules abstraction:
        Division: 
            - Per stirpes
            (id = 0)
            requirements:
                - people involved   
                - condition identifier 
                - divisible assets (boolean)
                - alive status of all persons involved in the directives

            - equally
            (id = 1)
            requirements:
                - people involved   
                - condition identifier
                - divisible assets (boolean)

            - by a certain proportion to each person
            (id = 3)
            requirements:
                - people involved   
                - condition identifier
                - proportions
                - divisible assets (boolean)
            return:
            - in this case return ONLY a list of assets, parties, and shares in that directive [('person_x_name', 'asset_x','share'),('person_y_name', 'asset_y','share')].
            There must be a person_name, an asset name and a share (%) per tuple in the returned list.
            example output under attribute 'division': [('person_x_name', 'asset_x','share'),('person_y_name', 'asset_y','share'),('organization-name', 'asset_y','share')]
            Share will always be a float number.

        If-else:
            - if persons (a and or b) is not alive, transfer assets to another party/person
            (id = 5)
            requirements:
                - people involved   
                - condition identifier
                - alive status of persons a and b
            return:
            - in this case return ONLY a list of assets, parties, and shares in that directive [('person_x_name', 'asset_x','share'),('person_x_name', 'asset_y','share')].
            also, return another list of tuples[('person_x_name'),('person_y_name'] for people who are supposed to be not alive for the directive conditions to be execute. 
            example output under attribute 'division': [('person_x_name', 'asset_x','share'),('person_x_name', 'asset_y','share')] 
            for people who are supposed to be not alive under the attribute 'unalive_people': [('person_x_name'),('person_y_name']
            Share will always be a float number.

            - if nobody is alive to bequeath, transfer assets as per state's law (default: transfer to state)
            requirements:
            (id = 6)
                - condition identifier
                - people involved   
                - alive status of all persons involved in the directives
                - state's law
            return:
            in this case return ONLY a list of assets, parties, and shares in that directive [('state_x', 'asset_x','share'),('person_x_name', 'asset_y','share')].
            There must be a person_name, an asset name and a share (%) per tuple in the returned list.
            example output under attribute 'division': [('state_x', 'asset_x','share'),('person_x_name', 'asset_y','share')]
            Share will always be a float number.

        Agre-related Rules:
         - Execute the directive if someone is of appropriate age.
         requirements:
         (id = 11)
            in this case return ONLY a list  of assets, parties, and shares in that directive [('person_x_name', 'asset_x'),('person_x_name', 'asset_y')]
         and also return another tuple people who are supposed to have certain age for the directive conditions to be valid[('person_x_name', 'age >= num1' ),('person_y_name', 'age >= num2') ].
         example output under attribute 'division': [('person_x_name', 'asset_x','share'),('person_y_name', 'asset_y','share')]
        for people who are supposed to be of certain age under attribute 'age_reqs': [('person_x_name', 'age >= num1' ),('person_y_name', 'age >= num2') ] Note that minimum_age attribute is to filled with the number provided in the directive's CONDITION."""


rules_text_id="""Rules abstraction:
        Division: 
            - Allocation Per stirpes
            (id = 0)
            requirements:
                - people involved   
                - condition identifier 
                - divisible assets (boolean)
                - alive status of all persons involved in the directives

            - Equal Allocation
            (id = 1)
            requirements:
                - people involved   
                - condition identifier
                - divisible assets (boolean)

            - Allocating a certain proportion to each person
            (id = 3)
            requirements:
                - people involved   
                - condition identifier
                - proportions
                - divisible assets (boolean)

        If-else:
            - If a person(s) is not alive, transfer assets to another person(s)
            (id = 5)
            requirements:
                - people involved   
                - condition identifier
                - alive status of persons a, b, etc

            - If nobody is alive to bequeath, transfer assets as per state Law
            requirements:
            (id = 6)
                - condition identifier
                - people involved   
                - alive status of all persons involved in the directives
                - state's law

        Agre-related Rules:
         - Execute the directive if someone is of appropriate age.
         (id = 11)
         requirements:
            - people involved 
            - age inequality"""

rule_id_to_text= {
0: "Allocation Per stirpes",
1: "Equal Allocation",
3: "Allocating a certain proportion to each person",
5: "If a person(s) is not alive, transfer assets to another person(s)",
6: "If nobody is alive to bequeath, transfer assets as per state Law",
11: "Execute the directive if someone is of appropriate age."
}

rule_id_to_return_text= {
0: "Allocation Per stirpes",
1: "Equal Allocation",
3: "Allocating a certain proportion to each person. Return: in this case return ONLY a list of assets, parties, and shares in that directive under 'division' attribute [('state_x', 'asset_x','share'),('person_x_name', 'asset_y','share')]. There must be a person_name, an asset name and a share (%) per tuple in the returned list. Example output under attribute 'division': [('state_x', 'asset_x','share'),('person_x_name', 'asset_y','share')] Share will always be a float number.",
5: "If a person(s) is not alive, transfer assets to another person(s). Return: in this case return a list of assets, parties, and shares in that directive under 'division' attribute [('person_x_name', 'asset_x','share'),('person_x_name', 'asset_y','share')]. Also, return another list of tuples[('person_x_name'),('person_y_name'] for people who are supposed to be not alive for the directive conditions to be execute. example output under attribute 'division': [('person_x_name', 'asset_x','share'),('person_x_name', 'asset_y','share')] for people who are supposed to be not alive under the attribute 'unalive_people': [('person_x_name'),('person_y_name'] Share will always be a float number.",
6: "If nobody is alive to bequeath, transfer assets as per state Law. Return: in this case return ONLY a list of assets, parties, and shares in that directive under 'division' attribute [('state_x', 'asset_x','share'),('person_x_name', 'asset_y','share')]. There must be a person_name, an asset name and a share (%) per tuple in the returned list. Example output under attribute 'division': [('state_x', 'asset_x','share'),('person_x_name', 'asset_y','share')] Share will always be a float number.",
11: "Execute the directive if someone is of appropriate age. Return: in this case return a list  of assets, parties, and shares in that directive [('person_x_name', 'asset_x'),('person_x_name', 'asset_y')] and also return another tuple people who are supposed to have certain age for the directive conditions to be valid[('person_x_name', 'age >= num1' ),('person_y_name', 'age >= num2') ]. example output under attribute 'division': [('person_x_name', 'asset_x','share'),('person_y_name', 'asset_y','share')] for people who are supposed to be of certain age under attribute 'age_reqs': [('person_x_name', 'age >= num1' ),('person_y_name', 'age >= num2') ] Note that minimum_age attribute is to filled with the number provided in the directive's CONDITION."
}

llm_directive_indentifier = 'Based on the provided rules, testator, available assets and beneficiaries, evaluate which rule will be applied (i.e., CHECK things like whether the someone is alive, age, etc). Return an id related with the rule. Return ONLY this Output Format: ID. Example output1: ID: 1, Example output2: ID: 2. Directive: {directive_text}. Testaor name: {t}, Testator Assets: {a}, Beneficiaries of Directive: {b}.\n Rules: '+rules_text_id 

llm_directive_return_items = 'Based on the provided rule, testator, available assets and beneficiaries, evaluate the people, assets, and other things requested under the "return" tab. Return the items. Return ONLY the Example Output Format and no other text. Rule: {r}, Directive: {directive_text}. Assets: {a}. Beneficiaries: {b}. Testaor: {t}. Testator children/heir: {children}' 


def fetch_rule( rule_id):
    rule_text = rule_id_to_return_text[rule_id]
    return rule_text


def handle_rule(id,directive_text, assets, testator, beneficiaries,children):
    """Fetch the rule and prepare the LLM directive based on the ID."""
    rule = fetch_rule(id).strip()
    
    llm_directive = llm_directive_return_items.format(
        directive_text=directive_text,
        a=assets, t=testator, b=beneficiaries, r=rule, children=children
    )
    return llm_directive, rule

def process_query_response(id, query_ans):
    """Process the response from the LLM query based on the ID."""
    if id in [3, 6]:
        divisions = []
        for div in query_ans.division:
            tuple_div = (div.person_name,div.asset_name,div.share)
            divisions.append(tuple_div)
        return divisions
    elif id == 5:
        divisions = []
        unalive_people = query_ans.unalive_people
        for div in query_ans.division:
            tuple_div = (div.person_name,div.asset_name,div.share)
            divisions.append(tuple_div)

        return divisions, unalive_people
    elif id == 11:
        divisions = []
        age_reqs = []
        for div in query_ans.division:
            tuple_div = (div.person_name,div.asset_name,div.share)
            divisions.append(tuple_div)
        for div in query_ans.age_reqs:

            tuple_age = (div.person_name,div.minimum_age)
            age_reqs.append(tuple_age)
        return divisions, age_reqs

    return None

def process_format(id):
    format= None
    if id  in [0,1]:
        pass
    elif id in [3,6]:
        format =RuleOutputDivision
    elif id == 5:
        format = RuleOutput5
    elif id == 11:
        format = RuleOutput11

    return format

    
def process_id(id_ans, directive_text, assets, testator, beneficiaries, children,n=5):

    rule_id_text = rule_id_to_text[id_ans]
    for _ in range(n):
        try:
            id = id_ans
            llm_directive, rule = handle_rule(id, directive_text, assets, testator, beneficiaries, children)
            fmt = process_format(id)
            if not fmt:
                return id, [], rule
            query_ans = query_llm_rule(llm_directive, fmt)
            result = process_query_response(id, query_ans)
            return id, result, rule_id_text
        except Exception as e:
            print(f"Error: {e}")
            print("... error querying LLM: trying again.")
    sys.exit(1)

def query_llm(prompt, model="gpt-4o-2024-08-06"):
    client = OpenAI()
    
    response = client.chat.completions.with_raw_response.create(
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        model=model,
        temperature=0.001
    )
    
    request_id = response.headers.get('x-request-id')
    completion = response.parse()
    message_content = completion.choices[0].message.content
    
    return message_content




def query_llm_rule(prompt, response_type=RuleOutputDivision, model="gpt-4o-2024-08-06"):
    client = OpenAI()
    
    response = client.beta.chat.completions.parse(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model=model,
        temperature=0.001,
        response_format=response_type
    )
    
    message_content = response.choices[0].message.parsed
    return message_content

def query_id_multiple_times (prompt, n):
    id_answers = []
    for _ in range(n):
        try:
            query_ans=query_llm_rule(prompt,RuleID)
            id_answers.append(query_ans.id)
        except Exception as e:
            pass
    counts = Counter(id_answers)
    return max(counts, key=counts.get)


def process_rule(directive_text, assets, testator, beneficiaries,children):

    llm_directive_indentifier_with_attributes = llm_directive_indentifier.format(directive_text=directive_text,a=assets,t=testator,b= beneficiaries)
    query_ans=query_id_multiple_times(llm_directive_indentifier_with_attributes,7)
    identifier, evals, rule = process_id(query_ans, directive_text, assets, testator, beneficiaries,children)

    return identifier, evals, rule