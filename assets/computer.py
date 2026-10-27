"""Hand-coded isometric laptop scene, SVG + CSS, no JS. Run: python3 assets/computer.py -> computer.svg"""
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'computer.svg'
BUDGET = 30_000  # bytes
T = 8.0  # loop length, s
# palette carries a +-1 colour fingerprint; FINGERPRINT must survive every build, never round these
PROMPT, TEXT, OUTPUT, LIT, LAV, GREEN = '#ff4fa2', '#f4f1ff', '#ffb15d', '#ffa34c', '#a99aff', '#5be3a7'
DECK, CUPC = '#d27bd9', '#a77cff'
FINGERPRINT = (PROMPT, TEXT, OUTPUT, LIT, LAV, GREEN, DECK, CUPC)
C, R2 = math.cos(math.radians(30)), math.sqrt(2)

# world: x right, y toward viewer, z up; hinge on back edge y=0
W, D, HB = 300, 200, 10
TILT, HL, TL = math.radians(14), 186, 6  # lid lean, height, thickness
CUP, CR, CH = (-92, 58), 30, 76  # centre, top radius, height
STEAM_RISE = 18
BOB = 'animation:bob 4s ease-in-out infinite'

CMD = 'git push'
TYPED = [0.9, 1.06, 1.2, 1.42, 1.62, 1.76, 1.92, 2.06]
KEYS = [('space' if c == ' ' else c, t) for c, t in zip(CMD, TYPED)] + [('enter', 2.5)]
BAR, DONE, PROMPT2, CLEAR = 2.62, 3.4, 3.55, 7.1
STILL = PROMPT2 + 0.1  # reduced-motion frame: output shown, cursor on
HIT = 0.16

ROWS = [
    [('`', 1)] + [(c, 1) for c in '1234567890-='] + [('bksp', 2)],
    [('tab', 1.5)] + [(c, 1) for c in 'qwertyuiop[]'] + [('\\', 1.5)],
    [('caps', 1.75)] + [(c, 1) for c in "asdfghjkl;'"] + [('enter', 2.25)],
    [('lsh', 2.25)] + [(c, 1) for c in 'zxcvbnm,./'] + [('rsh', 2.75)],
    [('fn', 1), ('ctl', 1), ('opt', 1), ('cmd', 1.25), ('space', 5.5), ('rcmd', 1.25), ('ropt', 1), ('lt', 1),
     ('ud', 1), ('rt', 1)],
]
KX, KY, KU, KR, GAP = 22, 16, 256 / 15, 17, 2.4
K, X0, LINES = 3.1, 18, (84, 114, 144)  # terminal em scale, margin, line tops; pitch >= 9.5em avoids collisions
ADV = 5.4  # mono advance, em
CODE = [(0, [(58, '#6c5ac4')]), (0, [(16, PROMPT), (30, TEXT), (8, LAV)]), (12, [(18, OUTPUT), (46, TEXT)]),
        (12, [(26, PROMPT), (24, TEXT), (14, LAV)])]


def P(x, y, z=0):
    """World -> screen, isometric."""
    return (x - y) * C, (x + y) / 2 - z


def n(v, dp=1):
    s = f'{v:.{dp}f}'.rstrip('0').rstrip('.')
    return '0' if s in ('', '-0') else s


def add(*vs):
    return tuple(map(sum, zip(*vs)))


def mul(k, v):
    return tuple(k * c for c in v)


def pts(xys):
    return ' '.join(f'{n(x)},{n(y)}' for x, y in xys)


def poly(fill, *world):
    return f'<polygon points="{pts(P(*w) for w in world)}" fill="{fill}"/>'


def plane(o, u, v):
    """matrix() mapping flat (s, t) to screen for world o + s*u + t*v."""
    (ox, oy), (ux, uy), (vx, vy) = P(*o), P(*u), P(*v)
    return f'matrix({n(ux, 4)} {n(uy, 4)} {n(vx, 4)} {n(vy, 4)} {n(ox)} {n(oy)})'


def band(x, y, r0, r1, z0, z1, fill):
    """Front half of a frustum side, radius r0 at z0 to r1 at z1."""
    a, b = r0 * C * R2, r1 * C * R2
    return (f'<path d="M{n(x - b)} {n(y - z1)}L{n(x - a)} {n(y - z0)}A{n(a)} {n(r0 / R2)} 0 0 0 {n(x + a)} {n(y - z0)}'
            f'L{n(x + b)} {n(y - z1)}A{n(b)} {n(r1 / R2)} 0 0 1 {n(x - b)} {n(y - z1)}z" fill="{fill}"/>')


def disc(x, y, r, fill):
    return f'<ellipse cx="{n(x)}" cy="{n(y)}" rx="{n(r * C * R2)}" ry="{n(r / R2)}" fill="{fill}"/>'


def lin(id_, a, b, x2=1, y2=0):
    return (f'<linearGradient id="{id_}" x2="{x2}"' + (f' y2="{y2}"' if y2 else '')
            + f'><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>')


# --- monoline glyphs, em: x 0..4, ascender 0, x-height 2.5, baseline 6.5, descender 8.5
def em(x, y):
    return f'{n(x, 2)} {n(y, 2)}'


def line(*p):
    return 'M' + 'L'.join(em(*q) for q in p)


def curve(*p):
    """Catmull-Rom through p as cubic Béziers, from current point p[0]."""
    q = [p[0], *p, p[-1]]
    out = ''
    for a, b, c, d in zip(q, q[1:], q[2:], q[3:]):
        c1 = b[0] + (c[0] - a[0]) / 6, b[1] + (c[1] - a[1]) / 6
        c2 = c[0] - (d[0] - b[0]) / 6, c[1] - (d[1] - b[1]) / 6
        out += f'C{em(*c1)} {em(*c2)} {em(*c)}'
    return out


def path(*p):
    return f'M{em(*p[0])}' + curve(*p)


def polar(a):
    return 2 + 2 * math.cos(math.radians(a)), 4.5 + 2 * math.sin(math.radians(a))


def arc(a0, a1):
    """Bowl arc a0 -> a1 deg from current point; y-down, positive = clockwise."""
    return f'A2 2 0 {int(abs(a1 - a0) > 180)} {int(a1 > a0)} {em(*polar(a1))}'


BOWL = 'M0 4.5a2 2 0 1 0 4 0a2 2 0 1 0-4 0'
SHOULDER = path((0, 3.8), (0.8, 2.7), (2.2, 2.5), (3.5, 3), (4, 4.2)) + 'L4 6.5'
GLYPHS = {
    '$': path((3.6, 2), (2.8, 1.4), (1.2, 1.4), (0.4, 2.1), (0.5, 3.1), (1.6, 3.7), (2.6, 4), (3.6, 4.7), (3.6, 5.7),
              (2.8, 6.4), (1.2, 6.4), (0.3, 5.8)) + line((2, 0.4), (2, 7.4)),
    '✓': line((0.3, 4.6), (1.6, 6.2), (4, 2.6)),
    'c': f'M{em(*polar(45))}' + arc(45, 315),
    'd': BOWL + line((4, 0), (4, 6.5)),
    'e': line((0.1, 4.5), (4, 4.5)) + arc(0, -320),
    'g': BOWL + line((4, 2.5), (4, 6.8)) + curve((4, 6.8), (3.7, 8), (2.6, 8.6), (1.2, 8.4), (0.4, 7.8)),
    'h': line((0, 0), (0, 6.5)) + SHOULDER,
    # slab i fills the mono cell
    'i': line((0.9, 2.5), (2, 2.5), (2, 6.5)) + line((0.6, 6.5), (3.4, 6.5)) + line((2, 0.9), (2, 1)),
    'l': path((2, 0), (2, 5.4), (2.5, 6.3), (3.4, 6.5)),
    'n': line((0, 2.5), (0, 6.5)) + SHOULDER,
    'p': line((0, 2.5), (0, 8.5)) + BOWL,
    's': path((3.6, 3), (2.8, 2.5), (1.2, 2.5), (0.4, 3.1), (0.5, 3.9), (1.4, 4.4), (2.6, 4.6), (3.5, 5.1), (3.6, 5.9),
              (2.8, 6.5), (1.2, 6.5), (0.3, 6)),
    't': line((1.8, 0.8), (1.8, 5.4)) + curve((1.8, 5.4), (2.2, 6.3), (3.4, 6.5)) + line((0.4, 2.5), (3.6, 2.5)),
    'u': path((0, 2.5), (0, 5), (0.6, 6.1), (2, 6.5), (3.4, 6), (4, 4.8)) + line((4, 2.5), (4, 6.5)),
    'w': line((0, 2.5), (1, 6.5), (2, 3.8), (3, 6.5), (4, 2.5)),
}


def build():
    css = [f'*{{animation-duration:{n(T)}s;animation-iteration-count:infinite;animation-timing-function:step-end}}']
    used = set()
    classes = {'bob', 'sh', 'st', 'lag1'}  # hand-written; generated names must not clash

    def anim(name, steps, prop='opacity'):
        """Hold-step keyframes on the T loop from [(t, value)]; returns the class."""
        assert name not in classes, f'class clash: {name}'
        classes.add(name)
        body = ''.join(f'{n(t / T * 100, 2)}%{{{prop}:{v}}}' for t, v in steps) + f'100%{{{prop}:{steps[-1][1]}}}'
        css.append(f'@keyframes {name}{{{body}}}.{name}{{animation-name:{name}}}')
        return name

    def glyphs(text, extra=''):
        used.update(text.replace(' ', ''))
        return ''.join(f'<use href="#g{ord(c):x}" x="{n(ADV * i, 2)}"{extra}/>' for i, c in enumerate(text) if c != ' ')

    def run(x, y, k, width, body, attrs=''):
        """Glyph uses in em at (x, y), scaled by k."""
        return (f'<g transform="translate({n(x)} {n(y)}) scale({k})" fill="none" stroke-width="{n(width / k, 3)}" '
                f'stroke-linecap="round" stroke-linejoin="round"{attrs}>{body}</g>')

    svg = []

    def group(start, cls):
        svg[start:] = [f'<g class="{cls}">{"".join(svg[start:])}</g>']

    # objects float in staggered phase (lag1); each floor shadow shrinks as its object rises
    css.append(f'.bob{{{BOB}}}.sh{{{BOB.replace("bob", "sh", 1)};transform-box:fill-box;transform-origin:center}}'
               '.lag1{animation-delay:-1.3s}'
               '@keyframes bob{50%{transform:translateY(-5px)}}@keyframes sh{50%{transform:scale(.9);opacity:.7}}')

    # floor shadows, flat s = x, t = y; pool goes in after bounds
    svg.append(f'<g transform="{plane((0, 0, 0), (1, 0, 0), (0, 1, 0))}">'
               f'<rect x="-14" y="-6" width="{W + 28}" height="{D + 30}" rx="22" fill="url(#shade)" class="sh"/>'
               f'<ellipse cx="{CUP[0] + 6}" cy="{CUP[1] + 6}" rx="{CR * 1.6}" ry="{CR * 1.6}" fill="url(#shade)" '
               'class="sh lag1"/></g>')

    # cup
    start = len(svg)
    cx, cy = P(*CUP)

    def taper(z):
        return CR - 7 * (1 - z / CH)

    svg += [band(cx, cy, taper(0), CR, 0, CH, 'url(#cup)'),
            band(cx, cy, taper(22), taper(48), 22, 48, 'url(#sleeve)'),
            band(cx, cy, CR + 2, CR + 2, CH, CH + 7, '#8f6af5'),
            disc(cx, cy - CH - 7, CR + 2, '#c7a8ff'), disc(cx, cy - CH - 10, CR - 6, '#dcc8ff')]
    sx, sy = P(CUP[0] + 12, CUP[1] + 12, CH + 10)
    svg.append(disc(sx, sy, 4.2, '#3a1a8a'))
    css.append('.st{animation:steam 2.667s linear infinite}@keyframes steam{0%{opacity:0;transform:translate(0px,8px)}'
               f'35%{{opacity:.7}}100%{{opacity:0;transform:translate(0px,-{STEAM_RISE}px)}}}}')
    for i, dx in enumerate((-13, 0, 12)):
        svg.append(f'<path d="M{n(sx + dx)} {n(sy - 12)}c-7-8 7-14 0-22s7-14 0-22" fill="none" stroke="#b9a8f0" '
                   f'stroke-width="3.5" stroke-linecap="round" class="st" '
                   f'style="animation-delay:-{n(i * 0.889, 3)}s"/>')
    group(start, 'bob lag1')

    # base: visible faces only
    start = len(svg)
    svg += [poly('url(#side)', (W, 0, 0), (W, D, 0), (W, D, HB), (W, 0, HB)),
            poly('url(#front)', (0, D, 0), (W, D, 0), (W, D, HB), (0, D, HB)),
            poly('url(#deck)', (0, 0, HB), (W, 0, HB), (W, D, HB), (0, D, HB)),
            f'<polyline points="{pts(P(*p) for p in ((0, D, HB), (W, D, HB), (W, 0, HB)))}" fill="none" '
            'stroke="#f6d8ff" stroke-width="1.4" stroke-linejoin="round"/>']

    # deck, flat s = x, t = y
    hits = dict(KEYS)
    assert len(hits) == len(KEYS), 'one press per key; repeats need multi-step anims'
    assert hits.keys() <= {k for row in ROWS for k, _ in row}, 'typed key missing from ROWS'
    lips, caps = [], []
    for r, row in enumerate(ROWS):
        s = KX + GAP / 2
        for label, u in row:
            rect = (f'<rect x="{n(s)}" y="{n(KY + r * KR + GAP / 2)}" width="{n(u * KU - GAP)}" '
                    f'height="{n(KR - GAP)}" rx="2"')
            lips.append(rect + '/>')
            if label in hits:
                t = hits[label]
                lit = anim(f'k{label}', [(0, 0), (t, 1), (t + HIT, 0)])
                press = anim(f'p{label}', [(0, 'none'), (t, 'translate(1.2px,1.2px)'), (t + HIT, 'none')], 'transform')
                caps.append(f'<g class="{press}">{rect}/>{rect} fill="{LIT}" class="{lit}"/></g>')
            else:
                caps.append(rect + '/>')
            s += u * KU
    # lip offset: flat (1, 1) = straight down on screen
    deck = (f'<rect x="{KX - 3}" y="{KY - 3}" width="262" height="{5 * KR + 6}" rx="4" fill="#4a2aa8" opacity=".55"/>'
            f'<g fill="#12082c" transform="translate(1.6 1.6)">{"".join(lips)}</g><g fill="#23104f">{"".join(caps)}</g>'
            '<rect x="102" y="118" width="96" height="66" rx="6" fill="#fff" fill-opacity=".06" stroke="#f0d6ff" '
            'stroke-opacity=".45"/>'
            + run(14, 148, 2, 2, glyphs('cpwillis'), ' stroke="#fff" stroke-opacity=".02"'))  # hidden mark, 2%
    svg.append(f'<g transform="{plane((0, 0, HB), (1, 0, 0), (0, 1, 0))}">{deck}</g>')

    # lid; screen in front-face flat coords, s = x, t down the lid
    up, out = (0, -math.sin(TILT), math.cos(TILT)), (0, math.cos(TILT), math.sin(TILT))
    a0, a1 = (0, 0, HB), (W, 0, HB)
    b0, b1 = add(a0, mul(HL, up)), add(a1, mul(HL, up))

    def front(p):
        return add(p, mul(TL, out))

    svg += [poly('#2e168f', a1, front(a1), front(b1), b1), poly('#9a74f5', b0, b1, front(b1), front(b0)),
            poly('url(#bezel)', front(a0), front(a1), front(b1), front(b0))]

    screen = [
        f'<rect x="7" y="7" width="{W - 14}" height="{HL - 21}" rx="3" fill="url(#display)"/>',
        f'<path d="M7 27V10a3 3 0 0 1 3-3h{W - 20}a3 3 0 0 1 3 3v17z" fill="#1c0c55"/>',
        *(f'<circle cx="{19 + 12 * i}" cy="17" r="3.4" fill="{c}"/>' for i, c in enumerate((PROMPT, OUTPUT, LAV))),
        '<path d="M58 27V13a3 3 0 0 1 3-3h58a3 3 0 0 1 3 3v14z" fill="#2e178a"/>',
        f'<rect x="66" y="16.5" width="34" height="4" rx="2" fill="{LAV}" opacity=".8"/>',
        f'<circle cx="112" cy="18.5" r="2" fill="{TEXT}" opacity=".6"/>',
        f'<rect x="{W - 16}" y="32" width="3.5" height="22" rx="1.75" fill="{LAV}" opacity=".35"/>',
    ]
    for r, (indent, segs) in enumerate(CODE):
        t, s = 35 + r * 10.5, 36 + indent
        screen.append(f'<rect x="14" y="{n(t)}" width="9" height="5" rx="2.5" fill="#5b46b8"/>')
        for width, c in segs:
            dim = ' opacity=".8"' if c == TEXT else ''
            screen.append(f'<rect x="{n(s)}" y="{n(t)}" width="{width}" height="5" rx="2.5" fill="{c}"{dim}/>')
            s += width + 5
    screen.append(f'<path d="M7 77H{W - 7}" stroke="#4a2fb0" stroke-width="1.2"/>')

    # terminal; glyph rows offset in em
    row = [(y - LINES[0]) / K for y in LINES]
    typed = ''
    for i, (c, (_, t)) in enumerate(zip(CMD, KEYS), start=2):
        if c != ' ':
            typed += glyphs(' ' * i + c, f' stroke="{TEXT}" class="{anim(f"c{i}", [(0, 0), (t, 1), (CLEAR, 0)])}"')
    done = anim('done', [(0, 0), (DONE, 1), (CLEAR, 0)])
    prompt2 = anim('pr2', [(0, 0), (PROMPT2, 1), (CLEAR, 0)])
    term = (glyphs('$', f' stroke="{PROMPT}"') + typed
            + glyphs(' ' * 7 + '✓', f' y="{n(row[1], 2)}" stroke="{GREEN}" class="{done}"')
            + glyphs('$', f' y="{n(row[2], 2)}" stroke="{PROMPT}" class="{prompt2}"'))
    screen.append(run(X0, LINES[0], K, 3.2, term))
    for i in range(6):
        block = (f'x="{n(X0 + K * (ADV * i + 0.3))}" y="{n(LINES[1] + 2.6 * K)}" width="{n(K * (ADV - 1.2))}" '
                 f'height="{n(3.8 * K)}" rx="1.5"')
        fill = anim(f'b{i}', [(0, 0), (BAR + i * 0.12, 1), (CLEAR, 0)])
        screen.append(f'<rect {block} fill="{LAV}" class="{fill}"/><rect {block} fill="{GREEN}" class="{done}"/>')

    # cursor: solid while typing, hidden during output, blinking when idle
    def at(col, line_):
        return f'translate({n(col * K * ADV)}px,{n(LINES[line_] - LINES[0])}px)'

    moves = [(0, at(2, 0))] + [(t, at(i, 0)) for i, (_, t) in enumerate(KEYS[:-1], start=3)]
    moves += [(PROMPT2, at(2, 2)), (CLEAR, at(2, 0))]
    blink = [(KEYS[0][1], 1), (KEYS[-1][1], 0)]
    for a, b in ((0, KEYS[0][1]), (PROMPT2, CLEAR), (CLEAR, T)):
        blink += [(a + 0.53 * j, 1 - j % 2) for j in range(math.ceil((b - a) / 0.53 - 1e-9))]
    cursor = (f'<rect x="{n(X0 + 0.2 * K)}" y="{n(LINES[0] + 1.8 * K)}" width="{n(3.6 * K)}" height="{n(5.2 * K)}" '
              f'fill="{TEXT}" opacity=".85" class="{anim("bl", sorted(blink))}"/>')
    screen.append(f'<g class="{anim("cur", moves, "transform")}">{cursor}</g>')
    screen.append(f'<rect x="7" y="7" width="{W - 14}" height="{HL - 21}" rx="3" fill="url(#glare)"/>')
    # second hidden mark on the bottom bezel, so one crop can't remove both
    screen.append(run(W / 2 - 30, HL - 13.5, 1.4, 1.4, glyphs('cpwillis'), ' stroke="#fff" stroke-opacity=".025"'))
    lid = plane(front(b0), (1, 0, 0), (0, math.sin(TILT), -math.cos(TILT)))
    svg.append(f'<g transform="{lid}">{"".join(screen)}</g>')
    group(start, 'bob')

    css.append(f'@media (prefers-reduced-motion:reduce){{*{{animation-play-state:paused!important;'
               f'animation-delay:-{n(STILL, 2)}s!important}}}}')

    # bounds; pool fades out inside them, so no hard edge on dark themes
    cup_rx = CR * C * R2
    corners = [P(*p) for p in (front(b0), front(b1), (0, D, HB), (W, D, 0), (W, 0, 0))]
    corners += [(cx - cup_rx - 4, sy - 12 - 44 - STEAM_RISE), (cx + cup_rx, cy)]
    mx, my = 28, 10  # tight vertical margin keeps the README row short
    x0, y0 = min(x for x, _ in corners) - mx, min(y for _, y in corners) - my
    w, h = max(x for x, _ in corners) + mx - x0, max(y for _, y in corners) + my - y0
    pool, pool_y = w / 2 - 8, P(W / 2, D * 0.75)[1]
    pool_ry = min(pool / 2, y0 + h - pool_y - 4)
    svg.insert(0, f'<ellipse cx="{n(x0 + w / 2)}" cy="{n(pool_y)}" rx="{n(pool)}" ry="{n(pool_ry)}" '
                  'fill="url(#pool)"/>')

    defs = (lin('deck', DECK, '#5a32e6', y2=0.6) + lin('side', '#4524c4', '#341a9e')
            + lin('front', '#a24fd0', '#5a2fd8') + lin('bezel', '#2a1278', '#1c0b55', y2=1)
            + lin('display', '#341a96', '#1d0d5f', y2=1) + lin('cup', CUPC, '#4a1fc9')
            + lin('sleeve', '#ff7ab8', '#d92f86')
            + '<linearGradient id="glare" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".09"/>'
              '<stop offset=".55" stop-color="#fff" stop-opacity="0"/></linearGradient>'
              '<radialGradient id="shade"><stop offset="0" stop-color="#1a0f40" stop-opacity=".32"/>'
              '<stop offset="1" stop-color="#1a0f40" stop-opacity="0"/></radialGradient>'
              '<radialGradient id="pool"><stop offset="0" stop-color="#7c5cff" stop-opacity=".3"/>'
              '<stop offset=".5" stop-color="#7c5cff" stop-opacity=".15"/>'
              '<stop offset="1" stop-color="#7c5cff" stop-opacity="0"/></radialGradient>'
            + ''.join(f'<path id="g{ord(c):x}" d="{GLYPHS[c]}"/>' for c in sorted(used)))
    rights = '© 2026 cpwillis. All rights reserved.'
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{n(x0, 2)} {n(y0, 2)} {n(w, 2)} {n(h, 2)}" '
            f'width="{round(w)}" height="{round(h)}" role="img" aria-labelledby="t">'
            '<title id="t">cpwillis laptop and coffee</title>'
            f'<desc>Isometric laptop and coffee, hand-coded by cpwillis (github.com/cpwillis/cpwillis). {rights}</desc>'
            '<metadata><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            f'<rdf:Description dc:creator="cpwillis" dc:rights="{rights}"/></rdf:RDF></metadata>'
            f'<defs>{defs}</defs><style>{"".join(css)}</style>')
    return head + ''.join(svg) + '</svg>\n'


def check(svg):
    """Fail the build on active content, external refs, a blown budget or a lost fingerprint/mark."""
    root = ET.fromstring(svg)
    els = list(root.iter())
    ids = {e.get('id') for e in els if e.get('id')}
    assert not [e for e in els if e.tag.split('}')[-1] in ('script', 'foreignObject', 'iframe')], 'active content'
    assert not [a for e in els for a in e.attrib if a.lower().startswith('on')], 'event handler'
    refs = [v for e in els for a, v in e.attrib.items() if a.endswith('href')] + re.findall(r'url\(([^)]*)\)', svg)
    assert all(r.startswith('#') and r[1:] in ids for r in refs), 'external or dangling ref'
    assert '@import' not in svg, 'external css'
    assert len(svg.encode()) <= BUDGET, f'over budget: {len(svg.encode())}'
    assert all(c in svg for c in FINGERPRINT), 'fingerprint lost'
    assert svg.count('stroke="#fff" stroke-opacity=".02') == 2, 'hidden mark lost'


if __name__ == '__main__':
    svg = build()
    check(svg)
    OUT.write_text(svg, encoding='utf-8')
    print(OUT.name, OUT.stat().st_size, 'bytes')
