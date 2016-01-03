import ephem
AmiLA = ephem.Observer()
AmiLA.lat = ephem.degrees('52.16977')
AmiLA.lon = ephem.degrees('0.059167')
AmiLA.horizon = ephem.degrees('20')
AmiLA.name = 'AMI-LA'
