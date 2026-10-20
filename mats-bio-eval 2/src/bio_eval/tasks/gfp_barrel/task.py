"""One fresh context per beta-strand residue. No tools."""

from inspect_ai import Task, task
from inspect_ai.log import HeadlineMetric
from inspect_ai.model import GenerateConfig
from inspect_ai.solver import generate, system_message

from bio_eval.tasks.gfp_barrel.dataset import build_dataset
from bio_eval.tasks.gfp_barrel.prompts import SYSTEM_PROMPT
from bio_eval.tasks.gfp_barrel.scorer import orientation_scorer


@task
def gfp_barrel_orientation(subset: str = "all") -> Task:
    return Task(
        dataset=build_dataset(subset),
        solver=[system_message(SYSTEM_PROMPT), generate()],
        scorer=orientation_scorer(),
        config=GenerateConfig(max_tokens=256),
        headline_metric=HeadlineMetric(metric="robust_accuracy"),
    )
