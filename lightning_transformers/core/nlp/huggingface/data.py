import os
from typing import Any, Dict, Optional, Union

from datasets import Dataset, DatasetDict, load_dataset
from pytorch_lightning.utilities.exceptions import MisconfigurationException
from transformers import PreTrainedTokenizerBase

from lightning_transformers.core.data import TransformerTokenizerDataModule
from lightning_transformers.core.nlp.huggingface.config import HFTransformerDataConfig


class HFTransformerDataModule(TransformerTokenizerDataModule):
    cfg: HFTransformerDataConfig
    tokenizer: PreTrainedTokenizerBase

    def __init__(self, cfg: HFTransformerDataConfig, tokenizer: PreTrainedTokenizerBase):
        super().__init__(cfg, tokenizer)
        os.environ["TOKENIZERS_PARALLELISM"] = "TRUE"  # todo: smarter handling of this env variable
        # call fit to setup any metadata required for the model initialization
        self.setup("fit")

    def setup(self, stage: Optional[str] = None):
        dataset = self.load_dataset()
        dataset = self.split_dataset(dataset)
        dataset = self.process_data(dataset, stage=stage)
        self.ds = dataset

    def process_data(self,
                     dataset: Union[Dataset, DatasetDict],
                     stage: Optional[str] = None) -> Union[Dataset, DatasetDict]:
        return dataset

    def load_dataset(self) -> Dataset:
        if self.cfg.dataset_name is not None:
            # Downloading and loading a dataset from the hub.
            return load_dataset(
                path=self.cfg.dataset_name,
                name=self.cfg.dataset_config_name,
                cache_dir=self.cfg.cache_dir,
            )
        data_files = {}
        if self.cfg.train_file is not None:
            data_files["train"] = self.cfg.train_file
        if self.cfg.validation_file is not None:
            data_files["validation"] = self.cfg.validation_file
        if not data_files:
            raise MisconfigurationException(
                "You have not specified a dataset name. A custom train and validation file is required"
            )
        extension = self.cfg.train_file.split(".")[-1]
        return load_dataset(extension, data_files=data_files, field="data")

    def split_dataset(self, dataset: Union[Dataset, DatasetDict]) -> Union[Dataset, DatasetDict]:
        if self.cfg.train_val_split is not None:
            split = dataset["train"].train_test_split(self.cfg.train_val_split)
            dataset["train"] = split["train"]
            dataset["validation"] = split["test"]
        dataset = self._select_samples(dataset)
        return dataset

    def _select_samples(self, dataset: Union[Dataset, DatasetDict]) -> Union[Dataset, DatasetDict]:
        samples = (("train", self.cfg.limit_train_samples), ("validation", self.cfg.limit_val_samples),
                   ("test", self.cfg.limit_test_samples))
        for column_name, n_samples in samples:
            if n_samples is not None and column_name in dataset:
                indices = range(min(len(dataset[column_name]), n_samples))
                dataset[column_name] = dataset[column_name].select(indices)
        return dataset

    def on_save_checkpoint(self, checkpoint: Dict[str, Any]):
        # Save tokenizer from datamodule for predictions
        checkpoint["tokenizer"] = self.tokenizer

    def on_load_checkpoint(self, checkpoint: Dict[str, Any]) -> None:
        self.tokenizer = checkpoint["tokenizer"]
