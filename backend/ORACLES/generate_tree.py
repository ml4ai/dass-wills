import os, sys, json
import pprint
import copy

def resolve_children (db, person,generation=0):
    if 'children' not in person:
        person['children']=[]
    if len(person['children_ids'])==0: 
        return
    for member in db['people']:
        if  member['id'] in person['children_ids']:
            copied_member = copy.deepcopy(member)
            generational_relation=['grand']*generation
            generational_relation.append('child')
            generational_relation='-'.join(generational_relation)
            copied_member['relation-with-testaor']=generational_relation
            person['children'].append(copied_member)
            resolve_children(db,copied_member, generation+1)

        
def generate_tree(db, person):
    testator=None
    for member in db['people']:
        if member['full_name']==person:
            testator = member
            break
    assert(testator!=None)
    if testator['spouse_id']!=None:
        for member in db['people']:
            if member['id']==testator['spouse_id']:
                testator['spouse']=member
    testator['children']=[]
    if len(testator['children_ids'])!=0:
        resolve_children(db,testator)
    return testator_tree


def main():
    family_db = None
    with open(sys.argv[1], 'r') as outfile:
        family_db= json.load( outfile)
    testator=sys.argv[2]
    pprint.pprint(generate_tree(family_db, testator))



if __name__ == "__main__":
    main()
