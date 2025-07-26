from google.adk.agents import Agent

class BaseAgent(Agent):
    """Common functionality for all domain agents."""
    def log(self, message: str) -> None:
        print(f"[{self.name}] {message}")
