import os
import json
import sys
from math import log10, floor

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

def extract_beneficiaries(obj):
    for key in ["beneficiaries", "beneficiares"]:
        if key in obj:
            return normalize_beneficiaries(obj[key])
    return {}

def normalize_beneficiaries(beneficiaries):
    normalized = {}
    for name, info in beneficiaries.items():
        norm_name = name.replace(" (through custodian)", "").strip()
        normalized[norm_name] = info
    return normalized

def round_sigfig(x, sig=3):
    if x == 0:
        return 0.0
    return round(x, sig - int(floor(log10(abs(x)))) - 1)

def shares_equal(share1, share2):
    return round_sigfig(float(share1)) == round_sigfig(float(share2))

def asset_shares_match(gt_asset, pred_asset):
    gt_bens = extract_beneficiaries(gt_asset)
    pred_bens = extract_beneficiaries(pred_asset)

    if set(gt_bens.keys()) != set(pred_bens.keys()):
        return False

    for person, gt_info in gt_bens.items():
        pred_info = pred_bens.get(person)
        if not pred_info or not shares_equal(gt_info.get("share", 0), pred_info.get("share", 0)):
            return False
    return True

def compute_will_score(folder_path):
    gt_path = os.path.join(folder_path, "gt.json")
    pred_path = os.path.join(folder_path, "full_oracle_revised_baseline.json")

    if not (os.path.exists(gt_path) and os.path.exists(pred_path)):
        return None

    gt = load_json(gt_path)
    pred = load_json(pred_path)

    matched_assets = 0

    for asset, gt_info in gt.items():
        pred_info = pred.get(asset)
        if pred_info and asset_shares_match(gt_info, pred_info):
            matched_assets += 1

    total_gt_assets = set(gt.keys())
    total_pred_assets = set(pred.keys())
    all_assets = total_gt_assets.union(total_pred_assets)

    score = matched_assets / len(all_assets) if all_assets else 0.0

    binary_score = 1.0 if (matched_assets == len(gt) and total_pred_assets == total_gt_assets) else 0.0

    return score, binary_score

def main(base_dir):
    will_normalized_scores = []
    will_binary_scores = []

    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        result = compute_will_score(folder_path)
        if result is None:
            continue

        score, binary = result
        will_normalized_scores.append(score)
        will_binary_scores.append(binary)
        print(f"{folder_name}: normalized = {score:.2f}, binary = {int(binary)}")

    total_wills = len(will_binary_scores)

    if total_wills > 0:
        avg_binary = sum(will_binary_scores) / total_wills
        avg_normalized = sum(will_normalized_scores) / total_wills
        print(f"\nOverall Will-Level Binary Accuracy: {sum(will_binary_scores)}/{total_wills} = {avg_binary:.2%}")
        print(f"Overall Will-Level Normalized Accuracy: {round(sum(will_normalized_scores),2)}/{total_wills} = {avg_normalized:.2%}")
    else:
        print("No valid wills found.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 compute_accuracy.py <dest_folder>")
        sys.exit(1)

    main(sys.argv[1])
