# Opties voor het maken van een Geo-kaart in Rotterdam

Op basis van de beschikbare data en de Rotterdam GeoAI skill zijn er diverse mogelijkheden voor het maken van kaarten. Hieronder staan de opties waaruit gekozen kan worden.

## 1. Beschikbare Data (Wat willen we visualiseren?)

### Asset Data (Objecten in de openbare ruimte)
*   **Afvalbakken**: Locaties van ~9.700 afvalbakken (met informatie over type, wijk, en straat).
*   **Bomen**: Een grote dataset van ~200.000 bomen (handig om dichtheden in kaart te brengen).
*   **Lichtpunten (Stadsdriehoek)**: Locaties van ~3.500 lantaarnpalen en overige lichtpunten in de Stadsdriehoek (met lichtpunttype en masttype).

### Gebiedsindelingen (TIR - Territoriale Indeling Rotterdam)
Deze data gebruiken we als achtergrond of om tellingen per gebied te structureren:
*   Gemeente (Heel Rotterdam)
*   Gebieden (21 gebieden, zoals Kralingen-Crooswijk of Centrum)
*   Buurten (91 buurten)
*   Subbuurten & Subbuurtdelen

---

## 2. Type Output (Hoe willen we de kaart gebruiken?)

*   **Interactieve HTML-kaart (Folium)**: Ideaal om in te zoomen, de kaart te verschuiven en op objecten te klikken voor meer informatie (pop-ups). Het resultaat is een lokaal `.html` bestand.
*   **Statische Analytische Kaart (Matplotlib/GeoPandas)**: Geschikt voor rapportages en presentaties. Voldoet strikt aan cartografische richtlijnen (altijd voorzien van een titel, legenda en schaalstok). Het resultaat is een `.png` of `.svg` afbeelding.

---

## 3. Visualisatievormen (Welk type kaart maken we?)

### Voor Puntlocaties (Exacte locaties tonen)
*   **Standaard Puntkaart (Point map)**: Toont de exacte locatie van objecten met een stip of markering. (Geschikt voor de lichtpunten in de Stadsdriehoek of specifieke buurten).
*   **Heatmap / Hexbin Map**: Ideaal voor het overzichtelijk in beeld brengen van grote hoeveelheden punten (zoals de 200k bomen in heel Rotterdam of alle afvalbakken). Dit toont concentraties en 'hotspots'.

### Voor Gebiedsanalyses (Vergelijken van gebieden of buurten)
*   **Choropleet (Vlakkenkaart)**: Buurten of wijken worden ingekleurd op basis van een bepaalde waarde. *Let op: Volgens de richtlijnen tonen we hierbij geen ruwe aantallen, maar genormaliseerde data (bijv. dichtheid van bomen per vierkante kilometer of per 1000 inwoners).*
*   **Proportionele Symbolen (Scaled symbol map)**: In elke buurt staat een cirkel, waarvan het oppervlak de hoeveelheid aangeeft (bijv. de relatieve hoeveelheid afvalbakken per gebied).
*   **Dot Density Map**: Punten worden verspreid binnen een gebied om dichtheid visueel aan te geven (bijv. 1 stip = 10 bomen).

---

## Mogelijke Scenario's om mee te starten:

Om direct aan de slag te gaan, kun je kiezen uit (een variatie op) de volgende opties:
1.  **Locatie verkenning**: "Maak een interactieve kaart van alle afvalbakken in het gebied Kralingen-Crooswijk." (Interactieve Folium kaart)
2.  **Dichtheidsanalyse**: "Wat is de dichtheid van bomen per buurt in Rotterdam Noord?" (Statische vlakkenkaart/choropleet)
3.  **Hotspots**: "Toon een heatmap van de lichtpunten in de Stadsdriehoek." (Statische of interactieve heatmap)
4.  **Categorisch overzicht**: "Maak een interactieve puntkaart met verschillende kleuren voor de verschillende soorten afvalbakken in het Centrum." (Interactieve categorische kaart)
