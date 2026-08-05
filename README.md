# ibrahimatlinux.com

Static site. No database, no build server, no dependencies. Plain HTML, one stylesheet,
a handful of small scripts. Everything runs inside what GitHub Pages can serve.

## Layout

    index.html              home
    404.html                dead links, carries the normal header and footer
    about/  library/  advisory/  speaking/  contact/
    contact/thanks/         form landing page, only reached when JavaScript is off
    assets/css/site.css     the whole stylesheet, tokens at the top
    assets/js/nav.js        mobile menu
    assets/js/library.js    library filtering, progressive enhancement only
    assets/js/external-links.js  opens outbound links and PDFs in a new tab
    assets/js/contact.js    submits the contact form without leaving the page
    data/publications.json  all 85 library items, single source of truth
    files/                  PDFs, clean paths
    wp-content/uploads/     the same PDFs at their original WordPress paths,
                            so links published between 2010 and 2026 keep working
    tools/build.py          regenerates library and homepage from the JSON
    tools/make-favicon.py   regenerates the IH monogram in every size
    tools/mirror-assets.sh  one-time download from the old WordPress site

## The contact form

Live and delivering. The site is static and cannot send email itself, so the form
posts to Web3Forms, which relays to the address registered against the access key
in `contact/index.html`.

**The destination address never appears anywhere public.** Not in the HTML, not in
this repository, not in the network request the browser makes. Only the access key
travels, and a key cannot be resolved back to an address. That is the entire reason
the form exists rather than a `mailto:` link, which scrapers harvest within days of
publication.

The access key itself is not a secret and is fine sitting in public HTML. It is a
routing identifier. The one thing someone could do with a copied key is post to the
form from elsewhere, which produces junk mail rather than any disclosure. If that
ever starts, generate a replacement key at https://web3forms.com against the same
address and swap it in.

To point the form at a different inbox, create a key for that address and replace
the `access_key` value. Nothing else changes.

The form also carries a honeypot field. Bots fill in every input they can find;
people never see this one, and Web3Forms rejects anything that arrives with it set.

Worth doing once after any change: send yourself a test message from the live site
and confirm it lands, including in spam.

## Adding a publication

Edit `data/publications.json`, then:

    python3 tools/build.py
    git add . && git commit -m "Add <title>" && git push

`build.py` validates the JSON first and refuses to write anything if an entry is
malformed. It only rewrites text between `<!-- BUILD:NAME:START -->` and
`<!-- BUILD:NAME:END -->` markers. Everything outside those is hand-edited and safe.

Set `"external": true` on anything hosted elsewhere. That is what stamps
`target="_blank"` onto the link at build time.

## Adding a logo to a logo row

**Run every new logo through the normaliser before committing it.**

    pip3 install pillow
    python3 tools/normalize-logo.py ~/Downloads/acme.png assets/img/collaborators/acme.jpg

The rows set `img { height: 30px; width: auto }`, which means the *file's*
canvas decides how big a logo looks, not the mark itself. Supplied logo files
arrive on wildly different canvases, so dropping one in untouched gets you either
a 5px smudge or something twice the size of its neighbours. Both have happened
here.

The script trims to the ink and rebuilds it on the 500x250 canvas every logo in
this repo uses. It prints the resulting ink percentages; if a new logo lands far
outside the range of its neighbours, the source art is probably cropped oddly and
worth a second look.

Then add the `<img>` to the row by hand. Collaborators on `/advisory/` are sorted
alphabetically, ignoring a leading "The" so the Linux Foundation files under L.
The homepage row is deliberately **not** alphabetical: it runs in employment
order, most recent first.

## Regenerating the social share card

`assets/img/og-card.png` is what LinkedIn, X and Slack render when anyone posts a
link to the site. Rebuild it if the claim on the homepage changes, or the portrait
does.

    pip3 install pillow
    python3 tools/make-og-card.py

Then re-scrape the URL at https://www.linkedin.com/post-inspector/ so LinkedIn
drops its cached copy. It will otherwise keep serving the old card for weeks.

## Regenerating the favicon

Only needed if the accent colour or the heading typeface changes.

    pip3 install fonttools pillow
    python3 tools/make-favicon.py

It downloads Newsreader, converts the I and H to outlines, and writes
`favicon.ico`, `assets/img/favicon.svg`, and the three PNG sizes. The letterforms
are baked in as paths, so the icon needs no webfont to render.

## Previewing locally

    python3 -m http.server 8000

Then open http://localhost:8000

## Notes

`.nojekyll` stops GitHub Pages running the site through Jekyll. Do not delete it.

`CNAME` holds the custom domain. GitHub rewrites this if you change the domain in
Settings, so leave it alone unless you are moving hosts.

The library page renders all 85 items as real HTML. JavaScript only hides and shows
them. With scripting disabled the page still lists everything.

Two counts are deliberately different and should not be reconciled. The homepage stat
strip counts distinct works, excluding translations and second editions. The library
lists every entry, including them. Separately, the library is a *selection*: it holds
what can be given away freely, while the full record of 150+ publications lives on
Google Scholar. The library page says so.

Every link leaving the site opens in a new tab. Most of that is baked into the HTML,
by hand in the header and footer and by `build.py` for publications.
`external-links.js` is the safety net for anything added later that was missed, so
turning JavaScript off degrades the behaviour rather than breaking it.

Two structured-data notes. Every page carries a schema.org `@graph` with a `Person`
and a `WebSite` node, both keyed by `@id` so crawlers understand it is one person
across six pages. `404.html` and `contact/thanks/` deliberately carry none, because
both are `noindex`.

There is one trap in `site.css`. Section 6 RESPONSIVE sits above the ADDITIONS
section at the bottom of the file, so its media queries cannot override anything
declared below them. Components declared in ADDITIONS get their breakpoints in the
block at the very end of the file. The comment there explains it.
