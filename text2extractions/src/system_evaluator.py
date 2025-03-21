import json
from collections import defaultdict
from sklearn.metrics import precision_score, recall_score, f1_score

# Load the JSON files -- switch to the actual paths before running the code
with open('/path/to/gold', 'r') as gold_file:
    gold_data = json.load(gold_file)

with open('/path/to/result', 'r') as result_file:
    result_data = json.load(result_file)

def normalize_devolution(data):
    """
    Normalizes the devolution data to a common format: {Asset: {Person: Share}}.
    """
    normalized = defaultdict(dict)
    for key, asset_data in data.items():
        if isinstance(asset_data, dict):
            for asset, details in asset_data.items():
                if isinstance(details, dict):
                    for person, share in details.items():
                        normalized[asset][person] = share
    return normalized

# Normalize the gold and result data
gold_devolution = normalize_devolution(gold_data)
result_devolution = normalize_devolution(result_data)

# Flatten the results for comparison
def flatten_devolution(devolution):
    """
    Flattens the devolution dictionary into a list of (Asset, Person, Share).
    """
    flat_list = []
    for asset, allocations in devolution.items():
        for person, share in allocations.items():
            flat_list.append((asset, person, share))
    return flat_list

gold_flat = flatten_devolution(gold_devolution)
result_flat = flatten_devolution(result_devolution)

# Convert to sets for comparison
gold_set = set(gold_flat)
result_set = set(result_flat)

# Metrics calculation
true_positive = len(gold_set & result_set)
false_positive = len(result_set - gold_set)
false_negative = len(gold_set - result_set)

precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

# Print the results
print("Comparison Results:")
print(f"Precision: {precision:.2f}")
print(f"Recall: {recall:.2f}")
print(f"F1-Score: {f1:.2f}")

# Optionally, print detailed comparisons
print("\nGold Devolution Set:", gold_set)
print("Result Devolution Set:", result_set)
print("True Positives:", gold_set & result_set)
print("False Positives:", result_set - gold_set)
print("False Negatives:", gold_set - result_set)