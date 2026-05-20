import re

def summarize_text(text: str, max_sentences: int = 6, max_words: int = 180) -> str:  # Uses simple sentence extraction
    if not text or not text.strip():
        return "No content available to summarize."

    cleaned = " ".join(text.split())

    boilerplate = [
        r"Page last reviewed.*",
        r"Next review due.*",
        r"Menu Search the NHS website.*",
        r"Home Health A to Z.*",
        r"Support links.*",
        r"Help us improve.*",
        r"NHS website.*",
        r"Find out more about.*cookies.*",
        r"We use cookies.*",
        r"You must accept.*cookies.*",
        r"GOV\.UK",
    ]
    
    for pattern in boilerplate:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    cleaned = " ".join(cleaned.split())

    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", cleaned)

    good_sentences = []
    for s in raw_sentences:
        s = s.strip()
        word_count = len(s.split())

        if word_count < 6 or word_count > 60:
            continue

        if re.match(r"^(Menu|Home|Skip|Back|Next|Previous|Contents|Overview|On this page)", s, re.IGNORECASE):
            continue

        words = s.split()
        cap_ratio = sum(1 for w in words if w[0].isupper()) / len(words)
        if cap_ratio > 0.6 and len(words) < 10:
            continue

        good_sentences.append(s)

    if not good_sentences:
        words = cleaned.split()
        return " ".join(words[:max_words]) + ("..." if len(words) > max_words else "")

    selected = good_sentences[:max_sentences]
    summary = " ".join(selected)

    words = summary.split()
    if len(words) > max_words:
        summary = " ".join(words[:max_words]) + "..."

    return summary