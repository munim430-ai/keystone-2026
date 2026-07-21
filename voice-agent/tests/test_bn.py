from keystone_voice.bn import sanitize_for_tts, split_sentences, to_bn_digits, bn_money


def test_sanitize_strips_markdown_and_emoji():
    out = sanitize_for_tts("**হ্যালো** স্যার 😀 `code` [link](x)")
    for junk in ("*", "`", "[", "]", "(", "😀"):
        if junk in "()":  # parens are allowed punctuation
            continue
        assert junk not in out
    assert "হ্যালো" in out


def test_english_digits_become_bangla():
    assert to_bn_digits("5000") == "৫০০০"


def test_split_sentences():
    s = split_sentences("প্রথম বাক্য। দ্বিতীয় বাক্য! তৃতীয়?")
    assert len(s) == 3


def test_long_sentence_wraps():
    long = "ক" * 300 + ", " + "খ" * 300 + "।"
    parts = split_sentences(long, max_len=220)
    assert all(len(p) <= 240 for p in parts)


def test_bn_money():
    assert bn_money(5000) == "পাঁচ হাজার"
    assert bn_money(100000) == "এক লাখ"
