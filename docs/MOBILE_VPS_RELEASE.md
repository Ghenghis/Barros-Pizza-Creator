# Barro's Creator Mobile 1.0 and Windows 1.6.1

## Release boundary

Mobile is an installable companion for the existing Windows Pizza Creator add-on. It does not contain the commercial game, its assets, or a claim that the Windows Unity 2017 executable runs natively on Android. Root is neither required nor used.

Supported first-party test layouts:

| Device | Layout | Android package |
|---|---|---|
| Samsung Galaxy Tab S9+ 12 GB | tablet/landscape and tablet/portrait | `Barros_Pizza_Creator_Mobile_v1.0.0.apk` |
| Samsung Galaxy S21 Ultra 5G 12 GB | phone portrait and phone landscape | `Barros_Pizza_Creator_Mobile_v1.0.0.apk` |

## Architecture

```text
Android APK or installed PWA
        |
        | HTTPS + bearer token + paired-device token
        v
creator.daveai.tech on Hostinger VPS
        |
        | durable recipe job, never an inbound home-PC connection
        v
Windows bridge polls outward every three seconds
        |
        | local-only http://127.0.0.1:48173/remote/import
        v
Barro's sidecar -> exact catalog validation -> in-game Barro's tab
        v
user Preview -> Apply -> Save
```

The game, game port and local AI helper remain unreachable from the public internet. A recipe is not applied automatically; the Windows user retains approval in the real Creator UI.

## Hostinger deployment

1. Create an `A` record for `creator.daveai.tech` pointing to the Hostinger VPS.
2. Extract `Barros_Creator_Hostinger_Server_v1.0.0.zip` on the VPS.
3. Copy `deploy/.env.example` to `deploy/.env`.
4. Replace `BARROS_API_TOKEN` with a long random value. Add provider and Azure Speech keys only to this private file.
5. Run `docker compose up -d --build` from `deploy`, or import `deploy/docker-compose.yml` through Hostinger Docker Manager.
6. Verify `https://creator.daveai.tech/api/health` returns `ok: true` and `mobile_api: 1.0.0`.
7. Open the site on each Samsung device, enter the private token under Settings, then use Add to Home Screen or install the APK.

The Compose deployment keeps the API on a private Docker network. Only Caddy owns ports 80/443. Caddy obtains HTTPS after DNS resolves. Persistent volumes retain service data, imported music and certificates across image replacement.

## Windows pairing

1. Install or repair Windows 1.6.1 so the plug-in includes the remote inbox.
2. Extract the bridge ZIP beside the Windows release and open `START_WINDOWS_BRIDGE.bat`.
3. Set `BARROS_REMOTE_URL` to `https://creator.daveai.tech/api` and `BARROS_API_TOKEN` to the same private access token before starting the bridge. These may also be placed in a private launcher shortcut or service configuration.
4. Enter the displayed six-digit code in the mobile **Connect** tab within 15 minutes.
5. Create a pizza and choose **Send to Windows**.
6. Open the in-game Barro's tab. The recipe appears after catalog validation; Preview, Apply and Save remain explicit actions.

Bridge credentials are written under `%LOCALAPPDATA%\BarrosPizzaCreator\windows-bridge.json`, never into the repository or an Android design.

## Android signing and updates

The release script keeps the long-lived Android key and password under `C:\private\barros-mobile`. The key is excluded from Git and public releases. Future APK updates must use this same key and application ID `tech.daveai.barroscreator`.

The generated certificate SHA-256 is written to `web/.well-known/assetlinks.json`. That exact file must be served at:

`https://creator.daveai.tech/.well-known/assetlinks.json`

When site ownership verification passes, the APK opens the PWA without a browser toolbar. Until DNS and HTTPS are live, the same APK may show a Custom Tab or connection page; that is an honest deployment dependency, not an APK failure.

## Verification performed for this release

- complete Python test suite, JavaScript syntax and JSON validation;
- phone viewport at 384×854 with no horizontal overflow;
- tablet viewport at 1280×800 with no horizontal overflow;
- live browser compose returning a game-valid 176-placement artwork recipe;
- six-digit browser pairing, remote job creation, Windows polling, local sidecar import and completed acknowledgement;
- Android Gradle signed APK/AAB build, manifest inspection and SHA-256 manifest;
- Windows plug-in rebuild, provenance refresh and installer/portable lifecycle verification.

Tests involving the physical microphone, Samsung permission dialogs, physical-device APK installation and the live Hostinger DNS/VPS are reported separately if those external devices or credentials are unavailable during the build.
