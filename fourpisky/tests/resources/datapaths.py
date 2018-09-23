import os
from fourpisky.tests.resources import __path__ as data_dir
data_dir = data_dir[0]
swift_bat_grb_pos_v2 = os.path.join(data_dir,
                                    'SWIFT_bat_position_v2.0_example.xml')
swift_bat_grb_circumpolar = os.path.join(data_dir, 'SWIFT_bat_circumpolar.xml')
swift_bat_grb_low_dec = os.path.join(data_dir, 'SWIFT_bat_low_dec.xml')
swift_bat_grb_lost_lock = os.path.join(data_dir, 'BAT_GRB_Pos_558756-820.xml')
swift_bat_known_source = os.path.join(data_dir, 'BAT_GRB_Pos_570069-383.xml')
swift_bat_grb_bad_duration_analysis = os.path.join(data_dir, 'BAT_GRB_Pos_707545-520.xml')

asassn_feed_page_2015_12_21 =  os.path.join(data_dir, 'asassn_feed_2015-12-21.html')
asassn_feed_page_2016_01_11 =  os.path.join(data_dir, 'asassn_feed_2016-01-11.html')
asassn_feed_page_2018_09_23 =  os.path.join(data_dir, 'asassn_feed_2018-09-23.html')

asassn_alert_16ab =  os.path.join(data_dir, '2016-01-3.62_ASASSN-16ab.xml')
asassn_alert_AT2016D =  os.path.join(data_dir, '2016-01-2.12_AT_2016D.xml')

gaia_feed_csv_2016_04_04 = os.path.join(data_dir, 'gaia_alerts.csv')

gaia_alert_16ajo = os.path.join(data_dir, 'Gaia16ajo.xml')