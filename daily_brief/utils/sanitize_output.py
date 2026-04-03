import re

def sanitize_output(value: str) -> str:
    safe_output = re.sub(r"[^\w-]", "_", value)
    safe_output = safe_output.split('_')
    safe_output = "_".join(word for word in safe_output if word != "")
    return safe_output