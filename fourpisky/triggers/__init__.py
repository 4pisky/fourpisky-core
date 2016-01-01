from __future__ import absolute_import
import fourpisky.triggers.swift
from fourpisky.voevent import ivorn_base, test_trigger_substream



def is_test_trigger(voevent):
    ivorn  = voevent.attrib['ivorn']
    if ivorn.startswith("ivo://"+ ivorn_base+'/'+test_trigger_substream+'#'):
        return True
    return False



