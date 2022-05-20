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

## De applicatie opslaan (dit is allemaal eenmalig)
1. Maak een map waarin je de bestanden willen opslaan, noem deze bijvoorbeeld _scripts_
1. Klik in de map _scripts_ met de rechtermuisknop en kies voor _Git Bash here_ (windows 10) of _Open Git Bash_ (windows 11)
1. Kopieer en plak (met rechtse muisknop of shift + Insert):
* `git clone https://github.com/Amsterdam/gefxml_viewer.git`
1. Je kan het Git bash venster nu afsluiten met `exit`

1. Er is nu een map gemaakt met de naam _gefxml\_viewer_ 
1. Controleer of er in de map _gefxml\_viewer_ een map is met de naam _output_ (let op kleine o, geen hoofdletter)
1. Is die er niet? Maak deze dan

1. Ga naar de Windows startknop en type daar `cmd`
1. Kies _Anaconda Prompt (Miniconda3)_
1. Ga in de prompt naar de map _gefxml\_viewer_
1. kopieer en plak:
* `conda env create --file environment.yml`

## Plaatjes maken van sonderingen en boringen
In de _Anaconda Prompt (Miniconda3)_ kopieer en plak:
* `conda activate geo_env` (dit moet je iedere keer doen wanneer je begint met een sessie)
* `python gui_plot.py` (dit start de applicatie, moet je iedere keer doen wanneer je plaatjes wil maken)
1. Als het goed is, opent er nu een venster met knoppen
1. Klik op _Select File(s)_ navigeer naar de map met de GEF of XML waarvan je een plaatje wil maken
1. Selecteer het bestand en klik _Openen_
1. Je komt terug in het venster met knoppen, klik daar _Continue_
1. Kijk in de map _output_ of daar een png is gemaakt
1. Wil je meer plaatjes maken, dan doe je weer `python gui_plot.py`
1. Als je klaar bent, sluit de prompt af met `exit`

## Vragen of opmerkingen?
1. Stuur een bericht aan Thomas van der Linden, bijvoorbeeld via [LinkedIn](https://www.linkedin.com/in/tjmvanderlinden/)

## Resultaten?
1. Heb je mooie resultaten gemaakt met deze applicatie? We vinden het heel leuk als je ze deelt (en Thomas tagt)