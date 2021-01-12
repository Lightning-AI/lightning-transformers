from dataclasses import dataclass
from typing import Optional

from lightning_transformers.core.config import HydraConfig, OptimizerConfig, SchedulerConfig
from lightning_transformers.core.data import TransformerDataConfig


@dataclass
class HFTransformerDataConfig(TransformerDataConfig):
    dataset_name: Optional[str] = None
    train_val_split: Optional[int] = None
    train_file: Optional[str] = None
    validation_file: Optional[str] = None
    padding: str = "max_length"
    truncation: str = "only_first"
    max_length: int = 128
    preprocessing_num_workers: int = 8
    load_from_cache_file: bool = True
    dataset_config_name: Optional[str] = None


@dataclass
class HFTokenizerConfig(HydraConfig):
    pretrained_model_name_or_path: Optional[str] = None
    use_fast: bool = True


@dataclass
class HFBackboneConfig(HydraConfig):
    downstream_model_type: Optional[str] = None
    pretrained_model_name_or_path: Optional[str] = None


@dataclass
class HFSchedulerConfig(SchedulerConfig):
    num_training_steps: int = -1
    num_warmup_steps: float = 0.1


@dataclass
class HFTaskConfig(HydraConfig):
    backbone: HFBackboneConfig = HFBackboneConfig()
    optimizer: OptimizerConfig = OptimizerConfig()
    scheduler: HFSchedulerConfig = HFSchedulerConfig()
