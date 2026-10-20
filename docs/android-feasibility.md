# Android management feasibility assessment

Status: assessment complete; backend + dashboard integration scaffold implemented
in Milestone 8. A full live enrollment has **not** been performed (it needs a
Google Cloud project, an Android Enterprise binding, and a physical Android
device). Facts below were verified against Google and vendor documentation on
2026-10-21; re-verify before relying on them, since terms change.

## Recommended approach: Android Management API (AMAPI)

For managing a small number of **company-owned** Android devices, the
**Android Management API** is the right choice. It is Google's current API and
ships a Google-provided management app ("Android Device Policy"), so we do **not**
build or distribute our own device app. The older Google Play EMM API with a
custom DPC is closed to new registrations, and legacy "Device Administrator"
enrollment is deprecated on Google-certified devices (since 2024-12-31).

## Cost

- **Android Enterprise and the Android Management API are free** from Google;
  there is no per-device fee for the API itself. Managed Google Play is also free.
- You need a **Google Cloud project** (free to create). AMAPI calls fall under
  normal Cloud usage; for a handful of devices this is effectively zero.
- Real costs in this space come from commercial EMM products (examples seen:
  ~$1.80-3/device/month and up). Building our own on AMAPI avoids those.
- **Conclusion:** fits the zero/near-zero-cost goal, unlike per-seat EMM products.

## What setup requires

1. A **Google Cloud project** with the Android Management API enabled.
2. A **service account** (for server-to-server API calls) with credentials.
3. An **enterprise binding**, created via the signup flow:
   `signupUrls.create` → an admin completes sign-up with a Google account not
   already bound to an enterprise → `enterprises.create`. This binds the
   enterprise to our Cloud project. No paid Google Workspace domain is required.
4. (For a published commercial EMM only) joining the Android Enterprise EMM
   partner community. **Not required** to manage your own organization's devices
   via the signup flow, but confirm current terms in the partner portal.

## Enrollment models and methods

| Model | Ownership | Notes |
| --- | --- | --- |
| Fully managed | Company-owned | Full control of the whole device. Best fit for company phones. |
| Dedicated (kiosk) | Company-owned | Locked to one/few apps (signage, single-purpose). |
| Work profile (COPE) | Company-owned, Android 8+ | Separate work profile on a company device. |
| Work profile | Personal (BYOD) | Manages only the work profile; limited visibility. |

Enrollment methods: **QR code** (simplest, Android 8+), zero-touch (participating
OEMs), NFC, and token. We will target **fully managed via QR code** for company
phones.

## Capability matrix (what AMAPI can actually do)

| Capability | Available? | How |
| --- | --- | --- |
| Device inventory (model, OS, security patch, memory, etc.) | ✅ | `enterprises.devices.get/list` |
| Compliance / security status | ✅ | Policy + device `nonComplianceDetails`, `appliedState` |
| Policy enforcement (80+ settings) | ✅ | `enterprises.policies` applied to devices |
| Managed app install/config | ✅ | Policy `applications` via managed Google Play |
| Remote **lock** | ✅ | `devices.issueCommand` type `LOCK` |
| Remote **wipe** (factory reset / remove work profile) | ✅ | `issueCommand` type `WIPE`, or `devices.delete` |
| Reset password, reboot, clear app data | ✅ | `issueCommand` |
| **Location** | ⚠️ Limited | **Only via Lost Mode** (`START_LOST_MODE`): fully managed Android 11+, company-owned work profile Android 13+. Locks the device and reports its location to admins. No continuous GPS stream. |
| Live screen view / screenshots | ❌ | Not available through standard MDM/AMAPI. |
| Foreground app usage / keystrokes | ❌ | Not exposed by AMAPI; do not attempt. |
| Real-time change notifications | ✅ | Pub/Sub topic (optional; polling also works) |

## What this means for our product

- **Do** integrate AMAPI for: enrollment (QR), inventory, compliance, managed
  apps, remote lock/wipe, and location-via-lost-mode.
- **Do not** promise continuous location, screenshots, live screen view, or app
  usage on Android. Those work on our Windows agent, not via Android MDM.
- Android devices appear in the same dashboard as Windows devices, but their
  management actions and available data differ by platform (shown in the UI).

## Implemented in Milestone 8

- Backend configuration detection and an AMAPI client scaffold (`core/android.py`)
  with the exact API calls mapped for status, device list/get, enrollment token,
  and commands. It is **inactive until configured** with a service account and
  enterprise, and that live path is **untested here** (no Google project/device).
- Admin endpoints for Android status, device inventory, enrollment tokens, and
  commands, all gated on configuration with clear "not configured" responses.
- A dashboard "Android management" page showing configuration status, setup
  steps, the capability matrix, and (when configured) enrolled Android devices.

## To complete on real hardware (documented, not yet done)

1. Create a Google Cloud project; enable the Android Management API.
2. Create a service account; download its JSON key; set `ANDROID_SA_JSON` and
   `ANDROID_PROJECT_ID`.
3. Run the signup flow to create an enterprise; set `ANDROID_ENTERPRISE_NAME`
   (e.g. `enterprises/LC...`).
4. Generate a QR enrollment token from the dashboard; factory-reset a test phone
   and scan it to enroll as fully managed.
5. Verify inventory, a remote lock, and lost-mode location on that device, then
   update the compatibility table from ❓/🚧 to ✅ for what passes.

## Sources

- [Android Management API overview](https://developers.google.com/android/management)
- [Create an enterprise](https://developers.google.com/android/management/create-enterprise)
- [devices.issueCommand reference](https://developers.google.com/android/management/reference/rest/v1/enterprises.devices/issueCommand)
- [Join the EMM provider community](https://developers.google.com/android/management/join)
- [Managing Android devices without an app (codelab)](https://developer.android.com/codelabs/android-management-api)
- [Lost mode (Google admin help)](https://support.google.com/work/android/answer/13581513)
- [Android Enterprise cost (Cortado)](https://blog.cortado.com/en/android-for-work-cost/)
- [Intune: enroll dedicated/fully managed Android](https://learn.microsoft.com/en-us/intune/intune-service/enrollment/android-dedicated-devices-fully-managed-enroll)
