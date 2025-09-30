from typing import Any, Callable


SECTION_DICT_T = dict[str, str | dict[str, Any]]
XML_FORMATTER = Callable[
    [
        SECTION_DICT_T,
    ],
    str,
]


def default_xml_formatter(section_dict: SECTION_DICT_T):
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


def hierarchical_xml_formatter(section_dict: SECTION_DICT_T):
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


def flat_xml_formatter(section_dict: SECTION_DICT_T):
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
