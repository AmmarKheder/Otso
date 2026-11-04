# Otso 2.0 — l'application iOS (App Store)

Ce dossier est l'enveloppe native de la page Otso : les fichiers de `../docs/` (la page, MapLibre, les dictionnaires)
sont embarqués dans une app iOS avec [Capacitor](https://capacitorjs.com) (WKWebView + plugins natifs), et les
données (prévision 0,4° et tuiles 1 km) sont lues en ligne comme sur le site. Rien ne tourne sur un serveur à nous.

Ce qui est natif dans l'app, en plus du site :
- position via le plugin Geolocation (une seule demande système, texte dans `Info.plist`) ;
- partage natif (feuille de partage iOS) du lieu choisi, bouton « Partager » dans la fiche ;
- retour haptique sur les puces (jours, couches, lignes de la fiche) ;
- barre d'état qui suit le thème clair/sombre, encoche et bords gérés (safe areas) ;
- écran de lancement et icône (générés depuis `../docs/assets/logo_mark.svg`) ;
- lieu mémorisé aussi dans les préférences natives (si le stockage web est vidé) ;
- les liens externes (article Foehn, GitHub, OSM) s'ouvrent dans une feuille Safari, pas dans l'app ;
- pas de service worker dans l'app (WKWebView met en cache les requêtes HTTP ; le hors-ligne complet viendra plus tard).

Identifiant : `com.ammarkheder.otso` · nom affiché : **Otso 2.0** · version 2.0.0 (build 1) · iOS 15 et plus · iPhone
(l'iPad en mode compatibilité ; passer `TARGETED_DEVICE_FAMILY` à `"1,2"` pour une vraie version iPad, avec ses captures).

## Sur le Mac : de zéro à TestFlight

Prérequis : Xcode à jour (App Store), Node 20 ou plus (`brew install node`), un compte
[Apple Developer Program](https://developer.apple.com/programs/) (99 USD par an ; l'inscription demande quelques jours).
CocoaPods n'est pas nécessaire : les plugins sont en Swift Package Manager.

```bash
git clone git@github.com:AmmarKheder/Otso.git && cd Otso/app      # ou git pull dans le clone existant
npm install                                                         # Capacitor 8 et les plugins
npm run sync                                                        # copie ../docs -> www/, puis "cap sync ios"
npx cap open ios                                                    # ouvre ios/App/App.xcodeproj dans Xcode
```

Dans Xcode :
1. Cible **App** → onglet *Signing & Capabilities* → cocher *Automatically manage signing* → choisir ton **Team**
   (ton compte développeur). Le bundle identifier `com.ammarkheder.otso` est créé dans ton compte au premier lancement.
2. Choisir un simulateur iPhone, ⌘R : l'app doit afficher la carte 1 km. Puis ton iPhone (câble, « Faire confiance »).
3. Première fois : Xcode télécharge les paquets Swift (Capacitor, plugins) ; si la résolution échoue, *File → Packages →
   Reset Package Caches*.
4. Pour l'App Store : *Product → Archive* (schéma « App », destination « Any iOS Device »), puis dans l'Organizer
   *Distribute App → App Store Connect → Upload*. À chaque nouvel envoi, augmenter le **Build** (`CURRENT_PROJECT_VERSION`,
   onglet *General* de la cible) : 1, 2, 3… ; la version marketing reste 2.0.0 jusqu'à la prochaine version.

Dans [App Store Connect](https://appstoreconnect.apple.com) :
1. *Apps → +* : nom **Otso 2.0**, langue principale anglais, bundle id `com.ammarkheder.otso`, SKU `otso`.
2. Onglet *TestFlight* : le build envoyé apparaît après traitement (10–30 min) ; s'ajouter en testeur interne et
   installer via l'app TestFlight sur l'iPhone. C'est le meilleur test réel avant la soumission.
3. Onglet *App Store* : remplir la fiche avec les textes de `STORE.md` (description, mots-clés, URL de confidentialité
   `https://ammarkheder.com/Otso/privacy/`, URL de support, captures d'écran), *App Privacy* (voir `STORE.md`),
   classification d'âge, puis *Add for Review → Submit*. Délai de relecture habituel : 1 à 3 jours.

## Mettre à jour l'app quand la page change

La page de l'app est une copie de `../docs/` au moment du `npm run sync`. Après un changement du site :

```bash
cd app && npm run sync && npx cap open ios     # puis Archive → Upload, build + 1
```

Les données (prévision, tuiles) ne sont pas embarquées : l'app lit toujours la dernière prévision en ligne, sans mise à
jour de l'app.

## Fichiers

- `capacitor.config.json` : identifiant, nom, dossier web, options iOS (écran de lancement, barre d'état).
- `build_www.sh` : construit `www/` depuis `../docs/` (sans la page classique, l'ancienne redirection 1km/, le QR, les
  côtes de la carte classique, le service worker) et insère `native.js` dans la page.
- `native.js` : le pont utilisé par la page quand elle tourne dans l'app (`window.OTSO_NATIVE`) : partage, haptique,
  position, préférences, barre d'état, navigateur intégré. Sur le site, ce fichier n'existe pas et la page l'ignore.
- `make_icons.js` → `assets/` : sources de l'icône (1024 px) et des écrans de lancement, puis
  `npm run assets` (ou `npx capacitor-assets generate --ios`) remplit `ios/App/App/Assets.xcassets/`.
- `ios/App/App/Info.plist` : texte de la demande de position, `ITSAppUsesNonExemptEncryption = false` (HTTPS seulement :
  pas de déclaration d'export à faire), orientations.
- `ios/App/App/PrivacyInfo.xcprivacy` : manifeste de confidentialité (pas de pistage, pas de donnée collectée ;
  UserDefaults via le plugin Preferences, raison CA92.1).
- `ios/App/CapApp-SPM/Package.swift` : les plugins (géré par `cap sync`, ne pas modifier à la main).
- `STORE.md` : textes de la fiche App Store, réponses *App Privacy*, notes pour la relecture, captures.

## Ce qui peut faire refuser l'app, et ce qu'on a fait

Apple refuse les apps qui ne sont « qu'un site dans une coque » (règle 4.2, fonctionnalité minimale). Otso 2.0 embarque
sa page (pas une URL distante), utilise des fonctions natives (position, partage, haptique, barre d'état, préférences),
a une icône et un écran de lancement propres, une politique de confidentialité et une page de support. Le texte de
l'app dit partout « prévision de recherche, pas une alerte officielle » : ce n'est pas une app médicale ni une alerte
(règles 1.4 et 5.1.3), et aucune donnée de santé n'est manipulée.

Si la relecture renvoie malgré tout un 4.2, les ajouts les plus efficaces sont, dans l'ordre : un widget d'écran
d'accueil (WidgetKit, Swift) avec la valeur du jour pour le lieu mémorisé ; une notification locale quotidienne quand
la prévision du jour est en ligne ; le hors-ligne complet (les dernières tuiles 1 km du lieu mémorisé).
