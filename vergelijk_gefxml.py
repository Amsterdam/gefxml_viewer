from gefxml_reader import Cpt
import os
from decimal import Decimal

xmlFile = 'input/vergelijk/2222692_EHZ3AB-S01.xml'
gefFile = 'input/vergelijk/2222692_EHZ3AB-S01.GEF'

xmlCpt = Cpt()
xmlCpt.load_xml(xmlFile)

gefCpt = Cpt()
gefCpt.load_gef(gefFile)

# gef en xml hebben verschillende hoeveelheden decimalen
for column in xmlCpt.data.columns:
    # bepaal het aantal decimalen van beide
    try:
        gefDecimals = gefCpt.data[column].apply(lambda x: len(str(Decimal(f'{x}')).split('.')[1])).max()
    except:
        gefDecimals = 0
    try:
        xmlDecimals = xmlCpt.data[column].apply(lambda x: len(str(Decimal(f'{x}')).split('.')[1])).max()
    except:
        xmlDecimals = 0
    
    # beide dataframes afknippen op het minimum aantal decimalen van beide
    dec = int(min(gefDecimals, xmlDecimals))

    xmlCpt.data[column] = xmlCpt.data[column].apply(lambda x: str(Decimal(str(x)).quantize(Decimal((0, (1,), -dec)), rounding="ROUND_FLOOR")))
    gefCpt.data[column] = gefCpt.data[column].apply(lambda x: str(Decimal(str(x)).quantize(Decimal((0, (1,), -dec)), rounding="ROUND_FLOOR")))


if all([gefCpt.easting == xmlCpt.easting, gefCpt.northing == xmlCpt.northing, gefCpt.groundlevel == gefCpt.groundlevel]):
    print('XYZ zijn gelijk')
    print(f'GEF: x: {gefCpt.easting}, y: {gefCpt.northing}, z: {gefCpt.groundlevel}')
    print(f'XML: x: {xmlCpt.easting}, y: {xmlCpt.northing}, z: {xmlCpt.groundlevel}')
else:
    print('Er zijn verschillen in XYZ')
    print(f'GEF: x: {gefCpt.easting}, y:{gefCpt.northing}, z:{gefCpt.groundlevel}')
    print(f'XML: x: {xmlCpt.easting}, y:{xmlCpt.northing}, z:{xmlCpt.groundlevel}')


if (gefCpt.data == xmlCpt.data).all().all():
    print('Alle meetdata (afgesneden op gelijk aantal decimalen) is gelijk')
else:
    print('Er zijn verschillen in de meetdata (afgesneden op gelijk aantal decimalen)')
    print(f'GEF: {gefCpt.data[gefCpt.data != xmlCpt.data].dropna(axis="rows", how="all")}')
    print(f'XML: {xmlCpt.data[gefCpt.data != xmlCpt.data].dropna(axis="rows", how="all")}')