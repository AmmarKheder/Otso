# Otso 2.0 — App Store listing (texts to paste in App Store Connect)

Everything here is in English (the primary language of the listing); add a French localisation later if wanted.

## Identity
- **Name:** Otso 2.0
- **Subtitle (30 chars max):** PM2.5 forecast at 1 km
- **Bundle ID:** com.ammarkheder.otso · **SKU:** otso · **Primary language:** English (U.K.)
- **Category:** Weather (primary), Education (secondary)
- **Copyright:** 2026 Ammar Kheder
- **Privacy policy URL:** https://ammarkheder.com/Otso/privacy/
- **Support URL:** https://github.com/AmmarKheder/Otso/issues
- **Marketing URL:** https://ammarkheder.com/Otso/
- **Age rating:** 4+ (no objectionable content; answer "No" to everything; "Unrestricted web access": No, the app only loads its own page and opens external links in Safari)
- **Price:** Free · no in-app purchases · no ads

## Promotional text (170 chars max)
Where will the fine particles be tomorrow, down to your street? A daily research forecast of PM2.5 at 1 km, five days ahead, on a street map.

## Description
Otso 2.0 shows where fine particulate matter (PM2.5) will be over the next five days, at the scale of a square kilometre, on a street map.

Every morning, a deep-learning model runs on the day's atmospheric analysis of the Copernicus Atmosphere Monitoring Service, the ECMWF weather forecast and the fires seen by satellite, computes the transport of the air and forecasts PM2.5 from all its sources: traffic, industry, heating, agriculture, dust, sea salt and fires, over all land, as an ensemble of eight members. A second, generative model then draws the forecast at 1 km, trained on a satellite and station record of PM2.5.

• Search any city, street or address, or use your position, and read the forecast for that square kilometre.
• Five days ahead: the daily mean at 1 km, how the day evolves every 12 hours, and what it means in plain words.
• Three map layers: the 1 km daily mean, the number of ensemble members above the WHO 24-hour guideline (15 µg/m³), and the 40 km forecast every 12 hours.
• A table of sixty cities, to which you can add your own.
• Dark mode, 37 languages, share a place with a link.
• Scores: how the forecast compares with air-quality monitors and with the Copernicus analysis, updated every day.

Otso is a research forecast from the Atmospheric Modelling Centre Lahti (University of Helsinki, LUT University). It is not an official air-quality service and does not replace the forecasts, indices and alerts of your national or local authorities. If you must decide something about your health, use those.

Contains modified Copernicus Atmosphere Monitoring Service information 2026; ECMWF open data (CC BY 4.0); street map © OpenMapTiles, data © OpenStreetMap contributors; city names © GeoNames (CC BY 4.0).

## Keywords (100 chars max, comma-separated)
air quality,PM2.5,pollution,forecast,particulate,smog,AQI,dust,wildfire smoke,weather,map

## What's new (version 2.0.0)
First App Store release: the Otso forecast drawn at 1 km on a street map, search of streets and addresses, five-day place card, native share and position.

## App Privacy (App Store Connect → App Privacy)
Answer: **data is collected** = No for everything that is not listed; declare only:
- **Location → Precise Location**: used for **App Functionality**; **Not linked** to the user's identity; **Not used for tracking**.
  Reason: when the user taps "My location", the coordinates are used on the device to centre the map, and are sent once to the
  place-search service (Photon, OpenStreetMap data) to display the street name; nothing is stored off the device.
  (If you prefer the strictest reading, "Data Not Collected" is defensible: the transmission only serves the request in real
  time. Declaring Precise Location is the safer choice with reviewers.)
- No other data type: no identifiers, no contact info, no usage data, no diagnostics (the anonymous visit counter of the
  website stores a per-device flag locally and sends no identifier; it is a public counter, not analytics).
- **Tracking:** No. The privacy manifest `PrivacyInfo.xcprivacy` says the same (NSPrivacyTracking = false).

## Export compliance
The app uses only HTTPS (standard encryption of the system): `ITSAppUsesNonExemptEncryption = false` is set in Info.plist,
so App Store Connect will not ask the encryption questions at each upload.

## Screenshots to take (on the iPhone or the simulator, in Xcode: ⌘S saves a PNG)
Required set: **6.9-inch iPhone** (e.g. iPhone 16 Pro Max / 17 Pro Max simulator, 1320 × 2868 px portrait). Three to six
images, in this order:
1. the map at 1 km over a polluted region at country scale (e.g. northern India or eastern China), layer "1 km · daily mean";
2. a street-level view with the popup (value, class, members above 15, 40 km cell);
3. the place card (big value, five days, 12-hour curve) for the user's city;
4. the "Members > 15" layer over Europe;
5. the cities table;
6. dark mode.
Take them with `?lang=en` (English listing). Optional: the same in French for the French localisation. No frames or text are
needed; Apple shows the raw screenshots.

## Notes for the reviewer (App Review Information → Notes)
Otso 2.0 is a research forecast of fine particulate matter (PM2.5) from a university group (Atmospheric Modelling Centre
Lahti, University of Helsinki / LUT University). There is no account and no sign-in: the app works as soon as it opens.
Tap "My location" or search a city (for instance "Helsinki" or "Lahti") to see the forecast for that place; tap the map to
read any square kilometre. The forecast data is fetched from GitHub (raw.githubusercontent.com) and the street map from
OpenFreeMap; both are public. The app is not a medical or safety app: every screen says that it is a research forecast
and does not replace official air-quality alerts. Location is used only on the device to centre the map (see the privacy
policy at https://ammarkheder.com/Otso/privacy/). Contact: https://github.com/AmmarKheder/Otso/issues

## Checklist before "Submit for Review"
- [ ] Build uploaded from Xcode (Archive → Distribute → App Store Connect), processed, visible in TestFlight.
- [ ] Tested on a real iPhone through TestFlight: map, search, position prompt text, share sheet, dark mode, external links.
- [ ] Listing: name, subtitle, description, keywords, promotional text, screenshots 6.9", support URL, marketing URL,
      privacy policy URL, copyright, category, age rating, App Privacy answers.
- [ ] Version 2.0.0, build number increased at each upload.
- [ ] Contact information for App Review (name, phone, e-mail) filled in; sign-in not required (tick "Sign-in not required").
