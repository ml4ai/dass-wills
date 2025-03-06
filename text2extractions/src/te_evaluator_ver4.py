import json
import os
import csv
from fuzzywuzzy import fuzz

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def exact_match(entity1, entity2):
    return entity1 == entity2

def fuzzy_match(text1, text2, threshold=70):
    return fuzz.ratio(text1, text2) >= threshold

def extract_entities_by_type(entities, entity_type):
    """
    Extracts entities of a given type from the entities list.
    """
    result = []
    for entity in entities:
        if entity_type in entity:
            result.extend(entity[entity_type]) if isinstance(entity[entity_type], list) else result.append(entity[entity_type])
    return result

def write_fuzzy_match_log(log_data, log_file):
    """
    Writes the fuzzy match log to a CSV file.
    Each row contains: Entity Type, Predicted Entity, Gold Entity, Similarity Score.
    """
    file_exists = os.path.isfile(log_file)

    with open(log_file, mode="a", newline="") as file:
        writer = csv.writer(file)

        # Write header if file doesn't exist
        if not file_exists:
            writer.writerow(["File Name", "Entity Type", "Predicted Entity", "Gold Entity", "Similarity Score"])

        # Write log data
        writer.writerows(log_data)

def write_entity_error_log(log_data, log_file):
    """
    Writes False Positives (FP) and False Negatives (FN) for entities to a CSV file.
    Each row contains: File Name, Entity Type, Error Type (FP/FN), Entity Text.
    """
    file_exists = os.path.isfile(log_file)

    with open(log_file, mode="a", newline="") as file:
        writer = csv.writer(file)

        # Write header if file doesn't exist
        if not file_exists:
            writer.writerow(["File Name", "Entity Type", "Error Type", "Entity Text"])

        # Write log data
        writer.writerows(log_data)

def compare_entities(pred_entities, gold_entities, entity_type, file_name, fuzzy_threshold=70, log_file="fuzzy_match_log.csv", entity_log_file="entity_error_log.csv"):
    """
    Compares predicted and gold entities for a specific entity type.
    - Exact match for Testator, Executor, Beneficiary.
    - Fuzzy match for Asset and Condition (best match selection).
    - Logs False Positives (FP), False Negatives (FN), and fuzzy matches (excluding exact matches).
    """
    tp = 0
    fp = 0
    fn = 0
    fuzzy_match_log = []
    entity_error_log = []

    # Extract entities of the specified type
    pred_list = extract_entities_by_type(pred_entities, entity_type)
    gold_list = extract_entities_by_type(gold_entities, entity_type)

    # Track matched indices
    matched_gold = set()  # Stores matched gold entity indices
    matched_pred = set()  # Stores matched predicted entity indices
    potential_matches = []  # Store potential matches (pred_idx, gold_idx, similarity)

    # First pass: Exact match for names (Testator, Executor, Beneficiary)
    if entity_type in ["testator", "executor", "beneficiary"]:
        for pred_idx, pred_entity in enumerate(pred_list):
            for gold_idx, gold_entity in enumerate(gold_list):
                if gold_idx in matched_gold:
                    continue  # Skip already matched gold entities

                if exact_match(pred_entity.get("name"), gold_entity.get("name")):
                    tp += 1
                    matched_gold.add(gold_idx)
                    matched_pred.add(pred_idx)
                    break  # Stop searching once a match is found

    # Second pass: Fuzzy match for Asset and Condition (find best match)
    elif entity_type in ["asset", "condition"]:
        for pred_idx, pred_entity in enumerate(pred_list):
            pred_text = pred_entity.get("description") or pred_entity.get("text")

            for gold_idx, gold_entity in enumerate(gold_list):
                if gold_idx in matched_gold:
                    continue  # Skip already matched gold entities

                gold_text = gold_entity.get("description") or gold_entity.get("text")
                similarity = fuzz.ratio(pred_text, gold_text)

                if similarity >= fuzzy_threshold:
                    potential_matches.append((pred_idx, gold_idx, similarity))

        # Sort matches by similarity (highest first)
        potential_matches.sort(key=lambda x: x[2], reverse=True)

        # Assign best matches
        for pred_idx, gold_idx, similarity in potential_matches:
            if pred_idx in matched_pred or gold_idx in matched_gold:
                continue  # Skip already matched entities

            tp += 1
            matched_pred.add(pred_idx)
            matched_gold.add(gold_idx)

            # **Log only non-exact fuzzy matches**
            if similarity < 100:  # ✅ Prevents logging exact matches
                pred_text = pred_list[pred_idx].get("description") or pred_list[pred_idx].get("text")
                gold_text = gold_list[gold_idx].get("description") or gold_list[gold_idx].get("text")
                fuzzy_match_log.append([file_name, entity_type, pred_text, gold_text, similarity])

    # False Positives: Unmatched predicted entities
    for pred_idx, pred_entity in enumerate(pred_list):
        if pred_idx not in matched_pred:
            fp += 1
            entity_error_log.append([
                file_name,  # ✅ Log file name
                entity_type,
                "FP",  # False Positive
                pred_entity.get("name") or pred_entity.get("description") or pred_entity.get("text")
            ])

    # False Negatives: Unmatched gold entities
    for gold_idx, gold_entity in enumerate(gold_list):
        if gold_idx not in matched_gold:
            fn += 1
            entity_error_log.append([
                file_name,  # ✅ Log file name
                entity_type,
                "FN",  # False Negative
                gold_entity.get("name") or gold_entity.get("description") or gold_entity.get("text")
            ])

    # ✅ Write fuzzy match log (only fuzzy matches, not exact matches)
    if fuzzy_match_log:
        write_fuzzy_match_log(fuzzy_match_log, log_file)

    # ✅ Write entity error log (FP/FN)
    if entity_error_log:
        write_entity_error_log(entity_error_log, entity_log_file)

    # Compute Precision, Recall, and F1 Score
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

    return tp, fp, fn, precision, recall, f1

def find_entity_by_id(entities, entity_id):
    """
    Finds an entity in the list of entities by its ID.
    """
    for entity in entities:
        for key, value in entity.items():
            if isinstance(value, list):
                for item in value:
                    if item.get("id") == entity_id:
                        return item
            elif isinstance(value, dict) and value.get("id") == entity_id:
                return value
    return {}


def extract_entities(entities):
    """Flattens the nested entity structure into a list of entity dictionaries."""
    flat_entities = []
    for entity_group in entities:
        for category, items in entity_group.items():
            if isinstance(items, list):
                flat_entities.extend(items)
            elif isinstance(items, dict):
                flat_entities.append(items)
    return flat_entities


def map_entity_ids(pred_entities, gold_entities, fuzzy_threshold=70):
    """
    Maps entity IDs from predicted to gold entities based on exact name matches (for people)
    and best fuzzy matches (for assets and conditions).
    Ensures all occurrences of a predicted entity ID are replaced with its mapped gold entity ID.
    """
    pred_entities = extract_entities(pred_entities)
    gold_entities = extract_entities(gold_entities)
    entity_mapping = {}
    used_gold_ids = set()

    for pred in pred_entities:
        best_match_id = None
        best_match_score = fuzzy_threshold  # Set threshold

        for gold in gold_entities:
            if gold["id"] in used_gold_ids:
                continue  # Prevent duplicate mapping

            # Exact match for people entities
            if "name" in pred and "name" in gold and pred["name"] == gold["name"]:
                entity_mapping[pred["id"]] = gold["id"]
                used_gold_ids.add(gold["id"])
                best_match_id = gold["id"]
                break  # Stop searching once an exact match is found

            # Fuzzy match for assets and conditions (description/text)
            pred_value = pred.get("description") or pred.get("text")
            gold_value = gold.get("description") or gold.get("text")

            if pred_value and gold_value:
                match_score = fuzz.ratio(pred_value, gold_value)
                if match_score > best_match_score:
                    best_match_score = match_score
                    best_match_id = gold["id"]

        if best_match_id:
            entity_mapping[pred["id"]] = best_match_id
            used_gold_ids.add(best_match_id)

    return entity_mapping


def resolve_entity_ids(entity_ids, entity_list):
    """
    Converts a list of entity IDs into their actual entity representations.
    Ensures only valid entities are returned.
    """
    resolved_entities = []
    entity_dict = {}  # Dictionary to store entity lookups by ID

    # Flatten the nested entity structure and build a lookup dictionary
    for entity_group in entity_list:
        for entity_type, entity_value in entity_group.items():
            if isinstance(entity_value, list):
                for item in entity_value:
                    if "id" in item:
                        entity_dict[item["id"]] = item  # Store entity by its ID
            elif isinstance(entity_value, dict) and "id" in entity_value:
                entity_dict[entity_value["id"]] = entity_value

    # Lookup entities based on provided IDs
    for entity_id in entity_ids:
        if entity_id in entity_dict:
            resolved_entities.append(entity_dict[entity_id])

    return resolved_entities  # Return only found entities


def extract_resolved_args(events, entities):
    """
    Extracts resolved arguments for events, replacing entity IDs with actual entity values (name, description, or text).
    Ensures all occurrences of a predicted entity ID are mapped correctly and returns a dictionary per role.
    """
    event_args = {}  # Structure: {event_id: {"Executor": [...], "Beneficiary": [...], ...}}
    entity_lookup = {}

    # Create lookup dictionary for entity details
    for entity_group in entities:
        for entity_type, entity_list in entity_group.items():
            if isinstance(entity_list, list):
                for entity in entity_list:
                    entity_lookup[entity["id"]] = entity
            elif isinstance(entity_list, dict):
                entity_lookup[entity_list["id"]] = entity_list

    # Replace event entity IDs with resolved entity objects using mapping
    for event in events:
        event_id = event["id"]
        event_args[event_id] = {role: [] for role in ["Testator", "Executor", "Beneficiary", "Asset", "Condition"]}

        for role in ["Testator", "Executor", "Beneficiary", "Asset", "Condition"]:
            if role in event and event[role]:
                entity_ids = event[role] if isinstance(event[role], list) else [event[role]]

                resolved_entities = []
                for e_id in entity_ids:
                    # Apply entity mapping
                    entity_obj = entity_lookup.get(e_id, {"id": e_id})

                    # Extract actual entity values instead of IDs
                    resolved_value = entity_obj.get("name") or entity_obj.get("description") or entity_obj.get("text") or mapped_id

                    # Debugging Step: Print each replacement
                    print(f"🔄 Resolving {e_id} → {resolved_value}")

                    resolved_entities.append(resolved_value)

                event_args[event_id][role].extend(resolved_entities)

    return event_args



def pair_events(pred_event_args, gold_event_args, fuzzy_threshold=70):
    """
    Ensures one-to-one event pairing by assigning each gold event to the best-matching predicted event.
    Uses similarity scores to prioritize assignments.
    """
    event_pairs = {}  # Stores final one-to-one event pairs {pred_id: gold_id}
    used_gold_events = set()  # Track assigned gold events
    used_pred_events = set()  # Track assigned predicted events

    all_pred_ids = set(pred_event_args.keys())
    all_gold_ids = set(gold_event_args.keys())

    # Step 1: Compute similarity scores for all possible pairings
    similarity_scores = []

    for pred_id, pred_args in pred_event_args.items():
        for gold_id, gold_args in gold_event_args.items():
            exact_matches, fuzzy_matches = {}, {}

            # Compare role-specific arguments
            for role in ["Testator", "Executor", "Beneficiary", "Asset", "Condition"]:
                pred_role_args = set(pred_args.get(role, []))
                gold_role_args = set(gold_args.get(role, []))

                # Compute exact matches
                exact_matches[role] = pred_role_args & gold_role_args

                # Remove exact matches before fuzzy comparison
                remaining_pred = pred_role_args - exact_matches[role]
                remaining_gold = gold_role_args - exact_matches[role]

                # Compute fuzzy matches (assets & conditions)
                fuzzy_matches[role] = {
                    p for p in remaining_pred for g in remaining_gold if fuzz.ratio(p, g) >= fuzzy_threshold
                }

            # Calculate total similarity score
            total_exact = sum(len(exact_matches[role]) for role in exact_matches)
            total_fuzzy = sum(len(fuzzy_matches[role]) for role in fuzzy_matches)
            total_score = total_exact + (0.5 * total_fuzzy)  # Fuzzy matches get half weight

            similarity_scores.append((pred_id, gold_id, total_score))

    # Step 2: Sort similarity scores in descending order (higher scores first)
    similarity_scores.sort(key=lambda x: x[2], reverse=True)

    # Step 3: Assign matches based on highest similarity, ensuring one-to-one matching
    for pred_id, gold_id, score in similarity_scores:
        if pred_id in used_pred_events or gold_id in used_gold_events:
            continue  # Skip if either event is already paired

        # Assign the best available match
        event_pairs[pred_id] = gold_id
        used_pred_events.add(pred_id)
        used_gold_events.add(gold_id)

    # Step 4: Handle unmatched predicted events as False Positives
    for pred_id in all_pred_ids:
        if pred_id not in event_pairs:
            event_pairs[pred_id] = None  # Mark as unmatched FP

    # Step 5: Handle unmatched gold events as False Negatives
    unmatched_gold_events = all_gold_ids - used_gold_events
    for gold_id in unmatched_gold_events:
        event_pairs[gold_id] = None  # Mark as unmatched FN

    return event_pairs


def write_event_error_log(log_data, log_file):
    file_exists = os.path.isfile(log_file)
    with open(log_file, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["File Name", "Event ID", "Error Type", "Event Details"])
        writer.writerows(log_data)

def write_argument_error_log(log_data, log_file):
    file_exists = os.path.isfile(log_file)
    with open(log_file, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["File Name", "Event ID", "Error Type", "Role", "Argument Details"])
        writer.writerows(log_data)

def compare_events(pred_events, gold_events, pred_entities, gold_entities, file_name, fuzzy_threshold=70, event_log_file="event_error_log.csv", arg_log_file="arg_error_log.csv"):
    """
    Compares predicted and gold events at both event and argument levels and logs errors.
    """
    event_tp, event_fp, event_fn = 0, 0, 0
    arg_tp, arg_fp, arg_fn = 0, 0, 0

    event_error_log = []
    arg_error_log = []

    # Extract resolved arguments for events
    gold_event_args = extract_resolved_args(gold_events, gold_entities)
    pred_event_args = extract_resolved_args(pred_events, pred_entities)

    # Track matched gold events
    matched_events = set()

    for pred_id, pred_args in pred_event_args.items():
        matched = False
        for gold_id, gold_args in gold_event_args.items():
            if gold_id in matched_events:
                continue

            exact_match = all(set(pred_args[role]) == set(gold_args[role]) for role in ["Testator", "Executor", "Beneficiary"])
            fuzzy_match_result = all(
                any(fuzz.ratio(p, g) >= fuzzy_threshold for p in pred_args[role] for g in gold_args[role])
                if pred_args[role] and gold_args[role] else True
                for role in ["Asset", "Condition"]
            )
            no_extra_args = all(
                set(pred_args[role]) == set(gold_args[role])
                for role in ["Testator", "Executor", "Beneficiary"]
            ) and all(
                len(pred_args[role]) == len(gold_args[role])
                for role in ["Asset", "Condition"]
            )

            if exact_match and fuzzy_match_result and no_extra_args:
                event_tp += 1
                matched_events.add(gold_id)
                matched = True
                break

        if not matched:
            event_fp += 1
            event_error_log.append([file_name, pred_id, "FP", pred_args])

    event_fn = len(gold_event_args) - len(matched_events)
    for gold_id in gold_event_args:
        if gold_id not in matched_events:
            event_error_log.append([file_name, gold_id, "FN", gold_event_args[gold_id]])

    # Argument-Level Matching
    for pred_id, gold_id in pair_events(pred_event_args, gold_event_args, fuzzy_threshold).items():
        pred_args = pred_event_args.get(pred_id, {})
        gold_args = gold_event_args.get(gold_id, {})

        for role in ["Testator", "Executor", "Beneficiary", "Asset", "Condition"]:
            pred_role_args = set(pred_args.get(role, []))
            gold_role_args = set(gold_args.get(role, []))

            exact_match_set = pred_role_args & gold_role_args
            remaining_pred = pred_role_args - exact_match_set
            remaining_gold = gold_role_args - exact_match_set

            fuzzy_match_set = set()
            matched_gold = set()
            if role in ["Asset", "Condition"]:
                sorted_matches = sorted(
                    [(p, g, fuzz.ratio(p, g)) for p in remaining_pred for g in remaining_gold if fuzz.ratio(p, g) >= fuzzy_threshold],
                    key=lambda x: x[2],
                    reverse=True
                )
                for p, g, _ in sorted_matches:
                    if g not in matched_gold:
                        fuzzy_match_set.add(p)
                        matched_gold.add(g)

            arg_tp += len(exact_match_set) + len(fuzzy_match_set)
            unmatched_gold = gold_role_args - exact_match_set - matched_gold
            unmatched_pred = pred_role_args - exact_match_set - fuzzy_match_set

            if unmatched_gold:
                arg_fn += len(unmatched_gold)
                arg_error_log.append([file_name, gold_id, "FN", role, list(unmatched_gold)])
            if unmatched_pred:
                arg_fp += len(unmatched_pred)
                arg_error_log.append([file_name, pred_id, "FP", role, list(unmatched_pred)])

    write_event_error_log(event_error_log, event_log_file)
    write_argument_error_log(arg_error_log, arg_log_file)

    event_precision = event_tp / (event_tp + event_fp) if (event_tp + event_fp) > 0 else 0
    event_recall = event_tp / (event_tp + event_fn) if (event_tp + event_fn) > 0 else 0
    event_f1 = (2 * event_precision * event_recall / (event_precision + event_recall)) if (event_precision + event_recall) > 0 else 0

    arg_precision = arg_tp / (arg_tp + arg_fp) if (arg_tp + arg_fp) > 0 else 0
    arg_recall = arg_tp / (arg_tp + arg_fn) if (arg_tp + arg_fn) > 0 else 0
    arg_f1 = (2 * arg_precision * arg_recall / (arg_precision + arg_recall)) if (arg_precision + arg_recall) > 0 else 0

    return event_tp, event_fp, event_fn, event_precision, event_recall, event_f1, arg_tp, arg_fp, arg_fn, arg_precision, arg_recall, arg_f1


def calculate_total_entity_scores(pred_entities, gold_entities, pred_file, fuzzy_threshold=70):
    total_tp = 0
    total_fp = 0
    total_fn = 0

    for entity_type in ["testator", "executor", "beneficiary", "asset", "condition"]:
        tp, fp, fn, _, _, _ = compare_entities(pred_entities, gold_entities, entity_type, pred_file, fuzzy_threshold)
        total_tp += tp
        total_fp += fp
        total_fn += fn

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

    return total_tp, total_fp, total_fn, precision, recall, f1


def compare_files(pred_dir, gold_dir, output_csv, fuzzy_threshold=70):
    results = []

    for pred_file in os.listdir(pred_dir):
        if pred_file.endswith(".json"):
            pred_file_path = os.path.join(pred_dir, pred_file)
            gold_file_name = pred_file.replace(".json", "_reviewed.json")
            gold_file_path = os.path.join(gold_dir, gold_file_name)

            if os.path.exists(gold_file_path):
                # Load prediction and gold files
                pred_data = load_json(pred_file_path)
                gold_data = load_json(gold_file_path)

                # Extract entities and events
                pred_entities = pred_data["extractions"]["entities"]
                gold_entities = gold_data["extractions"]["entities"]
                pred_events = pred_data["extractions"]["events"]
                gold_events = gold_data["extractions"]["events"]

                # Calculate metrics for entities (iterate over all entity types)
                entity_tp, entity_fp, entity_fn, entity_precision, entity_recall, entity_f1 = calculate_total_entity_scores(
                    pred_entities, gold_entities, pred_file, fuzzy_threshold=fuzzy_threshold
                )

                # Calculate metrics for events
                event_tp, event_fp, event_fn, event_precision, event_recall, event_f1, arg_tp, arg_fp, arg_fn, arg_precision, arg_recall, arg_f1 = compare_events(
                    pred_events, gold_events, pred_entities, gold_entities, pred_file
                )

                # Append results
                results.append({
                    "pred_file": pred_file,
                    "gold_file": gold_file_name,
                    "entity_tp": entity_tp,
                    "entity_fp": entity_fp,
                    "entity_fn": entity_fn,
                    "entity_precision": entity_precision,
                    "entity_recall": entity_recall,
                    "entity_f1": entity_f1,
                    "event_tp": event_tp,
                    "event_fp": event_fp,
                    "event_fn": event_fn,
                    "event_precision": event_precision,
                    "event_recall": event_recall,
                    "event_f1": event_f1,
                    "arg_tp": arg_tp,
                    "arg_fp": arg_fp,
                    "arg_fn": arg_fn,
                    "arg_precision": arg_precision,
                    "arg_recall": arg_recall,
                    "arg_f1": arg_f1
                })
            else:
                print(f"Gold file not found for {pred_file}")

    # Write results to CSV
    with open(output_csv, mode='w', newline='') as csvfile:
        fieldnames = ["pred_file", "gold_file", "entity_tp", "entity_fp", "entity_fn", "entity_precision", "entity_recall", "entity_f1", "event_tp", "event_fp", "event_fn", "event_precision", "event_recall", "event_f1", "arg_tp", "arg_fp", "arg_fn", "arg_precision", "arg_recall", "arg_f1"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    pred_dir = "/Users/alicekwak/repos/dass-wills/text2extractions/output/full_text_TN_5th"  # Replace with the actual path
    gold_dir = "/Users/alicekwak/Desktop/UA_2024_Fall/RA/Dataset/Tennessee/human annotations/simplified-review"  # Replace with the actual path
    output_csv = "/Users/alicekwak/Desktop/UA_2025_Spring/RA/comparison_results_5th.csv"  # Replace with the desired output file name

    compare_files(pred_dir, gold_dir, output_csv)