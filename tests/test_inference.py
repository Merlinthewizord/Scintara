import os
import pytest
from app.inference import load_model, generate

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY is not set",
)

@pytest.mark.timeout(300)
def test_generate_basic():
    # Loads model once, then generates a short reply.
    load_model()
    out = generate([{"role": "user", "content": "One sentence about neon rain. Keep it grounded."}],
                   max_new_tokens=48, temperature=0.7, top_p=0.95)
    assert isinstance(out, str) and len(out.strip()) > 0
