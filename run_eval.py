# run_eval.py — Execute chronological train/test model evaluation
from model import load_all_data, evaluate_chronological_model

if __name__ == "__main__":
    print("Loading historical match data...")
    all_data = load_all_data()
    
    print("Executing chronological evaluation (Train: 2012-2023, Test: 2023-2025)...")
    evaluate_chronological_model(all_data)