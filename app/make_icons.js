// Otso 2.0 icon and splash sources (1024 px icon, 2732 px splashes) from the site's logo, for @capacitor/assets.
const sharp = require("sharp"), fs = require("fs");
const svg = fs.readFileSync(__dirname + "/../docs/assets/logo_mark.svg");
(async () => {
  const logo = await sharp(svg, { limitInputPixels: false }).resize(1024, 1024, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } }).png().toBuffer();
  // icon: the logo on the site's blue, with a margin (iOS rounds the corners itself); opaque
  const inner = await sharp(logo).resize(820, 820, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } }).toBuffer();
  await sharp({ create: { width: 1024, height: 1024, channels: 4, background: "#1F5AA6" } }).composite([{ input: inner, gravity: "centre" }]).flatten({ background: "#1F5AA6" }).png().toFile(__dirname + "/assets/icon-only.png");
  await sharp({ create: { width: 1024, height: 1024, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } }).composite([{ input: inner, gravity: "centre" }]).png().toFile(__dirname + "/assets/icon-foreground.png");
  await sharp({ create: { width: 1024, height: 1024, channels: 4, background: "#1F5AA6" } }).png().toFile(__dirname + "/assets/icon-background.png");
  // splash: the logo centred on white (light) and on the dark background
  const mid = await sharp(logo).resize(560, 560, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } }).toBuffer();
  for (const [name, bg] of [["splash.png", "#ffffff"], ["splash-dark.png", "#0f1720"]])
    await sharp({ create: { width: 2732, height: 2732, channels: 4, background: bg } }).composite([{ input: mid, gravity: "centre" }]).flatten({ background: bg }).png().toFile(__dirname + "/assets/" + name);
  for (const f of fs.readdirSync(__dirname + "/assets")) { const m = await sharp(__dirname + "/assets/" + f).metadata(); console.log(f, m.width, m.height, m.channels, m.hasAlpha); }
})();
