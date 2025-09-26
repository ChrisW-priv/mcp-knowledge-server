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
    """Generate questions that can only be answered by the full section digest, not by individual subsections."""

    xml_content: str = dspy.InputField(desc="XML representation of the section digest")
    language: str = dspy.InputField(desc="Language for the questions")
    questions: list[str] = dspy.OutputField(
        desc="List of concise questions answerable only by the full section"
    )


class SectionDigestQuestionGenerator(dspy.Module):
    def __init__(self, xml_formatter: XML_FORMATTER | None = None):
        super().__init__()
        self.question_generator = dspy.ChainOfThought(GenerateUniqueQuestions)
        self.xml_formatter: XML_FORMATTER = xml_formatter or _default_xml_formatter

    def forward(self, section_dict: SECTION_DICT_T) -> dspy.Prediction:
        # Convert to XML representation using configured formatter
        xml_content = self.xml_formatter(section_dict)

        # Generate unique questions
        result = self.question_generator(
            xml_content=xml_content,
            language=section_dict.get("language", "en"),
        )

        return dspy.Prediction(
            xml_representation=xml_content,
            questions=result.questions,
        )


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
