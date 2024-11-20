import json
import sys
import os
from datetime import datetime

def load_json_obj(path):
    if os.path.exists(path):
        with open(path, 'r') as file:
            return json.load(file)
    return {"people": []}  

def save_json_obj(path, data):
    with open(path, 'w') as file:
        json.dump(data, file, indent=4)

def create_person_entry(full_name, age, assets, spouse, alive_status, json_data):
    names = full_name.split()
    first_name = names[0]
    last_name = " ".join(names[1:]) if len(names) > 1 else ""

    existing_person = None
    for person in json_data["people"]:
        if person["full_name"] == full_name:
            existing_person = person
            break

    if existing_person:
        new_id = existing_person["id"]
        print(f"Replacing existing person with ID {new_id}")
        json_data["people"].remove(existing_person)
    else:
        new_id = len(json_data["people"]) + 1
        print(f"Adding new person with ID {new_id}")

    new_person = {
        "id": new_id,
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "age": age,
        "date_of_birth": str(datetime.now().year - int(age)) + "-01-01",  
        "email": "",
        "phone": "",
        "address": "",
        "spouse_id": None,  
        "alive": alive_status,  
        "assets": [],
        "children_ids": []
    }

    # Add the assets
    for asset in assets:
        if ',' in asset:
            name, asset_type = asset.split(',', 1)  
            new_person["assets"].append({"name": name.strip(), "type": asset_type.strip()})
        else:
            print(f"Invalid asset format: {asset}. Expected format: 'name,type'")

    if spouse:
        for person in json_data["people"]:
            if person['full_name'] == spouse:
                new_person["spouse_id"] = person["id"]
                person["spouse_id"] = new_id 

    return new_person

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python add_person.py <json_file> <full_name> <age> <assets (comma-separated)> <alive_status (true/false)> <spouse_name (optional)>")
        sys.exit(1)

    json_file = sys.argv[1]
    full_name = sys.argv[2]
    age = sys.argv[3]
    assets_input = sys.argv[4]
    alive_status = sys.argv[5].lower() 
    spouse_name = sys.argv[6] if len(sys.argv) > 6 else None

    if alive_status not in ["true", "false"]:
        print("Invalid alive status. Use 'true' or 'false'.")
        sys.exit(1)

    json_data = load_json_obj(json_file)

    assets = [asset.strip() for asset in assets_input.split(';')]

    new_person = create_person_entry(full_name, age, assets, spouse_name, alive_status, json_data)

    json_data["people"].append(new_person)
    save_json_obj(json_file, json_data)

    print(f"Added or replaced person: {full_name} with ID {new_person['id']}")
