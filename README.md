# bendavidnormann.com

Static personal website for Ben David Normann, served by Cloudflare Workers (static assets).

- `src/content.json`: text and images for every page (same URLs as the old Squarespace site).
- `src/links.json`: the front-page hub, meaning channels (YouTube, TikTok, Instagram, ...) and projects. A channel with an empty `url` is hidden.
- `src/style.css`, `src/favicon.svg`, `src/_redirects`, `src/_headers`: assets copied into the build.
- `src/img/`: self-hosted images (optional; missing ones are fetched from the old Squarespace CDN with `--fetch-images`).

## Build and deploy

```
python3 src/build.py --fetch-images   # writes dist/
npx wrangler deploy                    # publishes the Worker "bendavidnormann"
```

On Cloudflare Workers Builds, use build command `python3 src/build.py --fetch-images` and deploy command `npx wrangler deploy`.
