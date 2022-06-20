from gefxml_reader import Bore

f = './input/DP14+074_MB_KR.xml'
f = './input/bore.xml'
f = './input/DCG0101_B_BHR000000347910.xml'

bore = Bore()
bore.load_xml(f)
bore.plot()
