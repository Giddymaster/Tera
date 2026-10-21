# Apple MDM (iPhone/iPad) feasibility assessment

Status: assessment complete; a configuration + status layer and dashboard page are
implemented in Milestone 9. A working Apple MDM requires running an MDM server,
an APNs certificate, Apple Business Manager, and a physical device, so the live
path is **not** implemented or tested here. Facts verified against Apple and
vendor documentation on 2026-10-21; re-verify before relying on them.

## The honest summary

Managing iPhones/iPads is **more involved and more costly** than Android for a
very small business. There is no free, self-contained path equivalent to the
Android Management API. You must either run an MDM server (open protocol, but it
needs a vendor-signed APNs certificate) or use a third-party MDM product.

## How Apple MDM works

- Apple's **MDM protocol is open**: an MDM server sends commands and config
  profiles to devices, and wakes devices via **APNs** push notifications.
- To send those pushes, the server needs an **APNs certificate**. For a
  third-party/self-hosted MDM, this requires an **MDM vendor signing
  certificate**, historically available only through the **Apple Developer
  Enterprise Program (~$299/year)**. This is the most complex and most expensive
  part, and the certificate must be renewed annually (365-day validity).
- **Apple Business Manager (ABM)** is **free** but requires organization
  verification (a D-U-N-S number, which is free; some regions now accept an EIN —
  verify on Apple's signup page). ABM enables **Automated Device Enrollment**
  (which makes devices *supervised*) and app licensing (VPP).
- **2025 APNs change:** MDM servers must trust the updated APNs server
  certificate chain (USERTrust RSA root) or push delivery (including MDM wake-ups)
  can fail.

## Costs (for a small business)

| Item | Cost | Notes |
| --- | --- | --- |
| Apple Business Manager | Free | Org verification required |
| D-U-N-S number | Free | Expedited processing costs extra |
| Apple Developer Program | ~$99/year | For building/signing your own apps |
| Apple Developer **Enterprise** Program | ~$299/year | Historically needed for the MDM **vendor** push certificate |
| Self-hosted MDM software | Free (open source) | e.g. NanoMDM/MicroMDM/Fleet — still needs the APNs vendor cert |
| Third-party MDM with a free tier | $0 up to a device limit | e.g. some vendors offer a small free tier; this is a vendor dependency |

So a **truly zero-cost** Apple MDM is hard: the cheapest self-hosted route still
implies the ~$299/year enterprise program for the vendor certificate. For only a
couple of iPhones, a free-tier third-party MDM (for inventory/compliance) may be
the pragmatic choice, accepting the vendor dependency.

## Enrollment models

| Model | Supervision | Notes |
| --- | --- | --- |
| Automated Device Enrollment (ADE, via ABM) | Supervised | Company-owned, bought through Apple/reseller; most capable |
| Apple Configurator | Supervised | Manually supervise company-owned devices via USB |
| Device Enrollment (profile) | Unsupervised | Install a profile manually; fewer capabilities |
| User Enrollment | BYOD | Personal devices; most limited; no Lost Mode |

For company-owned iPhones, target **ADE (supervised)** for full capability.

## Capability matrix (what Apple MDM can actually do)

| Capability | Available? | Notes |
| --- | --- | --- |
| Device inventory (model, serial, capacity) | ✅ | Standard MDM query |
| OS version / security info | ✅ | Standard MDM query |
| Managed app deployment | ✅ | Via ABM app licensing (VPP) |
| Configuration / restriction profiles | ✅ | Passcode, Wi-Fi, restrictions, etc. |
| Remote **lock** | ✅ | `DeviceLock` command |
| Remote **wipe** | ✅ | `EraseDevice` (erase all content and settings) |
| **Managed Lost Mode** (lock + locate + sound) | ⚠️ Supervised only | Can report location even if Location Services are off; the **only** location path |
| Continuous location tracking | ❌ | Not provided by MDM; only Lost Mode on supervised devices |
| Live screen view / screenshots | ❌ | Not permitted by standard MDM |
| App usage / keystroke monitoring | ❌ | Not exposed by MDM; do not attempt |

## What this means for our product

- **Do** support iOS via standard MDM for: enrollment, inventory, OS/security
  info, managed apps, restrictions, remote lock/wipe, and Lost Mode (location) on
  supervised devices.
- **Do not** promise live screen viewing, remote screenshots, app-activity
  monitoring, or keystroke recording on iOS. They are not possible via MDM.
- iOS devices appear in the same dashboard, with platform-appropriate actions.

## Implemented in Milestone 9

- Backend configuration detection (`core/apple.py`) and an Apple MDM status +
  capability endpoint (`GET /apple/status`), mirroring the Android integration.
- A dashboard "Apple (iOS/iPadOS)" page showing configuration status, the chosen
  approach, setup steps, costs, and the honest capability matrix.

## Not implemented here (requires real Apple infrastructure)

A full Apple MDM requires standing up an MDM server that speaks the MDM protocol
over APNs with signed profiles — this is a substantial system of its own, not a
simple REST client, and it cannot be built or tested without an APNs vendor
certificate, ABM, and a physical device. The recommended route is to deploy an
established open-source MDM server (e.g. **NanoMDM**) behind this dashboard, or to
integrate a free-tier third-party MDM, once the certificates and ABM are in place.
This milestone delivers the assessment, the configuration/status surface, and the
dashboard; the live MDM server integration is the documented next step.

## Sources

- [Apple Platform Security: Managed Lost Mode and remote wipe](https://support.apple.com/guide/security/secc46f3562c/web)
- [Apple Platform Deployment (MDM)](https://support.apple.com/guide/deployment/welcome/web)
- [Understanding MDM Certificates (MicroMDM)](https://micromdm.io/blog/certificates/)
- [APNs for MDM (Appaloosa)](https://www.appaloosa.io/blog/apple-push-notification-service-apns-mdm)
- [APNs server certificate update 2025](https://certpilot.app/changes/apple/apns-server-certificate-update-2025)
- [Enroll your organization in Apple Business Manager (Hexnode)](https://www.hexnode.com/mobile-device-management/help/how-to-enroll-in-apple-dep/)
