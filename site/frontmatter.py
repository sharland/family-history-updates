"""Read the front matter at the top of an item or post file.

The format is deliberately tiny: a block between two lines of '---',
'key: value' lines, and list values as following lines starting '- '.
No YAML library, so no surprises.
"""


def parse(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    meta: dict = {}
    key = None
    i = 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---":
            i += 1
            break
        stripped = line.strip()
        if stripped.startswith("- ") and key is not None:
            current = meta.get(key, "")
            if isinstance(current, str):
                current = [current] if current else []
            current.append(stripped[2:].strip())
            meta[key] = current
        elif ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            meta[key] = value.strip()
        i += 1
    body = "\n".join(lines[i:]).lstrip("\n")
    if text.endswith("\n") and body and not body.endswith("\n"):
        body += "\n"
    return meta, body
