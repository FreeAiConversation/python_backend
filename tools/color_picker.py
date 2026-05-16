"""
Tool: Color Picker
Route: GET /api/color-picker
"""
import colorsys
from flask import Blueprint, request, jsonify

bp = Blueprint("color_picker", __name__)

def _ok(data):  return jsonify({"success": True, **data}), 200
def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code


def _hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def _rgb_to_hex(r, g, b) -> str: return f"#{r:02X}{g:02X}{b:02X}"

def _rgb_to_hsl(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return round(h*360, 1), round(s*100, 1), round(l*100, 1)

def _hsl_to_rgb(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h/360, l/100, s/100)
    return int(r*255), int(g*255), int(b*255)

def _rgb_to_hsv(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    return round(h*360, 1), round(s*100, 1), round(v*100, 1)

def _rgb_to_cmyk(r, g, b):
    if r == g == b == 0: return 0.0, 0.0, 0.0, 100.0
    r_, g_, b_ = r/255, g/255, b/255
    k = 1 - max(r_, g_, b_)
    if k == 1: return 0.0, 0.0, 0.0, 100.0
    return (round((1-r_-k)/(1-k)*100, 1), round((1-g_-k)/(1-k)*100, 1),
            round((1-b_-k)/(1-k)*100, 1), round(k*100, 1))

def _luminance(r, g, b):
    def lin(c):
        c /= 255
        return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4
    return 0.2126*lin(r) + 0.7152*lin(g) + 0.0722*lin(b)

def _contrast(c1, c2):
    l1, l2 = _luminance(*c1), _luminance(*c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return round((lighter+0.05)/(darker+0.05), 2)

def _generate_shades(hex_color: str, steps: int = 10) -> list:
    r, g, b = _hex_to_rgb(hex_color)
    h, s, l = _rgb_to_hsl(r, g, b)
    shades  = []
    for i in range(steps):
        lightness = round(5 + (90 / (steps - 1)) * i, 1)
        sr, sg, sb = _hsl_to_rgb(h, s, lightness)
        shades.append({
            "hex":        _rgb_to_hex(sr, sg, sb),
            "hsl":        f"hsl({h}, {s}%, {lightness}%)",
            "rgb":        f"rgb({sr}, {sg}, {sb})",
            "lightness":  lightness,
            "text_color": "#000000" if _luminance(sr, sg, sb) > 0.179 else "#FFFFFF",
            "is_original": abs(lightness - l) < (45 / steps),
        })
    return shades

def _analyze_color(hex_color: str, shades: int = 10) -> dict:
    if not hex_color.startswith("#"): hex_color = "#" + hex_color
    r, g, b   = _hex_to_rgb(hex_color)
    h, s, l   = _rgb_to_hsl(r, g, b)
    hv, sv, v = _rgb_to_hsv(r, g, b)
    c, m, y, k= _rgb_to_cmyk(r, g, b)
    lum       = _luminance(r, g, b)
    cr_w = _contrast((r,g,b), (255,255,255))
    cr_b = _contrast((r,g,b), (0,0,0))
    def hshift(deg): return _rgb_to_hex(*_hsl_to_rgb((h+deg)%360, s, l))
    return {
        "hex":  hex_color.upper(), "rgb": f"rgb({r}, {g}, {b})",
        "rgba": f"rgba({r}, {g}, {b}, 1)", "hsl": f"hsl({h}, {s}%, {l}%)",
        "hsv":  f"hsv({hv}, {sv}%, {v}%)", "cmyk": f"cmyk({c}%, {m}%, {y}%, {k}%)",
        "rgb_raw":  {"r": r, "g": g, "b": b}, "hsl_raw": {"h": h, "s": s, "l": l},
        "hsv_raw":  {"h": hv, "s": sv, "v": v}, "cmyk_raw": {"c": c, "m": m, "y": y, "k": k},
        "brightness": "light" if lum > 0.179 else "dark", "luminance": round(lum, 4),
        "contrast_vs_white": cr_w, "contrast_vs_black": cr_b,
        "wcag_aa_white": "pass" if cr_w >= 4.5 else ("pass-large" if cr_w >= 3 else "fail"),
        "wcag_aa_black": "pass" if cr_b >= 4.5 else ("pass-large" if cr_b >= 3 else "fail"),
        "best_text": "#000000" if lum > 0.179 else "#FFFFFF",
        "palette": {
            "complementary": hshift(180),
            "triadic":   [hshift(120), hshift(240)],
            "analogous": [hshift(30), hshift(-30)],
            "split_comp":[hshift(150), hshift(210)],
            "tint":  _rgb_to_hex(*_hsl_to_rgb(h, s, min(90, l+30))),
            "shade": _rgb_to_hex(*_hsl_to_rgb(h, s, max(10, l-30))),
            "muted": _rgb_to_hex(*_hsl_to_rgb(h, max(0, s-40), l)),
            "vibrant":_rgb_to_hex(*_hsl_to_rgb(h, min(100, s+30), l)),
        },
        "shades": _generate_shades(hex_color, shades),
    }


@bp.route("/api/color-picker", methods=["GET"])
def route_color_picker():
    color  = request.args.get("color", "#667eea")
    shades = int(request.args.get("shades", 10))
    try:
        return _ok(_analyze_color(color, shades))
    except Exception as e:
        return _err(str(e))
