# ensure project root on sys.path
import sys, pathlib, os
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from src.api_router import route, next_best
from src.llm_clients.groq_client import GroqClient
from src.llm_clients.gemini_client import GeminiClient

def run_once(task_type: str, text: str):
    primary = route(task_type)
    groq = GroqClient(os.getenv("GROQ_API_KEY"))
    gemi = GeminiClient(os.getenv("GEMINI_API_KEY"))

    def call(dec):
        if dec.provider == "groq":
            return dec, groq.summarize(text, model=dec.model, timeout=15.0)
        else:
            return dec, gemi.analyze(text, model=dec.model, timeout=15.0)

    dec, out = call(primary)
    if out.get("status") == "ERROR":
        backup = next_best(primary)
        _, out2 = call(backup)
        return {"primary": dec.__dict__, "result": out, "backup": backup.__dict__, "backup_result": out2}
    else:
        return {"primary": dec.__dict__, "result": out}

if __name__ == "__main__":
    demo = "Stocks rose after jobs report; tech mixed; yields eased."
    for task in ["news_summary", "tech_summary", "strategy_synthesis"]:
        print(run_once(task, demo))
