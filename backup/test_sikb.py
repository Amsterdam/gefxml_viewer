from gefxml_reader import Bore, Multibore

mb = Multibore()
mb.load_xml_sikb0101('./input/2010P258.xml')
mb.load_xml_sikb0101('./input/imsikb_v14-project-229492_verkennendbodemonderzoekkabel-enleidingtraceterpl_20220610084424549.xml')

for bore in mb.bores:
    bore.plot()