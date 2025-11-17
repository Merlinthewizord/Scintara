from app.inference import load_model, generate
from app.personalities import all_personas_meta

def main():
    load_model()  # uses settings.model_dir
    print("Personas:", ", ".join(p["name"] for p in all_personas_meta()))

    messages = [
        {"role": "user", "content": "Write a tight, two-sentence entry about neon rain hitting old glass. Keep it grounded."}
    ]
    out = generate(messages, max_new_tokens=96, temperature=0.7, top_p=0.95)
    print("\n--- OUTPUT ---\n")
    print(out)

if __name__ == "__main__":
    main()
