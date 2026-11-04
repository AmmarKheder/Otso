// Otso 2.0: the Capacitor plugins the page uses, bundled by esbuild into plugins.js (no bundler in the page itself).
import { Capacitor } from "@capacitor/core";
import { Geolocation } from "@capacitor/geolocation";
import { Share } from "@capacitor/share";
import { Haptics } from "@capacitor/haptics";
import { StatusBar } from "@capacitor/status-bar";
import { SplashScreen } from "@capacitor/splash-screen";
import { Preferences } from "@capacitor/preferences";
import { Browser } from "@capacitor/browser";
import { App } from "@capacitor/app";
window.OTSO_PLUGINS = { Capacitor, Geolocation, Share, Haptics, StatusBar, SplashScreen, Preferences, Browser, App };
