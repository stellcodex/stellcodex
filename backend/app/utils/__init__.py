import string


def revision_label(index: int) -> str:
    alphabet = string.ascii_uppercase
    if index < 26:
        return alphabet[index]
    first = alphabet[(index // 26) - 1]
    second = alphabet[index % 26]
    return f"{first}{second}"
