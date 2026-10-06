#!/usr/bin/env python3
"""Build the Krastin CFO Partners website into ./_site.

Uses only the Python standard library. Text comes from content/*.json; layout lives here.

    python build.py                      # build with settings from content/site.json
    python build.py --serve              # build, then preview at http://localhost:8000
    python build.py --site-url URL --base-path /repo   # used by the GitHub Pages workflow
"""
import argparse
import hashlib
import html
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"
LANGS = ("en", "lv")
LOCALE = {"en": "en_GB", "lv": "lv_LV"}

# ---------------------------------------------------------------- design data (not copy)

AREA_ORDER_HOME = ["modelling", "profitability", "finance", "ma"]       # home, about, footer, contact select
AREA_ORDER_SERVICES = ["modelling", "profitability", "ma", "finance"]   # services page tiles
AREA_ICONS = {"modelling": "trending-up", "profitability": "layers", "finance": "calculator", "ma": "briefcase"}
STEP_ICONS = ["messages-square", "split", "file-text", "handshake"]
CIRCLE = "M70 6 A54 54 0 1 1 69.99 6 Z"

# Lucide 0.454.0 icon bodies (ISC licence)
ICONS = {
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "trending-up": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "layers": '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
    "calculator": '<rect width="16" height="20" x="4" y="2" rx="2"/><line x1="8" x2="16" y1="6" y2="6"/><line x1="16" x2="16" y1="14" y2="18"/><path d="M16 10h.01"/><path d="M12 10h.01"/><path d="M8 10h.01"/><path d="M12 14h.01"/><path d="M8 14h.01"/><path d="M12 18h.01"/><path d="M8 18h.01"/>',
    "briefcase": '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "menu": '<line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/>',
    "messages-square": '<path d="M14 9a2 2 0 0 1-2 2H6l-4 4V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2z"/><path d="M18 9h2a2 2 0 0 1 2 2v11l-4-4h-6a2 2 0 0 1-2-2v-1"/>',
    "split": '<path d="M16 3h5v5"/><path d="M8 3H3v5"/><path d="M12 22v-8.3a4 4 0 0 0-1.172-2.872L3 3"/><path d="m15 9 6-6"/>',
    "file-text": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "handshake": '<path d="m11 17 2 2a1 1 0 1 0 3-3"/><path d="m14 14 2.5 2.5a1 1 0 1 0 3-3l-3.88-3.88a3 3 0 0 0-4.24 0l-.88.88a1 1 0 1 1-3-3l2.81-2.81a5.79 5.79 0 0 1 7.06-.87l.47.28a2 2 0 0 0 1.42.25L21 4"/><path d="m21 3 1 11h-2"/><path d="M3 3 2 14l6.5 6.5a1 1 0 1 0 3-3"/><path d="M3 4h8"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
}

# Line illustrations for the case studies (from Insights.screen.js)
CASE_ART = {
    "carve-out": [
        ("M30 58 C70 54 130 57 176 56 C178 90 177 130 179 162 C130 165 72 163 32 164 C29 128 31 92 30 58 Z", "ink"),
        ("M120 57 C122 80 118 104 121 124 C140 123 160 125 178 124", "grey"),
        ("M204 64 C224 62 248 63 270 62 C272 80 271 98 272 114 C250 116 226 115 205 116 C203 98 204 80 204 64 Z", "ink"),
        ("M150 90 C166 84 180 92 196 88", "ink"),
        ("M188 81 L197 88 L189 96", "ink"),
        ("M46 84 C62 83 80 85 96 84 M46 104 C60 103 74 105 88 104 M46 124 C66 123 86 125 104 124", "grey"),
        ("M218 138 C236 136 252 138 268 137 C269 146 268 154 268 160 C252 162 234 161 219 162 C217 154 218 146 218 138 Z", "grey"),
        ("M236 116 C237 124 236 130 238 137", "grey"),
    ],
    "long-term-plan": [
        ("M28 164 C100 166 200 162 274 164", "grey"),
        ("M44 160 L44 168 M100 160 L100 168 M156 160 L156 168 M212 160 L212 168 M268 160 L268 168", "grey"),
        ("M44 134 C70 128 92 126 116 116 C146 104 168 98 196 84 C222 72 246 64 270 50", "ink"),
        ("M150 106 C184 98 220 98 270 86", "grey"),
        ("M150 106 C180 88 214 60 268 30", "grey"),
        ("M262 44 L271 50 L262 57", "ink"),
        ("M44 134 C46 131 50 131 51 135 C52 139 47 140 45 137 Z M116 116 C118 113 122 113 123 117 C124 121 119 122 117 119 Z M196 84 C198 81 202 81 203 85 C204 89 199 90 197 87 Z", "ink"),
    ],
    "unit-cost": [
        ("M34 64 C70 62 110 63 146 62 C148 98 147 134 148 166 C110 168 70 167 35 168 C32 132 34 98 34 64 Z", "ink"),
        ("M34 100 C72 99 110 101 147 100 M34 134 C72 133 110 135 147 134 M90 63 C92 98 89 132 91 167", "grey"),
        ("M58 76 C60 74 64 74 65 77 M112 112 C114 110 118 110 119 113", "grey"),
        ("M186 166 C186 150 187 132 186 118 C194 117 202 118 208 118 C209 134 208 150 209 166", "ink"),
        ("M218 166 C218 140 219 110 218 84 C226 83 234 84 240 84 C241 110 240 140 241 166", "ink"),
        ("M250 166 C250 156 251 146 250 138 C258 137 266 138 272 138 C273 148 272 158 273 166", "grey"),
        ("M176 167 C210 168 250 166 282 167", "grey"),
        ("M190 104 C200 98 210 96 222 72 C232 60 244 62 262 54", "grey"),
    ],
}

FONT_CSS = [
    "https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;1,6..72,300;1,6..72,400;1,6..72,500&family=Instrument+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap",
    "https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;0,8..60,500;1,8..60,300;1,8..60,400;1,8..60,500&text=%C4%AA%C4%AB&display=swap",
]
CSS_FILES = ["tokens/colors.css", "tokens/typography.css", "tokens/spacing.css", "tokens/radius.css",
             "tokens/elevation.css", "tokens/motion.css", "tokens/responsive.css", "base/elements.css", "site.css"]


# ---------------------------------------------------------------- helpers

def esc(s):
    return html.escape(str(s), quote=True)


def em(s):
    """Escape text, then turn *words* into the serif-italic accent."""
    return re.sub(r"\*(.+?)\*", r'<em class="k-em">\1</em>', esc(s))


def plain(s):
    return str(s).replace("*", "")


def icon(name, size=16, stroke=1.5, cls=""):
    return (f'<svg class="k-icon {cls}" aria-hidden="true" focusable="false" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="none" stroke="currentColor" stroke-width="{stroke}" stroke-linecap="square" stroke-linejoin="miter">{ICONS[name]}</svg>')


def circle_icon(name, w, h, isize):
    return (f'<svg class="k-circle" viewBox="0 0 140 120" width="{w}" height="{h}" aria-hidden="true">'
            f'<path d="{CIRCLE}" vector-effect="non-scaling-stroke"/></svg>'
            f'<span class="k-circle-icon">{icon(name, isize, 1)}</span>')


def slash(text, tag="h2", extra=""):
    return (f'<div class="k-slash"><span class="k-slash__bar" aria-hidden="true"></span>'
            f'<{tag} class="k-display k-display--h2"{extra}>{em(text)}</{tag}></div>')


def wordmark(suffix=True):
    s = '<span class="k-wordmark__suffix">&nbsp;CFO Partners</span>' if suffix else ""
    return (f'<span class="k-wordmark" role="img" aria-label="Krastin CFO Partners">Krast'
            f'<span class="k-wordmark__i" aria-hidden="true"></span>n{s}</span>')


def art(case_id, wide=False):
    paths = "".join(
        f'<path class="t-{tone}" d="{d}" pathLength="1" style="animation-delay:{i * 160}ms"/>'
        for i, (d, tone) in enumerate(CASE_ART[case_id]))
    return (f'<div class="k-art{" k-art--wide" if wide else ""}"><svg viewBox="0 0 300 200" '
            f'preserveAspectRatio="xMidYMid meet" aria-hidden="true">{paths}</svg></div>')


# ---------------------------------------------------------------- site builder

class Site:
    def __init__(self, site_url, base_path):
        self.cfg = json.loads((ROOT / "content" / "site.json").read_text("utf-8"))
        self.t = {l: json.loads((ROOT / "content" / f"{l}.json").read_text("utf-8")) for l in LANGS}
        self.site_url = (site_url or self.cfg["site_url"]).rstrip("/")
        if self.site_url.startswith("http://") and "localhost" not in self.site_url:
            self.site_url = "https://" + self.site_url[len("http://"):]  # Pages reports http:// until HTTPS is enforced
        self.base = (base_path or "").rstrip("/")
        self.routes = self.cfg["routes"]
        self.cases = self.cfg["case_order"]
        self.pages = []   # (route_key, {lang: path}) for the sitemap
        self.asset_v = ""

    # paths
    def path(self, key, lang, slug=None):
        p = self.routes[key][lang]
        return p + slug + "/" if slug else p

    def href(self, p):
        return self.base + p

    def abs(self, p):
        return self.site_url + p

    def asset(self, p):
        return f"{self.base}/assets/{p}"

    # ---------------------------------------------------------- shell
    def head(self, lang, title, desc, paths, og_type="website", jsonld=(), noindex=False):
        cfg = self.cfg
        alt = "".join(f'<link rel="alternate" hreflang="{l}" href="{self.abs(paths[l])}">' for l in LANGS)
        alt += f'<link rel="alternate" hreflang="x-default" href="{self.abs(paths["en"])}">'
        org = {
            "@context": "https://schema.org", "@type": "ProfessionalService",
            "name": cfg["brand"], "url": self.abs(self.routes["home"][lang]),
            "description": self.t[lang]["seo"]["org_description"],
            "address": {"@type": "PostalAddress", "streetAddress": cfg["street"],
                        "addressLocality": "Rīga" if lang == "lv" else "Riga",
                        "postalCode": cfg["postal_code"], "addressCountry": cfg["country_code"]},
            "telephone": cfg["phone_display"], "email": cfg["email"],
            "founder": {"@type": "Person", "name": "Elvis Krastiņš", "jobTitle": self.t[lang]["seo"]["founder_title"]},
            "areaServed": ["LV", "EE", "LT"], "knowsLanguage": ["lv", "en"],
        }
        if cfg.get("linkedin_url"):  # personal profile, so it belongs to the founder
            org["founder"]["sameAs"] = [cfg["linkedin_url"]]
        ld = "".join(f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>' for o in (org, *jsonld))
        analytics = ""
        if cfg.get("cloudflare_analytics_token"):
            analytics = ("<script type=\"module\" src=\"https://static.cloudflareinsights.com/beacon.min.js\" "
                         f"data-cf-beacon='{{\"token\": \"{esc(cfg['cloudflare_analytics_token'])}\"}}'></script>")
        elif cfg.get("plausible_domain"):
            analytics = f'<script defer data-domain="{esc(cfg["plausible_domain"])}" src="https://plausible.io/js/script.js"></script>'
        canonical = self.abs(paths[lang])
        og_img = self.abs("/assets/og-image.png")
        fonts = "".join(f'<link rel="stylesheet" href="{u}">' for u in FONT_CSS)
        desc_tags = f'<meta name="description" content="{esc(desc)}"><meta property="og:description" content="{esc(desc)}">' if desc else ""
        return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
{desc_tags}
<link rel="canonical" href="{canonical}">{'<meta name="robots" content="noindex, follow">' if noindex else ''}
{alt}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(cfg['brand'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="{LOCALE[lang]}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#F8F6F4">
<link rel="icon" href="{self.asset('favicon.svg')}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{self.asset('apple-touch-icon.png')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{fonts}
<link rel="stylesheet" href="{self.asset('site.css')}?v={self.asset_v}">
<script defer src="{self.asset('site.js')}?v={self.asset_v}"></script>
{analytics}
{ld}
</head>
<body>
"""

    def header(self, lang, active, paths):
        t = self.t[lang]["nav"]
        items = [("home", t["home"]), ("services", t["services"]), ("insights", t["insights"]), ("about", t["about"])]
        links = "".join(
            f'<a href="{self.href(self.path(k, lang))}"{" aria-current=\"page\"" if k == active else ""}>{esc(label)}</a>'
            for k, label in items)
        lang_links = '<span class="k-lang__sep" aria-hidden="true">/</span>'.join(
            f'<a href="{self.href(paths[l])}" hreflang="{l}" lang="{l}"{" aria-current=\"true\"" if l == lang else ""}>{l}</a>'
            for l in LANGS)
        contact = self.href(self.path("contact", lang))
        return f"""<a class="k-skip" href="#main">{esc(t['skip'])}</a>
<header class="k-header">
<div class="k-header__bar">
<a class="k-header__logo" href="{self.href(self.path('home', lang))}">{wordmark()}</a>
<nav class="k-nav">{links}</nav>
<div class="k-lang" role="group" aria-label="{esc(t['language'])}">{lang_links}</div>
<a class="k-btn k-btn--primary k-btn--sm k-header__cta" href="{contact}">{esc(t['cta'])}</a>
<button type="button" class="k-menu-btn" aria-expanded="false" aria-controls="k-menu" aria-label="{esc(t['open_menu'])}" data-open="{esc(t['open_menu'])}" data-close="{esc(t['close_menu'])}">{icon('menu', 24, 1.25, 'k-icon--menu')}{icon('x', 24, 1.25, 'k-icon--x')}</button>
</div>
<div class="k-menu" id="k-menu">
<nav>{links}</nav>
<div class="k-menu__cta"><a class="k-btn k-btn--primary" href="{contact}">{esc(t['cta'])}</a></div>
</div>
</header>
"""

    def footer(self, lang):
        t = self.t[lang]
        f = t["footer"]
        svc = "".join(
            f'<li><a href="{self.href(self.path("services", lang))}#{a}">{esc(t["areas"][a]["title"])}</a></li>'
            for a in AREA_ORDER_HOME)
        firm = [("about", f["about"]), ("insights", f["insights"]), ("faq", f["faq"]), ("contact", f["contact"])]
        firm_li = "".join(f'<li><a href="{self.href(self.path(k, lang))}">{esc(v)}</a></li>' for k, v in firm)
        if self.cfg.get("linkedin_url"):
            firm_li += f'<li><a href="{esc(self.cfg["linkedin_url"])}" rel="noopener">{esc(f["linkedin"])}</a></li>'
        return f"""<footer class="k-footer k-inverse">
<div class="k-wrap">
{wordmark()}
<div class="k-footer__grid">
<div><div class="k-label">{esc(f['services'])}</div><ul>{svc}</ul></div>
<div><div class="k-label">{esc(f['firm'])}</div><ul>{firm_li}</ul></div>
<div><div class="k-label">{esc(f['office_city'])}</div><div class="k-footer__addr">{esc(f['address'])}</div></div>
</div>
<div class="k-footer__bottom">
<div class="k-footer__legal"><span class="k-label">{esc(f['copyright'])}</span><a href="{self.href(self.path('privacy', lang))}">{esc(f['privacy'])}</a></div>
<span class="k-footer__disclaimer">{esc(f['disclaimer'])}</span>
</div>
</div>
</footer>
</body>
</html>
"""

    def write(self, path, key, lang, paths, title, desc, main, active=None, og_type="website", jsonld=(), noindex=False):
        doc = (self.head(lang, title, desc, paths, og_type, jsonld, noindex) + self.header(lang, active, paths)
               + f'<main id="main">\n{main}\n</main>\n' + self.footer(lang))
        target = OUT / path.lstrip("/") / "index.html" if path.endswith("/") else OUT / path.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(doc, "utf-8")
        if key and paths not in self.pages:  # each page is written once per language; list it once
            self.pages.append(paths)

    def btn(self, href, label, variant="primary", size="", arrow=False, extra=""):
        cls = f"k-btn k-btn--{variant}" + (f" k-btn--{size}" if size else "")
        a = icon("arrow-right", 16) if arrow else ""
        return f'<a class="{cls}" href="{href}"{extra}>{esc(label)}{a}</a>'

    def service_rows(self, lang, field):
        t = self.t[lang]
        rows = "".join(
            f'<a class="k-srow" href="{self.href(self.path("services", lang))}#{a}">'
            f'<span class="k-srow__icon">{circle_icon(AREA_ICONS[a], 72, 62, 26)}</span>'
            f'<span><span class="k-srow__title">{esc(t["areas"][a]["title"])}</span>'
            f'<span class="k-srow__text">{esc(t["areas"][a][field])}</span></span></a>'
            for a in AREA_ORDER_HOME)
        return rows + '<div class="k-srows__end"></div>'

    def steps(self, items, cls=""):
        out = "".join(
            f'<div class="k-step"><div class="k-step__icon"><div class="k-step__circle">{circle_icon(STEP_ICONS[i], 96, 82, 34)}</div></div>'
            f'<div class="k-step__title">{esc(title)}</div><p>{esc(text)}</p></div>'
            for i, (title, text) in enumerate(items))
        return f'<div class="k-tile-grid k-steps {cls}">{out}</div>'

    def card(self, lang, cid):
        c = self.t[lang]["cases"][cid]
        return (f'<a class="k-card" href="{self.href(self.path("insights", lang, cid))}">{art(cid)}'
                f'<div class="k-card__meta"><span class="k-tag">{esc(c["topic"])}</span><span class="k-label">{esc(c["date"])}</span></div>'
                f'<h3 class="k-card__title">{em(c["title"])}</h3>'
                f'<p class="k-card__excerpt">{esc(c["excerpt"])}</p>'
                f'<span class="k-card__more">{esc(self.t[lang]["insights"]["read_more"])} {icon("arrow-right", 14)}</span></a>')

    def cards(self, lang, extra_cls=""):
        return f'<div class="k-cols-3 {extra_cls}">' + "".join(self.card(lang, c) for c in self.cases) + "</div>"

    # ---------------------------------------------------------- pages
    def page_home(self, lang):
        t = self.t[lang]
        h = t["home"]
        paths = {l: self.path("home", l) for l in LANGS}
        contact = self.href(self.path("contact", lang))
        words = h["typed_words"]
        chips = "".join(f'<button type="button" class="k-chip" aria-pressed="false">{esc(p)}</button>' for p in h["problems"])
        main = f"""<section class="k-home-hero">
<div class="k-wrap">
<h1 class="k-display k-display--hero k-hero-q" aria-label="{esc(h['hero_aria'])}">
<span class="k-hero-q__l1">{esc(h['hero_line1'])} <span class="k-typed-line"><span class="k-typed" data-words="{esc(json.dumps(words, ensure_ascii=False))}"><span class="k-typed__text">{esc(words[0])}</span></span></span></span>
<span class="k-hero-q__l2">{em(h['hero_line2'])}</span>
</h1>
<div class="k-home-hero__body">
<p class="k-lede k-lede--lg">{esc(h['lede'])} <span>{esc(h['lede2'])}</span></p>
<div class="k-hero-cta">{self.btn('#problems', h['hero_cta'], 'secondary', 'lg', True, ' data-scroll-to="problems"')}</div>
</div>
</div>
</section>
<section class="k-section k-section--tight k-section--divider" id="problems">
<div class="k-wrap k-problems">
<div class="k-split k-problems__head">
{slash(h['problems_heading'])}
<p>{esc(h['problems_intro'])}</p>
</div>
<div class="k-chips">{chips}</div>
<div class="k-problems__foot">
{self.btn(contact, h['problems_cta'], 'primary', 'lg', True)}
<span class="k-helper" aria-live="polite" data-none="{esc(h['problems_none'])}" data-one="{esc(h['problems_one'])}" data-many="{esc(h['problems_many'])}">{esc(h['problems_none'])}</span>
</div>
</div>
</section>
<section class="k-section" id="services-intro">
<div class="k-wrap">
<div class="k-split k-services-intro">
<div>{slash(h['services_heading'])}<p class="k-services-intro__sub">{esc(h['services_sub'])}</p></div>
<div>{self.service_rows(lang, 'home')}</div>
</div>
</div>
</section>
<section class="k-section" id="home-insights">
<div class="k-wrap">
<div class="k-insights-head">{slash(h['insights_heading'])}<a href="{self.href(self.path('insights', lang))}">{esc(h['insights_all'])}</a></div>
{self.cards(lang, 'k-home-cards')}
</div>
</section>
<section class="k-section k-section--tight k-section--clay k-inverse">
<div class="k-wrap">
<div class="k-band"><h2 class="k-display k-display--h2" style="max-width:22ch">{em(h['closing_heading'])}</h2>{self.btn(contact, h['closing_cta'], 'inverse', 'lg')}</div>
</div>
</section>"""
        s = t["seo"]["home"]
        self.write(paths[lang], "home", lang, paths, s["title"], s["description"], main, "home")
        # Tracking aliases of the home page (e.g. the email signature link): same page, own path in
        # Cloudflare Web Analytics, kept out of Google and the sitemap.
        for alias in self.cfg.get("tracking_paths", {}).get(lang, []):
            self.write(alias, None, lang, paths, s["title"], s["description"], main, "home", noindex=True)

    def page_services(self, lang):
        t = self.t[lang]
        s = t["services"]
        paths = {l: self.path("services", l) for l in LANGS}
        tiles, panels = "", ""
        for i, a in enumerate(AREA_ORDER_SERVICES):
            area = t["areas"][a]
            first = i == 0
            tiles += (f'<button type="button" class="k-tile" id="{a}" data-area="{a}" aria-expanded="{"true" if first else "false"}" aria-controls="panel-{a}">'
                      f'<span class="k-tile__chev"><span>{icon("chevron-down", 18)}</span></span>'
                      f'<span class="k-tile__title">{esc(area["title"])}</span>'
                      f'<span class="k-tile__blurb">{esc(area["services"])}</span></button>')
            tasks = "".join(f'<button type="button" class="k-task" aria-pressed="false" aria-controls="task-{a}-{j}">{esc(tt)}</button>'
                            for j, (tt, _) in enumerate(area["tasks"]))
            details = "".join(
                f'<div id="task-{a}-{j}" hidden><div class="k-detail"><div class="k-detail__body">'
                f'<div class="k-detail__title">{esc(tt)}</div><p class="k-detail__text">{esc(td)}</p></div>'
                f'<button type="button" class="k-detail__close" aria-label="{esc(s["close"])}">{icon("x", 16)}</button></div></div>'
                for j, (tt, td) in enumerate(area["tasks"]))
            panels += (f'<div class="k-tile-panel" id="panel-{a}" data-area="{a}"{"" if first else " hidden"}>'
                       f'<div class="k-panel"><div class="k-tasks">{tasks}</div><div class="k-details">{details}</div></div></div>')
        sectors = "".join(f'<span class="k-tag">{esc(x)}</span>' for x in s["sectors"])
        main = f"""<section class="k-section">
<div class="k-wrap">
<h1 class="k-display k-display--h1" style="max-width:20ch">{em(s['h1'])}</h1>
<p class="k-lede" style="margin-top:var(--space-8)">{esc(s['lede'])}</p>
</div>
</section>
<section class="k-section k-section--tight k-section--divider">
<div class="k-wrap">
<div class="k-tile-grid k-tiles">{tiles}</div>
<div class="k-panels">{panels}</div>
</div>
</section>
<section class="k-section">
<div class="k-wrap">
{slash(s['process_heading'])}
{self.steps(s['process'])}
</div>
</section>
<section class="k-section k-section--tight k-section--sunken">
<div class="k-wrap">
<div class="k-band">
<div class="k-band__copy"><div class="k-tags">{sectors}</div><h2 class="k-display k-display--h3" style="margin-top:var(--space-5)">{em(s['sectors_heading'])}</h2></div>
{self.btn(self.href(self.path('contact', lang)), s['cta'])}
</div>
</div>
</section>"""
        seo = t["seo"]["services"]
        self.write(paths[lang], "services", lang, paths, seo["title"], seo["description"], main, "services")

    def page_insights(self, lang):
        t = self.t[lang]
        s = t["insights"]
        paths = {l: self.path("insights", l) for l in LANGS}
        main = f"""<section class="k-section">
<div class="k-wrap">
<h1 class="k-display k-display--h1">{em(s['h1'])}</h1>
<p class="k-lede" style="margin-top:var(--space-8)">{esc(s['lede'])}</p>
<div style="margin-top:var(--space-16)">{self.cards(lang)}</div>
</div>
</section>"""
        seo = t["seo"]["insights"]
        self.write(paths[lang], "insights", lang, paths, seo["title"], seo["description"], main, "insights")

    def page_case(self, lang, cid):
        t = self.t[lang]
        s = t["insights"]
        c = t["cases"][cid]
        paths = {l: self.path("insights", l, cid) for l in LANGS}
        facts = "".join(f'<div><dt class="k-label">{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in c["facts"])
        body = "".join(f'<div><h2>{esc(hh)}</h2><p>{esc(p)}</p></div>' for hh, p in c["body"])
        main = f"""<section class="k-section">
<div class="k-wrap k-wrap--narrow">
<div class="k-label">{esc(c['topic'])} · {esc(c['date'])}</div>
<h1 class="k-display k-display--h1 k-article-h1">{em(c['title'])}</h1>
<p class="k-lede" style="margin-top:var(--space-8)">{esc(c['lede'])}</p>
</div>
</section>
<section class="k-section k-section--tight k-section--flush-top">
<div class="k-wrap k-wrap--narrow">
{art(cid, wide=True)}
<dl class="k-facts">{facts}</dl>
<div class="k-prose">{body}</div>
<div class="k-divider" role="separator"></div>
<p class="k-outcome">{esc(c['outcome'])}</p>
<p class="k-note">{esc(s['anonymised'])}</p>
<div class="k-actions">{self.btn(self.href(self.path('contact', lang)), s['cta'])}{self.btn(self.href(self.path('insights', lang)), s['back'], 'ghost')}</div>
</div>
</section>"""
        title = f"{plain(c['title'])} — {self.cfg['brand']}"
        self.write(paths[lang], "case", lang, paths, title, c["excerpt"], main, "insights", og_type="article")

    def page_about(self, lang):
        t = self.t[lang]
        s = t["about"]
        cfg = self.cfg
        paths = {l: self.path("about", l) for l in LANGS}
        contacts = (f'<a href="tel:{cfg["phone"]}">{esc(cfg["phone_display"])}</a>&nbsp; &middot; &nbsp;'
                    f'<a href="mailto:{cfg["email"]}">{esc(cfg["email"])}</a>')
        contacts_rev = (f'<a href="mailto:{cfg["email"]}">{esc(cfg["email"])}</a>&nbsp; &middot; &nbsp;'
                        f'<a href="tel:{cfg["phone"]}">{esc(cfg["phone_display"])}</a>')
        body = "".join(f"<p>{esc(p)}</p>" for p in s["body"])
        main = f"""<section class="k-section">
<div class="k-wrap">
<div class="k-about-hero">
<div>
<h1 class="k-display k-display--h1 k-about-h1">{em(s['h1'])}</h1>
<p class="k-lede" style="margin-top:var(--space-8)">{esc(s['lede'])}</p>
<div class="k-about-body">{body}</div>
</div>
<div class="k-portrait">
<img src="{self.asset('team/elvis-krastins.webp')}" width="400" height="400" alt="{esc(s['name'])}">
<div class="k-portrait__cap">
<span class="k-portrait__name">{esc(s['name'])}</span>
<span class="k-label">{esc(s['role'])}</span>
<span class="k-portrait__contacts">{contacts}</span>
</div>
</div>
</div>
</div>
</section>
<section class="k-section k-section--tight k-section--divider">
<div class="k-wrap">
<div class="k-split k-work-split">
<div>{slash(s['work_heading'])}</div>
<div>{self.service_rows(lang, 'about')}</div>
</div>
</div>
</section>
<section class="k-section k-section--tight k-section--divider">
<div class="k-wrap">
{slash(s['how_heading'])}
{self.steps(s['steps'], 'k-steps--about')}
<p class="k-specialists">{esc(s['specialists'])}</p>
</div>
</section>
<section class="k-section k-section--tight k-section--sunken">
<div class="k-wrap">
<div class="k-band k-band--sm">
<div><h2 class="k-display k-display--h3" style="max-width:34ch">{em(s['closing'])}</h2><div class="k-band__contacts">{contacts_rev}</div></div>
{self.btn(self.href(self.path('contact', lang)), s['cta'])}
</div>
</div>
</section>"""
        seo = t["seo"]["about"]
        self.write(paths[lang], "about", lang, paths, seo["title"], seo["description"], main, "about")

    def page_contact(self, lang):
        t = self.t[lang]
        s = t["contact"]
        cfg = self.cfg
        paths = {l: self.path("contact", l) for l in LANGS}
        options = "".join(f'<option>{esc(t["areas"][a]["title"])}</option>' for a in AREA_ORDER_HOME) + f'<option>{esc(s["not_sure"])}</option>'
        redirect = self.abs(paths[lang]) + "?sent=1"
        req = '<span class="k-field__req" aria-hidden="true"> &middot;</span>'
        main = f"""<section class="k-section">
<div class="k-wrap">
<div class="k-split k-contact-split">
<div>
<h1 class="k-display k-display--h1">{em(s['h1'])}</h1>
<p class="k-lede" style="margin-top:var(--space-8)">{esc(s['lede'])}</p>
<div class="k-divider k-contact-divider" role="separator"></div>
<div class="k-contact-blocks">
<div><div class="k-eyebrow">{esc(s['office_label'])}</div><div class="k-contact-blocks__v">{esc(s['address'])}</div></div>
<div><div class="k-eyebrow">{esc(s['direct_label'])}</div><div class="k-contact-blocks__v"><a href="tel:{cfg['phone']}">{esc(cfg['phone_display'])}</a><br><a href="mailto:{cfg['email']}">{esc(cfg['email'])}</a></div></div>
</div>
<aside class="k-callout"><div class="k-label">{esc(s['note_title'])}</div><div class="k-callout__body">{esc(s['note'])}</div></aside>
</div>
<div class="k-form-card">
<form class="k-form" action="https://api.web3forms.com/submit" method="POST" data-sending="{esc(s['sending'])}" data-prefill="{esc(s['prefill'])}">
<input type="hidden" name="access_key" value="{esc(cfg.get('web3forms_key', ''))}">
<input type="hidden" name="subject" value="{esc(s['subject'])}">
<input type="hidden" name="from_name" value="{esc(cfg['brand'])} website">
<input type="hidden" name="redirect" value="{esc(redirect)}">
<input type="checkbox" name="botcheck" class="k-hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<div class="k-form__row">
<div class="k-field"><label for="f-name">{esc(s['name'])}{req}</label><input class="k-input" id="f-name" name="name" required autocomplete="name" placeholder="{esc(s['name_ph'])}"></div>
<div class="k-field"><label for="f-company">{esc(s['company'])}{req}</label><input class="k-input" id="f-company" name="company" required autocomplete="organization" placeholder="{esc(s['company_ph'])}"></div>
</div>
<div class="k-field"><label for="f-email">{esc(s['email'])}{req}</label><input class="k-input" id="f-email" name="email" type="email" required autocomplete="email" placeholder="{esc(s['email_ph'])}" aria-describedby="f-email-help"><div class="k-field__help" id="f-email-help">{esc(s['email_help'])}</div></div>
<div class="k-field"><label for="f-area">{esc(s['start'])}</label><span class="k-select"><select class="k-input" id="f-area" name="area">{options}</select>{icon('chevron-down', 16)}</span></div>
<div class="k-field"><label for="f-msg">{esc(s['message'])}</label><textarea class="k-input" id="f-msg" name="message" rows="4" placeholder="{esc(s['message_ph'])}"></textarea></div>
<p class="k-form__error" role="alert" hidden>{esc(s['error'])}</p>
<button type="submit" class="k-btn k-btn--primary k-btn--lg k-btn--full">{esc(s['submit'])}</button>
<span class="k-form__small">{esc(s['small'])}</span>
</form>
<div class="k-success" hidden>
<h2 class="k-display k-display--h3" tabindex="-1">{em(s['success_h'])}</h2>
<p>{esc(s['success_p'])}</p>
<button type="button" class="k-btn k-btn--secondary k-btn--sm">{esc(s['again'])}</button>
</div>
</div>
</div>
</div>
</section>"""
        seo = t["seo"]["contact"]
        self.write(paths[lang], "contact", lang, paths, seo["title"], seo["description"], main, None)

    def page_faq(self, lang):
        t = self.t[lang]
        s = t["faq"]
        paths = {l: self.path("faq", l) for l in LANGS}
        groups = ""
        for gi, g in enumerate(s["groups"]):
            items = ""
            for i, (q, a) in enumerate(g["items"]):
                first = gi == 0 and i == 0
                items += (f'<div class="k-faq-item"><h3><button type="button" class="k-faq-q" aria-expanded="{"true" if first else "false"}" aria-controls="faq-{gi}-{i}">'
                          f'<span>{esc(q)}</span><span>{icon("plus", 18)}</span></button></h3>'
                          f'<p class="k-faq-a" id="faq-{gi}-{i}"{"" if first else " hidden"}>{esc(a)}</p></div>')
            groups += f'<div class="k-faq-group"><h2>{esc(g["title"])}</h2>{items}<div class="k-faq-end"></div></div>'
        schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for g in s["groups"] for q, a in g["items"]]}
        main = f"""<section class="k-section">
<div class="k-wrap k-wrap--narrow">
<h1 class="k-display k-display--h1">{em(s['h1'])}</h1>
<p class="k-lede" style="margin-top:var(--space-8)">{esc(s['lede'])}</p>
</div>
</section>
<section class="k-section k-section--tight k-section--flush-top">
<div class="k-wrap k-wrap--narrow">
{groups}
<div class="k-faq-cta">{self.btn(self.href(self.path('contact', lang)), s['cta'])}<span class="k-helper">{esc(s['helper'])}</span></div>
</div>
</section>"""
        seo = t["seo"]["faq"]
        self.write(paths[lang], "faq", lang, paths, seo["title"], seo["description"], main, None, jsonld=(schema,))

    def page_privacy(self, lang):
        t = self.t[lang]
        s = t["privacy"]
        paths = {l: self.path("privacy", l) for l in LANGS}
        body = "".join(f"<h2>{esc(h)}</h2><p>{esc(p)}</p>" for h, p in s["sections"])
        main = f"""<section class="k-section">
<div class="k-wrap k-wrap--narrow">
<h1 class="k-display k-display--h1">{em(s['h1'])}</h1>
<p class="k-label" style="margin-top:var(--space-6)">{esc(s['updated'])}</p>
<div class="k-legal">{body}</div>
</div>
</section>"""
        seo = t["seo"]["privacy"]
        self.write(paths[lang], "privacy", lang, paths, seo["title"], seo["description"], main, None)

    def page_404(self):
        t = self.t["en"]
        s = t["notfound"]
        lv = self.t["lv"]["notfound"]
        paths = {l: self.path("home", l) for l in LANGS}
        main = f"""<section class="k-section">
<div class="k-wrap">
<h1 class="k-display k-display--h1">{em(s['h1'])}</h1>
<p class="k-lede" style="margin-top:var(--space-8)">{esc(s['text'])}</p>
<div class="k-actions" style="margin-top:var(--space-10)">{self.btn(self.href('/'), s['home'], 'primary', '', True)}{self.btn(self.href('/lv/'), lv['home'], 'ghost')}</div>
</div>
</section>"""
        self.write("/404.html", None, "en", paths, t["seo"]["notfound"]["title"], "", main, None)

    # ---------------------------------------------------------- static files
    def copy_static(self):
        css = "\n".join((ROOT / "static" / "css" / f).read_text("utf-8") for f in CSS_FILES)
        js = (ROOT / "static" / "js" / "site.js").read_text("utf-8")
        self.asset_v = hashlib.sha1((css + js).encode()).hexdigest()[:10]
        shutil.copytree(ROOT / "static" / "assets", OUT / "assets")
        (OUT / "assets" / "site.css").write_text(css, "utf-8")
        (OUT / "assets" / "site.js").write_text(js, "utf-8")

    def write_meta(self):
        base = self.site_url
        urls = ""
        for paths in self.pages:
            alts = "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{self.abs(paths[l])}"/>' for l in LANGS)
            alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{self.abs(paths["en"])}"/>'
            for l in LANGS:
                urls += f"<url><loc>{self.abs(paths[l])}</loc>{alts}</url>\n"
        (OUT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + urls + "</urlset>\n", "utf-8")
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n", "utf-8")
        t = self.t["en"]
        cfg = self.cfg
        lines = [f"# {cfg['brand']}", "",
                 f"> {t['seo']['org_description']} Based in Riga, Latvia; working in English and Latvian across the Baltics.", "",
                 "## Services", ""]
        for a in AREA_ORDER_HOME:
            area = t["areas"][a]
            lines.append(f"### {area['title']}")
            lines.append(area["services"])
            lines += [f"- {tt}: {td}" for tt, td in area["tasks"]]
            lines.append("")
        lines += ["## Case studies (anonymised)", ""]
        for cid in self.cases:
            c = t["cases"][cid]
            lines.append(f"- [{plain(c['title'])}]({self.abs(self.path('insights', 'en', cid))}): {c['excerpt']}")
        lines += ["", "## Contact", "",
                  f"- Founder and CFO: Elvis Krastiņš",
                  f"- Email: {cfg['email']}", f"- Phone: {cfg['phone_display']}",
                  f"- Office: {cfg['street']}, Riga, {cfg['postal_code']}, Latvia",
                  f"- First meeting is free of charge: {self.abs(self.path('contact', 'en'))}", "",
                  "## Pages", ""]
        for key in ("home", "services", "insights", "about", "contact", "faq"):
            lines.append(f"- {key.title()}: {self.abs(self.path(key, 'en'))} (Latvian: {self.abs(self.path(key, 'lv'))})")
        (OUT / "llms.txt").write_text("\n".join(lines) + "\n", "utf-8")

    def build(self):
        if OUT.exists():
            shutil.rmtree(OUT)
        OUT.mkdir()
        self.copy_static()
        for lang in LANGS:
            self.page_home(lang)
            self.page_services(lang)
            self.page_insights(lang)
            for cid in self.cases:
                self.page_case(lang, cid)
            self.page_about(lang)
            self.page_contact(lang)
            self.page_faq(lang)
            self.page_privacy(lang)
        self.page_404()
        self.write_meta()
        (OUT / ".nojekyll").write_text("", "utf-8")
        n = sum(1 for _ in OUT.rglob("*.html"))
        print(f"Built {n} pages into {OUT}  (site_url={self.site_url}, base_path='{self.base}')")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-url", default=os.environ.get("SITE_URL"))
    ap.add_argument("--base-path", default=os.environ.get("BASE_PATH", ""))
    ap.add_argument("--serve", action="store_true", help="preview at http://localhost:8000 after building")
    args = ap.parse_args()
    Site(args.site_url, args.base_path).build()
    if args.serve:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("Preview: http://localhost:8000  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("", 8000), handler).serve_forever()


if __name__ == "__main__":
    main()
