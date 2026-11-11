// Cloudflare Pages Functions: same-origin API reverse proxy to Render.
export async function onRequest(context) {
  const origin = context.env.RENDER_API_URL;
  if (!origin || !/^https:\/\//.test(origin)) {
    return Response.json({ error: "Configure RENDER_API_URL in Cloudflare Pages settings." }, { status: 503 });
  }
  const url = new URL(context.request.url);
  const suffix = Array.isArray(context.params.path) ? context.params.path.join("/") : (context.params.path || "");
  const upstream = new URL("/api/" + suffix, origin);
  upstream.search = url.search;
  return fetch(new Request(upstream.toString(), context.request), { redirect: "manual" });
}
