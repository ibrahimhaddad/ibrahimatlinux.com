# ibrahimatlinux.com

Static site. No database, no build server, no dependencies. Plain HTML, one stylesheet,
two small scripts.

## Layout

    index.html              home
    about/  library/  advisory/  speaking/  contact/
    assets/css/site.css     the whole stylesheet, tokens at the top
    assets/js/nav.js        mobile menu
    assets/js/library.js    library filtering, progressive enhancement only
    data/publications.json  all 85 library items, single source of truth
    files/                  PDFs, clean paths
    wp-content/uploads/     the same PDFs at their original WordPress paths,
                            so links published between 2010 and 2026 keep working
    tools/build.py          regenerates library and homepage from the JSON
    tools/mirror-assets.sh  one-time download from the old WordPress site

## Adding a publication

Edit `data/publications.json`, then:

    python3 tools/build.py
    git add . && git commit -m "Add <title>" && git push

`build.py` validates the JSON first and refuses to write anything if an entry is
malformed. It only rewrites text between `<!-- BUILD:NAME:START -->` and
`<!-- BUILD:NAME:END -->` markers. Everything outside those is hand-edited and safe.

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
lists every entry, including them.
