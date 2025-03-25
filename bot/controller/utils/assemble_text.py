def assemble_text(text, **substitutions: str) -> str:
    """
    Replaces placeholders in the given text with the provided values.

    :param text: The text containing placeholders to replace.
    :type text: str
    :param substitutions: The dictionary containing key-value pairs for replacing placeholders.
        Each key represents a placeholder, and the corresponding value is the replacement.
    :type substitutions: dict
    :return: The text with replaced placeholders.
    :rtype: str
    """
    for key, value in substitutions.items():
        text = text.replace(f'{{{key}}}', value)

    return text.strip()

