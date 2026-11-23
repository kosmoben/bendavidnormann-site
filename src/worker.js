// Picks the language of every page. Each page exists twice in dist/: Norwegian at /<path>, English at /en/<path>.
//   bendavidnormann.com -> English
//   bendavidnormann.no and other hosts -> Norwegian
//   <any page>?lang=en or ?lang=no -> the visitor's own choice, remembered in a cookie for a year.
// The address in the browser stays the same (/about, /research, ...) in both languages.
// Images, styles and /en/... addresses are served straight from dist/ (see run_worker_first in wrangler.jsonc).
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    const asked = url.searchParams.get("lang");
    if (asked === "no" || asked === "en") {
      url.searchParams.delete("lang");
      return new Response(null, {
        status: 302,
        headers: {
          Location: url.pathname + url.search,
          "Set-Cookie": `lang=${asked}; Path=/; Max-Age=31536000; SameSite=Lax; Secure`,
          "Cache-Control": "no-store",
        },
      });
    }

    const cookie = (request.headers.get("Cookie") || "").match(/(?:^|;\s*)lang=(no|en)/);
    const lang = cookie ? cookie[1] : url.hostname.endsWith("bendavidnormann.com") ? "en" : "no";

    let res;
    if (lang === "en") {
      const en = new URL(url);
      en.pathname = "/en" + url.pathname;
      // Unknown English addresses get dist/en/404.html (the nearest 404.html, see not_found_handling).
      res = await env.ASSETS.fetch(new Request(en, request));
    } else {
      res = await env.ASSETS.fetch(request);
    }

    const out = new Response(res.body, res);
    // Trailing-slash redirects for the English copy must keep the visitor on the clean address.
    const loc = out.headers.get("Location");
    if (lang === "en" && loc) {
      const l = new URL(loc, url);
      if (l.origin === url.origin && l.pathname.startsWith("/en/")) {
        out.headers.set("Location", l.pathname.slice(3) + l.search);
      }
    }
    out.headers.set("Vary", "Cookie");
    out.headers.set("Cache-Control", "private, no-cache");
    return out;
  },
};
