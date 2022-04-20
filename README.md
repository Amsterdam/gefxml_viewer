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