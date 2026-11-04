// Otso 2.0 native shell (Capacitor, iOS): the small bridge the page uses when it runs inside the app.
// Loaded before the page's script; does nothing on the website (no window.Capacitor there).
(() => {
  const C = window.Capacitor; if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  const P = C.Plugins || {};
  document.documentElement.classList.add("native");
  const N = window.OTSO_NATIVE = {
    platform: C.getPlatform(),
    share: (o) => (P.Share ? P.Share.share(o) : navigator.share ? navigator.share(o) : Promise.reject(new Error("no share"))),
    haptic: (t) => { try { if (!P.Haptics) return; if (t === "select") P.Haptics.selectionStart().then(() => P.Haptics.selectionChanged()).then(() => P.Haptics.selectionEnd()).catch(() => {}); else P.Haptics.impact({ style: t || "LIGHT" }).catch(() => {}); } catch (e) {} },
    getPosition: (opts) => (P.Geolocation ? P.Geolocation.getCurrentPosition(Object.assign({ enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 }, opts || {})) : new Promise((ok, err) => navigator.geolocation.getCurrentPosition(ok, err, opts))),
    prefsGet: async (k) => { try { return P.Preferences ? (await P.Preferences.get({ key: k })).value : null; } catch (e) { return null; } },
    prefsSet: async (k, v) => { try { if (P.Preferences) await P.Preferences.set({ key: k, value: v }); } catch (e) {} },
    statusBar: async (dark) => { try { if (P.StatusBar) await P.StatusBar.setStyle({ style: dark ? "DARK" : "LIGHT" }); } catch (e) {} },
    openExternal: (url) => { try { if (P.Browser) return P.Browser.open({ url, presentationStyle: "popover" }); } catch (e) {} window.open(url, "_blank"); },
    hideSplash: () => { try { P.SplashScreen && P.SplashScreen.hide(); } catch (e) {} },
  };
  // links to other sites open in an in-app browser sheet, never inside the app's own web view
  document.addEventListener("click", (ev) => { const a = ev.target.closest("a[href]"); if (!a) return; const u = a.getAttribute("href") || "";
    if (/^https?:\/\//i.test(u) && !u.startsWith("https://ammarkheder.com/Otso/?")) { ev.preventDefault(); N.openExternal(u); } }, true);
  window.addEventListener("load", () => setTimeout(N.hideSplash, 400));
})();
