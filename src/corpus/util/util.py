import re


def parse_roman_chord(chord_str):
    """
    Parse Roman numeral chord string into fields.
    """
    pattern = r"^(?P<numeral>[#b]*[IVXivx]+)(?P<form>[oø\+Mmin%]*)(?P<figbass>\d+)?(?P<changes>\(.*\))?$"

    match = re.match(pattern, chord_str.strip())

    if not match:
        return {
            "numeral": chord_str,
            "form": "",
            "figbass": "",
            "changes": "",
        }

    data = match.groupdict()

    parsed_result = {
        "numeral": data["numeral"] or "",
        "form": data["form"] or "",
        "figbass": data["figbass"] or "",
        "changes": data["changes"].strip("()") if data["changes"] else "",
    }

    return parsed_result