import os
from gefxml_reader import Cpt, Bore, Multibore, Test


def plot_tests(files, output, interpretCpt=False, outputType='png'):
    for f in files:
        print(f)
        if f.lower().endswith('gef'):
            try:
                testType = Test().type_from_gef(f)
                if testType == 'cpt':
                    cpt = Cpt()
                    cpt.load_gef(f, checkAddFrictionRatio=True, checkAddDepth=True)
                    cpt.plot(output,outputType=outputType)
                    if interpretCpt:
                        cptAsBore = Bore()
                        cptAsBore.from_cpt(cpt, interpretationModel='Robertson') # 'qcOnly', 'threeType', 'NEN', 'Robertson', 'customInterpretation' 
                        cptAsBore.plot(path='./output/cptasbore', outputType=outputType)
                elif testType == 'bore':
                    bore = Bore()
                    bore.load_gef(f)
                    bore.plot(output,outputType=outputType)
            except Exception as e: 
                print(f, e)
        elif f.lower().endswith('xml'):
            try:
                testType = Test().type_from_xml(f)
                if testType == 'cpt':
                    cpt = Cpt()
                    cpt.load_xml(f, checkAddFrictionRatio=True, checkAddDepth=True)
#                    cpt.interpret() # TODO: dit geeft soms een foutmelding met ontbrekende frictionRatio
                    cpt.plot(output, outputType=outputType)
                elif testType == 'sikb':
                    projectName = 'sikb' # TODO: dit kan beter een variabele zijn
                    mb = Multibore()
                    mb.load_xml_sikb0101(f, projectName)
#                    for bore in mb.bores:
#                        bore.plot(output, outputType=outputType)
                elif testType == 'bore':
                    bore = Bore()
                    bore.load_xml(f)
                    bore.plot(output,outputType=outputType)
            except Exception as e: 
                print(f, e)
folder = './input'
files = [f'{folder}/{f}' for f in os.listdir(folder) if f.lower().endswith('gef')]
plot_tests(files, './output', outputType='pdf')
