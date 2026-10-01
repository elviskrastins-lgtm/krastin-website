# Krastin CFO Partners — website

Bilingual (English / Latvian) static website, built from the Claude Design handoff.
It is plain HTML + CSS with a little JavaScript, so it loads fast and needs no server.

## Where things are

| What | File |
|---|---|
| All English text | `content/en.json` |
| All Latvian text | `content/lv.json` |
| Email, phone, form key, analytics, LinkedIn, page addresses | `content/site.json` |
| Design tokens (copied unchanged from the design system) | `static/css/tokens/`, `static/css/base/` |
| Page component styles | `static/css/site.css` |
| Interactions (typed word, chips, service tiles, FAQ, menu, form) | `static/js/site.js` |
| Logo, portrait, favicon, share image | `static/assets/` |
| Page layouts | `build.py` |

In the text files, words wrapped in `*asterisks*` appear in the serif italic accent,
e.g. `"Four things, done *properly*."`

## Changing text

1. Open `content/en.json` or `content/lv.json` (on GitHub: open the file → pencil icon).
2. Change the words between the quotes. Keep the quotes, commas and brackets.
3. Save / commit. GitHub rebuilds and republishes the site in about a minute.

Or ask Claude: *"On the Services page in Latvian, change X to Y."*

## Preview on your computer (optional)

Needs Python 3 (already installed on this PC).

```bash
python build.py --serve
```

Then open http://localhost:8000.

## Publishing (GitHub Pages)

The workflow in `.github/workflows/deploy.yml` builds and publishes the site on every push to `main`.

One-time setup:
1. Create a repository on GitHub and push this folder to it.
2. Repository → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. The site appears at `https://<username>.github.io/<repository>/`.

Note: GitHub Pages is free for **public** repositories. A private repository needs a paid GitHub plan for Pages.

### Custom domain

1. Repository → **Settings → Pages → Custom domain**: enter `krastin.eu` and save.
2. At your domain registrar add these DNS records:
   - `A` records for `@` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `CNAME` record for `www` → `<username>.github.io`
3. When the domain check passes, tick **Enforce HTTPS**.
4. Update `site_url` in `content/site.json` to the same domain.

### krastin.lv → krastin.eu/lv/

GitHub Pages serves one domain, so krastin.lv is redirected by Cloudflare (free):
1. Cloudflare → **Add a domain** → `krastin.lv` → Free plan. Check that the imported DNS records include any
   email records (MX, SPF/TXT, DKIM, DMARC) before continuing.
2. At the krastin.lv registrar, replace the nameservers with the two Cloudflare shows.
3. DNS: add `A` record `@` → `192.0.2.1` and `CNAME` `www` → `krastin.lv`, both **Proxied** (orange cloud).
   (The address is a placeholder; Cloudflare answers the request with the redirect.)
4. **Rules → Redirect Rules → Create rule**: when *Hostname is in* `krastin.lv`, `www.krastin.lv` →
   *Static* URL `https://krastin.eu/lv/`, status **301**.

## Contact form

The form sends to elvis@krastin.eu through [Web3Forms](https://web3forms.com) (free).
Create an access key with that email address and paste it into `web3forms_key` in `content/site.json`.
Until the key is set, submitting the form shows an error asking visitors to email directly.
A hidden honeypot field filters bots.

## Analytics

Cookie-less, so no cookie banner is needed. In `content/site.json` fill **one** of:
- `cloudflare_analytics_token` — free, from Cloudflare dashboard → Analytics & Logs → Web Analytics → Add a site → copy the token from the snippet.
- `plausible_domain` — paid, from plausible.io.

## SEO built in

Per-page titles and descriptions (both languages), canonical + `hreflang` links, Open Graph share image,
`sitemap.xml`, `robots.txt`, `llms.txt`, `ProfessionalService` structured data on every page and
`FAQPage` structured data on the FAQ pages.

After launch: add the site to Google Search Console and Bing Webmaster Tools and submit `/sitemap.xml`.
