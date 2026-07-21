# Intake — heb ik genoeg om een goede kaart te maken?

Lees dit **voordat** je data laadt of code schrijft, bij elke vraag om een kaart.

Doel: de keuzes die de kaart bepalen (gebied, detailniveau, maat, kaarttype) zijn *voor* het tekenen te maken en *achteraf* duur te repareren. De intake checkt of die keuzes vaststaan — uit de vraag, uit de skill-defaults, of anders uit een vraag aan de gebruiker.

Intake is **geen interview**. De meeste vragen zijn na drie regels denken al compleet.

## Werkwijze

1. Loop de checklist hieronder langs. Vul elk punt in met (a) wat de gebruiker zei, of (b) de default uit deze skill.
2. Blijft er een **blokkerend** punt open (kolom "Blokkerend?" = ja, en geen default toepasbaar) → **stel een vraag** en wacht op antwoord. Ga niet gokken.
3. Alleen niet-blokkerende punten open → **niet vragen**: neem de default/aanname, maak de kaart, en benoem de aanname in één regel bij de oplevering.
4. Vat vóór het renderen in **één regel** samen wat je gaat maken ("Ik maak een choropleet afvalbakken per km² per subbuurt, Rotterdam Zuid, PNG."). Zo kan de gebruiker vroeg bijsturen.

## Checklist

| # | Wat | Blokkerend? | Default als het niet genoemd is |
|---|-----|-------------|--------------------------------|
| 1 | **Onderwerp** — welk thema/welke laag? | **Ja** | geen |
| 2 | **Vraagtype** — locaties tonen / aantallen vergelijken / dichtheid / verdeling / relatie tussen twee variabelen | Nee | leid af uit de formulering; bij twijfel: locaties tonen |
| 3 | **Gebied** — hele stad, gebied, buurt, of een straal rond een adres? | **Ja**, tenzij afleidbaar | hele gemeente Rotterdam |
| 4 | **Detailniveau** — gebied / buurt / subbuurt (TIR) of CBS-wijk/buurt | **Ja** bij aggregatie (choropleet, "per …") | TIR-buurt (`WIJK`-veld, invariant 2) |
| 5 | **Kaarttype + maat** — zie de gekoppelde vraag hieronder | **Ja** bij aggregatie | choropleet per km² |
| 6 | **Selectie/filter** — alleen een bepaald type, eigenaar, status, conditie? | Nee | alles, ongefilterd |
| 7 | **Peilmoment** — actuele stand of een specifiek jaar/periode? | Nee | meest recente stand van de bron |
| 8 | **Kaarttype bij niet-geaggregeerde data** — punten of hexbin | Nee | volgens de map-type-beslisboom in `cartography.md` |
| 9 | **Publiek/medium** — analist, bestuurder, bewoner; scherm, A4-print, presentatie | Nee | interne analyse, scherm |
| 10 | **Output** — statische PNG of interactieve kaart | Nee | PNG via `save_map()` (invariant 5) |
| 11 | **Basemap** — kleur, grijs, luchtfoto, geen | Nee | kleur (invariant 10) |
| 12 | **Extra kaartelementen** — noordpijl/schaalstok nodig? | Nee | uit, tenzij navigatie of afstand relevant (invarianten 13/14) |

### Punt 5: kaarttype en maat zijn één vraag

Bij een aggregatievraag ("per buurt", "per gebied") mag je **niet aannemen dat het een choropleet wordt** — en dus ook niet los naar de normalisatie vragen alsof dat al vaststaat. Kaarttype en maat hangen samen: het kaarttype bepaalt óf normalisatie überhaupt nodig is.

- **Choropleet** — vlakken op kleur. Normalisatie is **verplicht** (invariant 3): per km² of per 1.000 inwoners. Een groot vlak lijkt anders altijd "veel", puur door zijn oppervlak.
- **Proportionele symbolen** — cirkel op de centroïde, oppervlak ∝ waarde. **Absolute aantallen zijn hier juist correct**; de cirkelgrootte draagt de waarde, niet het vlak. Normaliseren mag, maar hoeft niet.

Stel het daarom als **één keuze** met deze opties, niet als twee losse vragen:

1. Choropleet, per km² *(aanbevolen bij dichtheidsvragen)*
2. Choropleet, per 1.000 inwoners
3. Proportionele cirkels, absolute aantallen
4. Twee deelkaarten naast elkaar

Aanvullend, alleen relevant als het speelt:

- **Data niet in de skill** → geen intake-vraag maar invariant 7: vraag of je open dataportalen mag doorzoeken, of stoppen.
- **Vergelijking over tijd of tussen gebieden** → vraag of de klassegrenzen over de kaarten gelijk moeten blijven (anders is vergelijken onmogelijk).
- **Kleine aantallen op subbuurtniveau** → herleidbaarheid/privacy; meld het, aggregeer een niveau hoger als de gebruiker dat wil.

## Regels voor het vragen

- **Vraag alleen wat de gebruiker weet en jij niet kunt opzoeken.** Veldnamen, CRS, bestandslocaties, kleuren en beschikbare klassen zoek je zelf op in `data_sources.md` / de package — daar val je de gebruiker niet mee lastig.
- **Vraag alleen wat de kaart daadwerkelijk verandert.** Als beide antwoorden tot dezelfde kaart leiden: niet vragen.
- **Bundel** alle open punten in **één ronde** van maximaal 4 vragen (`AskUserQuestion`), niet druppelsgewijs.
- **Bied concrete opties**, geen open vragen. Zet je aanbeveling als eerste optie met "(aanbevolen)" erachter.
- **Één ronde is genoeg.** Antwoordt de gebruiker niet of zegt hij "kies maar", neem dan de defaults en meld ze.

## Voorbeelden

**Genoeg informatie — geen vragen.**
> "Maak een kaart van de afvalbakken in Charlois."
> Onderwerp ✓, gebied ✓, punten ✓, geen aggregatie → geen normalisatie nodig. Rest is default. Direct maken.

**Eén blokkerend punt.**
> "Laat de bomen per buurt zien."
> "Per buurt" impliceert aggregatie → detailniveau (#4: TIR-buurt of CBS-buurt) is blokkerend, en kaarttype+maat (#5) ook. Twee vragen, één ronde. Neem bij #5 níet aan dat het een choropleet wordt.

**Niet-blokkerende aanname.**
> "Maak een dichtheidskaart van lichtpunten in Rotterdam."
> Alles ingevuld via defaults; peilmoment en filter niet genoemd. Kaart maken, en bij oplevering melden: "Alle lichtpunten, actuele stand Obsurv, per km² op TIR-buurtniveau."
