// Otso 2.0 native shell (Capacitor, iOS): the small bridge the page uses when it runs inside the app.
// Loaded after plugins.js and before the page's script; does nothing on the website (no Capacitor there).
(() => {
  const B = window.OTSO_PLUGINS || {}, C = B.Capacitor || window.Capacitor; if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  const P = Object.keys(B).length ? B : (C.Plugins || {});                                   // plugins.js (bundled) first, the runtime's global as a fallback
  const SITE = "https://ammarkheder.com/Otso/";
  document.documentElement.classList.add("native");
  // the page's overflow-x:hidden on html/body turns off the sticky top bar, so content scrolled under the status bar:
  // clip keeps the sideways cut without breaking sticky (iOS 16+); the band behind the status bar covers iOS 15 too
  const st = document.createElement("style");
  st.textContent = "html.native,html.native body{overflow-x:clip}" +
    "html.native body::before{content:'';position:fixed;top:0;left:0;right:0;height:env(safe-area-inset-top);background:var(--bg);z-index:40;pointer-events:none}";
  document.head.appendChild(st);
  const N = window.OTSO_NATIVE = {
    platform: C.getPlatform(),
    share: (o) => (P.Share ? P.Share.share(o) : navigator.share ? navigator.share(o) : Promise.reject(new Error("no share"))),
    haptic: (t) => { try { if (!P.Haptics) return; if (t === "select") P.Haptics.selectionStart().then(() => P.Haptics.selectionChanged()).then(() => P.Haptics.selectionEnd()).catch(() => {}); else P.Haptics.impact({ style: t || "LIGHT" }).catch(() => {}); } catch (e) {} },
    // the native plugin rejects with string codes (OS-PLUG-GLOC-0003 denied, 0007 services off, 0008 restricted, 0010 timeout): mapped to the W3C codes the page tests (1 refused, 2 unavailable, 3 timeout)
    getPosition: (opts) => (P.Geolocation
      ? P.Geolocation.getCurrentPosition(Object.assign({ enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 }, opts || {}))
          .catch((e) => { const c = String((e && e.code) || ""); throw Object.assign(new Error((e && e.message) || "geolocation"), { code: /GLOC-000[38]$/.test(c) ? 1 : /GLOC-0010$/.test(c) ? 3 : 2, nativeCode: c }); })
      : new Promise((ok, err) => navigator.geolocation.getCurrentPosition(ok, err, opts))),
    prefsGet: async (k) => { try { return P.Preferences ? (await P.Preferences.get({ key: k })).value : null; } catch (e) { return null; } },
    prefsSet: async (k, v) => { try { if (P.Preferences) await P.Preferences.set({ key: k, value: v }); } catch (e) {} },
    statusBar: async (dark) => { sbDark = dark; if (intro()) return;                         // during the opening animation the bar stays light on the night blue
      try { if (P.StatusBar) await P.StatusBar.setStyle({ style: dark ? "DARK" : "LIGHT" }); } catch (e) {} },
    openExternal: (url) => { window.open(url, "_blank"); },   // a new-window request: Capacitor hands it to the system browser (Safari, outside the app); always called from a click
    hideSplash: (ms) => { try { P.SplashScreen && P.SplashScreen.hide({ fadeOutDuration: ms == null ? 200 : ms }); } catch (e) {} },
  };
  const intro = () => document.documentElement.classList.contains("intro");
  let sbDark = null;
  // links: other sites, and the site's other pages (classic/, privacy/, scores, the full site behind the About tab) open in Safari;
  // only in-page anchors stay in the app (the bundle holds the page alone)
  document.addEventListener("click", (ev) => { const a = ev.target.closest("a[href]"); if (!a) return; const u = a.getAttribute("href") || "";
    if (u.startsWith("#") || u === "") return;
    if (/^\?full=1/.test(u)) { ev.preventDefault(); N.openExternal(SITE + u); return; }
    if (/^https?:\/\//i.test(u)) { ev.preventDefault(); N.openExternal(u); return; }
    if (!/^[a-z]+:/i.test(u)) { ev.preventDefault(); N.openExternal(SITE + u.replace(/^\.?\//, "")); } }, true);
  // after a long stay in the background iOS may have killed the map's workers: the page reloads itself (its state is in the URL and the storage)
  let hiddenAt = 0;
  const onState = (active) => { if (!active) hiddenAt = Date.now(); else if (hiddenAt && Date.now() - hiddenAt > 15 * 60e3) location.reload(); else hiddenAt = 0; };
  try { if (P.App && P.App.addListener) P.App.addListener("appStateChange", (s) => onState(!!s.isActive)); } catch (e) {}
  document.addEventListener("visibilitychange", () => onState(document.visibilityState === "visible"));
  // launch: the launch screen and the opening animation share the same night blue, so the native screen is lifted as soon as the
  // page has painted one frame and the stars start lighting up on it (#intro in the page); without the animation, once the page has loaded
  if (intro()) {
    try { if (P.StatusBar) P.StatusBar.setStyle({ style: "DARK" }); } catch (e) {}
    requestAnimationFrame(() => requestAnimationFrame(() => { N.hideSplash(120); document.documentElement.classList.add("go"); }));
    window.addEventListener("otso-intro-done", () => N.statusBar(sbDark != null ? sbDark : document.documentElement.dataset.theme === "dark"), { once: true });
  } else window.addEventListener("load", () => setTimeout(N.hideSplash, 400));
})();
