# choose directory or file for selection
import tkinter as tk
from tkinter import filedialog
import os
from gefxml_reader import Cpt, Bore, Multibore, Test

main_win = tk.Tk()

logo1 = tk.PhotoImage(file='./img/LogoAmsterdam.png')
tk.Label(main_win, image=logo1).place(x=15, y=95)

logo2 = tk.PhotoImage(file='./img/LogoWapen_van_amsterdam.png')
tk.Label(main_win, image=logo2).place(x=15, y=5)

script_version = ''
script_name = 'Thomas van der Linden'
tk.Label(main_win, text='Plot GEF & XML Python Script ', fg='black', font='Courier 16 bold').pack()
tk.Label(main_win, text='Lees GEF & XML (BRO, SIKB) bestanden in een map of losse bestand(en)', fg='black', font='Courier 12').pack()
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

def plot_tests(files, output, interpretCpt=False):
    for f in files:
        print(f)
        if f.lower().endswith('gef'):
            try:
                testType = Test().type_from_gef(f)
                if testType == 'cpt':
                    cpt = Cpt()
                    cpt.load_gef(f, checkAddFrictionRatio=True, checkAddDepth=True)
                    cpt.plot(output)
                    if interpretCpt:
                        cptAsBore = Bore()
                        cptAsBore.from_cpt(cpt, interpretationModel='Robertson') # 'qcOnly', 'threeType', 'NEN', 'Robertson', 'customInterpretation' 
                        cptAsBore.plot(path='./output/cptasbore')
                elif testType == 'bore':
                    bore = Bore()
                    bore.load_gef(f)
                    bore.plot(output)
            except Exception as e: 
                print(f, e)
        elif f.lower().endswith('xml'):
            try:
                testType = Test().type_from_xml(f)
                if testType == 'cpt':
                    cpt = Cpt()
                    cpt.load_xml(f)
#                    cpt.interpret() # TODO: dit geeft soms een foutmelding met ontbrekende frictionRatio
                    cpt.plot(output)
                elif testType == 'sikb':
                    projectName = 'sikb' # TODO: dit kan beter een variabele zijn
                    mb = Multibore()
                    mb.load_xml_sikb0101(f, projectName)
#                    for bore in mb.bores:
#                        bore.plot(output)
                elif testType == 'bore':
                    bore = Bore()
                    bore.load_xml(f)
                    bore.plot(output)
            except Exception as e: 
                print(f, e)


if main_win.sourceFolder != '':
    filelist = os.listdir(main_win.sourceFolder)
    files = [f'{main_win.sourceFolder}/{f}' for f in filelist]
    plot_tests(files, main_win.sourceFolder)

elif len(main_win.sourceFiles) >= 1: 
    files = list(main_win.sourceFiles)
    plot_tests(files, './output')