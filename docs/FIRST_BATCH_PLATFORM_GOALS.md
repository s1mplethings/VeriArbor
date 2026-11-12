# VeriArbor / Promotion Studio: First-Batch Platform Goals

## Purpose

This document records the first real-platform experiment targets for the
VeriArbor research preview. It describes planned work and accepted evidence; it
does not claim that a platform integration is live.

The first release is a **Research Preview / Alpha**. It is not a production or
formally certified delivery.

## First batch

| Platform | First-round method | Completion evidence | Must not be claimed |
|---|---|---|---|
| Bluesky | Existing text-only AT Protocol adapter; use official endpoints; one explicitly authorized post at a time | Real authentication, one approved text post, URI/CID/link receipt, and recovery check | Offline tests are not a live post. Media, threads, facets, and analytics are not supported. |
| Reddit | Promotion Studio prepares title/body; a human posts in a community that permits it and records the URL | Real post URL, content mapping, human confirmation, and note of removal/restriction if any | Automatic submission is not implemented. No bulk promotion or platform-rule bypass. |
| YouTube | An original short demo video is uploaded manually and explicitly set to **Private** | Video ID, processing state, privacy state, and receipt record | Automatic video upload is not implemented. Unlisted is not Private. |

Bilibili and Xiaohongshu are second-batch candidates. X is outside this first
batch. Any scope change must update this document explicitly.

## Release target

- Repository: `s1mplethings/VeriArbor`.
- The pure policy library remains under `src/veriarbor`.
- Promotion Studio is a standalone application under `apps/promotion_studio`
  with its own README, tests, dependencies, and provenance.
- Release level: Research Preview / Alpha. Do not label it production-ready or
  formally trust-anchored.
- Publishing source on GitHub does not close the P11 security hold and does not
  deploy a formal trust anchor, signer, or final trusted-delivery process.

## Status vocabulary

Use these labels with evidence:

- `NOT_STARTED`: no implementation or evidence yet.
- `OFFLINE_TESTED`: local/offline tests pass; no live platform claim.
- `AUTH_VERIFIED`: real account authentication succeeded; no post implied.
- `LIVE_VERIFIED`: a real platform action was completed and independently
  checked.
- `MANUAL_CONFIRMED`: a human completed the action and recorded evidence.
- `BLOCKED`: a concrete blocker is recorded.

## Current status

| Item | Status | Evidence |
|---|---|---|
| Promotion Studio local GUI and local simulated publishing | OFFLINE_TESTED | Local test suite and smoke run |
| Bluesky text adapter | OFFLINE_TESTED | Offline adapter and reliability tests; no real credentials used |
| Bluesky live authentication/post | NOT_STARTED | Requires owner-supplied App Password and explicit approval |
| Reddit | NOT_STARTED | Human workflow only |
| YouTube | NOT_STARTED | Human upload, Private visibility |
| P11 formal trust anchor / signed delivery | BLOCKED | Security hold remains in place |

## Boundaries

- Do not run real social publishing as part of release validation.
- Do not read or commit App Passwords, OAuth/JWT tokens, cookies, browser
  profiles, private keys, or real local-data stores.
- Keep the local GUI bound to loopback by default.
- Keep Bluesky in dry-run by default; live publishing requires explicit
  authorization.
- Do not install an automatic scheduler as a system task without the user's
  explicit action.
