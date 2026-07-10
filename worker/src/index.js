// Shared clap/reaction counter for the Shadow Monarch blog.
// GET  /reactions?slug=<post-slug>                -> { clap, fire, bug, pwn, respect }
// POST /reactions?slug=<post-slug>&type=<field>    -> increments that field, returns the updated object
//
// Storage: one KV entry per post slug, holding a small JSON object.
// No auth needed (public counter), but origin is restricted to the blog's
// own domains and each field can only be one of the known reaction types.

const ALLOWED_ORIGINS = new Set([
  "https://danishahmed505.github.io",
  "https://shadowmonarch.com",
  "https://www.shadowmonarch.com",
]);

const FIELDS = ["clap", "fire", "bug", "pwn", "respect"];
const MAX_SLUG_LEN = 120;
const EMPTY = { clap: 0, fire: 0, bug: 0, pwn: 0, respect: 0 };

function corsHeaders(origin) {
  const allow = ALLOWED_ORIGINS.has(origin) ? origin : "";
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function json(data, origin, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders(origin) },
  });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders(origin) });
    }

    if (url.pathname !== "/reactions") {
      return json({ error: "not found" }, origin, 404);
    }

    const slug = (url.searchParams.get("slug") || "").trim();
    if (!slug || slug.length > MAX_SLUG_LEN) {
      return json({ error: "missing or invalid slug" }, origin, 400);
    }
    const key = "post:" + slug;

    if (request.method === "GET") {
      const stored = await env.REACTIONS.get(key, "json");
      return json(stored || EMPTY, origin);
    }

    if (request.method === "POST") {
      const type = url.searchParams.get("type") || "";
      if (!FIELDS.includes(type)) {
        return json({ error: "invalid reaction type" }, origin, 400);
      }
      const current = (await env.REACTIONS.get(key, "json")) || { ...EMPTY };
      current[type] = (current[type] || 0) + 1;
      await env.REACTIONS.put(key, JSON.stringify(current));
      return json(current, origin);
    }

    return json({ error: "method not allowed" }, origin, 405);
  },
};
