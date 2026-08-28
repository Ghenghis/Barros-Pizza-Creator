# Hostinger VPS deployment

This package serves the installable mobile/tablet app and the existing Barro's
AI service as one protected deployment. The public web container is the only
container with host ports. The Python API stays on the private Docker network.

1. Point `creator.daveai.tech` to the Hostinger VPS public IP.
2. Copy `.env.example` to `.env` on the VPS and replace the access token.
3. Add provider and Azure Speech keys only in the private VPS `.env` file.
4. From `deploy`, run `docker compose up -d --build`.
5. Verify `https://creator.daveai.tech/api/health` returns `ok: true`.

Do not commit `.env`, provider keys, the Android signing key, or a Windows bridge
configuration. Caddy obtains and renews HTTPS automatically after DNS resolves.

The same Compose file can be pasted or imported into Hostinger Docker Manager.
Persistent volumes keep history, pairing state, imported music, and TLS data
across container replacement.
