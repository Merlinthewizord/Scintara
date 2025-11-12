import argparse
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="HF repo, e.g. tinyllama/TinyLlama-1.1B-Chat-v1.0")
    ap.add_argument("--target", required=True, help="Local target directory (e.g., models/tinyllama)")
    args = ap.parse_args()

    target = Path(args.target)
    target.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {args.model} -> {target}")
    tok = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    tok.save_pretrained(target.as_posix())

    mdl = AutoModelForCausalLM.from_pretrained(args.model, trust_remote_code=True)
    mdl.save_pretrained(target.as_posix(), safe_serialization=True)

    print("Done.")

if __name__ == "__main__":
    main()
