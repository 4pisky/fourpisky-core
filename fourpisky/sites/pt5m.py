import ephem

# https://sites.google.com/site/point5metre/specifications
Pt5m = ephem.Observer()
Pt5m.lat = ephem.degrees('28.7636')
Pt5m.lon = ephem.degrees('-17.8947')
Pt5m.elevation = 2332
Pt5m.horizon = ephem.degrees('20')
Pt5m.name = 'pt5m'