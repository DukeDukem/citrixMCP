"""
Probe Sprinklr page for callable audio sources (WebRTC / <audio> / captions).

Usage (during a live CALL preferred):
  uv run python .cursor/skills/sprinklr-call-listen/probe_call_audio.py
  uv run python .cursor/skills/sprinklr-call-listen/probe_call_audio.py --lock

Writes:
  .cursor/reports/call-audio-probe-{FALL|nocall}.json
  With --lock: .cursor/skills/sprinklr-call-listen/capture_path.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SKILL = Path(__file__).resolve().parent
_REPO = _SKILL.parent.parent.parent
_REPORTS = _REPO / ".cursor" / "reports"
_CAPTURE_PATH = _SKILL / "capture_path.json"

# JS: inventory media / WebRTC / caption-like DOM (read-only; no recording).
_PROBE_JS = """
() => {
  const text = (document.body && document.body.innerText) || '';
  const lower = text.toLowerCase();

  // Existing RTCPeerConnections (may be empty if constructed before hook)
  const pcs = window.__sprCallPcs || [];
  let remoteAudioTracks = 0;
  let localAudioTracks = 0;
  const pcSummaries = [];
  for (const pc of pcs) {
    try {
      const recvs = pc.getReceivers ? pc.getReceivers() : [];
      const sends = pc.getSenders ? pc.getSenders() : [];
      let rA = 0, lA = 0;
      for (const r of recvs) {
        if (r.track && r.track.kind === 'audio') { rA++; remoteAudioTracks++; }
      }
      for (const s of sends) {
        if (s.track && s.track.kind === 'audio') { lA++; localAudioTracks++; }
      }
      pcSummaries.push({
        connectionState: pc.connectionState || null,
        iceConnectionState: pc.iceConnectionState || null,
        remoteAudio: rA,
        localAudio: lA,
      });
    } catch (e) {
      pcSummaries.push({ error: String(e) });
    }
  }

  const audioEls = Array.from(document.querySelectorAll('audio'));
  const audioInfo = audioEls.map((a, i) => {
    let hasSrcObject = false;
    try { hasSrcObject = !!(a.srcObject); } catch (e) {}
    return {
      index: i,
      paused: !!a.paused,
      muted: !!a.muted,
      currentSrc: (a.currentSrc || a.src || '').slice(0, 120),
      hasSrcObject,
      readyState: a.readyState,
      testId: a.getAttribute('data-testid') || null,
    };
  });

  const videoEls = document.querySelectorAll('video').length;

  // Caption / transcript heuristics
  const captionHints = [];
  const captionSelectors = [
    '[data-testid*="caption"]',
    '[data-testid*="transcript"]',
    '[data-testid*="live-caption"]',
    '[aria-label*="Untertitel"]',
    '[aria-label*="Transkript"]',
    '[class*="transcript"]',
    '[class*="caption"]',
  ];
  for (const sel of captionSelectors) {
    const n = document.querySelectorAll(sel).length;
    if (n) captionHints.push({ selector: sel, count: n });
  }
  const bodyHasCaptionWords =
    /live\\s*caption|untertitel|transkript|transcript|closed\\s*caption/i.test(text);

  // Call UI markers
  const markers = {
    imGespraech: text.indexOf('Im Gespräch') !== -1,
    eingehenderAnruf: text.indexOf('Eingehender Anruf') !== -1,
    anrufBeendet: text.indexOf('Anruf beendet') !== -1,
    disposition: text.indexOf('Disposition') !== -1,
    aufzeichnung: /Aufzeichnung/i.test(text),
    audioPres: document.querySelectorAll('[data-testid="audio_pres"]').length,
    omniMedia: document.querySelectorAll('[data-testid="omniMedia"], [data-testid*="mediaItems"]').length,
    htmlMessage: document.querySelectorAll('[data-testid="html-message-content"]').length,
  };

  return {
    url: location.href,
    title: document.title || '',
    hookedPcCount: pcs.length,
    remoteAudioTracks,
    localAudioTracks,
    pcSummaries,
    audioElements: audioInfo,
    videoElementCount: videoEls,
    captionHints,
    bodyHasCaptionWords,
    markers,
    mediaDevices: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
    rtcPeerConnectionDefined: typeof RTCPeerConnection !== 'undefined',
  };
}
"""

# Install a passive PC tracker so later probes (and listen) can see connections.
_HOOK_PCS_JS = """
() => {
  if (window.__sprCallPcHooked) return { already: true, count: (window.__sprCallPcs || []).length };
  window.__sprCallPcs = window.__sprCallPcs || [];
  const Orig = window.RTCPeerConnection;
  if (!Orig) return { already: false, error: 'no RTCPeerConnection' };
  window.RTCPeerConnection = function (...args) {
    const pc = new Orig(...args);
    try { window.__sprCallPcs.push(pc); } catch (e) {}
    return pc;
  };
  window.RTCPeerConnection.prototype = Orig.prototype;
  try {
    Object.keys(Orig).forEach((k) => {
      try { window.RTCPeerConnection[k] = Orig[k]; } catch (e) {}
    });
  } catch (e) {}
  window.__sprCallPcHooked = true;
  return { already: false, hooked: true };
}
"""


def _recommend_path(probe: dict) -> str:
    """Choose capture path from probe (plan default: webrtc_hook)."""
    markers = probe.get("markers") or {}
    if probe.get("captionHints") or probe.get("bodyHasCaptionWords"):
        # Prefer scraping captions if UI exposes them
        return "sprinklr_captions"
    if (probe.get("remoteAudioTracks") or 0) > 0:
        return "webrtc_hook"
    audio_els = probe.get("audioElements") or []
    if any(a.get("hasSrcObject") or (a.get("currentSrc") or "").startswith("blob:") for a in audio_els):
        return "html_audio"
    if markers.get("imGespraech") or markers.get("disposition"):
        # Live call UI but no tracks yet — still prefer webrtc after hook settles
        return "webrtc_hook"
    return "webrtc_hook"


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe Sprinklr call audio sources")
    ap.add_argument(
        "--lock",
        action="store_true",
        help="Write capture_path.json from this probe recommendation",
    )
    ap.add_argument("--cdp", default=None, help="CDP endpoint override")
    args = ap.parse_args()

    sys.path.insert(0, str(_SKILL))
    from cdp_util import (
        call_markers,
        connect_browser,
        extract_fall_id,
        find_sprinklr_page,
        is_call_channel,
        load_cdp_endpoint,
    )

    endpoint = args.cdp or load_cdp_endpoint()
    print(f"PROBE: connecting CDP {endpoint}")
    try:
        pw, browser, ep = connect_browser(endpoint)
    except Exception as e:
        print(f"ERROR: CDP connect failed: {e}", file=sys.stderr)
        print("Start Chrome with --remote-debugging-port=9222 and open Sprinklr.", file=sys.stderr)
        return 2

    try:
        page = find_sprinklr_page(browser)
        if not page:
            print("ERROR: No Sprinklr tab found", file=sys.stderr)
            return 3

        try:
            page.evaluate(_HOOK_PCS_JS)
        except Exception as e:
            print(f"[WARN] PC hook: {e}")

        fall = extract_fall_id(page) or "nocall"
        markers = call_markers(page)
        probe = page.evaluate(_PROBE_JS) or {}
        probe["fall"] = fall
        probe["call_markers_side"] = markers
        probe["is_call_channel"] = is_call_channel(markers) or is_call_channel(
            probe.get("markers") or {}
        )
        probe["probed_at"] = datetime.now(timezone.utc).isoformat()
        probe["cdp"] = ep
        recommended = _recommend_path(probe)
        probe["recommended_capture_path"] = recommended
        # Fallback note per plan
        probe["fallback_if_webrtc_fails"] = "windows_loopback"
        probe["notes"] = (
            "Run again while Im Gespräch is visible for best WebRTC track counts. "
            "If remoteAudioTracks stays 0 during a live call, lock path to windows_loopback."
        )

        _REPORTS.mkdir(parents=True, exist_ok=True)
        out = _REPORTS / f"call-audio-probe-{fall}.json"
        out.write_text(json.dumps(probe, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"PROBE_OK fall={fall}")
        print(f"PROBE_REPORT {out}")
        print(f"RECOMMENDED_CAPTURE_PATH {recommended}")
        print(f"IS_CALL {probe['is_call_channel']}")
        print(f"remoteAudioTracks={probe.get('remoteAudioTracks')} audioEls={len(probe.get('audioElements') or [])}")

        if args.lock:
            lock = {
                "capture_path": recommended,
                "fallback": "windows_loopback",
                "locked_at": datetime.now(timezone.utc).isoformat(),
                "locked_from_probe": str(out),
                "fall_at_lock": fall,
                "live_call_confirmed": bool(probe.get("is_call_channel")),
                "stt": "faster-whisper",
                "stt_language": "de",
                "notes": (
                    "v1 default webrtc_hook per plan. Re-run probe_call_audio.py --lock "
                    "during a live CALL to confirm tracks; if remoteAudioTracks=0, set "
                    "capture_path to windows_loopback."
                ),
            }
            _CAPTURE_PATH.write_text(
                json.dumps(lock, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(f"CAPTURE_PATH_LOCKED {_CAPTURE_PATH}")
            print(f"CAPTURE_PATH={recommended}")

        return 0
    finally:
        try:
            pw.stop()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
