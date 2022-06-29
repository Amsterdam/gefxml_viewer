"""
Script om sonderingen en boringen vanuit GEF of XML (BRO) in te lezen en te plotten
"""

__author__ = "Thomas van der Linden"
__credits__ = ""
__license__ = "EUPL-1.2"
__version__ = ""
__maintainer__ = "Thomas van der Linden"
__email__ = "t.van.der.linden@amsterdam.nl"
__status__ = "Dev"

from cmath import isnan
from dataclasses import dataclass
from operator import is_
from typing import OrderedDict
import pandas as pd
from io import StringIO
import numpy as np
import re
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
from datetime import date, datetime
from shapely.geometry import Point
from xml.etree.ElementTree import ElementTree
import pyproj

@dataclass
class Test():
    def __init__(self):
        self.type = str()
    
    def load_gef(self, gefFile):
        procedure_pattern = re.compile(r'#PROCEDURECODE\s*=\s*(?P<procedure>.*)\s*')
        report_pattern = re.compile(r'#REPORTCODE\s*=\s*(?P<report>.*)\s*')
        
        with open(gefFile) as f:
            raw_gef = f.read()
        try:
            match = re.search(procedure_pattern, raw_gef)
            procedure = match.group('procedure')
            if 'CPT' in procedure.upper():
                return 'cpt'
            elif 'BORE' in procedure.upper():
                return 'bore'
        except:
            pass

        try:
            match = re.search(report_pattern, raw_gef)
            report = match.group('report')
            if 'CPT' in report.upper():
                return 'cpt'
            elif 'BORE' in report.upper():
                return 'bore'
        except:
            pass

    def load_xml(self, xmlFile):
        with open(xmlFile) as f:
            raw_xml = f.read()

        # TODO: dit kan beter, maar er lijkt niet echt een standaard te zijn
        if 'CPTSTANDARD' in raw_xml.upper():
            return 'cpt'
        elif 'SIKB0101' in raw_xml.upper():
            return 'sikb'
        else:
            return 'bore'


@dataclass
class Cpt():
    def __init__(self):
        self.easting = None
        self.northing = None
        self.groundlevel = -9999
        self.srid = None
        self.testid = None
        self.date = None
        self.finaldepth = None
        self.removedlayers = {}
        self.data = None
        self.filename = None
        self.companyid = None
        self.projectid = None
        self.projectname = None

    def load_xml(self, xmlFile):

        # lees een CPT in vanuit een BRO XML
        tree = ElementTree()
        tree.parse(xmlFile)
        root = tree.getroot()

        for element in root.iter():

            if 'broId' in element.tag:
                self.testid = element.text

            if 'deliveredLocation' in element.tag:
                location = {re.sub(r'{.*}', '', p.tag) : re.sub(r'\n\s*', '', p.text) for p in element.iter() if p.text is not None}
                self.easting = float(location['pos'].split()[0])
                self.northing = float(location['pos'].split()[1])

            elif 'deliveredVerticalPosition' in element.tag:
                verticalPosition = {re.sub(r'{.*}', '', p.tag) : re.sub(r'\n\s*', '', p.text) for p in element.iter() if p.text is not None}
                self.groundlevel = float(verticalPosition['offset'])

            elif 'finalDepth' in element.tag:
                self.finaldepth = float(element.text)

            elif 'researchReportDate' in element.tag:
                date = {re.sub(r'{.*}', '', p.tag) : re.sub(r'\n\s*', '', p.text) for p in element.iter() if p.text is not None}
                try: # een datum is niet verplicht
                    self.date = datetime.strptime(date['date'], '%Y-%m-%d')
                except:
                    pass

            # er kan een dissipatietest inzitten, hiermee wordt alleen de cpt ingelezen. Die staat in dissipationTest
            elif 'conePenetrationTest' in element.tag: 
                for child in element.iter():
                    if 'values' in child.tag:
                        self.data = child.text

            elif 'removedLayer' in element.tag:
                # TODO: maak hier van een Bore() en plot die ook
                self.removedlayers = {re.sub(r'{.*}', '', p.tag) : re.sub(r'\n\s*', '', p.text) for p in element.iter() if p.text is not None}      

        filename_pattern = re.compile(r'(.*[\\/])*(?P<filename>.*)\.')
        match = re.search(filename_pattern, xmlFile)
        self.filename = match.group('filename')

        dataColumns = [
            "penetrationLength", "depth", "elapsedTime", 
            "coneResistance", "correctedConeResistance", "netConeResistance", 
            "magneticFieldStrengthX", "magneticFieldStrengthY", "magneticFieldStrengthZ", 
            "magneticFieldStrengthTotal", "electricalConductivity", 
            "inclinationEW", "inclinationNS", "inclinationX", "inclinationY", "inclinationResultant",
            "magneticInclination", "magneticDeclination",
            "localFriction",
            "poreRatio", "temperature", 
            "porePressureU1", "porePressureU2", "porePressureU3",
            "frictionRatio"]
        
        self.data = pd.read_csv(StringIO(self.data), names=dataColumns, sep=",", lineterminator=';')
        self.data = self.data.replace(-999999, np.nan)

        self.check_depth()

        self.data.sort_values(by="depth", inplace=True)

    def load_gef(self, gefFile):
        self.columnvoid_values = {}
        self.columninfo = {}
        self.columnseparator = " "
        self.recordseparator = ""
        
        # zelfde namen voor kolommen als in xml
        GEF_COLINFO = { 
            '1': 'penetrationLength',
            '2': 'coneResistance',
            '3': 'localFriction',
            '4': 'frictionRatio',
            '5': 'porePressureU1',
            '6': 'porePressureU2',
            '7': 'porePressureU3',
            '8': 'inclinationResultant',
            '9': 'inclinationNS',
            '10': 'inclinationEW',
            '11': 'depth',
            '12': 'elapsedTime',
            '13': 'correctedConeResistance',
            '14': 'netConeResistance',
            '15': 'poreRatio',
            '16': 'Nm [-]',
            '17': 'gamma [kN/m3]',
            '18': 'u0 [MPa]',
            '19': 'sigma_vo [MPa]',
            '20': 'sigma_vo_eff [MPa]',
            '21': 'inclinationX',
            '22': 'inclinationY'
        }

        filename_pattern = re.compile(r'(.*[\\/])*(?P<filename>.*)\.')
        gefid_pattern = re.compile(r'#GEFID\s*=\s*(?P<gefid>\d,\d,\d)\s*')
        xydxdy_id_pattern = re.compile(r'#XYID\s*=\s*(?P<coordsys>\d*)\s*,\s*(?P<X>\d*.?\d*)\s*,\s*(?P<Y>\d*.?\d*)\s*,\s*(?P<dx>\d*.?\d*),\s*(?P<dy>\d*.?\d*)\s*')
        xy_id_pattern = re.compile(r'#XYID\s*=\s*(?P<coordsys>\d*)\s*,\s*(?P<X>\d*.?\d*)\s*,\s*(?P<Y>\d*.?\d*)\s*')
        z_id_pattern = re.compile(r'#ZID\s*=\s*(?P<datum>\d*)\s*,\s*(?P<Z>.*)\s*')
        zdz_id_pattern = re.compile(r'#ZID\s*=\s*(?P<datum>\d*)\s*,\s*(?P<Z>.*)\s*,\s*(?P<dZ>.*)\s*')
        companyid_pattern = re.compile(r'#COMPANYID\s*=\s*(?P<companyid>.*),\s*\w*,\s*\d*\s*')
        projectid_pattern = re.compile(r'#PROJECTID\s*=\s*(?P<projectid>\d*)\s*')
        projectname_pattern = re.compile(r'#PROJECTNAME\s*=\s*(?P<projectname>.*)\s*')
        companyid_in_measurementext_pattern = re.compile(r'#MEASUREMENTTEXT\s*=\s*\d*,\s*(?P<companyid>.*),\s*boorbedrijf\s*')
        projectname_in_measurementtext_pattern = re.compile(r'#MEASUREMENTTEXT\s*=\s*\d*,\s*(?P<projectname>.*),\s*projectnaam\s*')
        startdate_pattern = re.compile(r'#STARTDATE\s*=\s*(?P<startdate>\d*,\s*\d*,\s*\d*)\s*')
        testid_pattern = re.compile(r'#TESTID\s*=\s*(?P<testid>.*)\s*')

        data_pattern = re.compile(r'#EOH\s*=\s*(?P<data>(.*\n)*)')

        columnvoid_pattern = re.compile(r'#COLUMNVOID\s*=\s*(?P<columnnr>\d*),\s*(?P<voidvalue>.*)\s*')
        columninfo_pattern = re.compile(r'#COLUMNINFO\s*=\s*(?P<columnnr>\d*),\s*(?P<unit>.*),\s*(?P<parameter>.*),\s*(?P<quantitynr>\d*)\s*')
        columnseparator_pattern = re.compile(r'#COLUMNSEPARATOR\s*=\s*(?P<columnseparator>.*)')
        recordseparator_pattern = re.compile(r'#RECORDSEPARATOR\s*=\s*(?P<recordseparator>.*)')

        with open(gefFile) as f:
            gef_raw = f.read()

        try:
            match = re.search(filename_pattern, gefFile)
            self.filename = match.group('filename')
        except:
            pass
        try:
            match = re.search(gefid_pattern, gef_raw)
            self.testid = match.group('gefid')
        except:
            pass
        try:
            match = re.search(testid_pattern, gef_raw)
            self.testid = match.group('testid')
        except:
            pass
        try:
            match = re.search(xydxdy_id_pattern, gef_raw)
            self.easting = float(match.group('X'))
            self.northing = float(match.group('Y'))
            self.srid = match.group('coordsys')
        except:
            pass
        try:
            match = re.search(xy_id_pattern, gef_raw)
            self.easting = float(match.group('X'))
            self.northing = float(match.group('Y'))
            self.srid = match.group('coordsys')
        except:
            pass

        # check oude RD-coördinaten
        if self.easting < 13500 or self.northing < 306000:
          
            rd = pyproj.Proj(projparams='epsg:28992')
            rd_oud = pyproj.Proj(projparams='epsg:28991')

            self.easting, self.northing = pyproj.transform(rd_oud, rd, self.easting, self.northing)

        try:
            match = re.search(zdz_id_pattern, gef_raw)
            self.groundlevel = float(match.group('Z'))
        except:
            pass
        try:
            match = re.search(z_id_pattern, gef_raw)
            self.groundlevel = float(match.group('Z'))
        except:
            pass
        try:
            match = re.search(companyid_pattern, gef_raw)
            self.companyid = match.group('companyid')
        except:
            pass
        try:
            match = re.search(companyid_in_measurementext_pattern, gef_raw)
            self.companyid = match.group('companyid')
        except:
            pass
        try:
            match = re.search(projectid_pattern, gef_raw)
            self.projectid = match.group('projectid')
        except:
            pass
        try:
            match = re.search(projectname_pattern, gef_raw)
            self.projectname = match.group('projectname')
        except:
            pass
        try:
            match = re.search(projectname_in_measurementtext_pattern, gef_raw)
            self.projectname = match.group('projectname')
        except:
            pass
        try:
            match = re.search(startdate_pattern, gef_raw)
            startdatestring = match.group('startdate')
            startdatelist = [int(x) for x in startdatestring.split(',')]
            self.date = date(startdatelist[0], startdatelist[1], startdatelist[2])
        except:
            pass
        try:
            match = re.search(data_pattern, gef_raw)
            self.data = match.group('data')
        except:
            pass
        try:
            match = re.search(columnseparator_pattern, gef_raw)
            self.columnseparator = match.group('columnseparator')
        except:
            pass
        try:
            match = re.search(recordseparator_pattern, gef_raw)
            self.recordseparator = match.group('recordseparator')
        except:
            pass
        try:
            matches = re.finditer(columnvoid_pattern, gef_raw)
            for match in matches:
                columnnr = match.group('columnnr')
                voidvalue = match.group('voidvalue')
                self.columnvoid_values[int(columnnr) - 1] = float(voidvalue)
        except:
            pass
        try:
            # informatie in kolommen kan meerdere namen hebben
            # nummers zijn wel gestandardiseerd
            matches = re.finditer(columninfo_pattern, gef_raw)
            for match in matches:
                columnnr = match.group('columnnr')
                quantitynr = match.group('quantitynr')
                # kolomnummers in pandas starten op 0, in gef op 1 
                self.columninfo[int(columnnr) - 1] = GEF_COLINFO[quantitynr]
        except:
            pass

        # zet de data om in een dataframe, dan kunnen we er wat mee
        # TODO: read_fwf lijkt beter te werken dan csv voor sommige GEF, maar er zijn er ook met gedeclareerde separators, toch?
        # TODO: maar soms zijn de kolommen niet precies even breed, dan gaat het mis C:/Users/User/PBK/CPT/GEF/002488\002488_S01.GEF
#        self.data = pd.read_fwf(StringIO(self.data), header=None)         
        self.data = pd.read_csv(StringIO(self.data), sep=self.columnseparator, skipinitialspace=True, lineterminator='\n', header=None) 
        
        # vervang de dummy waarden door nan
        for columnnr, voidvalue in self.columnvoid_values.items():
            self.data[columnnr] = self.data[columnnr].replace(voidvalue, np.nan)
        # geef de kolommen andere namen
        self.data = self.data.rename(columns=self.columninfo)

        # soms is er geen wrijvingsgetal gerapporteerd
        if "frictionRatio" not in self.data.columns or self.data["frictionRatio"].isna().all():
            # als er wel lokale wrijving is gerapporteerd, kan wrijvingsgetal berekend worden
            if "localFriction" in self.data.columns:
                self.data["frictionRatio"] = 100 * self.data["localFriction"] / self.data["coneResistance"]
            # anders is de waarde 0, ten behoeve van plot
            else:
                self.data["localFriction"] = 0
                self.data["frictionRatio"] = 0
        # soms is de ingelezen diepte positief en soms negatief
        # moet positief zijn 
        if "depth" in self.data.columns:
            self.data["depth"] = self.data["depth"].abs()

        self.check_depth()

        # nan waarden geven vervelende strepen in de afbeeldingen
        self.data.dropna(subset=["depth", "coneResistance", "localFriction", "frictionRatio"], inplace=True)

        # er komen soms negatieve waarden voor in coneResistance en frictionRatio, dat geeft vervelende strepen
        self.data = self.data[self.data["coneResistance"] >= 0]
        self.data = self.data[self.data["localFriction"] >= 0]
        self.data = self.data[self.data["frictionRatio"] >= 0]
        # frictionRatio kan ook heel groot zijn, dat geeft vervelende strepen
        self.data = self.data[self.data["frictionRatio"] <= 12]

        # lengte van sondering
        # gelijk aan finaldepth in xml
        self.finaldepth = self.data["depth"].max()

    def plot(self, path='./output'):
        if self.groundlevel == None:
            self.groundlevel = 0

        y = self.groundlevel - self.data["depth"]

        # x,y voor maaiveld in figuur
        x_maaiveld = [0, 10]
        y_maaiveld = [self.groundlevel, self.groundlevel]

        # figuur met conusweerstand, wrijving, wrijvingsgetal, helling en waterspanning
        # TODO: dit kunnen we ook op dezelfde manier doen als bij de boringen, zodat de verticale schaal altijd hetzelfde is
        # TODO: dat is wel lastiger met pdf maken

        colors = {'qc': 'red', 'fs': 'blue', 'Rf': 'green', 'inclination': 'grey', 'porepressure': 'black'}
        fig = plt.figure(figsize=(8.3 * 2,11.7 * 2)) # 8.3 x 11.7 inch is een A4
        gs = GridSpec(2, 1, height_ratios=[10,1])

        ax = fig.add_subplot(gs[0, 0])
        axes = [ax, ax.twiny(), ax.twiny()]

        # Rf plot vanaf rechts
        axes[2].invert_xaxis()  

        porePressures = ["porePressureU1", "porePressureU2", "porePressureU3"]
        for porePressure in porePressures:
            if porePressure in self.data.columns and not self.data[porePressure].isnull().all():
                axes.append(ax.twiny())
                axes[-1].plot(self.data[porePressure], y, label=porePressure[-2:], linewidth=1.25, color=colors['porepressure'], linestyle='-.')
                axes[-1].set_xlabel("u [Mpa]", loc='left')
                axes[-1].legend()
                axes[-1].set_xlim([-1, 1])
                axes[-1].spines['top'].set_position(('axes', 1.02))
                axes[-1].spines['top'].set_bounds(0,1)
                axes[-1].xaxis.label.set_color(colors['porepressure'])
                axes[-1].set_xticks([0,0.25,0.5,0.75,1.0])
                axes[-1].legend() 


        # maak een plot met helling, aan de rechterkant
        inclinations = ["inclinationEW", "inclinationNS", "inclinationX", "inclinationY", "inclinationResultant"]
        inclination_plots = 0
        for inclination in inclinations:
            if inclination in self.data.columns and not self.data[inclination].isnull().all():
                if inclination_plots == 0:
                    axes.append(ax.twiny())
                    axes[-1].invert_xaxis()
                    axes[-1].set_xlim([40, 0])
                    axes[-1].spines['top'].set_position(('axes', 1.02))
                    axes[-1].spines['top'].set_bounds(10,0)
                    axes[-1].set_xlabel("helling [deg]", loc='right')
                    axes[-1].xaxis.label.set_color(colors['inclination'])
                    axes[-1].set_xticks([0,2,4,6,8,10])
                axes[-1].plot(self.data[inclination], y, label=re.sub(r'inclination', '', inclination), linewidth=1.25, color=colors['inclination'])
                inclination_plots += 1
        if inclination_plots > 0:
            axes[-1].legend() 

        # plot data
        axes[0].plot(self.data['coneResistance'], y, label='qc [MPa]', linewidth=1.25, color=colors['qc'])
        axes[1].plot(self.data["localFriction"], y, label='fs [MPa]', linewidth=1.25, color=colors['fs'], linestyle='--')
        axes[2].plot(self.data["frictionRatio"], y, label='Rf [%]', linewidth=1.25, color=colors['Rf'])   

        # plot maaiveld, bestaat uit een streep en een arcering
        axes[0].plot(x_maaiveld, y_maaiveld, color='black')
        axes[0].barh(self.groundlevel, width=10, height=-0.4, align='edge', hatch='/\/', color='#ffffffff')

        # stel de teksten in voor de labels
        axes[0].set_ylabel("Niveau [m t.o.v. NAP]")
        axes[0].set_xlabel("qc [MPa]")
        axes[1].set_xlabel("fs [MPa]", loc='left')
        axes[2].set_xlabel("Rf [%]", loc='right')

        # verplaats de x-assen zodat ze niet overlappen       
        axes[1].spines['top'].set_bounds(0,1)
        axes[2].spines['top'].set_bounds(15,0)

        # kleur de labels van de x-assen hetzelfde als de data
        axes[0].xaxis.label.set_color(colors['qc'])
        axes[1].xaxis.label.set_color(colors['fs'])
        axes[2].xaxis.label.set_color(colors['Rf'])

        # stel de min en max waarden van de assen in
        axes[0].set_xlim([0, 40]) # conusweerstand
        axes[1].set_xlim([0, 2]) # plaatselijke wrijving 
        axes[2].set_xlim([40, 0]) # wrijvingsgetal
        
        axes[1].set_xticks([0,0.5,1.0])
        axes[2].set_xticks([0,2,4,6,8,10,12])

        # metadata in plot
        stempel = fig.add_subplot(gs[1, 0])
        stempel.set_axis_off()
        plt.text(0.05, 0.6, f'Sondering: {self.testid}\nx-coördinaat: {self.easting}\ny-coördinaat: {self.northing}\nmaaiveld: {self.groundlevel}\n', ha='left', va='top', fontsize=14, fontweight='bold')
        plt.text(0.35, 0.6, f'Uitvoerder: {self.companyid}\nDatum: {self.date}\nProjectnummer: {self.projectid}\nProjectnaam: {self.projectname}', ha='left', va='top', fontsize=14, fontweight='bold')
        plt.text(0.05, 0, 'Ingenieursbureau Gemeente Amsterdam - Team WGM - Vakgroep Geotechniek', fontsize=13.5)

        # maak het grid
        ax.minorticks_on()
        ax.tick_params(which='major', color='black')
        ax.tick_params(which='minor', color='black')
        ax.grid(which='major', linestyle='-', linewidth='0.15', color='black')
        ax.grid(which='minor', linestyle='-', linewidth='0.1')
        ax.grid(b=True, which='both')

        # sla de figuur op
        plt.tight_layout()
        plt.savefig(fname=f"./output/{self.filename}.png")
        plt.close('all')

        # andere optie voor bestandsnaam
        save_as_projectid_fromfile = False
        if save_as_projectid_fromfile:
            if self.projectid is not None: # TODO: dit moet ergens anders. Moet ook projectid uit mapid kunnen halen
                plt.savefig(fname=f"./output/{self.projectid}_{self.testid}.png")
                plt.close('all')
            elif self.projectname is not None:
                plt.savefig(fname=f"{path}/{self.projectname}_{self.testid}.png")
                plt.close('all')

    def check_depth(self):
        # soms is er geen diepte, maar wel sondeerlengte aanwezig
        # sondeerlengte als diepte gebruiken is goed genoeg als benadering
        # TODO: onderstaande blok voor diepte correctie is niet gecheckt op correctheid 
        if "depth" not in self.data.columns or self.data["depth"].isna().all():
            # verwijder de lege kolommen om het vervolg eenvoudiger te maken
            self.data.dropna(axis=1, how='all', inplace=True)
            # bereken diepte als inclinatie bepaald is
            if "penetrationLength" in self.data.columns:
                self.data.sort_values("penetrationLength", inplace=True)
                if "inclinationResultant" in self.data.columns:
                    self.data["correctedPenetrationLength"] = self.data["penetrationLength"].diff().abs() * np.cos(np.deg2rad(self.data["inclinationResultant"]))
                    self.data["depth"] = self.data["correctedPenetrationLength"].cumsum()                   
                elif "inclinationEW" in self.data.columns and "inclinationNS" in self.data.columns:
                    z = self.data["penetrationLength"].diff().abs()
                    x = z * np.tan(np.deg2rad(self.data["inclinationEW"]))
                    y = z * np.tan(np.deg2rad(self.data["inclinationNS"]))
                    self.data["inclinationResultant"] = np.rad2deg(np.cos(np.sqrt(x ** 2 + y ** 2 + z ** 2) / z))
                    self.data["correctedPenetrationLength"] = self.data["penetrationLength"].diff().abs() * np.cos(np.deg2rad(self.data["inclinationResultant"]))
                    self.data["depth"] = self.data["correctedPenetrationLength"].cumsum()
                elif "inclinationX" and "inclinationY" in self.data.columns:
                    z = self.data["penetrationLength"].diff().abs()
                    x = z * np.tan(np.deg2rad(self.data["inclinationX"]))
                    y = z * np.tan(np.deg2rad(self.data["inclinationY"]))
                    self.data["inclinationResultant"] = np.rad2deg(np.cos(np.sqrt(x ** 2 + y ** 2 + z ** 2) / z))
                    self.data["correctedPenetrationLength"] = self.data["penetrationLength"].diff().abs() * np.cos(np.deg2rad(self.data["inclinationResultant"]))
                    self.data["depth"] = self.data["correctedPenetrationLength"].cumsum()
                # anders is de diepte gelijk aan de penetration length
                else:
                    self.data["depth"] = self.data["penetrationLength"].abs()

    def interpret(self):
        # functie die later gebruikt wordt
        is_below = lambda p,a,b: np.cross(p-a, b-a) > 0
        
        # de threeType en NEN regels gelden voor log(qc)
        self.data['logConeResistance'] = np.log(self.data['coneResistance'])

        self.data = self.interpret_qc_only()
        self.data = self.interpret_three_type(is_below)
        self.data = self.interpret_nen(is_below)
        self.data = self.interpret_robertson()
        self.data = self.interpret_custom()

    def interpret_custom(self):
        conditions = [
            self.data['frictionRatio'].le(1.2),
            self.data['frictionRatio'].ge(4.8),
        ]
        choices = [
            'zand',
            'veen'
        ]
        self.data['customInterpretation'] = np.select(conditions, choices, 'klei')
        return self.data

    def interpret_qc_only(self):
        # DFoundations qc only rule
        conditionsQcOnly = [
            self.data['coneResistance'] > 4,
            self.data['coneResistance'] > 1,
            self.data['coneResistance'] > 0.1
        ]
        choicesQcOnly = ['zand', 'klei', 'veen']
        self.data['qcOnly'] = np.select(conditionsQcOnly, choicesQcOnly, None)
        return self.data

    def interpret_three_type(self, is_below):
        # DFoundations 3 type rule [frictionRatio, coneResistance] waarden voor lijn die bovengrens vormt
        # TODO: resultaat komt niet overeen met DFoundations
        soils3Type = OrderedDict([
            ['veen', [np.full((len(self.data), 2), [0., np.log10(0.00002)]), np.full((len(self.data), 2), [10, np.log10(0.2)])]],
            ['klei', [np.full((len(self.data), 2), [0., np.log10(0.01)]), np.full((len(self.data), 2), [10, np.log10(100)])]],
            ['zand', [np.full((len(self.data), 2), [0., np.log10(0.5)]), np.full((len(self.data), 2), [10, np.log10(5000)])]]
            ])
        # conditions: check of punt onder de bovengrens ligt
        conditions3Type = [
            is_below(self.data[['frictionRatio', 'logConeResistance']], value[0], value[1]) for value in soils3Type.values()
            ]
        choices3Type = soils3Type.keys()
        # toewijzen materialen op basis van de conditions
        self.data['threeType'] = np.select(conditions3Type, choices3Type, None)
        return self.data
    
    def interpret_nen(self, is_below):
        # DFoundations NEN rule [frictionRatio, coneResistance]
        # TODO: resultaat komt niet overeen met DFoundations
        soilsNEN = OrderedDict([
            #['veen', [[np.log10(0.0001), np.log10(0)], [np.log10(10), np.log10(0.08)]]], # slappe consistentie, past niet in schema
            ['veen', [[np.log10(0.0001), np.log10(0.000058)], [np.log10(10), np.log10(.58)]]], # coneResistance van het eerste punt aangepast 
            #['humeuzeKlei', [[np.log10(0.0001), np.log10(0.004)], [np.log10(10), np.log10(39.59)]]], # slappe consistentie, past niet in schema
            ['humeuzeKlei', [[np.log10(0.0001), np.log10(0.02)], [np.log10(10), np.log10(201)]]], 
            ['klei', [[np.log10(0.0001), np.log10(0.068)], [np.log10(10), np.log10(676.1)]]],
            ['zwakZandigeKlei', [[np.log10(0.0001), np.log10(0.292)], [np.log10(10), np.log10(2921)]]],
            ['sterkZandigeKlei', [[np.log10(0.0001), np.log10(0.516)], [np.log10(10), np.log10(5165)]]],
            ['zwakZandigSilt', [[np.log10(0.0001), np.log10(1.124)], [np.log10(10), np.log10(11240)]]],
            ['sterkZandigSilt', [[np.log10(0.0001), np.log10(2.498)], [np.log10(10), np.log10(24980)]]],
            ['sterkSiltigZand', [[np.log10(0.0001), np.log10(4.606)], [np.log10(10), np.log10(46060)]]],
            ['zwakSiltigZand', [[np.log10(0.0001), np.log10(8.594)], [np.log10(10), np.log10(85940)]]],
            ['zand', [[np.log10(0.0001), np.log10(13.11)], [np.log10(10), np.log10(131100)]]],
            ['grind', [[np.log10(0.0001), np.log10(24.92)], [np.log10(10), np.log10(249200)]]]
            ])
        
        conditionsNEN = [
            is_below(self.data[['frictionRatio', 'logConeResistance']], np.full((len(self.data), 2),value[0]), np.full((len(self.data), 2),value[1])) for value in soilsNEN.values()
            ]
        choicesNEN = soilsNEN.keys()
        self.data['NEN'] = np.select(conditionsNEN, choicesNEN, None)
        return self.data

    def interpret_robertson(self):
        # formula from: Soil Behaviour Type from the CPT: an update 
        # http://www.cpt-robertson.com/PublicationsPDF/2-56%20RobSBT.pdf

        # non-normalized soil behaviour types omgezet naar Nederlandse namen
        sbtDict = {
            'veen': 3.6,
            'klei': 2.95,
            'zwakKleiigSilt': 2.6,
            'zwakSiltigZand': 2.05,
            'sterkSiltigZand': 1.31,
            'zand': 0,
        }
        
        # formule voor non-normalized soil behaviour type
        # TODO: deze formule is er twee vormen
        # er is ook https://cpt-robertson.com/PublicationsPDF/CPT%20Guide%206th%202015.pdf
        sbt = lambda qc, rf, isbt: ((3.47 - np.log10(qc * 1000 / 100)) ** 2 + (np.log10(rf) + 1.22) ** 2) ** 0.5 - isbt > 0
        
        conditions = [
            sbt(self.data['coneResistance'], self.data['frictionRatio'], value) for value in sbtDict.values()
        ]
        choices = sbtDict.keys()
        self.data['Robertson'] = np.select(conditions, choices, None)

        return self.data

@dataclass
class Bore():
    #TODO: uitbreiden voor BHR-P en BHR-G, deels werkt het al
    def __init__(self):
        self.projectid = None
        self.projectname = None
        self.companyid = None
        self.testid = None
        self.easting = None
        self.northing = None
        self.groundlevel = None
        self.srid = None
        self.testid = None
        self.date = None
        self.finaldepth = None
        self.soillayers = {}
        self.analyses = []
        self.metadata = {}
        self.descriptionquality = None

    def load_xml(self, xmlFile):
        # lees een boring in vanuit een BRO XML
        tree = ElementTree()
        tree.parse(xmlFile)
        root = tree.getroot()

        for element in root.iter():

            if 'broId' in element.tag or 'requestReference' in element.tag: # TODO: er zijn ook boringen zonder broId, met requestReference dat toevoegen levert een vreemde waarde voor testid
                self.testid = element.text

            if 'deliveredLocation' in element.tag:
                location = {re.sub(r'{.*}', '', p.tag) : re.sub(r'\n\s*', '', p.text) for p in element.iter() if p.text is not None}
                self.easting = float(location['pos'].split()[0])
                self.northing = float(location['pos'].split()[1])

            elif 'deliveredVerticalPosition' in element.tag:
                verticalPosition = {re.sub(r'{.*}', '', p.tag) : re.sub(r'\n\s*', '', p.text) for p in element.iter() if p.text is not None}
                self.groundlevel = float(verticalPosition['offset'])

            elif 'finalDepthBoring' in element.tag:
                self.finaldepth = float(element.text)

            elif 'descriptionReportDate' in element.tag:
                date = {re.sub(r'{.*}', '', p.tag) : re.sub(r'\n\s*', '', p.text) for p in element.iter() if p.text is not None}
                self.date = datetime.strptime(date['date'], '%Y-%m-%d')
            

            elif 'descriptiveBoreholeLog' in element.tag:
                for child in element.iter():
                    if 'descriptionQuality' in child.tag:
                        descriptionquality = child.text
                    elif 'descriptionLocation' in child.tag:
                        descriptionLocation = child.text
                        soillayers = []
                    elif 'layer' in child.tag:
                        # TODO: onderscheid maken tussen veld en labbeschrijving
                        soillayers.append({re.sub(r'{.*}', '', p.tag) : re.sub(r'\s*', '', p.text) for p in child.iter() if p.text is not None})
                # zet soillayers om in dataframe om het makkelijker te verwerken
                self.soillayers[descriptionLocation] = pd.DataFrame(soillayers) 

            elif 'boreholeSampleAnalysis' in element.tag:
                for child in element.iter():
                    if 'investigatedInterval' in child.tag:
                        self.analyses.append({re.sub(r'{.*}', '', p.tag) : re.sub(r'\s*', '', p.text) for p in child.iter() if p.text is not None})
                self.analyses = pd.DataFrame().from_dict(self.analyses)
                self.analyses = self.analyses.astype(float, errors='ignore')

        self.metadata = {"easting": self.easting, "northing": self.northing, "groundlevel": self.groundlevel, "testid": self.testid, "date": self.date, "finaldepth": self.finaldepth}

        for descriptionLocation, soillayers in self.soillayers.items():
            # TODO: mogelijk verwarrend om soillayers en self.soillayers te combineren
            # voeg de componenten toe t.b.v. plot       
            self.soillayers[descriptionLocation] = self.add_components(soillayers)

            # specialMaterial was voor het maken van de componenten op NBE gezet, nu weer terug naar de oorspronkelijke waarde
            if "specialMaterial" in soillayers.columns:
                self.soillayers[descriptionLocation][self.soillayers[descriptionLocation]["soilName"] == "NBE"]["soilName"] = soillayers["specialMaterial"]
            
            # voeg kolommen toe met absolute niveaus (t.o.v. NAP)
            self.soillayers[descriptionLocation]["upperBoundary"] = pd.to_numeric(soillayers["upperBoundary"])
            self.soillayers[descriptionLocation]["lowerBoundary"] = pd.to_numeric(soillayers["lowerBoundary"])

            self.soillayers[descriptionLocation]["upper_NAP"] = self.groundlevel - soillayers["upperBoundary"] 
            self.soillayers[descriptionLocation]["lower_NAP"] = self.groundlevel - soillayers["lowerBoundary"] 

    def load_gef(self, gefFile):

        self.columninfo = {}
        self.columnvoid_values = {}
        self.descriptionquality = str() # TODO

        GEF_COLINFO = { 
            '1': 'upper',
            '2': 'lower'
        }

        test_id_pattern = re.compile(r'#TESTID\s*=\s*(?P<testid>.*)\s*')
        xy_id_pattern = re.compile(r'#XYID\s*=\s*(?P<refsystem>\d*),\s*(?P<X>\d*\.?\d*),\s*(?P<Y>\d*\.?\d*)(,\s*(?P<dX>\d*\.?\d*),\s*(?P<dY>\d*\.?\d*))?\s*')
        xydxdy_id_pattern = re.compile(r'#XYID\s*=\s*(?P<coordsys>\d*)\s*,\s*(?P<X>\d*.?\d*)\s*,\s*(?P<Y>\d*.?\d*)\s*,\s*(?P<dx>\d*.?\d*),\s*(?P<dy>\d*.?\d*)\s*')
        z_id_pattern = re.compile(r'#ZID\s*=\s*(?P<refsystem>\d*),\s*(?P<Z>\d*\.?\d*)(,\s*(?P<dZ>\d*\.?\d*))')
        zdz_id_pattern = re.compile(r'#ZID\s*=\s*(?P<datum>\d*)\s*,\s*(?P<Z>.*)\s*,\s*(?P<dZ>.*)\s*')

        companyid_pattern = re.compile(r'#COMPANYID\s*=\s*(?P<companyid>.*),\s*\w*,\s*\d*\s*')
        projectid_pattern = re.compile(r'#PROJECTID\s*=\s*(?P<projectid>\d*)\s*')
        projectname_pattern = re.compile(r'#PROJECTNAME\s*=\s*(?P<projectname>.*)\s*')
        companyid_in_measurementext_pattern = re.compile(r'#MEASUREMENTTEXT\s*=\s*\d*,\s*(?P<companyid>.*),\s*boorbedrijf\s*')
        projectname_in_measurementtext_pattern = re.compile(r'#MEASUREMENTTEXT\s*=\s*\d*,\s*(?P<projectname>.*),\s*projectnaam\s*')
        filedate_pattern = re.compile(r'#FILEDATE\s*=\s*(?P<filedate>\d*,\s*\d*,\s*\d*)\s*')

        data_pattern = re.compile(r'#EOH\s*=\s*(?P<data>(.*\n)*)')

        columnvoid_pattern = re.compile(r'#COLUMNVOID\s*=\s*(?P<columnnr>\d*),\s*(?P<voidvalue>.*)\s*')
        columninfo_pattern = re.compile(r'#COLUMNINFO\s*=\s*(?P<columnnr>\d*),\s*(?P<unit>.*),\s*(?P<parameter>.*),\s*(?P<quantitynr>\d*)\s*')
        columnseparator_pattern = re.compile(r'#COLUMNSEPARATOR\s*=\s*(?P<columnseparator>.*)')
        recordseparator_pattern = re.compile(r'#RECORDSEPARATOR\s*=\s*(?P<recordseparator>.*)')

        with open(gefFile) as f:
            gef_raw = f.read()

        try:
            match = re.search(test_id_pattern, gef_raw)
            self.testid = match.group('testid')
        except:
            pass

        try:
            match = re.search(xy_id_pattern, gef_raw)
            self.easting = float(match.group('X'))
            self.northing = float(match.group('Y'))
        except:
            pass
        try:
            match = re.search(xydxdy_id_pattern, gef_raw)
            self.easting = float(match.group('X'))
            self.northing = float(match.group('Y'))
        except:
            pass

        # check oude RD-coördinaten
        if self.easting < 13500 or self.northing < 306000:
          
            rd = pyproj.Proj(projparams='epsg:28992')
            rd_oud = pyproj.Proj(projparams='epsg:28991')

            self.easting, self.northing = pyproj.transform(rd_oud, rd, self.easting, self.northing)
            
        try:
            match = re.search(z_id_pattern, gef_raw)
            self.groundlevel = float(match.group('Z'))
        except:
            pass
        try:
            match = re.search(zdz_id_pattern, gef_raw)
            self.groundlevel = float(match.group('Z'))
        except:
            pass
        try:
            match = re.search(data_pattern, gef_raw)
            self.soillayers['veld'] = match.group('data') # TODO: lab toevoegen
        except:
            pass

        try:
            match = re.search(companyid_pattern, gef_raw)
            self.companyid = match.group('companyid')
        except:
            pass
        try:
            match = re.search(projectid_pattern, gef_raw)
            self.projectid = match.group('projectid')
        except:
            pass
        try:
            match = re.search(projectname_pattern, gef_raw)
            self.projectname = match.group('projectname')
        except:
            pass
        try:
            match = re.search(companyid_in_measurementext_pattern, gef_raw)
            self.companyid = match.group('companyid')
        except:
            pass
        try:
            match = re.search(projectname_in_measurementtext_pattern, gef_raw)
            self.projectname = match.group('projectname')
        except:
            pass
        try:
            match = re.search(filedate_pattern, gef_raw)
            filedatestring = match.group('filedate')
            filedatelist = [int(x) for x in filedatestring.split(',')]
            self.date = date(filedatelist[0], filedatelist[1], filedatelist[2])
        except:
            pass
        try:
            match = re.search(columnseparator_pattern, gef_raw)
            self.columnseparator = match.group('columnseparator')
        except:
            pass
        try:
            match = re.search(recordseparator_pattern, gef_raw)
            self.recordseparator = match.group('recordseparator')
        except:
            pass
        try:
            matches = re.finditer(columnvoid_pattern, gef_raw)
            for match in matches:
                columnnr = match.group('columnnr')
                voidvalue = match.group('voidvalue')
                self.columnvoid_values[int(columnnr) - 1] = float(voidvalue)
        except:
            pass
        try:
            # informatie in kolommen kan meerdere namen hebben
            # nummers zijn wel gestandardiseerd
            matches = re.finditer(columninfo_pattern, gef_raw)
            for match in matches:
                columnnr = match.group('columnnr')
                quantitynr = match.group('quantitynr')
                # kolomnummers in pandas starten op 0, in gef op 1 
                self.columninfo[int(columnnr) - 1] = GEF_COLINFO[quantitynr]
        except:
            pass
        
        # zet de data om in een dataframe, dan kunnen we er wat mee    
        self.soillayers['veld'] = pd.read_csv(StringIO(self.soillayers['veld']), sep=self.columnseparator, skipinitialspace=True, header=None)
        
        # vervang de dummy waarden door nan
        for columnnr, voidvalue in self.columnvoid_values.items():
            self.soillayers['veld'][columnnr] = self.soillayers['veld'][columnnr].replace(voidvalue, np.nan)

        # TODO: deze namen kloppen wellicht niet helemaal
        self.columninfo[max(self.columninfo.keys()) + 1] = 'soilName'
        self.columninfo[max(self.columninfo.keys()) + 1] = 'toelichting'
        self.columninfo[max(self.columninfo.keys()) + 1] = 'materialproperties'

        # geef de kolommen andere namen
        self.soillayers['veld'] = self.soillayers['veld'].rename(columns=self.columninfo)

        self.soillayers['veld'] = self.soillayers['veld'].replace("'", "", regex=True)

        # voeg niveaus t.o.v. NAP toe
        self.soillayers['veld']["upper_NAP"] = self.groundlevel - self.soillayers['veld']["upper"] 
        self.soillayers['veld']["lower_NAP"] = self.groundlevel - self.soillayers['veld']["lower"] 

        # geef de maximaal diepte t.o.v. maaiveld
        self.finaldepth = self.soillayers['veld']["upper_NAP"].max() - self.soillayers['veld']["lower_NAP"].min()

        # zet de codering om in iets dat geplot kan worden
        material_pattern = re.compile(r'(?P<main>[GKLSVZ])(?P<second>[ghklsvz])?(?P<secondQuantity>\d)?(?P<third>[ghklsvz])?(?P<thirdQuantity>\d)?(?P<fourth>[ghklsvz])?(?P<fourthQuantity>\d)?')

        components = []
        for row in self.soillayers['veld'].itertuples():
            componentsRow = {}
            material = str(getattr(row, 'soilName')) # kreeg een keer 0 als material, vandaar de str
            if 'NBE' in material or '0' in material:
                main = 'N'
                secondQuantity, thirdQuantity, fourthQuantity = 0, 0, 0
            else:
                match = re.search(material_pattern, material)
                main = match.group('main')

            try:
                match = re.search(material_pattern, material)
                second = match.group('second')
                secondQuantity = 0.05
            except:
                pass

            try:
                match = re.search(material_pattern, material)
                third = match.group('third')
                thirdQuantity = 0.
            except:
                pass

            try:
                match = re.search(material_pattern, material)
                fourth = match.group('fourth')
                fourthQuantity = 0.
            except:
                pass

            try:
                match = re.search(material_pattern, material)
                secondQuantity = int(match.group('secondQuantity')) * 0.05
            except:
                pass

            try:
                match = re.search(material_pattern, material)
                thirdQuantity = int(match.group('thirdQuantity')) * 0.049
            except:
                pass

            try:
                match = re.search(material_pattern, material)
                fourthQuantity = int(match.group('fourthQuantity')) * 0.048
            except:
                pass

            mainQuantity = 1 - secondQuantity - thirdQuantity - fourthQuantity

            material_components = {"G": 0, "Z": 1, "K": 2, "S": 5, "V": 4, "L": 3, "H": 4, "N": 6}

            componentsRow[mainQuantity] = material_components[main]
            try:
                componentsRow[secondQuantity] = material_components[second.upper()]
            except:
                pass
            try:
                componentsRow[thirdQuantity] = material_components[third.upper()]
            except:
                pass

            try:
                componentsRow[fourthQuantity] = material_components[fourth.upper()]
            except:
                pass

            components.append(componentsRow)
        self.soillayers['veld']["components"] = components


    def plot(self, path='./output'):

        materials = {0: 'grind', 1: 'zand', 2: 'klei', 3: 'leem', 4: 'veen', 5: 'silt', 6: 'overig'}
        colorsDict = {0: "orange", 1: "yellow", 2: "green", 3: "yellowgreen", 4: "brown", 5: "grey", 6: "black"} # BRO style
        hatchesDict = {0: "ooo", 1: "...", 2: "///", 3:"", 4: "---", 5: "|||", 6: ""} # BRO style

        # als er een veld- en een labbeschrijving is, dan maken we meer kolommen
        nrOfLogs = len(self.soillayers.keys())

        # figuur breedte instellen, 6 werkt goed voor alleen een veldbeschrijving
        if nrOfLogs == 1:
            width = 6
            width_ratios = [1, 3] # boorstaat, beschrijving

        # in geval van lab is het gecompliceerder
        # als er alleen veld- en labbeschrijving is, geen testen, dan is self.analyses nog een dict (niet omgezet in DataFrame)
        elif isinstance(self.analyses, dict):
            width = 18
            width_ratios = [1, 3, 0.5, 3]

        # zijn er wel testen, dan alleen de numerieke kolommen selecteren voor plot
        elif isinstance(self.analyses, pd.DataFrame):
            # filter alleen de numerieke kolommen
            self.analyses = self.analyses.apply(lambda x: pd.to_numeric(x.astype(str).str.replace(',',''), errors='coerce')).dropna(axis='columns', how='all')

            width = 24
            # voeg kolommen toe voor de plot van de meetwaarden
            # beginDepth en endDepth doen niet mee
            width_ratios = [1, 3, 0.5, 3, 1, 1] # TODO: lengte moet afhankelijk van aantal meetkolommen
            nrOfLogs += 1 # TODO: waarde moet afhankelijk van aantal meetkolommen

        # maak een diagram 
        fig = plt.figure(figsize=(width, self.finaldepth + 2)) 
        gs = GridSpec(nrows=2, ncols=2 * nrOfLogs, height_ratios=[self.finaldepth, 2], width_ratios=width_ratios, figure=fig)
        axes = []

        # als er veld- en labbeschrijving is, dan worden deze apart geplot
        for i, [descriptionLocation, soillayers] in enumerate(self.soillayers.items()):
            axes.append(fig.add_subplot(gs[0, i * 2])) # boorstaat 
            axes.append(fig.add_subplot(gs[0, i * 2 + 1], sharey=axes[0])) # toelichting 
        
            # maak een eenvoudige plot van een boring
            uppers = list(soillayers["upper_NAP"])
            lowers = list(soillayers["lower_NAP"])
            components = list(soillayers["components"])

            for upper, lower, component in reversed(list(zip(uppers, lowers, components))):
                left = 0
                try: # TODO: kan dit beter. Gemaakt vanwege een geval met component = nan (lab boring van Anthony Moddermanstraat)
                    for comp, nr in component.items():
                        barPlot = axes[i * 2].barh(lower, width=comp, left=left, height=upper-lower, color=colorsDict[nr], hatch=hatchesDict[nr], edgecolor="black", align="edge")
                        left += comp
                except:
                    pass

            axes[i * 2].set_ylim([self.groundlevel - self.finaldepth, self.groundlevel])
            axes[i * 2].set_xticks([])
            axes[i * 2].set_ylabel('diepte [m t.o.v. NAP]')
            plt.title(descriptionLocation) 

            # voeg de beschrijving toe
            for layer in soillayers.itertuples():
                y = (getattr(layer, "lower_NAP") + getattr(layer, "upper_NAP")) / 2
                propertiesText = ""
                for materialproperty in ['tertiaryConstituent', 'colour', 'dispersedInhomogeneity', 'carbonateContentClass',
                                            'organicMatterContentClass', 'mixed', 'sandMedianClass', 'grainshape', # TODO: sandMedianClass kan ook mooi visueel
                                            'sizeFraction', 'angularity', 'sphericity', 'fineSoilConsistency',
                                            'organicSoilTexture', 'organicSoilConsistency', 'peatTensileStrength']:
                    # TODO: dit werkt nog niet goed
                    if materialproperty in soillayers.columns:
                        value = getattr(layer, materialproperty)
                        try:
                            np.isnan(value)
                        except:
                            propertiesText += f', {value}'
                text = f'{getattr(layer, "soilName")}{propertiesText}'
                axes[i * 2 + 1].text(0, y, text, wrap=True)
                # verberg de assen van de beschrijving
                axes[i * 2 + 1].set_axis_off() 

                plt.title(descriptionLocation)
        
        # als er analyses zijn uitgevoerd, deze ook toevoegen
        # TODO: filteren welke wel / niet of samen
        # TODO: korrelgrootte uit beschrijving toevoegen?
        if isinstance(self.analyses, pd.DataFrame):
            averageDepth = self.groundlevel - self.analyses[['beginDepth', 'endDepth']].mean(axis=1)
            # voeg axes toe voor de plots
            for j, col in enumerate([col for col in self.analyses.columns if col not in ['beginDepth', 'endDepth']]):
                    axes.append(fig.add_subplot(gs[0, i * 2 + 2 + j], sharey=axes[0]))
                    axes[i * 2 + 2 + j].plot(self.analyses[col], averageDepth, '.')
                    plt.title(col)

        # voeg een stempel toe
        axes.append(fig.add_subplot(gs[1,:])) # stempel
        # verberg de assen van de stempel
        axes[-1].set_axis_off()
        # tekst voor de stempel
        plt.text(0.05, 0.6, f'Boring: {self.testid}\nx-coördinaat: {self.easting}\ny-coördinaat: {self.northing}\nmaaiveld: {self.groundlevel}\nkwaliteit: {self.descriptionquality}\ndatum: {self.date}', fontsize=14, fontweight='bold')
        plt.text(0.05, 0.2, 'Ingenieursbureau Gemeente Amsterdam Vakgroep Geotechniek Python ', fontsize=10)

#        plt.tight_layout() # TODO: werkt niet met text die wrapt
        plt.savefig(fname=f'{path}/{self.testid}.png')
        plt.close('all')


    def from_cpt(self, cpt, interpretationModel='Robertson'):

        # maak een object alsof het een boring is
        self.soillayers['cpt']= pd.DataFrame(columns=['geotechnicalSoilName', 'frictionRatio', 'coneResistance', 'upper_NAP', 'lower_NAP'])
        self.soillayers['cpt']['geotechnicalSoilName'] = cpt.data[interpretationModel]
        # TODO frictionRatio en coneResistance horen er eigenlijk niet in thuis, maar zijn handig als referentie
        self.soillayers['cpt'][['frictionRatio', 'coneResistance']] = cpt.data[['frictionRatio', 'coneResistance']]
        self.groundlevel = cpt.groundlevel
        self.finaldepth = cpt.data['depth'].max()
        self.descriptionquality = 'cpt'
        self.testid = cpt.testid
        self.easting = cpt.easting
        self.northing = cpt.northing
        self.soillayers['cpt'] = self.add_components(self.soillayers['cpt'])

        # verwijder de lagen met hetzelfde materiaal
        self.soillayers['cpt'] = self.soillayers['cpt'][self.soillayers['cpt']['geotechnicalSoilName'].ne(self.soillayers['cpt']['geotechnicalSoilName'].shift(1))]

        # voeg de laatste regel weer toe
        lastrow = self.soillayers['cpt'].iloc[-1]
        self.soillayers['cpt'].append(lastrow)

        # vul de regels die buiten de schaal vallen met wat er boven zit
        self.soillayers['cpt']['geotechnicalSoilName'].fillna(method='ffill', inplace=True)

        # voeg laaggrenzen toe    
        self.soillayers['cpt']['upper_NAP'] = cpt.groundlevel - cpt.data['depth']
        self.soillayers['cpt']['lower_NAP'] = self.soillayers['cpt']['upper_NAP'].shift(-1)
        # voeg de onderkant van de onderste laag toe
        self.soillayers['cpt'].loc[self.soillayers['cpt'].index.max(), 'lower_NAP'] = cpt.groundlevel - self.finaldepth
        
        self.soillayers['cpt'].dropna(inplace=True)

    def add_components(self, soillayers):
        # voeg verdeling componenten toe
        # van https://github.com/cemsbv/pygef/blob/master/pygef/broxml.py
        material_components = ["gravel_component", "sand_component", "clay_component", "loam_component", "peat_component", "silt_component", "special_material"]
        soil_names_dict_lists = {
            "betonOngebroken": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],  # specialMaterial
            "grind":  [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "humeuzeKlei": [0.0, 0.0, 0.9, 0.0, 0.1, 0.0],
            "keitjes": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "klei": [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
            "kleiigVeen": [0.0, 0.0, 0.3, 0.0, 0.7, 0.0],
            "kleiigZand": [0.0, 0.7, 0.3, 0.0, 0.0, 0.0],
            "kleiigZandMetGrind": [0.05, 0.65, 0.3, 0.0, 0.0, 0.0],
            "NBE": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], # specialMaterial
            "puin": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],  # specialMaterial
            "silt" : [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            "siltigZand": [0.0, 0.7, 0.0, 0.0, 0.0, 0.3],
            "siltigZandMetGrind": [0.05, 0.65, 0.0, 0.0, 0.0, 0.3],
            "sterkGrindigZand": [0.3, 0.7, 0.0, 0.0, 0.0, 0.0],
            "sterkGrindigeKlei": [0.3, 0.0, 0.7, 0.0, 0.0, 0.0],
            "sterkSiltigZand": [0.0, 0.7, 0.0, 0.0, 0.0, 0.3],
            "sterkZandigGrind": [0.7, 0.3, 0.0, 0.0, 0.0, 0.0],
            "sterkZandigSilt": [0.0, 0.3, 0.0, 0.0, 0.0, 0.7],
            "sterkZandigeKlei": [0.0, 0.3, 0.7, 0.0, 0.0, 0.0],
            "sterkZandigeKleiMetGrind": [0.05, 0.3, 0.65, 0.0, 0.0, 0.0],
            "sterkZandigVeen": [0.0, 0.3, 0.0, 0.0, 0.7, 0.0],
            "veen": [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            "zand": [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            "zwakGrindigZand": [0.1, 0.9, 0.0, 0.0, 0.0, 0.0],
            "zwakGrindigeKlei": [0.1, 0.0, 0.9, 0.0, 0.0, 0.0],
            "zwakSiltigZand": [0.0, 0.9, 0.0, 0.0, 0.0, 0.1],
            "zwakSiltigeKlei": [0.0, 0.0, 0.9, 0.0, 0.0, 0.1],
            "zwakZandigGrind": [0.9, 0.1, 0.0, 0.0, 0.0, 0.0],
            "zwakZandigSilt": [0.0, 0.9, 0.0, 0.0, 0.0, 0.1],
            "zwakZandigVeen": [0.0, 0.1, 0.0, 0.0, 0.9, 0.0],
            "zwakZandigeKlei": [0.0, 0.1, 0.9, 0.0, 0.0, 0.0],
            "zwakZandigeKleiMetGrind": [0.05, 0.1, 0.85, 0.0, 0.0, 0.0],
        }

        # voor sorteren op bijdrage is het handiger om een dictionary te maken
        soil_names_dict_dicts = {}
        
        # sorteer ze van groot naar klein voor de plot 
        for key, value in soil_names_dict_lists.items():
            soil_names_dict_dicts[key] = dict(sorted({v: i for i, v in enumerate(value)}.items(), reverse=True))

        # TODO: soilNameNEN5104 specialMaterial
        soillayers["soilName"] = np.where(soillayers["geotechnicalSoilName"].isna(), "NBE", soillayers["geotechnicalSoilName"])
        # voeg de componenten toe
        soillayers["components"] = soillayers["soilName"].map(soil_names_dict_dicts)
        return soillayers

@dataclass
class Multibore():
    def __init__(self):
        self.bores = []

    def load_xml_sikb0101(self, xmlFile):

        #TODO: dit moet eigenlijk met een boreVerzameling object zoals in het lengteprofiel

        # lees boringen in vanuit een SIKB0101 XML
        # anders dan de BRO komen alle boringen van een project in 1 bestand
        tree = ElementTree()
        tree.parse(xmlFile)
        root = tree.getroot()

        tests = {}
        properties = {}
        boreXYZ = {}

        # nodig voor omzetten latlong in rd
        wgs84 = pyproj.Proj(projparams='epsg:4326')
        rd = pyproj.Proj(projparams='epsg:28992')

        # vul de dictionary tests met keys voor de boringen
        for element in root.iter():
            # vul de dictionaries voor de boringen met lagen
            if 'Borehole' in element.tag:
                for key in element.attrib.keys():
                    if 'id' in key:
                        boreId = element.attrib[key]
                        if boreId not in boreXYZ.keys():
                            boreXYZ[boreId] = {}
                    for child in element.iter():
                        # lagen koppelen aan boringen
                        if 'relatedSamplingFeature' in child.tag:
                            for key in child.attrib.keys():
                                if 'href' in key:
                                    layerId = child.attrib[key].replace('#', '')
                                    tests[layerId] = boreId
                        elif 'groundLevel' in child.tag:
                            for p in child.iter(): 
                                if 'value' in p.tag:
                                    boreXYZ[boreId]['groundlevel'] = float(p.text)
                        elif 'geometry' in child.tag:
                            for p in child.iter(): 
                                if 'pos' in p.tag: 
                                    longitude = float(p.text.split()[0])
                                    latitude = float(p.text.split()[1])
                                    x, y = pyproj.transform(wgs84, rd, latitude, longitude)
                                    boreXYZ[boreId]['easting'] =  x
                                    boreXYZ[boreId]['northing'] = y

            # lagen inlezen
            # TODO: dit is niet mooi, maar het werkt wel.
            elif 'featureMember' in element.tag:
                featureId, upperDepth, lowerDepth, grondsoort = None, None, None, None
                for child in element.iter():
                    # bepaal de id van de featureMember
                    # deze komt altijd voor de andere waarden
                    for key in child.attrib.keys():
                        if 'Layer' in child.tag and 'id' in key: 
                            featureId = child.attrib[key]
                            if featureId not in properties.keys():
                                properties[featureId] = {}
                            for child in element.iter():
                                if 'upperDepth' in child.tag:
                                    for inmeting in child.iter():
                                        if 'value' in inmeting.tag:
                                            upperDepth = float(inmeting.text)
                                            properties[featureId]['upper'] = upperDepth / 100
                                elif 'lowerDepth' in child.tag:
                                    for inmeting in child.iter():
                                        if 'value' in inmeting.tag:
                                            lowerDepth = float(inmeting.text)
                                            properties[featureId]['lower'] = lowerDepth / 100

                    if 'relatedObservation' in child.tag:
                        for baby in child.iter():
                            for key in baby.attrib.keys():
                                if 'href' in key:
                                    featureId = baby.attrib[key].replace('#', '')
                                    if featureId not in properties.keys():
                                        properties[featureId] = {}
                    elif child.text is not None:
                        if 'Grondsoort:' in child.text: # er is ook GrondsoortMediaan
                            for inmeting in element.iter():
                                if 'remarks' in inmeting.tag:
                                    grondsoort = inmeting.text
                                    properties[featureId]['soilName'] = grondsoort

        # eigenschappen omzetten in een dataframe
        properties = pd.DataFrame().from_dict(properties).T
        properties = properties.astype(float, errors='ignore')

        properties.dropna(axis=0, how='all', inplace=True)
        properties.dropna(axis=0, subset=['soilName'], inplace=True)

        # een dictionary om materiaalnamen om te zetten in nummers die gebruikt kunnen worden voor de plot
        material_components = {"grind": 0, "zand": 1, "klei": 2, "silt": 5, "veen": 4, "leem": 3, "humeus": 4}

        # Grondsoort omzetten in een dict met hoeveelheden
        # voorbeeld: Klei zandig sterk, humeus matig of Veen zandig zwak
        
        components = []
        for row in properties.itertuples():
            soil = getattr(row, 'soilName')
            # een dictionary om licht, matig, sterk om te zetten
            amount_components = {'zwak': 0.05, 'matig': 0.1, 'sterk': 0.3}
            tempdict = {}
            for i, word in enumerate(soil.split(' ')):
                # het eerste materiaal is de hoofdcomponent
                if i == 0:
                    main = material_components[word.lower()]
                # als er een materiaal staat dan wordt dat een key in de dict
                # als het niet de hoofdcomponent is, dan eindigt het op -ig
                elif re.sub('ig', '', word) in material_components.keys():
                    material = material_components[re.sub('ig', '', word)]
                elif re.sub(',', '', word) in amount_components:
                    amount = amount_components[re.sub(',', '', word)]
                    # er kunnen meer materialen met dezelfde hoeveelheid zijn, maar een dict kan alleen unieke keys aan
                    amount_components[re.sub(',', '', word)] -= 0.01
                    tempdict[amount] = material
            tempdict[1 - sum(list(tempdict.keys()))] = main

            # sorteer ze van groot naar klein voor de plot 
            tempdict = dict(sorted(tempdict.items(), reverse=True))
            components.append(tempdict)

        properties['components'] = components
        properties['bore'] = properties.index.map(tests)

        for i, boreId in enumerate(properties['bore'].unique()): # TODO: kan dit beter met groupby?
            bore = Bore()
            bore.soillayers = {}
            bore.soillayers['veld'] = properties[properties['bore'] == boreId]
            
            # boreId is een lang en onduidelijk nummer, daarom een optie om eenvoudigere nummers te gebruiken
            testIdIsBoreId = False
            if testIdIsBoreId:
                bore.testid = boreId
            else:
                bore.testid = i
            
            bore.groundlevel = boreXYZ[boreId]['groundlevel']
            bore.easting = boreXYZ[boreId]['easting']
            bore.northing = boreXYZ[boreId]['northing']
            
            bore.soillayers['veld']['upper_NAP'] = bore.groundlevel - bore.soillayers['veld']['upper']
            bore.soillayers['veld']['lower_NAP'] = bore.groundlevel - bore.soillayers['veld']['lower']
            bore.finaldepth = bore.soillayers['veld']['upper'].max()
            self.bores.append(bore)