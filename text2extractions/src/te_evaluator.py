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
    return fuzz.token_set_ratio(text1, text2) >= threshold

def extract_entities_by_type(entities, entity_type):
    """
    Extracts entities of a given type from the entities list.
    """
    result = []
    for entity in entities:
        if entity_type in entity:
            result.extend(entity[entity_type]) if isinstance(entity[entity_type], list) else result.append(entity[entity_type])
    return result

def compare_entities(pred_entities, gold_entities, entity_type, fuzzy_threshold=70):
    tp = 0
    fp = 0
    fn = 0

    # Extract entities of the specified type
    pred_list = extract_entities_by_type(pred_entities, entity_type)
    gold_list = extract_entities_by_type(gold_entities, entity_type)

    matched_gold = set()
    for pred_entity in pred_list:
        matched = False
        for i, gold_entity in enumerate(gold_list):
            if i in matched_gold:
                continue
            if entity_type in ["testator", "executor", "beneficiary"]:
                if exact_match(pred_entity.get("name"), gold_entity.get("name")):
                    tp += 1
                    matched_gold.add(i)
                    matched = True
                    break
            elif entity_type == "asset":
                if fuzzy_match(pred_entity.get("description"), gold_entity.get("description"), threshold=fuzzy_threshold):
                    tp += 1
                    matched_gold.add(i)
                    matched = True
                    break
            elif entity_type == "condition":
                if fuzzy_match(pred_entity.get("text"), gold_entity.get("text"), threshold=fuzzy_threshold):
                    tp += 1
                    matched_gold.add(i)
                    matched = True
                    break
        if not matched:
            fp += 1

    fn += len(gold_list) - len(matched_gold)

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

def map_entity_ids(pred_events, gold_events, pred_entities, gold_entities, fuzzy_threshold=70):
    """
    Maps entity IDs between prediction and gold events using exact or fuzzy matching criteria.
    """
    mapping = {}

    def entity_match(gold_id, pred_id):
        """
        Matches entities based on type-specific criteria.
        """
        gold_entity = find_entity_by_id(gold_entities, gold_id)
        pred_entity = find_entity_by_id(pred_entities, pred_id)
        if not gold_entity or not pred_entity:
            return False

        # Exact match for testator, executor, and beneficiary
        if "name" in gold_entity and "name" in pred_entity:
            return gold_entity["name"] == pred_entity["name"]

        # Fuzzy match for asset and condition
        if "description" in gold_entity and "description" in pred_entity:
            return fuzzy_match(gold_entity["description"], pred_entity["description"], threshold=fuzzy_threshold)
        if "text" in gold_entity and "text" in pred_entity:
            return fuzzy_match(gold_entity["text"], pred_entity["text"], threshold=fuzzy_threshold)

        return False

    for gold_event in gold_events:
        for pred_event in pred_events:
            if gold_event["type"] != pred_event["type"]:
                continue

            gold_entities_in_event = {field: gold_event[field] for field in gold_event if isinstance(gold_event[field], list)}
            pred_entities_in_event = {field: pred_event[field] for field in pred_event if isinstance(pred_event[field], list)}

            match = True
            for field, gold_ids in gold_entities_in_event.items():
                pred_ids = pred_entities_in_event.get(field, [])
                matched_ids = set()

                for gold_id in gold_ids:
                    matched = False
                    for pred_id in pred_ids:
                        if pred_id in matched_ids:
                            continue
                        if entity_match(gold_id, pred_id):
                            matched_ids.add(pred_id)
                            matched = True
                            break
                    if not matched:
                        match = False
                        break
                if not match:
                    break

            if match:
                mapping[gold_event["id"]] = pred_event["id"]

    return mapping


def compare_events(pred_events, gold_events, pred_entities, gold_entities, fuzzy_threshold=70):
    """
    Compares events between prediction and gold data, calculating precision, recall, and F1 score.
    """
    tp = 0
    fp = 0
    fn = 0

    # Map entity IDs between prediction and gold events
    mapping = map_entity_ids(pred_events, gold_events, pred_entities, gold_entities, fuzzy_threshold)

    print(f"Mapping of gold to predicted event IDs: {mapping}")

    # Track matched prediction IDs
    matched_pred_ids = set()

    # Process gold events
    for gold_event in gold_events:
        gold_id = gold_event["id"]
        if gold_id in mapping:
            pred_event_id = mapping[gold_id]
            pred_event = next((e for e in pred_events if e["id"] == pred_event_id), None)
            if pred_event:
                # Check if all fields match
                all_fields_match = True
                for field in gold_event:
                    gold_field = gold_event[field]
                    pred_field = pred_event[field]

                    if isinstance(gold_field, list):
                        gold_entities_resolved = [find_entity_by_id(gold_entities, eid) for eid in gold_field]
                        pred_entities_resolved = [find_entity_by_id(pred_entities, eid) for eid in pred_field]
                        if sorted(gold_entities_resolved, key=lambda x: x.get("id", "")) != sorted(pred_entities_resolved, key=lambda x: x.get("id", "")):
                            all_fields_match = False
                            break
                    elif isinstance(gold_field, str):
                        if find_entity_by_id(gold_entities, gold_field) != find_entity_by_id(pred_entities, pred_field):
                            all_fields_match = False
                            break

                if all_fields_match:
                    matched_pred_ids.add(pred_event['id'])
                    tp += 1
                    print(f"True Positive: Gold Event {gold_id} matches Predicted Event {pred_event['id']}")
                else:
                    fn += 1
                    print(f"False Negative: Gold Event {gold_id} does not match Predicted Event {pred_event['id']}")
        else:
            fn += 1
            print(f"False Negative: Gold Event {gold_id} has no matching Predicted Event")

    # Count false positives: unmatched predicted events
    for pred_event in pred_events:
        if pred_event["id"] not in matched_pred_ids:
            fp += 1
            print(f"False Positive: Predicted Event {pred_event['id']} has no matching Gold Event")

    # Debugging final counts
    print(f"Final Counts: TP={tp}, FP={fp}, FN={fn}")

    # Calculate precision, recall, and F1 score
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

    return tp, fp, fn, precision, recall, f1


def calculate_total_entity_scores(pred_entities, gold_entities, fuzzy_threshold=70):
    total_tp = 0
    total_fp = 0
    total_fn = 0

    for entity_type in ["testator", "executor", "beneficiary", "asset", "condition"]:
        tp, fp, fn, _, _, _ = compare_entities(pred_entities, gold_entities, entity_type, fuzzy_threshold)
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
                    pred_entities, gold_entities, fuzzy_threshold=fuzzy_threshold
                )

                # Calculate metrics for events
                event_tp, event_fp, event_fn, event_precision, event_recall, event_f1 = compare_events(
                    pred_events, gold_events, pred_entities, gold_entities, fuzzy_threshold=fuzzy_threshold
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
                    "event_f1": event_f1
                })
            else:
                print(f"Gold file not found for {pred_file}")

    # Write results to CSV
    with open(output_csv, mode='w', newline='') as csvfile:
        fieldnames = ["pred_file", "gold_file", "entity_tp", "entity_fp", "entity_fn", "entity_precision", "entity_recall", "entity_f1", "event_tp", "event_fp", "event_fn", "event_precision", "event_recall", "event_f1"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    pred_dir = "../pred_dir"  # Replace with the actual path
    gold_dir = "../gold_dir"  # Replace with the actual path
    output_csv = "../comparison_results.csv"  # Replace with the desired output file name

    compare_files(pred_dir, gold_dir, output_csv)