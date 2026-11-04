// Otso 2.0 native shell (Capacitor, iOS): the small bridge the page uses when it runs inside the app.
// Loaded after plugins.js and before the page's script; does nothing on the website (no Capacitor there).
(() => {
  const B = window.OTSO_PLUGINS || {}, C = B.Capacitor || window.Capacitor; if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  const P = Object.keys(B).length ? B : (C.Plugins || {});                                   // plugins.js (bundled) first, the runtime's global as a fallback
  const SITE = "https://ammarkheder.com/Otso/";
  document.documentElement.classList.add("native");
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
    statusBar: async (dark) => { try { if (P.StatusBar) await P.StatusBar.setStyle({ style: dark ? "DARK" : "LIGHT" }); } catch (e) {} },
    openExternal: (url) => { try { if (P.App && P.App.openUrl) return P.App.openUrl({ url }); } catch (e) {} window.open(url, "_blank"); },   // the system browser (outside the app): no in-app web browsing
    hideSplash: () => { try { P.SplashScreen && P.SplashScreen.hide(); } catch (e) {} },
  };
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
  window.addEventListener("load", () => setTimeout(N.hideSplash, 400));
})();
