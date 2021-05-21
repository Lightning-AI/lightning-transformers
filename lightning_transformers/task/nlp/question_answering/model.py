# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from functools import partial
from typing import Any, Dict

import torch

from lightning_transformers.core.nlp import HFTransformer
from lightning_transformers.task.nlp.question_answering import QuestionAnsweringDataModule
from lightning_transformers.task.nlp.question_answering.datasets.squad.metric import SquadMetric

class QuestionAnsweringTransformer(HFTransformer):
    """
    Defines ``LightningModule`` for the Question Answering Task.

    Args:
        *args: :class:`lightning_transformers.core.nlp.HFTransformer` arguments.
        downstream_model_type: Downstream HuggingFace AutoModel to load.
            (default ``transformers.AutoModelForQuestionAnswering``)
        **kwargs: :class:`lightning_transformers.core.nlp.HFTransformer` arguments.
    """

    def __init__(
        self, *args, downstream_model_type: str = 'transformers.AutoModelForQuestionAnswering', **kwargs
    ) -> None:
        super().__init__(downstream_model_type, *args, **kwargs)

    def training_step(self, batch: Any, batch_idx: int) -> torch.Tensor:
        outputs = self.model(**batch)
        loss = outputs[0]
        self.log("train_loss", loss)
        return loss

    @property
    def hf_pipeline_task(self) -> str:
        return "question-answering"

    def validation_step(self, batch: Any, batch_idx: int, dataloader_idx: int = 0) -> Dict[str, torch.Tensor]:
        batch.pop("offset_mapping")
        example_ids = batch.pop("example_id")
        outputs = self.model(**batch)
        loss = outputs[0]
        self.log("val_loss", loss, prog_bar=True, sync_dist=True)
        self.metric(example_ids, outputs.start_logits, outputs.end_logits)
        return loss
    
    def validation_epoch_end(self, outputs: Any) -> None:
        self.metric.compute()

    '''
    def test_step(self, batch: Any, batch_idx: int, dataloader_idx: int = 0):
        outputs = self.model(**batch)
        loss, logits = outputs[:2]
        return loss
    '''

    def configure_metrics(self, stage: str):
        dataset: QuestionAnsweringDataModule = self.trainer.datamodule
        validation_dataset = dataset.ds["validation"]
        original_validation_dataset = dataset.ds["validation_original"]
        postprocess_func = partial(
            dataset.postprocess_func,
            dataset=dataset.ds,
            validation_dataset=validation_dataset,
            original_validation_dataset=original_validation_dataset,
        )
        example_id_strings = dataset.example_id_strings
        self.metric = SquadMetric(
            postprocess_func=postprocess_func, 
            example_id_strings=example_id_strings
        )
