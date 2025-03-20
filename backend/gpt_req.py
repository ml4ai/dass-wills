from openai import OpenAI

rules_text_backup="""Rules abstraction:
        Division: 
            - Per stirpes
            (id = 0)
            requirements:
                - people involved   
                - condition identifier 
                - divisible assets (boolean)
                - alive status of all persons involved in the directives
            return:
            - in this case return a list of children named in that directive [('person_x_name','person_y_name')]
            example output: [('person_x_name', 'person_y_name)]

            - equally
            (id = 1)
            requirements:
                - people involved   
                - condition identifier
                - divisible assets (boolean)
            return:
            - in this case return ONLY a list of  peoples in that directive [('person_x_name', 'person_y_name)]
            example output: [('person_x_name', 'person_y_name)]
            
            - equally (minus people who are not alive)
            (id = 2)
            requirements:
                - people involved   
                - condition identifier
                - divisible assets (boolean)
                - alive status of all persons involved in the directives
            return:
            - in this case return ONLY a list of  peoples in that directive [('person_x_name', 'person_y_name)] 
            return another list of tuples [('person_z_name'),('person_a_name'] for people who are supposed to be not alive for the directive conditions to be execute. 
            There must be a person_name in the returned list. 
            example output: [('person_x_name', 'person_y_name)] | [('person_z_name'),('person_a_name'] 

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
            example output: [('person_x_name', 'asset_x','share'),('person_y_name', 'asset_y','share'),('organization-name', 'asset_y','share')]
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
            example output: [('person_x_name', 'asset_x','share'),('person_x_name', 'asset_y','share')] | [('person_x_name'),('person_y_name']
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
            example output: [('state_x', 'asset_x','share'),('person_x_name', 'asset_y','share')]
            Share will always be a float number.

        Bequeath whatever's left:
            - give all assets to multiple people. This assumes that the division is equal per asset.
            (id = 7)
            requirements:
                - people involved   
                - condition identifier
                - state of all assets of testator
                - alive status of all persons involved in the directives
            return:
            In this case return ONLY a list of assets, parties, and shares in that directive [('person_x_name', 'asset_x'),('person_y_name', 'asset_y')]. 
            There must be a person_name and an asset name  per tuple in the returned list.
            example output: [('person_x_name', 'person_y_name)]


        Agre-related Rules:
         - Execute the directive if someone is of appropriate age.
         (id = 11)
            in this case return ONLY a list  of assets, parties, and shares in that directive [('person_x_name', 'asset_x'),('person_x_name', 'asset_y')]
        and also return another tuple people who are supposed to have certain age for the directive conditions to be valid[('person_x_name', 'age >= num1' ),('person_y_name', 'age >= num2') ].
         example output: [('person_x_name', 'asset_x','share'),('person_y_name', 'asset_y','share')] | [('person_x_name', 'age >= num1' ),('person_y_name', 'age >= num2') ]

    """

rules_text_2="""Rules abstraction:
        Division: 
            - Per stirpes
            (id = 0)
            requirements:
                - people involved   
                - condition identifier 
                - divisible assets (boolean)
                - alive status of all persons involved in the directives
            return:
            - in this case return a list of children named in that directive [('person_x_name','person_y_name')]
            example output: [('person_x_name', 'person_y_name)]

            - equally
            (id = 1)
            requirements:
                - people involved   
                - condition identifier
                - divisible assets (boolean)
            return:
            - in this case return ONLY a list of  peoples in that directive [('person_x_name', 'person_y_name)]
            example output: [('person_x_name', 'person_y_name)]

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
            example output: [('person_x_name', 'asset_x','share'),('person_y_name', 'asset_y','share'),('organization-name', 'asset_y','share')]
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
            example output: [('person_x_name', 'asset_x','share'),('person_x_name', 'asset_y','share')] | [('person_x_name'),('person_y_name']
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
            example output: [('state_x', 'asset_x','share'),('person_x_name', 'asset_y','share')]
            Share will always be a float number.

        Agre-related Rules:
         - Execute the directive if someone is of appropriate age.
         (id = 11)
            in this case return ONLY a list  of assets, parties, and shares in that directive [('person_x_name', 'asset_x'),('person_x_name', 'asset_y')]
        and also return another tuple people who are supposed to have certain age for the directive conditions to be valid[('person_x_name', 'age >= num1' ),('person_y_name', 'age >= num2') ].
         example output: [('person_x_name', 'asset_x','share'),('person_y_name', 'asset_y','share')] | [('person_x_name', 'age >= num1' ),('person_y_name', 'age >= num2') ]

    """

llm_directive_indentifier = 'Based on the provided rules, testator, available assets and beneficiaries, evaluate which rule will be applied (i.e., CHECK things like whether the someone is alive, age, etc). Return an id related with the rule. Return ONLY this Output Format: ID_NUMBER. Example output1: 1, Example output1: 2. Directive: {directive_text}. Assets: {a}. Beneficiaries: {b}. Testaor: {t}. Rules: '+rules_text_2 

llm_directive_indentifier_return_items = 'Based on the provided rule, testator, available assets and beneficiaries, evaluate the people, assets, and other things requested under the "return" tab. Return the items. Return ONLY the Example Output Format and no other text. Rule: {r}, Directive: {directive_text}. Assets: {a}. Beneficiaries: {b}. Testaor: {t}. Testator children/heir: {children}' 

def fetch_rule (rules, id):
    split_rules = rules.split(f'id = {id}')
    part1 = '\n'.join(split_rules[0].split('\n')[-2:])
    part2 = '\n'.join(split_rules[1].split('id =')[0].split('\n')[:-3])

    return part1 + part2

def fetch_rule(rules, rule_id):
    try:
        rule_sections = rules.split(f'id = {rule_id}')
        if len(rule_sections) < 2:
            raise ValueError(f"Rule with id = {rule_id} not found.")
        before_rule = '\n'.join(rule_sections[0].splitlines()[-2:])
        after_rule = '\n'.join(rule_sections[1].split('id =')[0].splitlines()[:-3])
        return before_rule + '\n' + after_rule
    except Exception as e:
        print(f"Error fetching rule for id = {rule_id}: {e}")
        return None


def handle_rule(id,directive_text, assets, testator, beneficiaries,children):
    """Fetch the rule and prepare the LLM directive based on the ID."""
    rule = fetch_rule(rules_text_2, id)
    llm_directive = llm_directive_indentifier_return_items.format(
        directive_text=directive_text,
        a=assets, t=testator, b=beneficiaries, r=rule, children=children
    )
    return llm_directive, rule

def process_query_response(id, query_ans):
    """Process the response from the LLM query based on the ID."""
    if id in [2, 5, 11]:
        l1, l2 = query_ans.split('|')
        return [eval(l1), eval(l2)]
    else:
        return eval(query_ans)


def process_id(string_answer,directive_text, assets, testator, beneficiaries,children):
    id = None
    iters = 0
    while not id:
        iters+=1
        try:
            id = int(string_answer)
            # Prepare and send the LLM query
            llm_directive, rule = handle_rule(id,directive_text, assets, testator, beneficiaries,children)
            query_ans = query_llm(llm_directive)
            result = process_query_response(id, query_ans)
            return id, result, rule
        except Exception as e:
            print(f"Error: {e}")
            print(string_answer )
            print("... error querying LLM: trying again.")
            if iters==10:
                sys.exit(1)
    return id, [], rule

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


def process_rule(directive_text, assets, testator, beneficiaries,children):

    llm_directive_indentifier_with_attributes = llm_directive_indentifier.format(directive_text=directive_text,a=assets,t=testator,b= beneficiaries)
    query_ans=query_llm(llm_directive_indentifier_with_attributes)
    identifier, evals, rule = process_id(query_ans, directive_text, assets, testator, beneficiaries,children)

    return identifier, evals, rule