import asyncio
from fast_agent import FastAgent
from pydantic import BaseModel
from typing import Any, Callable


SECTION_DICT_T = dict[str, str | dict[str, Any]]
XML_FORMATTER = Callable[
    [
        SECTION_DICT_T,
    ],
    str,
]


class Questions(BaseModel):
    questions: list[str]


# Updated requirements focusing on search-like queries
COMMON_REQUIREMENTS = """_search queries_ that should satisfy all of the following:

1. **Short and natural** - like actual user search queries (2-6 words typically)
2. **Keyword-focused** - use key terms from the content without complex sentence structure
3. **Answerable** by the full section content
4. **Varied specificity** - mix of general and specific terms
5. **Natural language** - how people actually search, not formal questions
6. **Include synonyms** - use alternative terms users might search with
7. **Cover main topics** - address different aspects of the content

Examples of BAD query: "What are the specific benefits that cloud computing provides to businesses?"
Examples of GOOD query: "cloud computing benefits" """

query_gen_agent = FastAgent("Evaluator-Optimizer")


@query_gen_agent.agent(
    name="generator",
    instruction=f"""Think of search queries that real users would type when
    looking for information covered in this section. Think like a search engine
    user - short, keyword-focused, natural language queries. Write
    {COMMON_REQUIREMENTS}

    Focus on generating queries that match how people actually search: - Use noun
    phrases and keyword combinations - Include both general and specific terms -
    Think about different ways users might phrase their search - Consider synonyms
    and alternative terminology - Generate queries of varying lengths (2-6 words
    typically)

    The queries should feel natural and be the kind of thing someone would type into
    a search box when looking for this information.""",
    use_history=True,
)
@query_gen_agent.agent(
    name="evaluator",
    instruction=f"""You are an expert at evaluating search query quality for RAG systems.

    You are given:
    1) The original section content
    2) A list of search queries generated for it

    Evaluate {COMMON_REQUIREMENTS}

    Rate the overall set as: EXCELLENT, GOOD, FAIR, or POOR

    Focus on whether these queries would have high semantic similarity to actual
    user searches while still being answerable by the content.""",
)
@query_gen_agent.evaluator_optimizer(
    name="query_refiner",
    generator="generator",
    evaluator="evaluator",
    min_rating="EXCELLENT",
    max_refinements=3,
)
async def generate_queries(text) -> Questions | None:
    async with query_gen_agent.run() as agent:
        questions, _ = await agent.query_refiner.structured(text, Questions)
        return questions


class QueryGenerator:
    def __init__(self, xml_formatter: XML_FORMATTER):
        self.xml_formatter = xml_formatter

    def __call__(self, section: SECTION_DICT_T) -> Questions | None:
        """Generate search queries for a given section."""
        section_digest = self.xml_formatter(section)
        return asyncio.run(generate_queries(section_digest))
