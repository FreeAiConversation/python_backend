"""
Tool: Password Generator
Route: GET /api/password-generator
"""
import math
import string
import secrets
from flask import Blueprint, request, jsonify

bp = Blueprint("password_generator", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code


def _count_charset(password: str) -> int:
    pool = 0
    if any(c.islower() for c in password): pool += 26
    if any(c.isupper() for c in password): pool += 26
    if any(c.isdigit() for c in password): pool += 10
    if any(not c.isalnum() for c in password): pool += 32
    return max(pool, 1)

def _get_strength(password: str) -> dict:
    n       = len(password)
    charset_size = _count_charset(password)
    entropy = n * math.log2(charset_size)
    
    # Brute force estimates
    # Offline: 100 billion guesses/sec
    # Online: 1000 guesses/sec (optimistic)
    total_combinations = charset_size ** n
    crack_time_offline_sec = total_combinations / (10**11)
    crack_time_online_sec = total_combinations / 1000

    COMMON  = ("1234", "abcd", "qwerty", "password")
    lp      = password.lower()
    if entropy < 28:   score, label = 0, "Very Weak"
    elif entropy < 36: score, label = 1, "Weak"
    elif entropy < 60: score, label = 2, "Fair"
    elif entropy < 80: score, label = 3, "Strong"
    else:              score, label = 4, "Very Strong"
    
    COMMON  = ("1234", "abcd", "qwerty", "password")
    lp      = password.lower()
    if any(s in lp for s in COMMON): score = max(0, score - 1)

    # Detected character sets
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    return {
        "score": score, 
        "label": label, 
        "entropy_bits": round(entropy, 2),
        "crack_time_offline": crack_time_offline_sec,
        "crack_time_online": crack_time_online_sec,
        "charset_diversity": {
            "uppercase": has_upper,
            "lowercase": has_lower,
            "digits": has_digit,
            "special": has_special
        }
    }

def _generate_password(
    length=16, use_uppercase=True, use_lowercase=True,
    use_digits=True, use_special=True,
    special_chars="!@#$%^&*()-_=+", exclude_chars="",
) -> str:
    def filt(chars): return "".join(c for c in chars if c not in exclude_chars)
    uppers   = filt(string.ascii_uppercase)
    lowers   = filt(string.ascii_lowercase)
    digits   = filt(string.digits)
    specials = filt(special_chars)
    pool, musts = "", []
    if use_uppercase and uppers: pool += uppers; musts.append(secrets.choice(uppers))
    if use_lowercase and lowers: pool += lowers; musts.append(secrets.choice(lowers))
    if use_digits    and digits:  pool += digits;  musts.append(secrets.choice(digits))
    if use_special   and specials: pool += specials; musts.append(secrets.choice(specials))
    if not pool: raise ValueError("Empty character pool")
    chars = musts + [secrets.choice(pool) for _ in range(length - len(musts))]
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)


@bp.route("/api/password-generator", methods=["GET"])
def route_password_generator():
    try:
        length = int(request.args.get("length", 16))
        count  = int(request.args.get("count", 1))
        uppercase = request.args.get("uppercase", "true").lower() == "true"
        lowercase = request.args.get("lowercase", "true").lower() == "true"
        digits    = request.args.get("digits",    "true").lower() == "true"
        special   = request.args.get("special",   "true").lower() == "true"
        exclude   = request.args.get("exclude",   "")
        passwords = []
        for _ in range(min(count, 50)):
            pwd = _generate_password(
                length=length, use_uppercase=uppercase, use_lowercase=lowercase,
                use_digits=digits, use_special=special, exclude_chars=exclude,
            )
            passwords.append({"password": pwd, "strength": _get_strength(pwd)})
        return _ok({"passwords": passwords, "count": len(passwords), "length": length})
    except Exception as e:
        return _err(str(e))
