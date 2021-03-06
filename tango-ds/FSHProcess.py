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


from PyTango import DeviceProxy, EventType, DevFailed


class Logger(object):
    def __init__(self, error=None, warning=None, info=None, debug=None,
                 *args, **kwargs):
        super(Logger, self).__init__(*args, **kwargs)
        self._error = error
        self._warning = warning
        self._info = info
        self._debug = debug

    def error(self, msg):
        if self._error is None:
            print("ERROR: %s" % msg)
        else:
            self._error(msg)

    def warning(self, msg):
        if self._warning is None:
            print("WARNING: %s" % msg)
        else:
            self._warning(msg)

    def info(self, msg):
        if self._info is None:
            print("INFO: %s" % msg)
        else:
            self._info(msg)

    def debug(self, msg):
        if self._debug is None:
            print("DEBUG: %s" % msg)
        else:
            self._debug(msg)


class Monitor(Logger):
    def __init__(self, devName, attrName, minPeriod=0.1, minChange=0.001,
                 callbacks=None, *args, **kwargs):
        super(Monitor, self).__init__(*args, **kwargs)
        self._devName = devName
        self._attrName = attrName
        self._name = "%s/%s" % (devName, attrName)
        try:
            self._proxy = DeviceProxy(self._devName)
        except:
            raise ReferenceError("DeviceProxy for %s not available"
                                 % self._name)
        self._eventId = None
        self._value = None
        self._quality = None
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
        self.debug("%s subscribed: %d" % (self._name, self._eventId))

    def unsubscribe(self):
        if hasattr(self, '_proxy') and self._proxy is not None:
            self._proxy.unsubscribe_event(self._eventId)

    def push_event(self, event):
        if event is not None and event.attr_value is not None:
            if self._checkPeriod(event.attr_value.time.totime()):
                self._timestamp = event.attr_value.time.totime()
                if self._checkChange(event.attr_value.value):
                    self._value = event.attr_value.value
                    self._quality = event.attr_value.quality
                    self.info("%s new value %s (%s, %s)"
                              % (self._name, self._value,
                                 self._quality, self._timestamp))
                    self._reviewCallbacks()

    @property
    def minPeriod(self):
        return self._minPeriod

    @minPeriod.setter
    def minPeriod(self, value):
        self._minPeriod = float(value)

    def _checkPeriod(self, timestamp):
        if self._timestamp is None:
            self.debug("%s: No previous timestamp" % (self._name))
            return True
        else:
            t_diff = timestamp - self._timestamp
            if t_diff > self._minPeriod:
                self.debug("%s: old enough value (%f)" % (self._name, t_diff))
                return True
            self.debug("%s: to recent (%f)" % (self._name, t_diff))
        return False

    @property
    def minChange(self):
        return self._minChange

    @minChange.setter
    def minChange(self, value):
        self._minChange = float(value)

    def _checkChange(self, value):
        if self._value is None:
            self.debug("%s: No previous value" % (self._name))
            return True
        else:
            v_diff = abs(value - self._value)
            if v_diff > self._minChange:
                self.debug("%s: change enough value (%f)" % (self._name,
                                                             v_diff))
                return True
            self.debug("%s: to small change (%f)" % (self._name, v_diff))
        return False

    def _value_getter(self):
        return self._value

    value = property(_value_getter)

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def quality(self):
        return self._quality

    @property
    def callbacks(self):
        return self._callbacks

    def appendCb(self, function):
        if hasattr(function, '__call__'):
            if self._callbacks is None:
                self._callbacks = []
            self._callbacks.append(function)

    def _reviewCallbacks(self):
        if self._callbacks is not None:
            for callback in self._callbacks:
                callback()


class Writter(Monitor):
    def __init__(self, *args, **kwargs):
        super(Writter, self).__init__(*args, **kwargs)

    def _value_setter(self, value):
        self._value = value
        self.info("%s: write: %s" % (self._name, value))
        self.write2proxy(self._value)

    def write2proxy(self, value):
        try:
            self._proxy[self._attrName] = value
        except DevFailed as e:
            self.error("%s: %s" % (e[0].reason, e[0].desc))
        except Exception as e:
            self.error("Exception in write: %s" % (e))

    value = property(Monitor._value_getter, _value_setter)

    def push_event(self, event):
        if event is not None and event.attr_value is not None:
            if event.attr_value.value is None:
                self.info("Received a %s value (%s)"
                          % (event.attr_value.value, self.value))
            elif self.value is None:
                self.info("Received a value %g when self structure "
                          "not yet initialised (%s)" % (event.attr_value.value,
                                                        self.value))
                self._value = event.attr_value.value
                self._reviewCallbacks()
            elif self.value == event.attr_value.value:
                self.info("Received a confirmation of the write (%g)"
                          % event.attr_value.value)
                self._timestamp = event.attr_value.time.totime()
                self._reviewCallbacks()
            else:
                self.warning("Received a value change but it doesn't "
                             "corresponds with what shall be (%g != %g)"
                             % (self.value, event.attr_value.value))
                # rewrite
                self.write2proxy(self._value)


class Formula(Logger):
    def __init__(self, formulaStr, motor, *args, **kwargs):
        super(Formula, self).__init__(*args, **kwargs)
        self._offset = 0
        self._motor = motor
        self._formulaStr = None
        self._extendedFormula = ""
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

    @property
    def extendedFormula(self):
        return self._extendedFormula

    @formulaStr.setter
    def formulaStr(self, value):
        if value.count("OFFSET") == 0:
            self.warning("Formula doesn't have OFFSET (%s)" % value)
        elif value.count("POSITION") == 0:
            self.warning("Formula doesn't have POSITION (%s)" % value)
        self._formulaStr = value

    def evaluate(self):
        extendedFormula = formula = self._formulaStr
        if formula.count("OFFSET"):
            formula = formula.replace("OFFSET", 'self.offset')
            try:
                value = " %g " % self.offset
            except:
                self.warning("Cannot replace OFFSET as a float")
                value = " %s " % self.offset
            extendedFormula = extendedFormula.replace("OFFSET", value)
        if formula.count("POSITION"):
            formula = formula.replace("POSITION", 'self.position')
            try:
                value = " %g " % self.position
            except:
                self.warning("Cannot replace OFFSET as a float")
                value = " %s " % self.position
            extendedFormula = extendedFormula.replace("POSITION", value)
        self._extendedFormula = extendedFormula
        try:
            result = eval(formula)
            self.debug("with offset = %s, position = %s, "
                       "the formula %s returns %s = %s"
                       % (self.offset, self.position, self.formulaStr,
                          extendedFormula, result))
            return result
        except Exception as e:
            self.error("Exception in the _eval_: %s" % (e))


class FSH(Logger):
    def __init__(self, motorName, ibaName=None, formula=None,
                 *args, **kwargs):
        super(FSH, self).__init__(*args, **kwargs)
        if ibaName is None or ibaName == []:
            ibaName = motorName+"-iba"
        if formula is None or formula == []:
            formula = "OFFSET-POSITION"
        self._chamberObj = Writter(ibaName, 'ChamberOffsetX', *args, **kwargs)
        self._positionObj = Monitor(motorName, 'Position', *args, **kwargs)
        self._formulaObj = Formula(formula, self._positionObj, *args, **kwargs)
        self._positionObj.appendCb(self.evaluate)
        # to check if it has been written from another side
        self._chamberObj.appendCb(self.check)

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
        value = self._formulaObj.evaluate()
        if value is not None:
            self._chamberObj.value = value
            return self._chamberObj.value

    def check(self):
        itIs = self._chamberObj.value
        shallBe = self._formulaObj.evaluate()
        if shallBe is not None and itIs != shallBe:
            self.warning("ChamberOffsetX is %g and shall be %g"
                         % (itIs, shallBe))


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
