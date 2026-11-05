# Hallituspohjakone

Kevyt staattinen sivu, jolla voi kokeilla Suomen hallituspohjia tuoreimpien Ylen ja HS:n kannatusmittausten perusteella. Luvut päivittyvät automaattisesti.

## Tiedostot

| Tiedosto | Mitä se on |
|---|---|
| `index.html` | Koko sivu: ulkoasu, paikkamalli ja hallituspohjien laskenta |
| `polls.json` | Kannatusluvut. Sivu lukee ne tästä tiedostosta. |
| `scripts/update_polls.py` | Hakee uusimmat Taloustutkimuksen (Yle) ja Verianin (HS) luvut Wikipedian mittauskoosteesta |
| `.github/workflows/update-polls.yml` | Ajaa skriptin joka aamu ja tallentaa muutokset, jos uusi mittaus on julkaistu |
| `CNAME` | Oma verkkotunnus GitHub Pagesille |

## Julkaisu GitHub Pagesiin (noin 15 min)

1. **Luo repositorio.** GitHubissa: New repository, nimeksi esim. `hallituspohjat`, julkinen (Public).
2. **Lataa tiedostot.** Pura zip ja vie kaikki tiedostot repositorion juureen (Add file → Upload files). Huomaa piilokansio `.github` – jos selain ei näytä sitä, käytä GitHub Desktopia tai komentoriviä (`git push`).
3. **Salli automaattinen tallennus.** Settings → Actions → General → Workflow permissions → *Read and write permissions* → Save.
4. **Ota Pages käyttöön.** Settings → Pages → Source: *Deploy from a branch*, Branch: `main`, kansio `/ (root)`. Sivu tulee näkyviin osoitteeseen `https://<käyttäjä>.github.io/hallituspohjat/` noin minuutissa.
5. **Testaa päivitys.** Actions → *Päivitä kannatusluvut* → Run workflow. Ajon pitäisi päättyä vihreänä (joko "Ei uusia mittauksia" tai uusi commit).

## Oma verkkotunnus (esim. hallituspohjat.fi)

1. Tarkista vapaus Traficomin verkkotunnushausta ja rekisteröi se jonkin .fi-välittäjän kautta.
2. Lisää välittäjän DNS-asetuksiin:
   - neljä **A**-tietuetta juureen (`@`): `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - **CNAME**-tietue `www` → `<käyttäjä>.github.io`
3. GitHubissa Settings → Pages → Custom domain: `hallituspohjat.fi` → Save, ja kun varmenne on valmis, rastita *Enforce HTTPS*.
4. Jos valitset toisen osoitteen, vaihda se `CNAME`-tiedostoon.

## Miten päivitys toimii

Skripti lukee Wikipedian sivun *Opinion polling for the 2027 Finnish parliamentary election* ja ottaa uusimman Taloustutkimuksen ja Verianin rivin. Se päivittää `polls.json`-tiedoston vain, jos keruujakso on uudempi kuin tiedostossa ja jos luvut läpäisevät tarkistuksen (kaikki yhdeksän puoluetta mukana ja summa noin 100 %). Muuten tiedosto jää ennalleen. Wikipedia päivittyy yleensä samana tai seuraavana päivänä mittauksen julkaisusta.

Lukuja voi korjata myös käsin muokkaamalla `polls.json`-tiedostoa GitHubissa.

## Paikkamalli

Manner-Suomen 199 paikkaa jaetaan d'Hondtin menetelmällä 12 vaalipiirissä. Valtakunnallinen kannatus jaetaan vaalipiireihin alueprofiileilla, jotka on viritetty vuoden 2023 vaalitulokseen (virhe enintään kolme paikkaa puoluetta kohden). Ahvenanmaan paikka lasketaan erikseen. Todennäköisyydet tulevat 800 simulaatiosta otantavirheen mukaan.
