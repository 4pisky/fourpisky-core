import unittest
from unittest import TestCase

from .resources import datapaths
from pysovo import voevent as voe
from lxml import objectify
from astropysics.coords.coordsys import FK5Coordinates



class TestBuilders(TestCase):

    def test_builders_on_voe_v2(self):
        vff = voe.build.from_file(datapaths.swift_bat_grb_pos_v2)
        with open(datapaths.swift_bat_grb_pos_v2) as f:
            vfs = voe.build.from_string(f.read())
        self.assertEqual(objectify.dump(vff), objectify.dump(vfs))
        self.assertEqual(vfs.tag, '{}VOEvent')
        print vfs.attrib['ivorn']


class TestAstroCoords(TestCase):
    def setUp(self):
        self.swift_grb_v2 = voe.build.from_file(datapaths.swift_bat_grb_pos_v2)
        self.swift_grb_posn = FK5Coordinates(ra=74.741200, dec= -9.313700,
                                             raerr=0.05, decerr=0.05)
    def test_swift_grb_v2(self):
        p = voe.pull_astro_coords(self.swift_grb_v2)
        self.assertEqual(p, self.swift_grb_posn)





