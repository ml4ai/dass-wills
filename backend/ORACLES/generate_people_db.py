import json
import random
from datetime import datetime, timedelta

def generate_random_date():
    start_date = datetime(2000, 1, 1)
    end_date = datetime.now()
    return start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
def calculate_age(birth_date):
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return random.randint(0, age)

def add_spouse(member):
    date_of_birth = generate_random_date()

    spouse = {
        "id": len(family_members) + 1,
        "first_name": f"Person-{len(family_members) + 1}",
        "last_name": "",
        "full_name":  f"Person-{len(family_members) + 1}",
        "age": calculate_age(date_of_birth),
        "date_of_birth": date_of_birth.strftime("%Y-%m-%d"),
        "email": "",
        "phone": "",
        "address": "",
        "spouse_id": member["id"],
        "assets": [],
        "children_ids":[]
    }
    family_members.append(spouse)
    member["spouse_id"] = spouse["id"]

def add_children(member):
    num_children = int(input("How many children to add for " + member["full_name"] + "? "))
    for _ in range(num_children):
        date_of_birth = generate_random_date()
        child = {
            "id": len(family_members) + 1,
            "first_name": f"Person-{len(family_members) + 1}",
            "last_name": "",
            "full_name":  f"Person-{len(family_members) + 1}",
            "age": calculate_age(date_of_birth),
            "date_of_birth": date_of_birth.strftime("%Y-%m-%d"),
            "email": "",
            "phone": "",
            "address": "",
            "spouse_id": None,
            "assets": [],
            "children_ids":[]
        }
        family_members.append(child)
        member.setdefault("children_ids", []).append(child["id"])

def add_grandchildren(member):
    
    num_grandchildren = int(input("How many grandchildren to add for " + member["full_name"] + "? "))
    for _ in range(num_grandchildren):
        date_of_birth = generate_random_date()
        grandchild = {
            "id": len(family_members) + 1,
            "first_name": f"Person-{len(family_members) + 1}",
            "last_name": "",
            "full_name":  f"Person-{len(family_members) + 1}",
            "age": calculate_age(date_of_birth),
            "date_of_birth": date_of_birth.strftime("%Y-%m-%d"),
            "email": "",
            "phone": "",
            "address": "",
            "spouse_id": None,
            "assets": [],
            "children_ids":[]
        }
        family_members.append(grandchild)

def add_assets(member):
    
    num_assets = int(input("How many assets to add for " + member["full_name"] + "? "))
    for _ in range(num_assets):
        asset = {
            "name": input("Asset name: "),
            "type": input("Asset type: "),
        }
        if asset["type"] == "House":
            asset["address"] = input("Asset address: ")
        elif asset["type"] == "Car":
            asset["brand"] = input("Car brand: ")
            asset["model"] = input("Car model: ")
            asset["year"] = int(input("Car year: "))
        elif asset["type"] == "Land":
            asset["location"] = input("Land location: ")
            asset["size"] = input("Land size: ")

        member.setdefault("assets", []).append(asset)

def generate_family_tree():
    global family_members
    family_members = []
    num_family_members = int(input("How many family members? "))

    for _ in range(num_family_members):
        date_of_birth = generate_random_date()
        member = {
            "id": len(family_members) + 1,
            "first_name": f"Person-{len(family_members) + 1}",
            "last_name": "",
            "full_name":  f"Person-{len(family_members) + 1}",
            "age": calculate_age(date_of_birth),
            "date_of_birth": date_of_birth.strftime("%Y-%m-%d"),
            "email": "",
            "phone": "",
            "address": "",
            "spouse_id": None,
            "assets": [],
            "children_ids":[]
        }
        family_members.append(member)

        add_spouse_option = input("Do you want to add spouse for " + member["full_name"] + "? (yes/no): ").lower()
        if add_spouse_option == "yes":
            add_spouse(member)

        add_children_option = input("Do you want to add children for " + member["full_name"] + "? (yes/no): ").lower()
        if add_children_option == "yes":
            add_children(member)

        add_assets_option = input("Do you want to add assets for " + member["full_name"] + "? (yes/no): ").lower()
        if add_assets_option == "yes":
            add_assets(member)

        add_grandchildren_option = input("Do you want to add grandchildren for " + member["full_name"] + "? (yes/no): ").lower()
        if add_grandchildren_option == "yes":
            add_grandchildren(member)

    return {"family_members": family_members}

def main():
    family_tree = generate_family_tree()
    with open('family_tree.json', 'w') as outfile:
        json.dump(family_tree, outfile, indent=4)

if __name__ == "__main__":
    main()
