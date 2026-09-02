#!/usr/bin/env python3
"""
build.py  --  regenerates the parts of the site that come from data/publications.json

WHEN TO RUN THIS
    After you add, edit or remove an entry in data/publications.json.

HOW TO RUN IT
    From inside the ibrahimatlinux-site folder, type:

        python3 tools/build.py

    That is it. No installation, no libraries, nothing to set up. It uses only
    what ships with Python.

WHAT IT TOUCHES
    library/index.html   the full filterable list of everything
    index.html           the "Recent reports and e-books" row on the homepage
    sitemap.xml          so search engines see new pages

    It only rewrites the text between the marker comments, for example
    <!-- BUILD:LIBRARY:START --> and <!-- BUILD:LIBRARY:END -->.
    Everything outside those markers is yours and is never touched.

ADDING A NEW PUBLICATION
    Open data/publications.json and copy an existing block. Fields:

      type     "ebook", "book" or "article"
      title    the full title
      date     short form, e.g. "Sep 2026"
      year     the year as a number, e.g. 2026
      month    the month as a number, 1 to 12
      topic    one of: ospo, compliance, ai, government, ma, strategy
               For a piece that belongs under more than one, use a list:
               "topic": ["strategy", "ai"]. It then appears under both
               filters, and both labels show on the row. Put the topic it
               belongs to most first.
      url      where it lives. "/files/2026/09/name.pdf" for something you host,
               or a full https:// address for something published elsewhere
      legacy   null, unless the file also needs to exist at an old path
      cover    "/assets/img/covers/name.png", or null for articles
      note     ISBN and role for books, otherwise null
      external true if the url points somewhere other than this site

    Save the file, run the command above, then commit both the JSON and the
    HTML files it changed.
"""

import json, os, re, sys, html
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'publications.json')

TOPIC_LABEL = {
    'ospo': 'OSPO', 'compliance': 'Compliance', 'ai': 'AI',
    'government': 'Government', 'ma': 'M&amp;A', 'strategy': 'Strategy',
}
TYPE_LABEL = {'ebook': 'E-book', 'book': 'Book', 'article': 'Article'}
VALID_TOPICS = set(TOPIC_LABEL)
VALID_TYPES = set(TYPE_LABEL)


def esc(s):
    """Escape a bare & but leave entities that are already written out alone."""
    return re.sub(r'&(?!(?:amp|lt|gt|quot|#\d+|middot|nbsp|rarr);)', '&amp;', s or '')


def topics(i):
    """An entry's topics, always as a list.

    "topic": "ai"            one topic,  the original form
    "topic": ["ai", "ospo"]  several,    the first one leads
    """
    t = i.get('topic')
    return t if isinstance(t, list) else [t]


def validate(items):
    problems = []
    for n, i in enumerate(items, 1):
        where = f'entry {n} ("{i.get("title", "no title")[:50]}")'
        if i.get('type') not in VALID_TYPES:
            problems.append(f'{where}: type must be one of {sorted(VALID_TYPES)}')
        ts = topics(i)
        if not ts:
            problems.append(f'{where}: topic list is empty, give it at least one')
        for t in ts:
            if t not in VALID_TOPICS:
                problems.append(f'{where}: topic "{t}" must be one of {sorted(VALID_TOPICS)}')
        if len(ts) != len(set(ts)):
            problems.append(f'{where}: the same topic is listed twice')
        if not i.get('url'):
            problems.append(f'{where}: url is missing')
        if not isinstance(i.get('year'), int):
            problems.append(f'{where}: year must be a number, not text')
        if not isinstance(i.get('month'), int) or not 1 <= i['month'] <= 12:
            problems.append(f'{where}: month must be a number from 1 to 12')
        if i.get('type') in ('ebook', 'book') and not i.get('cover'):
            problems.append(f'{where}: books and e-books need a cover image')
    return problems


def ext_attrs(item):
    return ' target="_blank" rel="noopener"' if item.get('external') else ''


def card(i):
    note = ''
    if i.get('note'):
        note = (f'\n            <p class="pub__note">{esc(i["note"])}</p>')
    return f'''        <a class="pub" data-type="{i['type']}" data-topic="{' '.join(topics(i))}" data-year="{i['year']}"
           href="{html.escape(i['url'], quote=True)}"{ext_attrs(i)}>
          <div class="pub__cover">
            <img loading="lazy" src="{i['cover']}" alt="Cover of {esc(i['title'])}">
          </div>
          <div class="pub__body">
            <p class="pub__title">{esc(i['title'])}</p>{note}
            <div class="pub__meta">
              <span class="badge">{TYPE_LABEL[i['type']]}</span><span>{i['date']}</span>
            </div>
          </div>
        </a>'''


def row(i):
    badges = ' '.join(f'<span class="badge">{TOPIC_LABEL[t]}</span>' for t in topics(i))
    return f'''        <div class="row" data-type="{i['type']}" data-topic="{' '.join(topics(i))}" data-year="{i['year']}">
          <div class="row__date">{i['date']}</div>
          <div class="row__title">
            <a href="{html.escape(i['url'], quote=True)}"{ext_attrs(i)}>{esc(i['title'])}</a>
          </div>
          <div class="row__tag">{badges}</div>
        </div>'''


def featured(i):
    return f'''        <a class="pub" href="{html.escape(i['url'], quote=True)}"{ext_attrs(i)}>
          <div class="pub__cover">
            <img loading="lazy" src="{i['cover']}" alt="Cover of {esc(i['title'])}">
          </div>
          <div class="pub__body">
            <p class="pub__title">{esc(i['title'])}</p>
            <div class="pub__meta">
              <span class="badge">{TYPE_LABEL[i['type']]}</span><span>{i['date']}</span>
            </div>
          </div>
        </a>'''


def replace_block(path, name, new_html):
    """Swap the text between <!-- BUILD:NAME:START --> and :END --> markers."""
    full = os.path.join(ROOT, path)
    with open(full, encoding='utf-8') as f:
        src = f.read()
    start, end = f'<!-- BUILD:{name}:START -->', f'<!-- BUILD:{name}:END -->'
    if start not in src or end not in src:
        print(f'  ! {path}: markers for {name} not found, skipping')
        return False
    pattern = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.S)
    out = pattern.sub(lambda m: f'{start}\n{new_html}\n      {end}', src, count=1)
    if out != src:
        with open(full, 'w', encoding='utf-8') as f:
            f.write(out)
        print(f'  updated {path}  ({name})')
    else:
        print(f'  unchanged {path}  ({name})')
    return True


def build_sitemap(pages):
    today = date.today().isoformat()
    urls = '\n'.join(
        f'  <url><loc>https://www.ibrahimatlinux.com{p}</loc>'
        f'<lastmod>{today}</lastmod></url>' for p in pages)
    out = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f'{urls}\n</urlset>\n')
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(out)
    print('  updated sitemap.xml')


def main():
    if not os.path.exists(DATA):
        sys.exit(f'ERROR: cannot find {DATA}\nRun this from the site folder: python3 tools/build.py')

    try:
        with open(DATA, encoding='utf-8') as f:
            items = json.load(f)['items']
    except json.JSONDecodeError as e:
        sys.exit(
            f'ERROR: data/publications.json is not valid JSON.\n'
            f'  {e}\n\n'
            f'Most likely a missing comma, a trailing comma before a closing bracket,\n'
            f'or a quote mark that was never closed. Look at line {e.lineno}.'
        )

    problems = validate(items)
    if problems:
        print('ERROR: problems in data/publications.json\n')
        for p in problems:
            print('  -', p)
        sys.exit('\nNothing was written. Fix the entries above and run again.')

    items.sort(key=lambda i: (-i['year'], -i['month'], i['title']))

    covers = [i for i in items if i['type'] in ('ebook', 'book')]
    articles = [i for i in items if i['type'] == 'article']

    print(f'\nReading {len(items)} entries')
    for t in ('ebook', 'book', 'article'):
        print(f'  {TYPE_LABEL[t]+"s":<10} {sum(1 for i in items if i["type"] == t)}')
    print()

    replace_block('library/index.html', 'LIBRARY',
                  '\n'.join(card(i) for i in covers))
    replace_block('library/index.html', 'ARTICLES',
                  '\n'.join(row(i) for i in articles))
    replace_block('library/index.html', 'COUNT',
                  f'        <span id="count">{len(items)}</span> items')

    # Homepage: four newest e-books, translations excluded so an English edition
    # is never pushed below its own translation.
    def is_translation(i):
        t = i['title']
        return ('(Mandarin)' in t or '(Japanese)' in t
                or any(ord(c) > 0x2E80 for c in t))

    recent = [i for i in items if i['type'] == 'ebook' and not is_translation(i)][:4]
    replace_block('index.html', 'RECENT', '\n'.join(featured(i) for i in recent))

    latest = articles[:5]
    replace_block('index.html', 'LATEST', '\n'.join(row(i) for i in latest))

    build_sitemap(['/', '/about/', '/library/', '/advisory/', '/speaking/', '/contact/'])

    print('\nDone. Commit the changed files and the site will update within a minute.\n')


if __name__ == '__main__':
    main()
