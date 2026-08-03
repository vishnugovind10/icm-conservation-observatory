# Deployment

The current hosted artifact is a static evidence demo, not live Fuji ICTT monitoring.

## GitHub Pages Rehearsal

When the repository is published and GitHub Pages is enabled for Actions, `.github/workflows/pages.yml` will:

1. build `public/` with `python scripts/package_static_demo.py`;
2. verify `public/deployment-manifest.json` is explicitly not live-demo-ready in fixture mode;
3. publish `public/` to GitHub Pages.

The resulting URL is suitable as a public rehearsal/demo of the evidence-backed dashboard, but it is not live Fuji ICTT monitoring until it is backed by live Fuji ICTT state.

## Live Fuji Package

After `config/fuji.local.json` contains real ICTT home/remote addresses and the live snapshot path has been verified:

```bash
python scripts/package_static_demo.py --config config/fuji.local.json --public-demo-url https://YOUR_DEMO_URL
./scripts/check-live-readiness.sh config/fuji.local.json https://YOUR_DEMO_URL
```

Treat the deployment as live evidence only when the readiness command returns success.

## Expected Public Evidence

A live-ready deployment must expose:

- `/index.html`;
- `/demo-data/bundle.json`;
- `/demo-data/conservation.json`;
- `/demo-data/correlation.json`;
- `/demo-data/EXCEPTIONS.md`;
- `/demo-data/merkle.json`;
- `/deployment-manifest.json` with `ready_for_public_live_demo: true`.
