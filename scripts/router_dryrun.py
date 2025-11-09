import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from src.api_router import route

def main():
    for task in ["news_summary", "tech_summary", "strategy_synthesis", "unknown_task"]:
        d = route(task)
        print({"task": task, "provider": d.provider, "model": d.model, "reason": d.reason})

if __name__ == "__main__":
    main()
