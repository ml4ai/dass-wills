import json


def get_person_details():
    """Collects information for a single person."""
    person = {
        "id": int(input("Enter ID: ")),
        "first_name": input("Enter first name: "),
        "last_name": input("Enter last name (leave blank if not applicable): "),
        "full_name": input("Enter full name: "),
        "age": int(input("Enter age: ")),
        "date_of_birth": input("Enter date of birth (YYYY-MM-DD): "),
        "email": input("Enter email (leave blank if not applicable): "),
        "phone": input("Enter phone number (leave blank if not applicable): "),
        "address": input("Enter address (leave blank if not applicable): "),
        "spouse_id": input("Enter spouse ID (leave blank if not applicable): "),
        "alive": input("Is the person alive? (true/false): ").lower(),
        "assets": get_assets(),
        "children_ids": get_children_ids()
    }
    # Convert empty spouse_id to None
    if person["spouse_id"] == "":
        person["spouse_id"] = None
    else:
        person["spouse_id"] = int(person["spouse_id"])

    return person


def get_assets():
    """Collects information about a person's assets."""
    assets = []
    add_asset = input("Does the person have any assets? (yes/no): ").lower()
    while add_asset == "yes":
        asset = {
            "name": input("Enter asset name: "),
            "type": input("Enter asset type (e.g., Property, Vehicle, Financial): ")
        }
        location = input("Enter asset location (leave blank if not applicable): ")
        if location:
            asset["Location"] = location
        assets.append(asset)
        add_asset = input("Add another asset? (yes/no): ").lower()
    return assets


def get_children_ids():
    """Collects IDs of children for a person."""
    children_ids = []
    add_child = input("Does the person have any children? (yes/no): ").lower()
    while add_child == "yes":
        child_id = int(input("Enter child ID: "))
        children_ids.append(child_id)
        add_child = input("Add another child? (yes/no): ").lower()
    return children_ids


def create_oracle():
    """Creates an oracle based on user inputs."""
    dataset = {"people": []}
    add_person = input("Do you want to add a person to the oracle? (yes/no): ").lower()
    while add_person == "yes":
        person = get_person_details()
        dataset["people"].append(person)
        add_person = input("Add another person? (yes/no): ").lower()
    return dataset


def main():
    # Create the oracle
    oracle = create_oracle()

    # Save the oracle to a JSON file
    with open('scenario_2.json', 'w') as f:
        json.dump(oracle, f, indent=4)

    print("\nOracle created and saved as 'scenario_2.json'!")


# Run the main function
if __name__ == "__main__":
    main()
