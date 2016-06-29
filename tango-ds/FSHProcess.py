# -*- coding: utf-8 -*-
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

__author__ = "Sergi Blanch-Torne"
__email__ = "sblanch@cells.es"
__copyright__ = "Copyright 2016, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


from PyTango import DeviceProxy, EventType


class Monitor(object):
    def __init__(self, devName, attrName, minPeriod=0.1, minChange=0.001,
                 callbacks=None, *args, **kwargs):
        super(Monitor, self).__init__(*args, **kwargs)
        self._devName = devName
        self._attrName = attrName
        self._name = "%s/%s" % (devName, attrName)
        self._proxy = DeviceProxy(self._devName)
        self._eventId = None
        self._value = None
        self._minPeriod = minPeriod
        self._minChange = minChange
        self._timestamp = None
        self._callbacks = callbacks
        self.subscribe()

    def __del__(self):
        self.unsubscribe()

    def subscribe(self):
        self._eventId = self._proxy.subscribe_event(self._attrName,
                                                    EventType.CHANGE_EVENT,
                                                    self, stateless=True)
        print("%s subscribed: %d" % (self._name, self._eventId))

    def unsubscribe(self):
        self._proxy.unsubscribe_event(self._eventId)

    def push_event(self, event):
        if event is not None and event.attr_value is not None:
            # print("%s event received: %s" % (self._name, event.attr_value))
            if self._checkPeriod(event.attr_value.time.totime()):
                self._timestamp = event.attr_value.time.totime()
                if self._checkChange(event.attr_value.value):
                    self._value = event.attr_value.value
                    print("%s new value %s (%s)" % (self._name, self._value,
                                                    self._timestamp))
                    if self._callbacks is not None:
                        for callback in self._callbacks:
                            callback()

    @property
    def minPeriod(self):
        return self._minPeriod

    @minPeriod.setter
    def minPeriod(self, value):
        self._minPeriod = float(value)

    def _checkPeriod(self, timestamp):
        if self._timestamp is None:
            print("%s: No previous timestamp" % (self._name))
            return True
        else:
            t_diff = timestamp - self._timestamp
            if t_diff > self._minPeriod:
                print("%s: old enough value (%f)" % (self._name, t_diff))
                return True
            print("%s: to recent (%f)" % (self._name, t_diff))
        return False

    @property
    def minChange(self):
        return self._minChange

    @minChange.setter
    def minChange(self, value):
        self._minChange = float(value)

    def _checkChange(self, value):
        if self._value is None:
            print("%s: No previous value" % (self._name))
            return True
        else:
            v_diff = abs(value - self._value)
            if v_diff > self._minChange:
                print("%s: change enough value (%f)" % (self._name, v_diff))
                return True
            print("%s: to small change (%f)" % (self._name, v_diff))
        return False

    def _value_getter(self):
        return self._value

    value = property(_value_getter)

    @property
    def callbacks(self):
        return self._callbacks

    def appendCb(self, function):
        if hasattr(function, '__call__'):
            if self._callbacks is None:
                self._callbacks = []
            self._callbacks.append(function)


class Writter(Monitor):
    def __init__(self, *args, **kwargs):
        super(Writter, self).__init__(*args, **kwargs)

    def _value_setter(self, value):
        print("%s: write: %s" % (self._name, value))
        self._proxy[self._attrName] = value

    value = property(Monitor._value_getter, _value_setter)


class Formula(object):
    def __init__(self, formulaStr, motor, *args, **kwargs):
        super(Formula, self).__init__(*args, **kwargs)
        self._offset = 0
        self._motor = motor
        self._formulaStr = None
        self.formulaStr = formulaStr

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = float(value)

    @property
    def position(self):
        return self._motor.value

    @property
    def formulaStr(self):
        return self._formulaStr

    @formulaStr.setter
    def formulaStr(self, value):
        if value.count("OFFSET") == 0:
            print("Formula doesn't have OFFSET")
        elif value.count("POSITION") == 0:
            print("Formula doesn't have POSITION")
        self._formulaStr = value

    def evaluate(self):
        formula = self._formulaStr
        formula = formula.replace("OFFSET", 'self.offset')
        formula = formula.replace("POSITION", 'self.position')
        return eval(formula)


class FSH(object):
    def __init__(self, motorName, ibaName, formula="OFFSET-POSITION",
                 *args, **kwargs):
        super(FSH, self).__init__(*args, **kwargs)
        self._chamberObj = Writter(ibaName, 'ChamberOffsetX')
        self._positionObj = Monitor(motorName, 'Position')
        self._formulaObj = Formula(formula, self._positionObj)
        self._positionObj.appendCb(self.evaluate)

    @property
    def positionObj(self):
        return self._positionObj

    @property
    def chamberObj(self):
        return self._chamberObj

    @property
    def formulaObj(self):
        return self._formulaObj

    @property
    def offset(self):
        return self._formulaObj.offset

    @offset.setter
    def offset(self, value):
        if self._formulaObj.offset != value:
            self._formulaObj.offset = value
            self.evaluate()

    @property
    def formula(self):
        return self._formulaObj.formulaStr

    def evaluate(self):
        print("FSH.evaluate()")
        self._chamberObj.value = self._formulaObj.evaluate()
        return self._chamberObj.value


# ##########################################################################---
# TEST AREA ---


def main():
    from time import sleep
    from optparse import OptionParser
    from gc import collect
    parser = OptionParser()
    parser.add_option('', "--motor", help="Tango device name of the "
                                          "Pool motor.")
    parser.add_option('', "--iba",
                      help="Tango device name of the ImgBeamAnalyzer "
                           "(if not specified suffix the motor name).")
    parser.add_option('', "--offset", help="Offset to apply.")
    parser.add_option('', "--formula", help="Formula to apply.")
    (options, args) = parser.parse_args()
    if options.motor is not None:
        motorName = options.motor
        if options.iba is not None:
            ibaName = options.iba
        else:
            ibaName = options.motor+"-iba"
        fsh = FSH(motorName, ibaName)
        print("motor position: %g" % fsh.positionObj.value)
        print("iba chamber offset: %g" % fsh.chamberObj.value)

        print("\neval with offset 0")
        result = fsh.evaluate()
        print("formula %s = %g" % (fsh.formula, result))
        sleep(1)

        if options.offset is not None:
            fsh.offset = options.offset
        else:
            fsh.offset = 1.1
        print("\neval with offset %f" % fsh.offset)
        result = fsh.evaluate()
        print("formula %s = %g" % (fsh.formula, result))

        fsh.offset = 2*fsh.offset
        print("\neval with offset %f" % fsh.offset)
        result = fsh.evaluate()
        print("formula %s = %g" % (fsh.formula, result))
    else:
        print("\nPlease check the help.\n")

# controls02 testing
#   $ python FSHOffset.py --motor=motor/sbtestdummymotorctrl/1 \
#      --iba=lab/el/test-01-iba
# or
# >>> import FSHOffset
# >>> fsh = FSHOffset.FSH('motor/sbtestdummymotorctrl/1',
#                         'lab/el/test-01-iba')

if __name__ == '__main__':
    main()
