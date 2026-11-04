# Otso 2.0 — App Store listing (texts to paste in App Store Connect)

Everything here is in English (the primary language of the listing); add a French localisation later if wanted.

## Identity
- **Name:** Otso 2.0
- **Subtitle (30 chars max):** PM2.5 forecast at 1 km
- **Bundle ID:** com.ammarkheder.otso · **SKU:** otso · **Primary language:** English (U.K.)
- **Category:** Weather (primary), Education (secondary)
- **Copyright:** 2026 Ammar Kheder
- **Privacy policy URL:** https://ammarkheder.com/Otso/privacy/
- **Support URL:** https://ammarkheder.com/Otso/privacy/#contact (e-mail and the GitHub issues, no account needed)
- **Marketing URL:** https://ammarkheder.com/Otso/
- **Age rating:** 4+. In the 2025 questionnaire answer "None" to Medical/Treatment Information and Health/Wellness topics (an air-quality research forecast, not health advice), "No" to "Shared Location" (the position never leaves the device except the one place search, nothing is shared with other users), "No" to "Unrestricted Web Access" (the app loads only its own bundled page; every link opens in Safari, outside the app), "No" to everything else.
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
  Reason: when the user taps "My location", the coordinates are used on the device to centre the map, and are sent once,
  rounded to about 100 m, to the place-search service (Photon, OpenStreetMap data) to display the street name; nothing is
  stored off the device. The privacy manifest `PrivacyInfo.xcprivacy` declares the same (precise location, not linked, not
  for tracking, purpose app functionality).
- No other data type: no identifiers, no contact info, no usage data (the app does not call the website's visit counter),
  no diagnostics.
- **Tracking:** No (NSPrivacyTracking = false in the manifest).

## Export compliance
The app uses only HTTPS (standard encryption of the system): `ITSAppUsesNonExemptEncryption = false` is set in Info.plist,
so App Store Connect will not ask the encryption questions at each upload.

## Screenshots to take (on the iPhone or the simulator, in Xcode: ⌘S saves a PNG)
Required set (App Store Connect, November 2026): **iPhone with Dynamic Island, medium display**: 1206 × 2622 px portrait
(iPhone 17 / 17 Pro simulator) or 1179 × 2556 px (iPhone 16 simulator). Optional second set for the Plus / Pro Max / Air
product pages: large display, 1320 × 2868 px (iPhone 17 Pro Max simulator). No iPad set (iPhone-only app). Three to six
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
OpenFreeMap; both are public. The app is not a medical or safety app and gives no health advice: every screen says that it
is an experimental research forecast that does not replace official air-quality alerts; it does not diagnose, treat or
prevent any disease. Location is used on the device to centre the map; its coordinates, rounded to about 100 m, are sent
once to the OpenStreetMap place search (Photon) to name the street, and never to us (privacy policy:
https://ammarkheder.com/Otso/privacy/). Native features: position (system prompt), share sheet on the place card,
haptics on the day and layer chips, status bar following the theme, launch screen. Contact: ammar.kheder@lut.fi,
https://github.com/AmmarKheder/Otso/issues

## Checklist before "Submit for Review"
- [ ] Build uploaded from Xcode (Archive → Distribute → App Store Connect), processed, visible in TestFlight.
- [ ] Tested on a real iPhone through TestFlight: map, search, position prompt text, share sheet, dark mode, external links.
- [ ] Listing: name, subtitle, description, keywords, promotional text, screenshots (Dynamic Island medium display),
      support URL, marketing URL, privacy policy URL, copyright, category, age rating, App Privacy answers.
- [ ] Apple Developer Program enrollment done (web, 99 USD/year; from a few days to several weeks: start now); Agreements,
      Tax and Banking: the free-apps agreement accepted in App Store Connect; DSA: "not a trader" if the app stays free.
- [ ] Version 2.0.0, build number increased at each upload.
- [ ] Contact information for App Review (name, phone, e-mail) filled in; sign-in not required (tick "Sign-in not required").
