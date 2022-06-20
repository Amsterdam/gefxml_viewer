from gefxml_reader import Cpt
import os

path = 'C:/Users/linden082/Desktop/temp'

filelist = os.listdir(path)
filepaths = [f'{path}/{f}' for f in filelist if f.lower().endswith('xml')]

for f in filepaths:
    cpt = Cpt()
    cpt.load_xml(f)
    print(cpt.data)
    cpt.plot()
