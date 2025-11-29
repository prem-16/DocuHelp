"""VLM model definitions and wrappers."""


class VLMModel:
    def __init__(self, model_path: str = None):
        self.model_path = model_path

    def predict(self, frames):
        return []
