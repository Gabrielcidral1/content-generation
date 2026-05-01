from inspect_ai.model import ModelOutput
from inspect_ai.solver import TaskState, solver

from content_generation.generator import ContentGeneratorBase
from content_generation.models import PropertyData


@solver
def content_generation_solver(generator: ContentGeneratorBase):
    """Calls the content generator and stores the result in state output + metadata."""

    async def solve(state: TaskState, generate) -> TaskState:
        property_data = PropertyData.model_validate(state.metadata["property"])
        content = generator.generate(property_data)

        state.output = ModelOutput.from_content(
            model="content-generator",
            content=content.model_dump_json(),
        )
        state.metadata["generated"] = content.model_dump()
        return state

    return solve
