from typing import Any, Callable
import dspy


SECTION_DICT_T = dict[str, str | dict[str, Any]]
XML_FORMATTER = Callable[
    [
        SECTION_DICT_T,
    ],
    str,
]


class GenerateUniqueQuestions(dspy.Signature):
    """Generate questions that can only be answered by the full section digest,
    not by individual subsections. Do not generate questions that are too
    generic or do not directly address the content. Also, ensure that the
    questions are grammatically correct and coherent, as well as concise and
    specific. Questions should be written in the language specified. Be sure
    question include relevant keywords from the section digest."""

    section_digest_xml: str = dspy.InputField(
        desc="XML representation of the section digest"
    )
    language: str = dspy.InputField(desc="Language for the questions")
    questions: list[str] = dspy.OutputField(
        desc="List of concise questions answerable only by the full section"
    )


class EvaluateGeneratedQuestions(dspy.Signature):
    """Decide if the generated questions are relevant to the section digest they
    were proposed for. Correct questions if they are not relevant, too generic,
    or do not directly address the content. Also, ensure that the questions are
    grammatically correct and coherent, as well as concise and specific.
    Questions should be written in the language specified. Be sure question
    include relevant keywords from the section digest."""

    section_digest_xml: str = dspy.InputField(
        desc="XML representation of the section digest"
    )
    language: str = dspy.InputField(desc="Language for the questions")
    questions: list[str] = dspy.InputField(
        desc="List of questions generated originally"
    )
    better_questions: list[str] = dspy.OutputField(
        desc="List of questions that are improved compared to the original"
    )


class SectionDigestQuestionGenerator(dspy.Module):
    def __init__(
        self,
        xml_formatter: XML_FORMATTER | None = None,
        correction_turns: int | None = None,
    ):
        super().__init__()
        self.question_generator = dspy.ChainOfThought(GenerateUniqueQuestions)
        self.question_evaluator = dspy.ChainOfThought(EvaluateGeneratedQuestions)
        self.xml_formatter: XML_FORMATTER = xml_formatter or _default_xml_formatter
        self.correction_turns: int = correction_turns or 2

    def forward(self, section_dict: SECTION_DICT_T) -> dspy.Prediction:
        # Convert to XML representation using configured formatter
        section_digest_xml = self.xml_formatter(section_dict)

        # Generate unique questions
        prediction = self.question_generator(
            section_digest_xml=section_digest_xml,
            language=section_dict.get("language", "en"),
        )
        questions = prediction.questions

        for _ in range(self.correction_turns):
            prediction = self.question_evaluator(
                section_digest_xml=section_digest_xml,
                questions=questions,
                language=section_dict.get("language", "en"),
            )
            questions = prediction.better_questions

        return dspy.Prediction(questions=questions)


def get_section_digest_question_generator(xml_formatter: XML_FORMATTER | None = None):
    return SectionDigestQuestionGenerator(xml_formatter)


def _default_xml_formatter(section_dict: SECTION_DICT_T):
    """Default XML formatter - can be replaced with custom formatters."""
    section_digest = section_dict["section_digest"]

    xml_parts = [f"<section title='{section_digest.get('title', '')}'>"]
    xml_parts.append(f"<text>{section_digest.get('text', '')}</text>")

    subsections = section_digest.get("subsections", [])
    if subsections:
        xml_parts.append("<subsections>")
        for subsection in subsections:
            xml_parts.append(f"<subsection title='{subsection.get('title', '')}'>")
            xml_parts.append(f"<text>{subsection.get('text', '')}</text>")
            xml_parts.append("</subsection>")
        xml_parts.append("</subsections>")

    xml_parts.append("</section>")
    return "\n".join(xml_parts)


def _hierarchical_xml_formatter(section_dict: SECTION_DICT_T):
    """Alternative XML formatter with more hierarchy."""
    section_digest = section_dict["section_digest"]
    language = section_dict.get("language", "en")

    xml_parts = [f"<document language='{language}'>"]
    xml_parts.append("<main_section>")
    xml_parts.append(f"<title>{section_digest.get('title', '')}</title>")
    xml_parts.append(f"<content>{section_digest.get('text', '')}</content>")

    subsections = section_digest.get("subsections", [])
    if subsections:
        for i, subsection in enumerate(subsections, 1):
            xml_parts.append(f"<subsection_{i}>")
            xml_parts.append(f"<title>{subsection.get('title', '')}</title>")
            xml_parts.append(f"<content>{subsection.get('text', '')}</content>")
            xml_parts.append(f"</subsection_{i}>")

    xml_parts.append("</main_section>")
    xml_parts.append("</document>")
    return "\n".join(xml_parts)


def _flat_xml_formatter(section_dict: SECTION_DICT_T):
    """Flat XML formatter."""
    section_digest = section_dict["section_digest"]

    xml_parts = []
    xml_parts.append(
        f"<main>{section_digest.get('title', '')}: {section_digest.get('text', '')}</main>"
    )

    subsections = section_digest.get("subsections", [])
    for subsection in subsections:
        xml_parts.append(
            f"<sub>{subsection.get('title', '')}: {subsection.get('text', '')}</sub>"
        )

    return "\n".join(xml_parts)
