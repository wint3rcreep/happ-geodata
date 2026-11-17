# Happ geodata

Minimal Xray-compatible GeoSite for selective proxy routing, refreshed every six hours by GitHub Actions. GeoIP is refreshed from upstream without modification. Public source data only; no VPN subscriptions, user identifiers, or credentials.

## Stable URLs

- https://raw.githubusercontent.com/wint3rcreep/happ-geodata/release/geosite.dat
- https://raw.githubusercontent.com/wint3rcreep/happ-geodata/release/geoip.dat
- https://raw.githubusercontent.com/wint3rcreep/happ-geodata/release/manifest.json

GeoSite categories:
- `private`: original RunetFreedom group, unchanged.
- `ru-blocked`: original RunetFreedom group, unchanged.
- `geo-block`: suffix rules from itdoginfo GeoBlock.
- `beemoov`: maintained publisher/game suffix rules in build.py.

Use `geosite:ru-blocked`, `geosite:geo-block`, `geosite:beemoov` as proxy destinations with DIRECT fallback. Blocked-only lists do not represent every publisher's georestrictions. Server-side deny policies remain independent.

## Sources and attribution

- https://github.com/runetfreedom/russia-v2ray-rules-dat
- https://github.com/itdoginfo/allow-domains (Categories/geoblock.lst)
- Beemoov public publisher/game domains.

The independent lists retain their upstream terms. No blanket license is asserted over upstream data. Domain overlaps are reported in manifest.json, not removed from their original categories. No broad CDN IP proxy ranges are introduced.

## Safety and updating

Run `python3 -m unittest -v test_build`, then `python3 build.py --root /tmp/geodata`.
Build validates protobuf structure, required groups, domain syntax, CIDRs and cardinality. A failed build does not change the published release branch. All files in a generation publish in one Git commit. Previous commits remain available for rollback.

Schedule: 00:23 / 06:23 / 12:23 / 18:23 UTC (GitHub may delay execution). Manual run: Actions → Build and publish geodata → Run workflow. GitHub may disable scheduled workflows after prolonged repository inactivity; monitor run history. No phone wake/push is implemented: Happ must fetch geofiles under its own refresh policy. Client caches and updates are distinct from upstream rebuilds.

Only the named categories are included. If adding a new geosite rule to a client, ensure that category exists here. Beemoov domains are maintained locally; upstream GeoBlock and ru-blocked update automatically.
