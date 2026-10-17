.pragma library
// generated from build/schemes.py - do not edit
var schemes = [{"slug": "cathode", "name": "Cathode", "sel": "#064ed8", "title": [[0.0, "#01118d"], [0.45, "#064ed8"], [1.0, "#28aff3"]], "deskLight": "#008080", "deskDark": "#004848"}, {"slug": "brick", "name": "Brick", "sel": "#cc1010", "title": [[0.0, "#6b0404"], [0.45, "#cc1010"], [1.0, "#fa5e46"]], "deskLight": "#803030", "deskDark": "#421919"}, {"slug": "pumpkin", "name": "Pumpkin", "sel": "#ba590f", "title": [[0.0, "#6b3104"], [0.45, "#cc6210"], [1.0, "#faac46"]], "deskLight": "#805330", "deskDark": "#422b19"}, {"slug": "wheat", "name": "Wheat", "sel": "#91720b", "title": [[0.0, "#6b5304"], [0.45, "#cca010"], [1.0, "#fae846"]], "deskLight": "#806d30", "deskDark": "#423919"}, {"slug": "ember", "name": "Ember", "sel": "#cc3610", "title": [[0.0, "#6b1904"], [0.45, "#cc3610"], [1.0, "#fa8246"]], "deskLight": "#804030", "deskDark": "#422119"}, {"slug": "spruce", "name": "Spruce", "sel": "#0b8734", "title": [[0.0, "#046b27"], [0.45, "#10cc4f"], [1.0, "#46fa9a"]], "deskLight": "#30804b", "deskDark": "#194227"}, {"slug": "meadow", "name": "Meadow", "sel": "#4b850a", "title": [[0.0, "#3b6b04"], [0.45, "#74cc10"], [1.0, "#8efa46"]], "deskLight": "#5b8030", "deskDark": "#2f4219"}, {"slug": "marine", "name": "Marine", "sel": "#0b875d", "title": [[0.0, "#046b49"], [0.45, "#10cc8d"], [1.0, "#46fad6"]], "deskLight": "#308065", "deskDark": "#194235"}, {"slug": "teal", "name": "Teal", "sel": "#0b818f", "title": [[0.0, "#04616b"], [0.45, "#10b9cc"], [1.0, "#46d0fa"]], "deskLight": "#307880", "deskDark": "#193e42"}, {"slug": "plum", "name": "Plum", "sel": "#ad10cc", "title": [[0.0, "#5a046b"], [0.45, "#ad10cc"], [1.0, "#f446fa"]], "deskLight": "#723080", "deskDark": "#3b1942"}, {"slug": "eggplant", "name": "Eggplant", "sel": "#5b10cc", "title": [[0.0, "#2d046b"], [0.45, "#5b10cc"], [1.0, "#a646fa"]], "deskLight": "#503080", "deskDark": "#2a1942"}, {"slug": "rose", "name": "Rose", "sel": "#cc107b", "title": [[0.0, "#6b043f"], [0.45, "#cc107b"], [1.0, "#fa4694"]], "deskLight": "#80305d", "deskDark": "#421930"}, {"slug": "storm", "name": "Storm", "sel": "#101dcc", "title": [[0.0, "#040b6b"], [0.45, "#101dcc"], [1.0, "#5246fa"]], "deskLight": "#303680", "deskDark": "#191c42"}, {"slug": "slate", "name": "Slate", "sel": "#5e656b", "title": [[0.0, "#323538"], [0.45, "#676d73"], [1.0, "#bbc1c7"]], "deskLight": "#697480", "deskDark": "#2a2e33"}, {"slug": "spectrum", "name": "Spectrum", "sel": "#1450c8", "title": [[0.0, "#b40a14"], [0.22, "#d2640a"], [0.42, "#b49600"], [0.6, "#1e9628"], [0.8, "#1450c8"], [1.0, "#7a32d2"]], "deskLight": "#2e5478", "deskDark": "#12243a"}, {"slug": "sunset", "name": "Sunset", "sel": "#c0144e", "title": [[0.0, "#4a0a3e"], [0.4, "#c0144e"], [0.75, "#e8501e"], [1.0, "#ffa03c"]], "deskLight": "#7a3a4c", "deskDark": "#2e141c"}];

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
