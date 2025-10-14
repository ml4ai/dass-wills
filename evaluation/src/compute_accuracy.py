import os
import json
import sys

def load_json(path):
    """Load JSON safely."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

def extract_beneficiaries(obj):
    """Return normalized beneficiaries dictionary."""
    for key in ["beneficiaries", "beneficiares"]:
        if key in obj:
            return normalize_beneficiaries(obj[key])
    return {}

def normalize_beneficiaries(beneficiaries):
    """Normalize names (remove custodians etc.)."""
    normalized = {}
    for name, info in beneficiaries.items():
        norm_name = name.replace(" (through custodian)", "").strip()
        normalized[norm_name] = info
    return normalized

def shares_equal(share1, share2):
    """Check if two share values are approximately equal."""
    try:
        return round(float(share1), 2) == round(float(share2), 2)
    except Exception:
        return False

def asset_shares_match(gt_asset, pred_asset):
    """Check if all beneficiary shares match between GT and prediction."""
    gt_bens = extract_beneficiaries(gt_asset)
    pred_bens = extract_beneficiaries(pred_asset)

    if set(gt_bens.keys()) != set(pred_bens.keys()):
        return False

    for person, gt_info in gt_bens.items():
        pred_info = pred_bens.get(person)
        if not pred_info or not shares_equal(gt_info.get("share", 0), pred_info.get("share", 0)):
            return False
    return True

def compute_will_score(will_path):
    """Compute accuracy for a single will folder."""
    gt_path = os.path.join(will_path, "gt.json")
    pred_path = os.path.join(will_path, "will.devolution.json")

    # Case 1: no ground-truth → invalid
    if not os.path.exists(gt_path):
        return None

    gt = load_json(gt_path)
    if gt is None:
        return None

    # Case 2: no predicted file → 0 score
    if not os.path.exists(pred_path):
        print(f"  Missing will.devolution.json in {os.path.basename(will_path)} → 0 score")
        return 0.0, 0.0

    # Normal case
    pred = load_json(pred_path)
    if pred is None:
        print(f"  Error reading will.devolution.json in {os.path.basename(will_path)} → 0 score")
        return 0.0, 0.0

    matched_assets = 0
    for asset, gt_info in gt.items():
        pred_info = pred.get(asset)
        if pred_info and asset_shares_match(gt_info, pred_info):
            matched_assets += 1

    extra_assets = set(pred.keys()) - set(gt.keys())
    all_assets = set(gt.keys()).union(set(pred.keys()))
    score = matched_assets / len(all_assets) if all_assets else 0.0
    binary_score = 1.0 if (score == 1.0 and not extra_assets) else 0.0

    return score, binary_score

def compute_folder_scores(folder_path):
    """Compute accuracy for all wills inside one reviewed folder."""
    will_scores = []
    will_binaries = []

    print(f"\nEvaluating folder: {os.path.basename(folder_path)}")

    for will_name in sorted(os.listdir(folder_path)):
        will_path = os.path.join(folder_path, will_name)
        if not os.path.isdir(will_path):
            continue

        result = compute_will_score(will_path)
        if result is None:
            continue

        score, binary = result
        will_scores.append(score)
        will_binaries.append(binary)
        print(f"  {will_name}: normalized = {score:.2f}, binary = {int(binary)}")

    if not will_scores:
        print("  No valid wills found in this folder.")
        return None, None

    avg_norm = sum(will_scores) / len(will_scores)
    avg_bin = sum(will_binaries) / len(will_binaries)
    print(f"  → Folder Avg Normalized: {avg_norm:.2%}, Binary: {avg_bin:.2%}")

    return avg_norm, avg_bin

def main(root_dir):
    """Compute averages for all reviewed folders and overall."""
    folder_averages = []

    print(f"=== Evaluating All Folders in {root_dir} ===")

    for folder_name in sorted(os.listdir(root_dir)):
        folder_path = os.path.join(root_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        avg_norm, avg_bin = compute_folder_scores(folder_path)
        if avg_norm is not None:
            folder_averages.append((avg_norm, avg_bin))

    if not folder_averages:
        print("\nNo valid results found in any folder.")
        return

    overall_norm = sum(x[0] for x in folder_averages) / len(folder_averages)
    overall_bin = sum(x[1] for x in folder_averages) / len(folder_averages)

    print("\n=== Overall Summary ===")
    print(f"Overall Average Normalized Accuracy: {overall_norm:.2%}")
    print(f"Overall Average Binary Accuracy: {overall_bin:.2%}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 compute_accuracy.py <root_folder>")
        sys.exit(1)
    main(sys.argv[1])
