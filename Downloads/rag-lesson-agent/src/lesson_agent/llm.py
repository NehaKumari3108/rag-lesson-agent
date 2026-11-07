"""Thin provider-agnostic LLM wrapper. Swap models with env vars, no code change."""
import json, os, re
from pathlib import Path

DATA = Path(__file__).parent / "data"


class LangChainLLM:
    def __init__(self, provider: str, model: str, temperature: float):
        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            self.m = ChatAnthropic(model=model, temperature=temperature, max_tokens=4096)
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            self.m = ChatOpenAI(model=model, temperature=temperature)
        elif provider == "ollama":
            from langchain_ollama import ChatOllama
            self.m = ChatOllama(model=model, temperature=temperature,
                                base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"))
        else:
            raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

    def complete(self, system: str, user: str) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage
        out = self.m.invoke([SystemMessage(content=system), HumanMessage(content=user)]).content
        if isinstance(out, list):  # some providers return content blocks
            out = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in out)
        return out


class MockLLM:
    """Offline, scripted stand-in used for tests/CI and for checking the loop plumbing.
    It is NOT a quality signal: real runs must use a real provider."""

    def complete(self, system: str, user: str) -> str:
        if "ROLE:GENERATE" in system or "ROLE:REWRITE" in system:
            lesson = (DATA / "mock_lesson.md").read_text()
            if "ROLE:REWRITE" in system:
                return ("<changes>\n- Removed the false claim about retraining.\n"
                        "- Replaced the deep technical sentence with a simple one.\n</changes>\n"
                        f"<lesson>\n{lesson}\n</lesson>")
            return f"<lesson>\n{lesson}\n</lesson>"
        if "ROLE:JUDGE" in system:
            text = user.split("<lesson>")[-1].lower()
            ids = re.findall(r"^- id: (J\d+)", user, re.M)
            bad = {
                "J1": ("retrains the whole model" in text, "Claims RAG retrains the model; RAG never changes the model's weights."),
                "J5": ("cosine similarity" in text or "high-dimensional" in text, "Uses expert words (cosine similarity, high-dimensional) a beginner cannot follow."),
            }
            res = []
            for i in ids:
                fail, why = bad.get(i, (False, ""))
                res.append({"id": i, "passed": not fail, "reason": why or "ok", "evidence": ""})
            return json.dumps({"checks": res})
        if "ROLE:REFLECT" in system:
            ids = sorted(set(re.findall(r"CHECK (\w+)", user)))
            return json.dumps({"rules": [{"check_id": i, "rule": f"Before finishing, re-read the lesson and make sure check {i} would pass."} for i in ids]})
        return ""


def build_llm(role: str):
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    if provider == "mock":
        return MockLLM()
    defaults = {"anthropic": ("claude-sonnet-5-5", "claude-opus-5-5"),
                "openai": ("gpt-4o-mini", "gpt-4o"),
                "ollama": ("llama3.1:8b", "llama3.1:8b")}[provider]
    if role == "judge":
        return LangChainLLM(provider, os.getenv("JUDGE_MODEL", defaults[1]), 0.0)
    return LangChainLLM(provider, os.getenv("GEN_MODEL", defaults[0]), 0.7)
