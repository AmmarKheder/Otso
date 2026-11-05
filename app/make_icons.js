// Otso 2.0 icons from the two logo sources in ../docs/assets (Otava's seven stars as particles in the PM2.5 colours):
//   logo_icon.svg (square, night blue) -> the iOS app icon and the site's home-screen / PWA icons
//   logo_mark.svg (round)              -> the site's favicon (the top bar uses the SVG itself)
// The launch screen is plain night blue: the opening animation in the page lights the stars up on it (index.html, #intro).
// Run: node make_icons.js   (writes into ios/App/App/Assets.xcassets, assets/ and ../docs; no "cap sync" needed for these)
const sharp = require("sharp"), fs = require("fs"), path = require("path");
const D = path.join(__dirname, "..", "docs"), A = path.join(__dirname, "assets"), X = path.join(__dirname, "ios/App/App/Assets.xcassets");
const NIGHT = "#0F1B3D";
const icon = fs.readFileSync(path.join(D, "assets/logo_icon.svg")), mark = fs.readFileSync(path.join(D, "assets/logo_mark.svg"));
const png = (svg, size) => sharp(svg, { density: Math.ceil(72 * size / 1024) + 1 }).resize(size, size).png();
const flat = (svg, size, file) => png(svg, size).flatten({ background: NIGHT }).removeAlpha().toFile(file);
const plain = (size, file) => sharp({ create: { width: size, height: size, channels: 3, background: NIGHT } }).png().toFile(file);
(async () => {
  fs.mkdirSync(A, { recursive: true });
  // iOS: one 1024 px opaque icon; the launch screen image set (1366 pt, @1x @2x @3x, light and dark) in night blue
  await flat(icon, 1024, path.join(X, "AppIcon.appiconset/AppIcon-512@2x.png"));
  for (const [s, n] of [[1366, "1x"], [2732, "2x"], [4098, "3x"]])
    for (const dark of ["", "-dark"]) await plain(s, path.join(X, `Splash.imageset/Default@${n}~universal~anyany${dark}.png`));
  // the sources @capacitor/assets would use (kept in step, e.g. for an Android build)
  await flat(icon, 1024, path.join(A, "icon-only.png"));
  await plain(1024, path.join(A, "icon-background.png"));
  await sharp(Buffer.from(icon.toString().replace(/<rect[^>]*\/>/, ""))).resize(1024, 1024).png().toFile(path.join(A, "icon-foreground.png"));
  await plain(2732, path.join(A, "splash.png")); await plain(2732, path.join(A, "splash-dark.png"));
  // the website: home-screen icon (iOS), PWA icons (the maskable one keeps the stars inside the central 80 % circle), favicon
  await flat(icon, 180, path.join(D, "apple-touch-icon.png"));
  await flat(icon, 192, path.join(D, "icon-192.png"));
  await flat(icon, 512, path.join(D, "icon-512.png"));
  const inner = await png(icon, 420).toBuffer();
  await sharp({ create: { width: 512, height: 512, channels: 3, background: NIGHT } }).composite([{ input: inner, gravity: "centre" }]).flatten({ background: NIGHT }).removeAlpha().png().toFile(path.join(D, "icon-512-maskable.png"));
  await png(mark, 64).toFile(path.join(D, "assets/favicon.png"));
  for (const f of [path.join(X, "AppIcon.appiconset/AppIcon-512@2x.png"), path.join(D, "apple-touch-icon.png"), path.join(D, "assets/favicon.png"), path.join(D, "icon-512-maskable.png")]) {
    const m = await sharp(f).metadata(); console.log(path.relative(path.join(__dirname, ".."), f), m.width + "x" + m.height, m.hasAlpha ? "alpha" : "opaque"); }
})();
