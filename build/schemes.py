"""The Cathode colour schemes: one place that defines every colour variant.

Each scheme has a light and a dark version. Everything else (colour scheme
files, window-frame title bars, Start buttons, logos, previews, the Display
Properties app) is generated from this table.

To add a scheme: add an entry to SCHEMES and run ./build.sh.
"""
import colorsys

# slug: (display name, logo hue in degrees or a special mode, extra settings)
# Hues were sampled from the Cathode logo variants sheet.
SCHEMES = [
    ("cathode",  "Cathode",  dict(hue=215)),
    ("brick",    "Brick",    dict(hue=0, logo_hue=4)),
    ("pumpkin",  "Pumpkin",  dict(hue=26)),
    ("wheat",    "Wheat",    dict(hue=46, logo_hue=50)),
    ("ember",    "Ember",    dict(hue=12)),
    ("spruce",   "Spruce",   dict(hue=140)),
    ("meadow",   "Meadow",   dict(hue=88)),
    ("marine",   "Marine",   dict(hue=160)),
    ("teal",     "Teal",     dict(hue=186)),
    ("plum",     "Plum",     dict(hue=290)),
    ("eggplant", "Eggplant", dict(hue=264)),
    ("rose",     "Rose",     dict(hue=326)),
    ("storm",    "Storm",    dict(hue=236)),
    ("slate",    "Slate",    dict(hue=210, gray=True)),
    ("spectrum", "Spectrum", dict(logo="spectrum")),
    ("sunset",   "Sunset",   dict(logo="sunset")),
]

LOGO_BASE_HUE = 215   # hue of the original blue Cathode logo


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, max(0, min(1, s)), max(0, min(1, v)))
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def rgb(hexc):
    return tuple(int(hexc[i:i + 2], 16) for i in (1, 3, 5))


def lum(hexc):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(hexc)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def darken_until(c, against, ratio):
    """Darken colour c (keeping hue) until it reaches `ratio` contrast with `against`."""
    h, s, v = colorsys.rgb_to_hsv(*[x / 255 for x in rgb(c)])
    while contrast(hsv(h * 360, s, v), against) < ratio and v > 0.05:
        v -= 0.01
    return hsv(h * 360, s, v)


def lighten_until(c, against, ratio):
    h, s, v = colorsys.rgb_to_hsv(*[x / 255 for x in rgb(c)])
    while contrast(hsv(h * 360, s, v), against) < ratio and (v < 1 or s > 0):
        if v < 1:
            v = min(1, v + 0.01)
        else:
            s = max(0, s - 0.02)
    return hsv(h * 360, s, v)


def comma(hexc):
    return ",".join(str(x) for x in rgb(hexc))


def build(slug, name, opts):
    """Resolve every colour a scheme needs."""
    if slug == "cathode":
        # the original Cathode blue, exactly as designed
        title = [(0.0, "#01118d"), (0.45, "#064ed8"), (1.0, "#28aff3")]
        sel = "#064ed8"
        desk_light, desk_dark = "#008080", "#004848"
    elif opts.get("logo") == "spectrum":
        title = [(0.0, "#b40a14"), (0.22, "#d2640a"), (0.42, "#b49600"), (0.6, "#1e9628"),
                 (0.8, "#1450c8"), (1.0, "#7a32d2")]
        sel = "#1450c8"
        desk_light, desk_dark = "#2e5478", "#12243a"
    elif opts.get("logo") == "sunset":
        title = [(0.0, "#4a0a3e"), (0.4, "#c0144e"), (0.75, "#e8501e"), (1.0, "#ffa03c")]
        sel = "#c0144e"
        desk_light, desk_dark = "#7a3a4c", "#2e141c"
    elif opts.get("gray"):
        h = opts["hue"]
        title = [(0.0, hsv(h, 0.10, 0.22)), (0.45, hsv(h, 0.10, 0.45)), (1.0, hsv(h, 0.06, 0.78))]
        sel = hsv(h, 0.12, 0.42)
        desk_light, desk_dark = hsv(h, 0.18, 0.50), hsv(h, 0.18, 0.20)
    else:
        h = opts["hue"]
        title = [(0.0, hsv(h, 0.96, 0.42)), (0.45, hsv(h, 0.92, 0.80)), (1.0, hsv(h + 8, 0.72, 0.98))]
        sel = hsv(h, 0.92, 0.80)
        desk_light, desk_dark = hsv(h, 0.62, 0.50), hsv(h, 0.62, 0.26)

    deep, tip = title[0][1], title[-1][1]
    sel = darken_until(sel, "#ffffff", 4.5)          # white text on selections
    link_light = darken_until(sel, "#f4f3ef", 4.5)   # links on off-white
    link_dark = lighten_until(tip, "#2a2a2a", 4.5)   # links on dark views
    return dict(slug=slug, name=name, title=title, deep=deep, tip=tip, sel=sel,
                link_light=link_light, link_dark=link_dark,
                desk_light=desk_light, desk_dark=desk_dark, opts=opts)


ALL = [build(*s) for s in SCHEMES]
BY_SLUG = {s["slug"]: s for s in ALL}


def theme_id(slug, dark):
    """Theme/colour-scheme id. The standard blue keeps the original ids."""
    base = "Cathode98" if slug == "cathode" else "Cathode98" + slug.capitalize()
    return base + ("Dark" if dark else "")


def theme_name(slug, dark):
    name = "Cathode 98" if slug == "cathode" else "Cathode 98 " + BY_SLUG[slug]["name"]
    return name + (" Dark" if dark else "")


JS_FUNCS = """
// Find the scheme from its selection colour (Kirigami/SystemPalette highlight).
function scheme(c) {
    var best = schemes[0], bd = 1e9;
    for (var i = 0; i < schemes.length; i++) {
        var h = schemes[i].sel;
        var r = parseInt(h.substr(1, 2), 16) / 255, g = parseInt(h.substr(3, 2), 16) / 255, b = parseInt(h.substr(5, 2), 16) / 255;
        var d = (r - c.r) * (r - c.r) + (g - c.g) * (g - c.g) + (b - c.b) * (b - c.b);
        if (d < bd) { bd = d; best = schemes[i]; }
    }
    return bd < 0.01 ? best : schemes[0];
}

// Gradient stop i of 6 (padded with the last stop). reverse: lightest first.
function stop(c, i, reverse) {
    var t = scheme(c).title.slice();
    if (reverse) t.reverse();
    var s = t[Math.min(i, t.length - 1)];
    var pos = i < t.length ? (reverse ? 1 - s[0] : s[0]) : 1.0;
    return { position: pos, color: s[1] };
}
"""


def js_library():
    """QML JavaScript library with the scheme table (used by Cathode Start and the shell screens)."""
    import json
    table = [{"slug": x["slug"], "name": x["name"], "sel": x["sel"], "title": [[p, c] for p, c in x["title"]],
              "deskLight": x["desk_light"], "deskDark": x["desk_dark"]} for x in ALL]
    return (".pragma library\n// generated from build/schemes.py - do not edit\n"
            "var schemes = " + json.dumps(table) + ";\n" + JS_FUNCS)


def app_table():
    """What Cathode Display Properties needs to know about each scheme."""
    return [{"slug": x["slug"], "name": x["name"],
             "light": theme_id(x["slug"], False), "dark": theme_id(x["slug"], True),
             "icons": "Cathode" if x["slug"] == "cathode" else "Cathode-" + x["name"],
             "deskLight": x["desk_light"], "deskDark": x["desk_dark"], "sel": x["sel"]} for x in ALL]


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["--json"]:
        import json
        with open(sys.argv[2], "w") as f:
            json.dump(app_table(), f, indent=1)
        sys.exit(0)
    if sys.argv[1:2] == ["--js"]:
        with open(sys.argv[2], "w") as f:
            f.write(js_library())
        sys.exit(0)
    for s in ALL:
        print(f'{s["slug"]:9} sel {s["sel"]} ({contrast(s["sel"], "#ffffff"):.1f}:1)  '
              f'title {s["deep"]}->{s["tip"]}  desk {s["desk_light"]}/{s["desk_dark"]}  '
              f'links {s["link_light"]}/{s["link_dark"]}')
