# Lab Opening Times — TRMNL private plugin

A private [TRMNL](https://trmnl.com) plugin that shows your lab's **rental opening
times** and live **state**, read straight from a Google Calendar.

- **Column 1 (large):** current status — `OPEN` with today's hours, or `DO NOT DISTURB`
  / `CLOSED`. When closed or in DND, today's opening hours stay on screen, just smaller.
- **Column 2:** the next 7 days, each with its hours or `Closed` / `DND`.
- Sized for the 800×480, 1-bit e-ink panel this firmware drives. Rendering happens on
  TRMNL's servers; the firmware just pulls the finished image.

State is taken from **keywords in each event's title**. Matching is **case-insensitive**
(`OPEN`, `Open`, and `open` are all equivalent), and an event matches if its title
*contains* any keyword from a list.

| State | Meaning | Default title keywords |
|-------|---------|------------------------|
| **open** | Renting possible | `open` |
| **busy / DND** | Lab in use, do not disturb | `busy`, `dnd`, `do not disturb`, `reserved`, `maintenance`, `workshop`, `in use` |
| **closed** | Holiday / outside hours | `closed`, `holiday`, `vacation`, `public holiday` |

Keyword lists are editable form fields, so you can use whatever wording your team prefers
(comma-separated). When a title matches more than one list, priority is
**closed > busy > open**. A title that matches none falls back to the **Default state**
field (default: `open`). Outside any event → `CLOSED`.

## How the calendar should look

- An **OPEN** event each day defines that day's hours, e.g. a *Open hours* event
  09:00–17:00. Multiple OPEN events on one day → the row spans the earliest start to the
  latest end.
- A **BUSY** event (e.g. *Reserved*, *Maintenance*) over part of the day flips the live
  status to *DO NOT DISTURB* while it's active; the day still shows its open hours with a
  `·DND` mark.
- A **CLOSED** all-day event (e.g. *Public holiday*) marks a holiday; that day shows
  `Closed`.

## One-time Google setup

1. **Make the lab calendar public.** Google Calendar → *Settings* → your calendar →
   *Access permissions* → tick **Make available to public** (See only free/busy is not
   enough; pick *See all event details*). Copy the **Calendar ID** from *Integrate
   calendar* (looks like `…@group.calendar.google.com`).
   *Privacy note:* a public calendar exposes event titles. Since state is read from the
   title keywords, keep titles simple and non-sensitive (e.g. "Open hours", "Reserved").
2. **Create an API key.** [Google Cloud Console](https://console.cloud.google.com) →
   new/any project → *APIs & Services* → **enable “Google Calendar API”** → *Credentials*
   → **Create credentials → API key**. Then *Edit* the key → **API restrictions →
   restrict to Google Calendar API** (and optionally an HTTP referrer/IP restriction).

## Install the plugin

1. Zip the **contents** of this folder (flat — `settings.yml` and the `*.liquid` files at
   the root of the zip, no enclosing folder).
2. TRMNL dashboard → **Plugins → Private Plugin → Import**, upload the zip.
3. Open the plugin's settings and fill the form fields:
   - **Lab name** — title bar text.
   - **Google Calendar ID** — from step 1.
   - **Google API key** — from step 2.
   - **OPEN / BUSY / CLOSED keywords** — comma-separated title words (case-insensitive).
     Defaults match the table above; change them to whatever wording your team uses.
   - **Default state** — what an unmatched event title means (usually `open`).
4. **Add the plugin to a playlist** and attach it to your device. Choose the **Full**
   layout for the two-column design (half/quadrant render a compact status-only view).

`refresh_interval` is 15 min in `settings.yml`; raise it (60/360/720/1440) to save battery.

## Previewing before you wire up the calendar

`sample-response.json` is a ready-made Calendar API payload (one open day, a midday DND,
a holiday, and varied upcoming days). In the plugin's **Edit Markup** screen, paste it as
the sample/preview data to see `full.liquid` render all three states at 800×480, then
switch the strategy to live polling.

## Files

| File | Purpose |
|------|---------|
| `settings.yml` | Import manifest: polling strategy, dynamic Calendar API URL, form fields. |
| `full.liquid` | **Primary** 800×480 two-column layout (status + this week). |
| `half_horizontal.liquid`, `half_vertical.liquid` | Compact status + today's hours. |
| `quadrant.liquid` | Minimal status badge + hours. |
| `sample-response.json` | Sample payload for the markup preview. |

## How it works (under the hood)

`settings.yml` builds a Calendar API URL with a dynamic window using TRMNL's Liquid date
helpers (`{{ 1 | days_ago }}`, `{{ "now" | date: "%s" | plus: … }}`) and your form fields
(`##{{ calendar_id }}`, `##{{ api_key }}`). TRMNL polls it; the JSON's `items` array lands
in the template. `full.liquid` classifies each event by the keywords in its title
(lower-cased on both sides, so capitalisation never matters), finds the active state now
(priority **closed > busy > open**), computes today's open span, and lays out the next
7 days. All time maths use UTC epoch seconds with `trmnl.user.utc_offset`, so it stays
correct across the lab's timezone.
