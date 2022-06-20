import re
from xml.etree.ElementTree import ElementTree

xml = './input/DCG0101_B_BHR000000347910.xml'
xml = '../verzamel_grondonderzoek/omgenoemd/DCG0201/DCG0201_B_BHR000000347896.xml'

tree = ElementTree()
tree.parse(xml)
root = tree.getroot()
layers = {}
i = 0
for element in root.iter():

    if 'broId' in element.tag:
        print(element.text)

    elif 'deliveredLocation' in element.tag:
        location = {re.sub(r'{.*}', '', p.tag) : re.sub(r'\n\s*', '', p.text) for p in element.iter()}
        print(location['pos'].split()[0])
        x = location['pos'].split()[0]
        y = location['pos'].split()[1]

    elif 'deliveredVerticalPosition' in element.tag:
        verticalPosition = {re.sub(r'{.*}', '', p.tag) : re.sub(r'\n\s*', '', p.text) for p in element.iter()}
        print(verticalPosition['offset'])
        z = verticalPosition['offset']

    elif 'layer' in element.tag:
        layers[i] = {re.sub(r'{.*}', '', p.tag) : re.sub(r'\s*', '', p.text) for p in element.iter()}
        i += 1


#['geotechnicalSoilName']
#['specialMaterial']