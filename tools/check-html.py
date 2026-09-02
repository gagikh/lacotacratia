#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Լակոտակրատիա — index.html-ի կառուցվածքային ստուգում։

Գործարկել ամեն շաբաթական թարմացման ՎԵՐՋՈՒՄ (շապիկը թարմացնելուց հետո).
    python3 tools/check-html.py
Ելքի կոդը՝ 0՝ եթե ամեն ինչ կարգին է, 1՝ եթե սխալ կա (հարմար է CI-ի համար)։

Ստուգում է.
  1. HTML պիտակների հավասարակշռությունը
  2. Կրկնվող id-ները
  3. Կոտրված ներքին խարիսխները (href="#...")
  4. JSON-LD-ի վավերականությունը
  5. Ծանոթագրությունների <ol>-ի հերթականությունը և <sup>-ի ցուցադրվող համարները
     (գլուխների id-ների նախածանցները ՉԵՆ համընկնում ցուցադրվող համարների հետ՝
      Գլուխ 13-ի բաժինը գտնվում է id="gl12" խարիսխի տակ․ սա սպասելի է)
  6. Հավելվածների աղյուսակների սյունակների թիվը
  7. Հավելված Ա-ի ամսաթվերի ժամանակագրական հերթականությունը
"""
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser

FILE = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr', 'path', 'circle', 'rect',
        'line', 'polygon', 'polyline', 'ellipse', 'use', 'stop', 'image'}
# Հավելված → (սկիզբ, վերջ, սյունակների սպասվող թիվը)
APPENDICES = [
    ('Ա', 'id="hav-a"', 'id="hav-b"', 3),
    ('Բ', 'id="hav-b"', 'id="hav-g"', 4),
    ('Գ', 'id="hav-g"', 'id="hav-d"', 3),
    ('Ե', 'id="hav-e"', 'id="hav-z"', 3),
    ('Զ', 'id="hav-z"', '</main>', 3),
]

problems = []


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in VOID:
            return
        self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag.lower() in VOID:
            return
        if not self.stack:
            self.errors.append(('ավելորդ փակող', tag, self.getpos()))
            return
        if self.stack[-1][0] != tag:
            for k in range(len(self.stack) - 1, -1, -1):
                if self.stack[k][0] == tag:
                    for unclosed in self.stack[k + 1:]:
                        self.errors.append(('չփակված', unclosed[0], unclosed[1]))
                    del self.stack[k:]
                    return
            self.errors.append(('անհամապատասխան', tag, self.getpos()))
            return
        self.stack.pop()


def sortable(date_text):
    """Ամսաթվի բջիջը → (տարի, ամիս, օր) կամ None, եթե ամբողջական ամսաթիվ չէ։

    Ճանաչում է՝
      «25.06.2026»                        → (2026, 6, 25)
      «08–18.12.2025», «26–27.08.2026»    → միջակայքի ՎԵՐՋԻՆ օրը
      «09.01.2025 → 06.03.2025»           → առաջին ամսաթիվը
      «31.07.2026 (զարգացումը՝ 04.08)»    → առաջին ամսաթիվը
    Ամփոփիչ բլոկները՝ «06.2026», «2019 աշուն», «2025 I կիս.», «03.2026» —
    վերադարձնում են None և ԴՈՒՐՍ են մնում խիստ հերթականության ստուգումից,
    քանի որ գրքի պայմանավորվածությամբ դրանք դրվում են տարվա բլոկի վերջում։

    ԿԱՆՈՆ ՄԻՋԱԿԱՅՔԵՐԻ ՀԱՄԱՐ. գիրքը մի քանի օր ընդգրկող տողը դնում է այն
    ժամանակահատվածի ՎԵՐՋՈՒՄ, որը այն ընդգրկում է — «09–15.07.2026»-ը գալիս է
    «14.07.2026»-ից հետո, «05–07.08.2026»-ը՝ «07.08.2026»-ից հետո։ Այս
    պայմանավորվածությունը հետևողական է ողջ Հավելված Ա-ում, ուստի միջակայքը
    դասավորվում է ըստ վերջին օրվա, ոչ առաջինի։
    """
    # «08–18.12.2025» / «26–27.08.2026» — միջակայք՝ մեկ ամսվա ներսում
    m = re.search(r'\d{1,2}\s*[–—-]\s*(\d{1,2})\.(\d{2})\.(\d{4})', date_text)
    if m:
        return (int(m.group(3)), int(m.group(2)), int(m.group(1)))
    # Ամբողջական dd.mm.yyyy
    m = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', date_text)
    if m:
        return (int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None


def main():
    h = open(FILE, encoding='utf-8').read()

    # 1. Պիտակների հավասարակշռություն
    p = Balance()
    p.feed(h)
    if p.errors or p.stack:
        for e in p.errors[:10]:
            problems.append(f'պիտակ՝ {e[0]} <{e[1]}> տող {e[2][0]}')
        for t, pos in p.stack[:10]:
            problems.append(f'պիտակ՝ չփակված <{t}> տող {pos[0]}')
    print(f'1. Պիտակների հավասարակշռություն՝ {len(p.errors) + len(p.stack)} սխալ')

    # 2. Կրկնվող id
    ids = re.findall(r'\sid="([^"]+)"', h)
    dups = [k for k, v in Counter(ids).items() if v > 1]
    if dups:
        problems.append(f'կրկնվող id՝ {dups}')
    print(f'2. Կրկնվող id՝ {dups if dups else "չկան"} (ընդամենը {len(ids)})')

    # 3. Կոտրված ներքին խարիսխներ
    broken = sorted({a for a in re.findall(r'href="#([^"]+)"', h)
                     if a and a not in set(ids)})
    if broken:
        problems.append(f'կոտրված խարիսխ՝ {broken}')
    print(f'3. Կոտրված խարիսխներ՝ {broken if broken else "չկան"}')

    # 4. JSON-LD
    bad_json = 0
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            json.loads(m.group(1))
        except Exception as exc:
            bad_json += 1
            problems.append(f'JSON-LD անվավեր՝ {exc}')
    print(f'4. JSON-LD՝ {"վավեր" if not bad_json else f"{bad_json} անվավեր"}')

    # 5. Ծանոթագրություններ
    chapters = sorted({c for c in re.findall(r'id="(g\d+)-src\d+"', h)},
                      key=lambda x: int(x[1:]))
    for ch in chapters:
        i = h.find(f'id="{ch}-src1"')
        ol, end = h.rfind('<ol', 0, i), h.find('</ol>', i)
        order = [int(x) for x in re.findall(rf'id="{ch}-src(\d+)"', h[ol:end])]
        if order != list(range(1, len(order) + 1)):
            problems.append(f'{ch}՝ <ol>-ի հերթականությունը խախտված է — {order}')
        refs = {int(x) for x in re.findall(rf'href="#{ch}-src(\d+)"', h)}
        orphans = [n for n in order if n not in refs]
        if orphans:
            problems.append(f'{ch}՝ առանց հղման ծանոթագրություններ — {orphans}')
    mismatched = [x for x in re.findall(r'href="#(g\d+)-src(\d+)"[^>]*>\[(\d+)\]', h)
                  if x[1] != x[2]]
    if mismatched:
        problems.append(f'<sup>-ի ցուցադրվող համարները չեն համընկնում՝ {mismatched}')
    print(f'5. Ծանոթագրություններ՝ {len(chapters)} գլուխ, '
          f'համարակալման սխալ՝ {len(mismatched)}')

    # 6–7. Հավելվածներ
    for name, start, stop, ncols in APPENDICES:
        try:
            a = h.index(start)
            b = h.index(stop, a)
        except ValueError:
            problems.append(f'Հավելված {name}՝ չի գտնվել')
            continue
        rows = re.findall(r'<tr>(.*?)</tr>', h[a:b], re.S)
        bad = [i for i, r in enumerate(rows)
               if (r.count('<td') + r.count('<th')) != ncols and 'colspan' not in r]
        if bad:
            problems.append(f'Հավելված {name}՝ սյունակների սխալ տողեր {bad}')
        note = ''
        if name == 'Ա':
            dates = [re.match(r'<td>([^<]*)</td>', r).group(1)
                     for r in rows if re.match(r'<td>([^<]*)</td>', r)]
            keyed = [(d, sortable(d)) for d in dates]
            exact = [(d, k) for d, k in keyed if k]        # ամբողջական ամսաթվեր
            aggregate = [d for d, k in keyed if not k]     # ամփոփիչ բլոկներ
            out = [(exact[i - 1][0], exact[i][0])
                   for i in range(1, len(exact)) if exact[i][1] < exact[i - 1][1]]
            if out:
                problems.append(f'Հավելված Ա՝ ժամանակագրական խախտում — {out}')
            note = (f', {len(exact)} ամբողջական ամսաթիվ'
                    f' + {len(aggregate)} ամփոփիչ բլոկ (հերթականությունը չի ստուգվում)')
        print(f'6. Հավելված {name}՝ {len(rows)} տող{note}, '
              f'սյունակի սխալ՝ {bad if bad else "չկա"}')

    print()
    if problems:
        print(f'✘ ԳՏՆՎԵՑ {len(problems)} ԽՆԴԻՐ.')
        for x in problems:
            print('   -', x)
        return 1
    print('✔ Բոլոր ստուգումներն անցան։')
    return 0


if __name__ == '__main__':
    sys.exit(main())
