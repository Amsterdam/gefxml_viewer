"""
Script om sonderingen in te lezen vanuit GEF of XML
kan ook boringen in XML inlezen
en sonderingen plotten

Geschreven door Thomas van der Linden, Ingenieursbureau Amsterdam
19 oktober 2021
"""

from typing import List
import pandas as pd
from io import StringIO
import numpy as np
import re
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
from datetime import date, datetime

class Cpt():
    def __init__(self):
        self.easting = None
        self.northing = None
        self.groundlevel = -9999
        self.srid = None
        self.testid = None
        self.reportdate = None
        self.finaldepth = None
        self.removedlayers = {}
        self.data = None
        self.filename = None

    def load_xml(self, xmlFile):

        filename_pattern = re.compile(r'.*\\(?P<filename>.*)')
        testid_pattern = re.compile(r'<ns\d*:broId>\s*(?P<testid>.*)</ns\d*:broId>')
        objectid_pattern = re.compile(r'<ns\d*:objectIdAccountableParty>\s*(?P<testid>.*)\s*</ns\d*:objectIdAccountableParty>')
        xy_id_pattern = re.compile(r'<ns\d*:location srsName="urn:ogc:def:crs:EPSG::28992"\s*.*\d*?:id="BRO_\d*">\s*' + 
                                        r'<.*\d*?:pos>(?P<X>\d*.?\d*)\s*(?P<Y>\d*.?\d*)</.*\d*?:pos>')
        z_id_pattern = re.compile(r'<ns\d*:offset uom="(?P<z_unit>.*)">(?P<Z>-?\d*.?\d*)</ns\d*:offset>')
        trajectory_pattern = re.compile(r'<ns\d*:trajectory>\s*' + 
                                            r'<ns\d*:predrilledDepth uom="m">(?P<predrilled>\d*.?\d*)\s*</ns\d*:predrilledDepth>\s*' + 
                                            r'<ns\d*:finalDepth uom="m">(?P<finalDepth>\d*.?\d*)</ns\d*:finalDepth>\s'+ 
                                        r'*</ns\d*:trajectory>')
        report_date_pattern = re.compile(r'<ns\d*:researchReportDate>\s*<ns\d*:date>(?P<report_date>\d*-\d*-\d*)</ns\d*:date>')
        removed_layer_pattern = re.compile(r'<ns\d*:removedLayer>\s*'+ 
                                                r'<ns\d*:sequenceNumber>(?P<layerNr>\d*)</ns\d*:sequenceNumber>\s*' + 
                                                r'<ns\d*:upperBoundary uom="m">(?P<layerUpper>\d*.?\d*)</ns\d*:upperBoundary>\s*' + 
                                                r'<ns\d*:lowerBoundary uom="m">(?P<layerLower>\d*.?\d*)</ns\d*:lowerBoundary>\s*' + 
                                                r'<ns\d*:description>(?P<layerDescription>.*)</ns\d*:description>\s*' + 
                                            r'</ns\d*:removedLayer>\s*')
        data_pattern = re.compile(r'<ns\d*:values>(?P<data>.*)</ns\d*:values>')

        with open(xmlFile) as f:
            xml_raw = f.read()

        try:
            match = re.search(filename_pattern, xmlFile)
            self.filename = match.group('filename')
        except:
            pass
        try:
            match = re.search(xy_id_pattern, xml_raw)
            self.easting = float(match.group('X'))
            self.northing = float(match.group('Y'))
            self.srid = match.group('coordsys')
        except:
            pass
        try:
            match = re.search(z_id_pattern, xml_raw)
            self.groundlevel = float(match.group('Z'))
        except:
            pass
        try:
            match = re.search(testid_pattern, xml_raw)
            self.testid = match.group('testid')
        except:
            pass
        try:
            match = re.search(objectid_pattern, xml_raw)
            self.testid = match.group('testid')
        except:
            pass
        try:
            match = re.search(report_date_pattern, xml_raw)
            self.reportdate = match.group('report_date')
        except:
            pass
        try:
            match = re.search(trajectory_pattern, xml_raw)
            self.finaldepth = float(match.group('finalDepth'))
        except:
            pass
        try:
            matches = re.finditer(removed_layer_pattern, xml_raw)
            for match in matches:
                layernr = match.group('layerNr')
                layerupper = match.group('layerUpper')
                layerlower = match.group('layerLower')
                layerdescription = match.group('layerDescription')
                self.removedlayers[layernr] = {"upper": layerupper, "lower": layerlower, "description": layerdescription}
        except:
            pass
        try:
            match = re.search(data_pattern, xml_raw)
            self.data = match.group('data')
        except:
            pass

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

        filename_pattern = re.compile(r'.*\\(?P<filename>.*)')
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
        filedate_pattern = re.compile(r'#FILEDATE\s*=\s*(?P<filedate>\d*,\s*\d*,\s*\d*)\s*')
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
            match = re.search(filedate_pattern, gef_raw)
            filedatestring = match.group('filedate')
            filedatelist = [int(x) for x in filedatestring.split(',')]
            self.filedate = date(filedatelist[0], filedatelist[1], filedatelist[2])
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
        if "frictionRatio" not in self.data.columns:
            # als er wel lokale wrijving is gerapporteerd, kan wrijvingsgetal berekend worden
            if "localFriction" in self.data.columns:
                self.data["frictionRatio"] = 100 * self.data["localFriction"] / self.data["coneResistance"]
            # anders is de waarde 0, ten behoeve van plot
            else:
                self.data["frictionRatio"] = 0
        # soms is de ingelezen diepte positief en soms negatief
        # moet positief zijn 
        if "depth" in self.data.columns:
            if (self.data["depth"].min() < 0):
                self.data["depth"] = - self.data["depth"]

        # soms is er geen diepte, maar wel sondeerlengte aanwezig
        # sondeerlengte als diepte gebruiken is goed genoeg als benadering
        elif "penetrationLength" in self.data.columns:
            self.data["depth"] = self.data["penetrationLength"]

        # lengte van sondering
        # gelijk aan finaldepth in xml
        self.finaldepth = self.data["depth"].min()


    def plot(self):
        if self.groundlevel == None:
            self.groundlevel = 0

        if "depth" in self.data.columns:
            if (self.data["depth"].min() < 0): # TODO: dit moet ergens anders. depth moet altijd dezelfde conventie volgen
                y = self.groundlevel + self.data["depth"]
            else:
                y = self.groundlevel - self.data["depth"]
        else:
            if (self.data["penetrationLength"].min() < 0):
                y = self.groundlevel + self.data["penetrationLength"]
            else:
                y = self.groundlevel - self.data["penetrationLength"]
        x1 = self.data["coneResistance"]
        x2 = self.data["frictionRatio"]

        # x,y voor maaiveld in figuur
        x_maaiveld = [0, 10]
        y_maaiveld = [self.groundlevel, self.groundlevel]

        # figuur met twee grafieken
        fig = plt.figure(constrained_layout=True, figsize=(8,10))
        gs = GridSpec(nrows=2, ncols=2, figure=fig, width_ratios=[4,1], height_ratios=[10,1])
        # grafiek 1 is conusweerstand
        ax1 = fig.add_subplot(gs[0,0])
        # grafiek 2 is wrijvingsgetal
        ax2 = fig.add_subplot(gs[0,1])
        # een rechthoek voor de metadata
        ax3 = fig.add_subplot(gs[1,:])
        # plot conusweerstand
        ax1.plot(x1, y)
        # plot maaiveld, bestaat uit een streep en een arcering
        ax1.plot(x_maaiveld, y_maaiveld, color='black')
        ax1.barh(self.groundlevel, width=10, height=-0.4, align='edge', hatch='/\/', color='#ffffffff')
        # plot wrijvingsgetal
        ax2.plot(x2, y)

        # stel maximum en minimum waarden in voor assen
        ax1.set_xlim(0,40)
        ax2.set_xlim(0,10)
        ax1.set_ylim(y.min(), int(self.groundlevel) + 1)
        ax2.set_ylim(y.min(), int(self.groundlevel) + 1)

        # stel markeringen op de x-assen in
        ax1.set_xticks(ticks=np.arange(0, 40, 5))
        ax2.set_xticks(ticks=np.arange(0, 10, 2))
        ax1.set_xticks(ticks=np.arange(0, 40, 1), minor=True)
        ax2.set_xticks(ticks=np.arange(0, 10, 1), minor=True)
        
        # stel markeringen op de y-assen in
        ax1.set_yticks(ticks=np.arange(int(y.min())-1, int(self.groundlevel)+1, 1))
        ax2.set_yticks(ticks=np.arange(int(y.min())-1, int(self.groundlevel)+1, 1))
        ax1.set_yticks(ticks=np.arange(int(y.min())-1, int(y.max())+1, 0.5), minor=True)
        ax2.set_yticks(ticks=np.arange(int(y.min())-1, int(y.max())+1, 0.5), minor=True)

        # maak een grid
        ax1.grid(True, which="major", axis="both", color="black", linestyle='-')
        ax1.grid(True, which="minor", axis="both", linestyle='--')
        ax2.grid(True, which="major", axis="both", color="black", linestyle='-')
        ax2.grid(True, which="minor", axis="both", linestyle='--')

        # stel labels bij de assen in
        ax1.set_xlabel("qc [MPa]")
        ax1.set_ylabel("Niveau [m t.o.v. NAP]")
        ax1.text(10, self.groundlevel, f'Maaiveld: NAP {self.groundlevel} m')
        ax2.set_xlabel("Rf [%]")

        # voeg metadata toe aan
        ax3.text(0.05, 0.9, self.testid, va="center", ha="left")
        ax3.text(0.05, 0.75, self.easting, va="center", ha="left")
        ax3.text(0.25, 0.75, self.northing, va="center", ha="left")
        ax3.text(0.05, 0.6, self.filedate, va="center", ha="left")
        
        # stel een titel in
        plt.suptitle(self.testid)
        # sla de figuur op
        plt.savefig(fname=f"./output/{self.filename}.png")

        # andere optie
        save_as_projectid_fromfile = False
        if save_as_projectid_fromfile:
            if self.projectid is not None: # TODO: dit moet ergens anders. Moet ook projectid uit mapid kunnen halen
                plt.savefig(fname=f"./output/{self.projectid}_{self.testid}.png")
            elif self.projectname is not None:
                plt.savefig(fname=f"./output/{self.projectname}_{self.testid}.png")


class Bore():
    def __init__(self):
        self.easting = None
        self.northing = None
        self.groundlevel = None
        self.srid = None
        self.testid = None
        self.reportdate = None
        self.finaldepth = None
        self.soillayers = []
        self.sandlayers = []
        self.claylayers = []
        self.peatlayers = []
        self.metadata = {}
    
    def load_xml(self, xmlFile):
        # lees een boring in vanuit een BRO XML
        testid_pattern = re.compile(r'<broId>\s*(?P<testid>.*)</broId>')
        xy_id_pattern = re.compile(r'<ns\d*:Point\s*srsName="urn:ogc:def:crs:EPSG::(?P<coordsys>.*)"\s*ns\d*:id="BRO_0001">\s*' +
                        r'<ns\d*:pos>(?P<X>\d*.?\d*)\s*(?P<Y>\d*.?\d*)</ns\d*:pos>')
        z_id_pattern = re.compile(r'<ns\d*:offset uom="(?P<z_unit>.*)">(?P<Z>.*)</ns\d*:offset>')
        trajectory_pattern = re.compile(r'<ns\d*:finalDepthBoring uom="m">(?P<finalDepth>\d*.?\d*)</ns\d*:finalDepthBoring>')
        report_date_pattern = re.compile(r'<ns\d*:descriptionReportDate>\s*<date>(?P<report_date>\d*-\d*-\d*)</date>')

        # TODO: dit kan worden opgesplitst, maar dan raak je wel de samenhang kwijt

        soil_pattern = re.compile(r'<ns\d*:layer>\s*' + 
                                    r'<ns\d*:upperBoundary uom="m">(?P<layerUpper>\d*.?\d*)</ns\d*:upperBoundary>\s*' +
                                    r'<ns\d*:upperBoundaryDetermination codeSpace="urn:bro:bhrgt:BoundaryPositioningMethod">.*</ns\d*:upperBoundaryDetermination>\s*' +
                                    r'<ns\d*:lowerBoundary uom="m">(?P<layerLower>\d*.?\d*)</ns\d*:lowerBoundary>\s*' +
                                    r'<ns\d*:lowerBoundaryDetermination codeSpace="urn:bro:bhrgt:BoundaryPositioningMethod">.*</ns\d*:lowerBoundaryDetermination>\s*' +
                                    r'<ns\d*:anthropogenic>(?P<anthropogenic>.*)</ns\d*:anthropogenic>\s*' +
                                    r'(<ns\d*:slant>(?P<slant>.*)</ns\d*:slant>\s*)?' +
                                    r'(<ns\d*:internalStructureIntact>(?P<internalstructure>.*)</ns\d*:internalStructureIntact>\s*)?' +
                                    r'(<ns\d*:bedded>(?P<bedded>.*)</ns\d*:bedded>\s*)?' +
                                    r'(<ns\d*:compositeLayer>(?P<compositelayer>.*)</ns\d*:compositeLayer>\s*)?'
                                    r'<ns\d*:soil>\s*' +
                                        r'<ns\d*:geotechnicalSoilName codeSpace="urn:bro:bhrgt:GeotechnicalSoilName">(?P<soilName>.*)</ns\d*:geotechnicalSoilName>\s*' +
                                        r'<ns\d*:tertiaryConstituent codeSpace="urn:bro:bhrgt:TertiaryConstituent">(?P<tertiaryConstituent>.*)</ns\d*:tertiaryConstituent>\s*' +
                                        r'<ns\d*:colour codeSpace="urn:bro:bhrgt:Colour">(?P<colour>.*)</ns\d*:colour>\s*' +
                                        r'<ns\d*:dispersedInhomogeneity codeSpace="urn:bro:bhrgt:DispersedInhomogeneity">(?P<inhomogeneity>.*)</ns\d*:dispersedInhomogeneity>\s*')

        sand_pattern = re.compile(      r'(<ns\d*:carbonateContentClass codeSpace="urn:bro:bhrgt:CarbonateContentClass">(?P<carbonatecontent>.*)</ns\d*:carbonateContentClass>\s*)?' +
                                        r'<ns\d*:organicMatterContentClass codeSpace="urn:bro:bhrgt:OrganicMatterContentClass">(?P<organicMatter>.*)</ns\d*:organicMatterContentClass>\s*' +
                                        r'<ns\d*:sandMedianClass codeSpace="urn:bro:bhrgt:SandMedianClass">(?P<sandMedian>.*)</ns\d*:sandMedianClass>\s*' +
                                        r'<ns\d*:grainshape>\s*' +
                                            r'<ns\d*:sizeFraction codeSpace="urn:bro:bhrgt:SizeFraction">(?P<sizeFraction>.*)</ns\d*:sizeFraction>\s*' +
                                            r'<ns\d*:angularity codeSpace="urn:bro:bhrgt:Angularity">(?P<angularity>.*)</ns\d*:angularity>\s*' +
                                            r'<ns\d*:sphericity codeSpace="urn:bro:bhrgt:Sphericity">(?P<sphericity>.*)</ns\d*:sphericity>\s*' +
                                        r'</ns\d*:grainshape>\s*'
                                    )

        peat_pattern = re.compile(      r'(<ns\d*:mixed>(?P<mixed>.*)</ns\d*:mixed>\s*)?' +
                                        r'<ns\d*:peatType codeSpace="urn:bro:bhrgt:PeatType">(?P<type>.*)</ns\d*:peatType>\s*' +
                                        r'(<ns\d*:organicSoilTexture codeSpace="urn:bro:bhrgt:OrganicSoilTexture">(?P<soiltexture>.*)</ns\d*:organicSoilTexture>\s*)?' +
                                        r'(<ns\d*:organicSoilConsistency codeSpace="urn:bro:bhrgt:OrganicSoilConsistency">(?P<consistency>.*)</ns\d*:organicSoilConsistency>\s*)?' +
                                        r'(<ns\d*:peatTensileStrength codeSpace="urn:bro:bhrgt:PeatTensileStrength">(?P<tensilestrength>.*)</ns\d*:peatTensileStrength>\s*)?'
                                    )

        clay_pattern = re.compile(      r'(<ns\d*:carbonateContentClass codeSpace="urn:bro:bhrgt:CarbonateContentClass">(?P<carbonatecontent>.*)</ns\d*:carbonateContentClass>\s*)?' +
                                        r'<ns\d*:organicMatterContentClass codeSpace="urn:bro:bhrgt:OrganicMatterContentClass">(?P<organicMatter>.*)</ns\d*:organicMatterContentClass>\s*' +
                                        r'(<ns\d*:mixed>(?P<mixed>.*)</ns\d*:mixed>\s*)?'+ 
                                        r'(<ns\d*:fineSoilConsistency codeSpace="urn:bro:bhrgt:FineSoilConsistency">(?P<consistency>.*)</ns\d*:fineSoilConsistency>\s*)?'
                                    )

        with open(xmlFile) as f:
            xml_raw = f.read()

        try:
            match = re.search(xy_id_pattern, xml_raw)
            self.easting = float(match.group('X'))
            self.northing = float(match.group('Y'))
            self.srid = match.group('coordsys')
        except:
            pass
        try:
            match = re.search(z_id_pattern, xml_raw)
            self.groundlevel = float(match.group('Z'))
        except:
            pass
        try:
            match = re.search(testid_pattern, xml_raw)
            self.testid = match.group('testid')
        except:
            pass
        try:
            match = re.search(report_date_pattern, xml_raw)
            reportdateString = match.group('report_date')
            self.reportdate = datetime.strptime(reportdateString, '%Y-%m-%d')
        except:
            pass
        try:
            match = re.search(trajectory_pattern, xml_raw)
            self.finaldepth = float(match.group('finalDepth'))
        except:
            pass
        try:
            matches = re.finditer(soil_pattern, xml_raw)
            for i, match in enumerate(matches):
                layerupper = float(match.group('layerUpper'))
                layerlower = float(match.group('layerLower'))
                soilname = match.group('soilName')
                anthropogenic = match.group('anthropogenic')
                tertiary = match.group('tertiaryConstituent')
                colour = match.group('colour')
                inhomogeneity = match.group('inhomogeneity')
                self.soillayers.append({"upper": layerupper, "lower": layerlower, "soilName": soilname, "anthropogenic": anthropogenic, "tertiary": tertiary, "colour": colour, "inhomogeneity": inhomogeneity})
        except:
            pass
        try:
            matches = re.finditer(sand_pattern, xml_raw)
            for i, match in enumerate(matches):
                organicmatter = match.group('organicMatter')
                sandmedian = match.group('sandMedian')
                self.sandlayers.append({"organicmatter": organicmatter, "sandmedian": sandmedian})
        except:
            pass
        try:
            matches = re.finditer(peat_pattern, xml_raw)
            for i, match in enumerate(matches):
                peatType = match.group('type')
                self.peatlayers.append({"type": peatType})
        except:
            pass
        try:
            matches = re.finditer(clay_pattern, xml_raw)
            for i, match in enumerate(matches):
                organicmatter = match.group('organicMatter')
                self.claylayers.append({"organicmatter": organicmatter})
        except:
            pass
        
        self.metadata = {"easting": self.easting, "northing": self.northing, "groundlevel": self.groundlevel, "testid": self.testid, "reportdate": self.reportdate, "finaldepth": self.finaldepth}

        # voeg eigenschappen toe die afhankelijk zijn van het hoofdmateriaal
        for layer in self.soillayers:
            if layer["soilName"].lower().endswith("zand") and len(self.sandlayers) > 0:
                layer["sandproperties"] = self.sandlayers.pop(0)
            elif layer["soilName"].lower().endswith("klei") and len(self.claylayers) > 0:
                layer["clayproperties"] = self.claylayers.pop(0)
            elif layer["soilName"].lower().endswith("veen") and len(self.peatlayers) > 0:
                layer["peatproperties"] = self.peatlayers.pop(0)
        
        # zet om in een dataframe om het makkelijker te verwerken
        self.soillayers = pd.DataFrame(self.soillayers)

        # voeg kolommen toe met absolute niveaus (t.o.v. NAP)
        self.soillayers["upper_NAP"] = self.groundlevel - self.soillayers["upper"] 
        self.soillayers["lower_NAP"] = self.groundlevel - self.soillayers["lower"] 

    def plot(self):
        # maak een eenvoudige plot van een boring, alleen het hoofdmateriaal
        fig, ax = plt.subplots(figsize=(10,5))
        colorsDict = {"zand": "yellow", "veen": "brown", "klei": "green", "grind": "orange", "silt": "blue"}
        hatchesDict = {"zand": "...", "veen": "---", "klei": "///", "grind": "ooo", "silt": "xxx"}

        colors = self.soillayers["soilName"]
        for soil, color in colorsDict.items():
            colors = np.where(self.soillayers["soilName"].str.lower().str.endswith(soil), color, colors)
        
        hatches = self.soillayers["soilName"]
        for soil, hatch in hatchesDict.items():
            hatches = np.where(self.soillayers["soilName"].str.lower().str.endswith(soil), hatch, hatches)

        uppers = list(self.soillayers["upper_NAP"])
        labels = list(self.soillayers["soilName"])

        # maak een staafdiagram, met overlappende staven
        for upper, color, hatch, label in reversed(list(zip(uppers, colors, hatches, labels))):
            barPlot = ax.bar(self.testid, upper, width=0.5, color=color, hatch=hatch, edgecolor="black")

            # voeg labels toe met de materiaalnaam
            # TODO: positie moet beter
            for rect in barPlot:
                height = rect.get_height()
                ax.text(rect.get_x() + rect.get_width(), height,
                        label,
                        ha='left', va='bottom')
        plt.show()

        # TODO: toevoegen van specialMaterial?