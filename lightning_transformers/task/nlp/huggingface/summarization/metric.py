from typing import Dict, List

import numpy as np
import torch
from pytorch_lightning.metrics import Metric
from rouge_score import rouge_scorer, scoring
from rouge_score.scoring import AggregateScore, Score

from lightning_transformers.task.nlp.huggingface.summarization.utils import add_newline_to_end_of_each_sentence


class RougeMetric(Metric):

    def __init__(
        self,
        rouge_newline_sep: bool,
        use_stemmer: bool,
        rouge_keys: List[str] = ("rouge1", "rouge2", "rougeL", "rougeLsum"),
    ):
        super().__init__()
        self.rouge_newline_sep = rouge_newline_sep
        self.rouge_keys = rouge_keys
        self.use_stemmer = use_stemmer
        self.aggregator = RougeBatchAggregator()
        self.scorer = rouge_scorer.RougeScorer(rouge_keys, use_stemmer=self.use_stemmer)

        for key in rouge_keys:
            self.add_state(key, [])

    def update(self, pred_lns: List[str], tgt_lns: List[str]):
        for pred, tgt in zip(pred_lns, tgt_lns):
            # rougeLsum expects "\n" separated sentences within a summary
            if self.rouge_newline_sep:
                pred = add_newline_to_end_of_each_sentence(pred)
                tgt = add_newline_to_end_of_each_sentence(tgt)
            results = self.scorer.score(pred, tgt)
            for key, score in results.items():
                score = torch.tensor([score.precision, score.recall, score.fmeasure])
                getattr(self, key).append(score)

    def compute(self) -> Dict[str, float]:
        scores = {key: getattr(self, key) for key in self.rouge_keys}
        self.aggregator.add_scores(scores)
        result = self.aggregator.aggregate()
        return format_rouge_results(result)


class RougeBatchAggregator(scoring.BootstrapAggregator):

    def aggregate(self):
        """
        Override function to wrap the final results in `Score` objects.
        This is due to the scores being replaced with a list of torch tensors.
        """
        result = {}
        for score_type, scores in self._scores.items():
            # Stack scores into a 2-d matrix of (sample, measure).
            score_matrix = np.vstack(tuple(scores))
            # Percentiles are returned as (interval, measure).
            percentiles = self._bootstrap_resample(score_matrix)
            # Extract the three intervals (low, mid, high).
            intervals = tuple((Score(*percentiles[j, :]) for j in range(3)))
            result[score_type] = AggregateScore(low=intervals[0], mid=intervals[1], high=intervals[2])
        return result

    def add_scores(self, scores):
        self._scores = scores


def format_rouge_results(result: Dict[str, AggregateScore], decimal_places: int = 4) -> Dict[str, float]:
    flattened_result = {}
    for rouge_key, rouge_aggregate_score in result.items():
        for stat in ["precision", "recall", "fmeasure"]:
            mid = rouge_aggregate_score.mid
            score = round(getattr(mid, stat), decimal_places)
            flattened_result[f"{rouge_key}_{stat}"] = score
    return flattened_result
