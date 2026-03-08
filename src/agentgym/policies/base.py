from typing import Dict, Any


class BasePolicy:
    def act(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
