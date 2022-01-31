"""
Script om sonderingen in te lezen vanuit GEF of XML
en sonderingen plotten

Geschreven door Thomas van der Linden, Ingenieursbureau Amsterdam
19 oktober 2021
"""

from ctypes import alignment
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
        self.companyid = None
        self.projectid = None
        self.projectname = None

    def load_xml(self, xmlFile):

        filename_pattern = re.compile(r'(.*[\\/])*(?P<filename>.*)\.')
        testid_pattern = re.compile(r'<.*:broId>\s*(?P<testid>.*)</.*:broId>')
        objectid_pattern = re.compile(r'<.*:objectIdAccountableParty>\s*(?P<testid>.*)\s*</.*:objectIdAccountableParty>')
        xy_id_pattern = re.compile(r'<.*:location srsName="urn:ogc:def:crs:EPSG::28992"\s*.*\d*?:id="BRO_\d*">\s*' + 
                                        r'<.*\d*?:pos>(?P<X>\d*.?\d*)\s*(?P<Y>\d*.?\d*)</.*\d*?:pos>')
        z_id_pattern = re.compile(r'<.*:offset uom="(?P<z_unit>.*)">(?P<Z>-?\d*.?\d*)</.*:offset>')
        trajectory_pattern = re.compile(r'<.*:finalDepth uom="m">(?P<finalDepth>\d*.?\d*)</.*:finalDepth>\s')
        report_date_pattern = re.compile(r'<.*:researchReportDate>\s*<.*:date>(?P<report_date>\d*-\d*-\d*)</.*:date>')
        removed_layer_pattern = re.compile(r'<.*:removedLayer>\s*'+ 
                                                r'<.*:sequenceNumber>(?P<layerNr>\d*)</.*:sequenceNumber>\s*' + 
                                                r'<.*:upperBoundary uom="m">(?P<layerUpper>\d*.?\d*)</.*:upperBoundary>\s*' + 
                                                r'<.*:lowerBoundary uom="m">(?P<layerLower>\d*.?\d*)</.*:lowerBoundary>\s*' + 
                                                r'<.*:description>(?P<layerDescription>.*)</.*:description>\s*' + 
                                            r'</.*:removedLayer>\s*')
        data_pattern = re.compile(r'<.*:values>(?P<data>.*)</.*:values>')

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
            self.startdate = date(startdatelist[0], startdatelist[1], startdatelist[2])
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
            self.data["depth"] = self.data["depth"].abs()

        # soms is er geen diepte, maar wel sondeerlengte aanwezig
        # sondeerlengte als diepte gebruiken is goed genoeg als benadering
        # TODO: onderstaande blok voor diepte correctie is niet gecheckt op correctheid 
        # TODO: vraag me af of het gebruik hiervan ooit mogelijk / nodig is, want indien de hoek gemeten is, dan is meestal ook de gecorrigeerde diepte gerapporteerd
        elif "penetrationLength" in self.data.columns:
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
            else:
                self.data["depth"] = self.data["penetrationLength"].abs()

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

    def plot(self):
        if self.groundlevel == None:
            self.groundlevel = 0

        y = self.groundlevel - self.data["depth"]

        # x,y voor maaiveld in figuur
        x_maaiveld = [0, 10]
        y_maaiveld = [self.groundlevel, self.groundlevel]

        # figuur met twee grafieken
        # TODO: dit kunnen we ook op dezelfde manier doen als bij de boringen, zodat de verticale schaal altijd hetzelfde is
        # TODO: dat is wel lastiger met pdf maken
        fig, axes = plt.subplots(nrows=1, ncols=5, figsize=(18,24), sharey=True, gridspec_kw = {'width_ratios':[5, 1, 1, 1, 1]})

        axes[0].plot(self.data['coneResistance'], y, label='qc [MPa]', linewidth=1.25, color='#4b0082')
        axes[1].plot(self.data["localFriction"], y, label='fs [MPa]', linewidth=1.25, color='blue')
        axes[2].plot(self.data["frictionRatio"], y, label='Rf [%]', linewidth=1.25, color='red')
        
        inclinations = ["inclinationEW", "inclinationNS", "inclinationX", "inclinationY", "inclinationResultant"]
        for inclination in inclinations:
            if inclination in self.data.columns:
                axes[3].plot(self.data[inclination], y, label=re.sub(r'inclination', '', inclination), linewidth=1.25, color='green')
        
        porePressures = ["porePressureU1", "porePressureU2", "porePressureU3"]
        for porePressure in porePressures:
            if porePressure in self.data.columns:
                axes[4].plot(self.data[porePressure], y, label=porePressure[-2:], linewidth=1.25, color='blue')

        # plot maaiveld, bestaat uit een streep en een arcering
        axes[0].plot(x_maaiveld, y_maaiveld, color='black')
        axes[0].barh(self.groundlevel, width=10, height=-0.4, align='edge', hatch='/\/', color='#ffffffff')

        axes[0].set_ylabel("Niveau [m t.o.v. NAP]")
        axes[0].set_xlabel("qc [MPa]")
        axes[1].set_xlabel("fs [MPa]")
        axes[2].set_xlabel("Rf [%]")
        axes[3].set_xlabel("helling [deg]")
        axes[4].set_xlabel("u [Mpa]")
        axes[3].legend()
        axes[4].legend()

        axes[0].set_xlim([0, 40])
        axes[2].set_xlim([0, 12])

        # Plot top datablock with CPT information
        plt.suptitle(f'CPT: {self.testid}\nx-coördinaat: {self.easting}\ny-coördinaat: {self.northing}\nz-coördinaat: {self.groundlevel}\n', x=0.15, y=0.09, ha='left', fontsize=14, fontweight='bold')
        fig.supxlabel(f'Uitvoerder: {self.companyid}\nDatum: {self.reportdate}\nProjectnummer: {self.projectid}\nProjectnaam: {self.projectname}', y=0.05 , ha='left', va='bottom', fontsize=14, fontweight='bold')
        # Plot datablock with general information
        # TODO: positie is verkeerd
        plt.title('Ingenieursbureau\n Gemeente Amsterdam\n Vakgroep Geotechniek\n Python ', loc='left', fontsize=13.5)

        for ax in axes:

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
                plt.savefig(fname=f"./output/{self.projectname}_{self.testid}.png")
                plt.close('all')


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
        testid_pattern_broid = re.compile(r'<broId>\s*(?P<testid>.*)</broId>')
        testid_pattern_accountableparty = re.compile(r'<objectIdAccountableParty>\s*(?P<testid>.*)</objectIdAccountableParty>')
        xy_id_pattern_crs_first = re.compile(r'<.*:Point\s*srsName="urn:ogc:def:crs:EPSG::(?P<coordsys>.*)"\s*.*:id=".*">\s*' +
                        r'<.*:pos>(?P<X>\d*.?\d*)\s*(?P<Y>\d*.?\d*)</.*:pos>')
        xy_id_pattern_id_first = re.compile(r'<.*:Point\s*.*:id=".*"\s*srsName="urn:ogc:def:crs:EPSG::(?P<coordsys>.*)">\s*' +
                        r'<.*:pos>(?P<X>\d*.?\d*)\s*(?P<Y>\d*.?\d*)</.*:pos>')
        z_id_pattern = re.compile(r'<.*:offset uom="(?P<z_unit>.*)">(?P<Z>.*)</.*:offset>')
        trajectory_pattern = re.compile(r'<.*:finalDepthBoring uom="m">(?P<finalDepth>\d*.?\d*)</.*:finalDepthBoring>')
        report_date_pattern = re.compile(r'<.*:descriptionReportDate>\s*<date>(?P<report_date>\d*-\d*-\d*)</date>')

        # TODO: dit kan worden opgesplitst, maar dan raak je wel de samenhang kwijt
        # TODO: met """ i.p.v. ' ' + ' '
        soil_pattern = re.compile(r'<.*:layer>\s*' + 
                                    r'<.*:upperBoundary uom="m">(?P<layerUpper>\d*.?\d*)</.*:upperBoundary>\s*' +
                                    r'<.*:upperBoundaryDetermination codeSpace="urn:bro:bhrgt:BoundaryPositioningMethod">.*</.*:upperBoundaryDetermination>\s*' +
                                    r'<.*:lowerBoundary uom="m">(?P<layerLower>\d*.?\d*)</.*:lowerBoundary>\s*' +
                                    r'<.*:lowerBoundaryDetermination codeSpace="urn:bro:bhrgt:BoundaryPositioningMethod">.*</.*:lowerBoundaryDetermination>\s*' +
                                    r'<.*:anthropogenic>(?P<anthropogenic>.*)</.*:anthropogenic>\s*' +
                                    r'(<.*:slant>(?P<slant>.*)</.*:slant>\s*)?' +
                                    r'(<.*:internalStructureIntact>(?P<internalstructure>.*)</.*:internalStructureIntact>\s*)?' +
                                    r'(<.*:bedded>(?P<bedded>.*)</.*:bedded>\s*)?' +
                                    r'(<.*:compositeLayer>(?P<compositelayer>.*)</.*:compositeLayer>\s*)?'
                                    r'<.*:soil>\s*' +
                                        r'<.*:geotechnicalSoilName codeSpace="urn:bro:bhrgt:GeotechnicalSoilName">(?P<soilName>.*)</.*:geotechnicalSoilName>\s*' +
                                        r'(<.*:tertiaryConstituent codeSpace="urn:bro:bhrgt:TertiaryConstituent">(?P<tertiaryConstituent>.*)</.*:tertiaryConstituent>\s*)?' +
                                        r'(<.*:colour codeSpace="urn:bro:bhrgt:Colour">(?P<colour>.*)</.*:colour>\s*)?' +
                                        r'(<.*:dispersedInhomogeneity codeSpace="urn:bro:bhrgt:DispersedInhomogeneity">(?P<inhomogeneity>.*)</.*:dispersedInhomogeneity>\s*)?')

        sand_pattern = re.compile(      r'(<.*:carbonateContentClass codeSpace="urn:bro:bhrgt:CarbonateContentClass">(?P<carbonatecontent>.*)</.*:carbonateContentClass>\s*)?' +
                                        r'<.*:organicMatterContentClass codeSpace="urn:bro:bhrgt:OrganicMatterContentClass">(?P<organicMatter>.*)</.*:organicMatterContentClass>\s*' +
                                        r'<.*:sandMedianClass codeSpace="urn:bro:bhrgt:SandMedianClass">(?P<sandMedian>.*)</.*:sandMedianClass>\s*' +
                                        r'<.*:grainshape>\s*' +
                                            r'<.*:sizeFraction codeSpace="urn:bro:bhrgt:SizeFraction">(?P<sizeFraction>.*)</.*:sizeFraction>\s*' +
                                            r'<.*:angularity codeSpace="urn:bro:bhrgt:Angularity">(?P<angularity>.*)</.*:angularity>\s*' +
                                            r'<.*:sphericity codeSpace="urn:bro:bhrgt:Sphericity">(?P<sphericity>.*)</.*:sphericity>\s*' +
                                        r'</.*:grainshape>\s*'
                                    )

        peat_pattern = re.compile(      r'(<.*:mixed>(?P<mixed>.*)</.*:mixed>\s*)?' +
                                        r'<.*:peatType codeSpace="urn:bro:bhrgt:PeatType">(?P<type>.*)</.*:peatType>\s*' +
                                        r'(<.*:organicSoilTexture codeSpace="urn:bro:bhrgt:OrganicSoilTexture">(?P<soiltexture>.*)</.*:organicSoilTexture>\s*)?' +
                                        r'(<.*:organicSoilConsistency codeSpace="urn:bro:bhrgt:OrganicSoilConsistency">(?P<consistency>.*)</.*:organicSoilConsistency>\s*)?' +
                                        r'(<.*:peatTensileStrength codeSpace="urn:bro:bhrgt:PeatTensileStrength">(?P<tensilestrength>.*)</.*:peatTensileStrength>\s*)?'
                                    )

        clay_pattern = re.compile(      r'(<.*:carbonateContentClass codeSpace="urn:bro:bhrgt:CarbonateContentClass">(?P<carbonatecontent>.*)</.*:carbonateContentClass>\s*)?' +
                                        r'<.*:organicMatterContentClass codeSpace="urn:bro:bhrgt:OrganicMatterContentClass">(?P<organicMatter>.*)</.*:organicMatterContentClass>\s*' +
                                        r'(<.*:mixed>(?P<mixed>.*)</.*:mixed>\s*)?'+ 
                                        r'(<.*:fineSoilConsistency codeSpace="urn:bro:bhrgt:FineSoilConsistency">(?P<consistency>.*)</.*:fineSoilConsistency>\s*)?'
                                    )

        with open(xmlFile) as f:
            xml_raw = f.read()

        try:
            match = re.search(xy_id_pattern_crs_first, xml_raw)
            self.easting = float(match.group('X'))
            self.northing = float(match.group('Y'))
            self.srid = match.group('coordsys')
        except:
            pass
        try:
            match = re.search(xy_id_pattern_id_first, xml_raw)
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
            match = re.search(testid_pattern_broid, xml_raw)
            self.testid = match.group('testid')
        except:
            pass
        try:
            match = re.search(testid_pattern_accountableparty, xml_raw)
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

        # voeg verdeling componenten toe
        # van https://github.com/cemsbv/pygef/blob/master/pygef/broxml.py
        material_components = ["gravel_component", "sand_component", "clay_component", "loam_component", "peat_component", "silt_component"]
        soil_names_dict_lists = {
            "betonOngebroken": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # specialMaterial
            "keitjes": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "klei": [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
            "kleiigVeen": [0.0, 0.0, 0.3, 0.0, 0.7, 0.0],
            "kleiigZand": [0.0, 0.7, 0.3, 0.0, 0.0, 0.0],
            "kleiigZandMetGrind": [0.05, 0.65, 0.3, 0.0, 0.0, 0.0],
            "puin": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # specialMaterial
            "siltigZand": [0.0, 0.7, 0.0, 0.0, 0.0, 0.3],
            "siltigZandMetGrind": [0.05, 0.65, 0.0, 0.0, 0.0, 0.3],
            "sterkGrindigZand": [0.3, 0.7, 0.0, 0.0, 0.0, 0.0],
            "sterkGrindigeKlei": [0.3, 0.0, 0.7, 0.0, 0.0, 0.0],
            "sterkZandigGrind": [0.7, 0.3, 0.0, 0.0, 0.0, 0.0],
            "sterkZandigSilt": [0.0, 0.3, 0.0, 0.0, 0.0, 0.7],
            "sterkZandigeKlei": [0.0, 0.3, 0.7, 0.0, 0.0, 0.0],
            "sterkZandigeKleiMetGrind": [0.05, 0.3, 0.65, 0.0, 0.0, 0.0],
            "veen": [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            "zand": [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            "zwakGrindigZand": [0.1, 0.9, 0.0, 0.0, 0.0, 0.0],
            "zwakGrindigeKlei": [0.1, 0.0, 0.9, 0.0, 0.0, 0.0],
            "zwakZandigGrind": [0.9, 0.1, 0.0, 0.0, 0.0, 0.0],
            "zwakZandigVeen": [0.0, 0.1, 0.0, 0.0, 0.9, 0.0],
            "zwakZandigeKlei": [0.0, 0.1, 0.9, 0.0, 0.0, 0.0],
            "zwakZandigeKleiMetGrind": [0.05, 0.1, 0.85, 0.0, 0.0, 0.0],
        }
        # voor sorteren op bijdrage is het handiger om een dictionary te maken
        soil_names_dict_dicts = {}
        for key, value in soil_names_dict_lists.items():
            soil_names_dict_dicts[key] = dict(sorted({v: i for i, v in enumerate(value)}.items(), reverse=True))
        self.soillayers["components"] = self.soillayers["soilName"].map(soil_names_dict_dicts)

        # voeg een plotkleur toe
        colorsDict = {"zand": "yellow", "veen": "brown", "klei": "green", "grind": "orange", "silt": "blue"}
        colors = self.soillayers["soilName"]
        for soil, color in colorsDict.items():
            colors = np.where(self.soillayers["soilName"].str.lower().str.endswith(soil), color, colors)
        self.soillayers["plotColor"] = colors

        # voeg een arcering toe
        hatchesDict = {"zand": "...", "veen": "---", "klei": "///", "grind": "ooo", "silt": "xxx"}
        hatches = self.soillayers["soilName"]
        for soil, hatch in hatchesDict.items():
            hatches = np.where(self.soillayers["soilName"].str.lower().str.endswith(soil), hatch, hatches)
        self.soillayers["plotHatch"] = hatches

        # voeg kolommen toe met absolute niveaus (t.o.v. NAP)
        self.soillayers["upper_NAP"] = self.groundlevel - self.soillayers["upper"] 
        self.soillayers["lower_NAP"] = self.groundlevel - self.soillayers["lower"] 

    def plot(self):
        # maak een eenvoudige plot van een boring, alleen het hoofdmateriaal
        # TODO: dit moet met secundair (en tertiair) materiaal
        fig, ax = plt.subplots(figsize=(10,5))

        uppers = list(self.soillayers["upper_NAP"])
        lowers = list(self.soillayers["lower_NAP"])
        labels = list(self.soillayers["soilName"])
        colors = list(self.soillayers["plotColor"])
        hatches = list(self.soillayers["plotHatch"])

        # maak een diagram met primaire en secundaire componenten
        # TODO: dit is een samenraapsel van code van hiervoor, dit moet opgeruimd
        fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(6, self.finaldepth + 2), gridspec_kw = {'height_ratios':[self.finaldepth, 2]})
        components = list(self.soillayers["components"])
        colorsDict = {1: "yellow", 4: "brown", 2: "green", 0: "orange", 5: "blue", 3: "purple"}
        hatchesDict = {1: "...", 4: "---", 2: "///", 0: "ooo", 5: "xxx", 3:""}
        for upper, lower, component in reversed(list(zip(uppers, lowers, components))):
            left = 0
            for comp, nr in component.items():
                barPlot = ax[0].barh(lower, width=comp, left=left, height=upper-lower, color=colorsDict[nr], hatch=hatchesDict[nr], edgecolor="black", align="edge")
                left += comp

        ax[0].set_ylim([self.groundlevel - self.finaldepth, self.groundlevel])
        ax[0].set_xticks([])
        ax[0].set_ylabel('diepte [m t.o.v. NAP]')

        # verberg de assen van de tweede plot zodat deze gebruikt kan worden voor een stempel
        ax[1].set_axis_off()
        plt.title(f'Boring: {self.testid}\nx-coördinaat: {self.easting}\ny-coördinaat: {self.northing}\nmaaiveld: {self.groundlevel}\n', x=0.05, y=0.09, ha='left', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(fname=f'./output/{self.testid}.png')
        plt.close('all')

        # TODO: toevoegen van specialMaterial?