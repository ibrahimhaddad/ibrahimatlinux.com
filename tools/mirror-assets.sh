#!/usr/bin/env bash
#
# mirror-assets.sh
# Downloads every PDF, cover image, photo and logo from the live WordPress site
# and files them into the new site's folder structure.
#
# RUN THIS WHILE THE OLD SITE IS STILL ONLINE. Once hosting is switched off the
# files are gone and this cannot be re-run.
#
# Usage, from inside the ibrahimatlinux-site folder:
#     bash tools/mirror-assets.sh
#
# Safe to run more than once. Files already downloaded are skipped, so if it
# stops halfway or a few fail, just run it again.
#
# Needs nothing but curl, which is already on every Mac.
#
# Optional: set BASE to mirror from somewhere other than the live site.
#     BASE=https://staging.example.com bash tools/mirror-assets.sh

set -u

MANIFEST="tools/assets-manifest.tsv"
LOG="tools/mirror-report.txt"
BASE="${BASE:-}"

# Some WordPress security plugins reject requests that do not look like a
# browser. Send a normal user agent so we are not mistaken for a scraper.
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

cd "$(dirname "$0")/.." || exit 1

if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: cannot find $MANIFEST"
  echo "Run this from inside the ibrahimatlinux-site folder, like this:"
  echo "    bash tools/mirror-assets.sh"
  exit 1
fi

total=0; ok=0; skipped=0; failed=0
: > "$LOG"

# Did we get the document, or did the server hand back an HTML error page with
# a 200 status? Cheap check on the first few bytes.
#   $1 = downloaded file, $2 = intended destination (for the extension)
content_ok() {
  case "$2" in
    *.pdf)
      head -c 5 "$1" | grep -q '%PDF' || return 1 ;;
    *.png|*.jpg|*.jpeg)
      head -c 200 "$1" | LC_ALL=C grep -qi '<html\|<!doctype' && return 1 ;;
  esac
  return 0
}

echo ""
echo "Mirroring assets from the live site"
echo "-----------------------------------"
echo ""

while IFS=$'\t' read -r url dest legacy; do
  case "$url" in \#*|"") continue ;; esac
  total=$((total + 1))

  [ -n "$BASE" ] && url="${BASE%/}/${url#*://*/}"

  if [ -f "$dest" ] && [ -s "$dest" ]; then
    skipped=$((skipped + 1))
  else
    tmp="$(mktemp)"
    # -f fail on HTTP errors, -L follow redirects, -sS quiet but show errors
    if ! curl -fLsS --retry 3 --retry-delay 2 --connect-timeout 20 \
              -A "$UA" -o "$tmp" "$url"; then
      rm -f "$tmp"; failed=$((failed + 1))
      printf "  FAILED   %s\n" "$url" | tee -a "$LOG"
      continue
    fi
    if [ ! -s "$tmp" ]; then
      rm -f "$tmp"; failed=$((failed + 1))
      printf "  EMPTY    %s\n" "$url" | tee -a "$LOG"
      continue
    fi
    if ! content_ok "$tmp" "$dest"; then
      rm -f "$tmp"; failed=$((failed + 1))
      printf "  NOT A FILE  %s\n" "$url" | tee -a "$LOG"
      printf "              server returned a web page, not the document\n"
      continue
    fi
    mkdir -p "$(dirname "$dest")"
    mv "$tmp" "$dest"
    ok=$((ok + 1))
    printf "  ok       %s\n" "$dest"
  fi

  # Second copy at the original WordPress path, so links published between
  # 2010 and 2026 keep resolving.
  if [ "$legacy" != "-" ] && [ -n "$legacy" ] && [ ! -f "$legacy" ]; then
    mkdir -p "$(dirname "$legacy")"
    cp "$dest" "$legacy"
  fi
done < "$MANIFEST"

# Tidy up any directories left empty by a failed download.
find files wp-content assets/img -type d -empty -delete 2>/dev/null
mkdir -p files wp-content/uploads assets/img/covers assets/img/logos assets/img/collaborators

echo ""
echo "-----------------------------------"
echo "  listed in manifest : $total"
echo "  downloaded now     : $ok"
echo "  already present    : $skipped"
echo "  failed             : $failed"
echo ""
printf "  files/            %s\n" "$(du -sh files 2>/dev/null | cut -f1)"
printf "  wp-content/       %s\n" "$(du -sh wp-content 2>/dev/null | cut -f1)"
printf "  assets/img/       %s\n" "$(du -sh assets/img 2>/dev/null | cut -f1)"
echo ""
printf "  TOTAL SITE SIZE   %s     (GitHub Pages ceiling is 1 GB)\n" "$(du -sh . 2>/dev/null | cut -f1)"
echo ""

if [ "$failed" -gt 0 ]; then
  echo "  $failed file(s) did not come down. The list is in $LOG."
  echo ""
  echo "  Run the script again first. It skips what it already has, so it only"
  echo "  retries the failures, and transient network errors are common."
  echo ""
  echo "  If the same file fails three times, open its URL in a browser. If the"
  echo "  browser cannot load it either, the file is no longer on the old server"
  echo "  and we will need to remove that entry from data/publications.json."
  echo ""
  exit 1
fi

echo "  All files present. Next: preview the site with"
echo "      python3 -m http.server 8000"
echo ""
