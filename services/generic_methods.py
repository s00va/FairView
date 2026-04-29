import re


def getWordCount(txtIn: str) -> int:
    """
    Get the number of words in a string.

    Args:
        txtIn (str): The text to compute word count.

    Returns:
        int: The number of words in txtIn.
    """
    return len(re.findall(r"\w+", txtIn))
