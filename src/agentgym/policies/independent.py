from .base import BasePolicy


class IndependentPolicy(BasePolicy):
    def act(self, observation):
        return {"action": "wait"}
