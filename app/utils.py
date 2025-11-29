from typing import List

def trim_prompt_echo(generated: str, prompt: str) -> str:
    return generated[len(prompt):] if generated.startswith(prompt) else generated

def apply_stops(text: str, stops: List[str] | None) -> str:
    if not stops:
        return text
    cut = len(text)
    for s in stops:
        i = text.find(s)
        if i != -1 and i < cut:
            cut = i
    return text[:cut]
