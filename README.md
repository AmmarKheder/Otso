# Otso 1 km: live verification at the monitors

`history.json` is rebuilt every day by the Otso chain on LUMI: the published 1 km forecast of each issue day, kept at the
pixels of the OpenAQ monitors, is compared with the UTC daily means of those monitors once they reach the OpenAQ public
archive (about 4 days later). Monitors are used for this verification only: never as an input of Otso, never to train,
choose or adjust it. Rows with `final: false` may still change when late measurements arrive.
