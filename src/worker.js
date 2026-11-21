// Picks the language of the front page. Everything else is served straight from dist/.
//   bendavidnormann.com -> English front page (/en/)
//   bendavidnormann.no and other hosts -> Norwegian front page (/)
//   /?lang=en or /?lang=no -> the visitor's own choice, remembered in a cookie for a year.
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== "/") return env.ASSETS.fetch(request);

    const asked = url.searchParams.get("lang");
    if (asked === "no" || asked === "en") {
      return new Response(null, {
        status: 302,
        headers: {
          Location: "/",
          "Set-Cookie": `lang=${asked}; Path=/; Max-Age=31536000; SameSite=Lax; Secure`,
          "Cache-Control": "no-store",
        },
      });
    }

    const cookie = (request.headers.get("Cookie") || "").match(/(?:^|;\s*)lang=(no|en)/);
    const lang = cookie ? cookie[1] : url.hostname.endsWith("bendavidnormann.com") ? "en" : "no";
    if (lang === "en") {
      url.pathname = "/en/";
      url.search = "";
    }
    const res = await env.ASSETS.fetch(new Request(url, request));
    const out = new Response(res.body, res);
    out.headers.set("Vary", "Cookie");
    out.headers.set("Cache-Control", "private, no-cache");
    return out;
  },
};
