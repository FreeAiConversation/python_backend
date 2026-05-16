"""
Tool: Word Counter
Route: POST /api/word-counter
"""
import re
from collections import Counter
from flask import Blueprint, request, jsonify

bp = Blueprint("word_counter", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code

_STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "by","from","as","is","was","are","were","be","been","have","has","had",
    "do","did","will","would","could","should","this","that","these","those",
    "i","you","he","she","it","we","they","my","your","his","her","its",
    "not","no","so","if","up","out","what","which","who","than","more",
}

def _analyze_text(text: str, top_n: int = 10) -> dict:
    words   = re.findall(r'\b\w+\b', text)
    wc      = len(words)
    wl      = [w.lower() for w in words]
    sents   = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text.strip())
    sents   = [s for s in sents if s.strip()]
    sc      = max(1, len(sents))
    paras   = [p for p in re.split(r'\n\s*\n', text.strip()) if p.strip()]
    filtered = [w for w in wl if w not in _STOPWORDS and len(w) > 1]
    top     = Counter(filtered).most_common(top_n)

    def syl(w):
        w = re.sub(r'[^a-z]', '', w.lower())
        c = len(re.findall(r'[aeiouy]+', w))
        if w.endswith('e') and not w.endswith('le'): c -= 1
        return max(1, c)

    tot_syl = sum(syl(w) for w in words)
    flesch  = round(206.835 - 1.015*(wc/sc) - 84.6*(tot_syl/wc), 1) if wc and sc else 0
    flesch  = max(0, min(100, flesch))

    def rt(wpm):
        s = int(wc / wpm * 60)
        return f"{s//60}m {s%60}s" if s >= 60 else f"{s}s"

    return {
        "word_count":             wc,
        "unique_words":           len(set(wl)),
        "sentence_count":         sc,
        "paragraph_count":        max(1, len(paras)),
        "chars_total":            len(text),
        "chars_no_spaces":        len(text.replace(" ", "")),
        "letters_only":           len(re.sub(r'[^a-zA-Z]', '', text)),
        "digits_only":            len(re.sub(r'[^0-9]', '', text)),
        "avg_word_length":        round(len(re.sub(r'[^a-zA-Z]','',text)) / wc, 1) if wc else 0,
        "avg_words_per_sentence": round(wc / sc, 1),
        "total_syllables":        tot_syl,
        "flesch_ease":            flesch,
        "readability":            ("Easy" if flesch>=70 else "Moderate" if flesch>=50 else
                                   "Difficult" if flesch>=30 else "Very Difficult"),
        "reading_time_slow":      rt(150),
        "reading_time_average":   rt(238),
        "reading_time_fast":      rt(400),
        "speaking_time":          rt(130),
        "top_words":              [{"word": w, "count": c} for w, c in top],
    }


@bp.route("/api/word-counter", methods=["POST"])
def route_word_counter():
    body  = request.get_json(silent=True) or {}
    text  = body.get("text", "")
    top_n = int(body.get("top_n", 10))
    if not text: return _err("No text provided.")
    try:
        return _ok(_analyze_text(text, top_n))
    except Exception as e:
        return _err(str(e))
