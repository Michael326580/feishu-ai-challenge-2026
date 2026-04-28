from pathlib import Path

from agent.auto_repair_agent import AutoRepairAgent


if __name__ == "__main__":
    repo = Path(__file__).resolve().parent
    outcome = AutoRepairAgent(repo).repair_from_log(repo / "logs" / "service_error.log")
    print("Auto repair completed:")
    print(outcome)