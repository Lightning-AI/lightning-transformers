from functools import partial
from typing import Any, Callable, Optional, Tuple

from datasets import Dataset
from transformers import default_data_collator, PreTrainedTokenizerBase

from lightning_transformers.core.nlp.huggingface import HFTransformerDataModule
from lightning_transformers.core.nlp.huggingface.seq2seq.config import HFSeq2SeqDataConfig


class Seq2SeqDataModule(HFTransformerDataModule):
    cfg: HFSeq2SeqDataConfig

    def process_data(self, dataset: Dataset, stage: Optional[str] = None) -> Dataset:
        src_text_column_name, tgt_text_column_name = self.source_target_column_names

        convert_to_features = partial(
            self.convert_to_features,
            tokenizer=self.tokenizer,
            padding=self.cfg.padding,
            max_source_length=self.cfg.max_source_length,
            max_target_length=self.cfg.max_target_length,
            src_text_column_name=src_text_column_name,
            tgt_text_column_name=tgt_text_column_name,
        )
        dataset = dataset.map(
            convert_to_features,
            batched=True,
            num_proc=self.cfg.preprocessing_num_workers,
            load_from_cache_file=self.cfg.load_from_cache_file,
        )

        cols_to_keep = [x for x in ["input_ids", "attention_mask", "labels"] if x in dataset["train"].features]
        dataset.set_format(columns=cols_to_keep)
        return dataset

    @property
    def source_target_column_names(self) -> Tuple[str, str]:
        raise NotImplementedError

    @staticmethod
    def convert_to_features(
        examples: Any,
        tokenizer: PreTrainedTokenizerBase,
        padding: str,
        max_source_length: int,
        max_target_length: int,
        src_text_column_name: str,
        tgt_text_column_name: str,
    ):
        encoded_results = tokenizer.prepare_seq2seq_batch(
            src_texts=examples[src_text_column_name],
            tgt_texts=examples[tgt_text_column_name],
            max_length=max_source_length,
            max_target_length=max_target_length,
            padding=padding,
        )
        return encoded_results

    @property
    def collate_fn(self) -> Callable:
        return default_data_collator
