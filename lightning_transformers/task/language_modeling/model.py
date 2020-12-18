from lightning_transformers.core.base import LitTransformer
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


class LitLanguageModelingTransformer(LitTransformer):
    def __init__(self, pretrained_model_name_or_path: str, tokenizer: AutoTokenizer, optim_config):
        super().__init__(
            model_name_or_path=pretrained_model_name_or_path,
            tokenizer=tokenizer,
            optim_config=optim_config,
            model_type=AutoModelForSequenceClassification
        )
