# sisi-yu-works

Source for Sisi Yu's portfolio site, deployed on Netlify.

## Layout

- `site/` is what Netlify publishes: `index.html` plus images, videos and PDFs.
- `src/page.html` is the page as designed (the Claude artifact version, without the Netlify reaction form).
- `tools/build.py` turns `src/page.html` into `site/index.html`, adding the full HTML head, social preview tags, favicon and the reaction form.

## Updating

1. Edit `src/page.html` (or add files to `site/`).
2. Run `python3 tools/build.py` from the repo root.
3. Commit and push to `main`. Netlify redeploys automatically.

## Reactions

The "Leave a reaction" buttons post to a Netlify Form named `reaction`.
In Netlify: Forms → enable form detection, then Forms → Form notifications → add an email notification.
