# gefxml_reader

Application to read geotechnical CPT and bore data in GEF or BRO XML format

## Dependecies
See environment.yml

## Instruction
Create an empty object:
`test = Cpt()` or `test = Bore()`    
Read in a file:
`test.load_gef(filename)` or `test.load_xml(filename)`  
Create a plot in folder ./output
`test.plot()`  

gui_plot.py provides a point and click interface to make plots of individual files or of all the files in a folder
gui_gef2gpkg.py provides a point and click interface to get coordinates and other data from files to gpkg to plot in a GIS

# Heb je geen ervaring met Python? Volg dan deze stappen
## Benodigde programma's
1. Download en installeer deze programma's met de standaardinstellingen:
* [Miniconda](https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe)
* [Git](https://github.com/git-for-windows/git/releases/download/v2.36.1.windows.1/Git-2.36.1-64-bit.exe)

## De applicatie opslaan
1. Maak een map waarin je de bestanden willen opslaan, noem deze bijvoorbeeld _scripts_
2. Klik met de rechtermuisknop en kies voor _Git bash here_
3. kopieer en plak:
* `git pull https://github.com/Amsterdam/gefxml_viewer.git`
4. Als het goed is er nu een nieuwe map _cpt\_viewer_ gemaakt in de map waar je was
5. Controleer of in de map _cpt\_viewer_ ook een map _output_ bestaat, maak deze anders (let op kleine o, geen hoofdletter)
6. Je kan het Git bash venster nu afsluiten met `exit`

## Plaatjes maken van sonderingen en boringen
1. Ga naar de Windows startknop en type daar `cmd`
2. Kies _Anaconda Prompt (Miniconda3)_
3. Ga in de prompt naar de map waarin de cpt_viewer staat
4. kopieer en plak:
* `conda env create --file environment.yml` (dit is eenmalig)
* `conda activate geo_env` (dit moet je iedere keer doen wanneer je begint met een sessie)
* `python gui_plot.py` (dit moet je doen wanneer je plaatjes wil maken)
5. Als het goed is, opent er nu een venster met knoppen
6. Klik op _Select File(s)_ navigeer naar de map met de GEF of XML waarvan je een plaatje wil maken
7. Selecteer het bestand en klik _Openen_
8. Je komt terug in het venster met knoppen, klik daar _Continue_
9. Kijk in de map output of daar een png is gemaakt
10. Wil je meer plaatjes maken, dan doe je weer `python gui_plot.py`
11. Als je klaar bent, sluit de prompt af met `exit`