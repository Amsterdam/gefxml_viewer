# choose directory or file for selection
import tkinter as tk
from tkinter import filedialog
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from gefxml_reader import Cpt, Bore, Test

main_win = tk.Tk()

logo1 = tk.PhotoImage(file='./img/LogoAmsterdam.png')
tk.Label(main_win, image=logo1).place(x=15, y=95)

logo2 = tk.PhotoImage(file='./img/LogoWapen_van_amsterdam.png')
tk.Label(main_win, image=logo2).place(x=15, y=5)

script_version = ''
script_name = 'Thomas van der Linden'
tk.Label(main_win, text='GEF to gpkg Python Script ', fg='black', font='Courier 16 bold').pack()
tk.Label(main_win, text='Lees GEF bestanden in map met Python =) of kies één of meerdere GEF-file(s)', fg='black', font='Courier 12').pack()
tk.Label(main_win, text = 'Script: ' + script_name, fg='grey', font='Courier 10').place(x=800, y=280)
tk.Label(main_win, text = 'Versie: ' + script_version, fg='grey', font='Courier 10').place(x=1095, y=280)

main_win.geometry("1200x300")
main_win.sourceFolder = ''
main_win.sourceFiles = []

def chooseDir():
    main_win.sourceFolder = filedialog.askdirectory(parent=main_win, title='Please select a directory')

b_chooseDir = tk.Button(main_win, text="Select Folder", width=20, height= 3, command=chooseDir)
b_chooseDir.place(x=335, y=95)
b_chooseDir.width = 100
b_chooseDir.config(font=('Courier 14'))

def chooseFiles():
    main_win.sourceFiles = filedialog.askopenfilenames(parent=main_win, title='Please select files')

b_chooseFiles = tk.Button(main_win, text="Select File(s)", width=20, height=3, command=chooseFiles)
b_chooseFiles.place(x=635, y=95)
b_chooseFiles.width = 100
b_chooseFiles.config(font=('Courier 14'))

def ContinueButton():
    main_win.destroy()

b_ContinueButton = tk.Button(text="Continue", width=20, height=3, command=ContinueButton)
b_ContinueButton.place(x=635, y=195)
b_ContinueButton.width = 100
b_ContinueButton.config(font=('Courier 14 bold'))

main_win.mainloop()

projectids = []
projectnames = []
companies = []
tests = []
geometries = []
xs = []
ys = []
zs = []
dates = []
types = []
fileids = []
df = pd.DataFrame()

def appendData(test, projectids, projectnames, tests, companies, geometries, xs, ys, zs, dates):
            projectids.append(test.projectid)
            projectnames.append(test.projectname)
            tests.append(test.testid)
            companies.append(test.companyid)
            geometries.append(Point(test.easting, test.northing))
            xs.append(test.easting)
            ys.append(test.northing)
            zs.append(test.groundlevel)
            dates.append(test.date)
            return projectids, projectnames, tests, companies, geometries, xs, ys, zs, dates

def gef_xml2shp(files):
    for f in files:
        print(f)
        if f.lower().endswith('gef'):
            try:
                testType = Test().load_gef(f)
                types.append(testType)
                fileids.append(f)
                if testType == 'cpt':
                    test = Cpt()
                    test.load_gef(f)
                    projectids, projectnames, tests, companies, geometries, xs, ys, zs, dates = appendData(test, projectids, projectnames, tests, companies, geometries, xs, ys, zs, dates)
                elif testType == 'bore':
                    test = Bore()
                    test.load_gef(f)
                    projectids, projectnames, tests, companies, geometries, xs, ys, zs, dates = appendData(test, projectids, projectnames, tests, companies, geometries, xs, ys, zs, dates)
            except:
                print(f'{f} fout in bestand')
                pass
        elif f.lower().endswith('xml'):
            try:
                testType = Test().load_xml(f)
                types.append(testType)
                fileids.append(f)
                if testType == 'cpt':
                    test = Cpt()
                    test.load_gef(f)
                    projectids, projectnames, tests, companies, geometries, xs, ys, zs, dates = appendData(test, projectids, projectnames, tests, companies, geometries, xs, ys, zs, dates)

                elif testType == 'bore':
                    test = Bore()
                    test.load_gef(f)
                    projectids, projectnames, tests, companies, geometries, xs, ys, zs, dates = appendData(test, projectids, projectnames, tests, companies, geometries, xs, ys, zs, dates)
            except:
                print(f'{f} fout in bestand')
                pass

    df["projectid"] = projectids
    df["projectname"] = projectnames
    df["test"] = tests
    df["company"] = companies
    df["type"] = types
    df['x'] = xs
    df['y'] = ys
    gdf = gpd.GeoDataFrame(df, geometry=geometries).set_crs("EPSG:28992")
    return gdf 

if main_win.sourceFolder != '':
    filelist = os.listdir(main_win.sourceFolder)
    files = [f'{main_win.sourceFolder}/{f}' for f in filelist]
    gdf = gef_xml2shp(files)
    gdf.to_file(f'{main_win.sourceFolder}/grondonderzoek')

elif len(main_win.sourceFiles) >= 1: 
    files = list(main_win.sourceFiles)
    gdf = gef_xml2shp(files)
    gdf.to_file(f'./output/grondonderzoek')
