"""Agent task: one orientation tool, no fluorescence lookup."""

from inspect_ai import Task, task
from inspect_ai.agent import AgentPrompt, react
from inspect_ai.log import HeadlineMetric
from inspect_ai.model import GenerateConfig

from bio_eval.tasks.gfp_tolerant_site.dataset import build_dataset
from bio_eval.tasks.gfp_tolerant_site.prompts import SYSTEM_PROMPT
from bio_eval.tasks.gfp_tolerant_site.scorer import tolerant_site_scorer
from bio_eval.tasks.gfp_tolerant_site.tools import residue_orientation


@task
def gfp_tolerant_site() -> Task:
    return Task(
        dataset=build_dataset(),
        solver=react(
            prompt=AgentPrompt(
                instructions=SYSTEM_PROMPT,
                handoff_prompt=None,
                assistant_prompt=None,
                submit_prompt=None,
            ),
            tools=[residue_orientation()],
            submit=False,
        ),
        scorer=tolerant_site_scorer(),
        config=GenerateConfig(max_tokens=512),
        message_limit=24,
        headline_metric=HeadlineMetric(metric="accuracy"),
    )
