#!/usr/bin/env python
# -*- coding:utf-8 -*-


# ############################################################################
#  license :
# ============================================================================
#
#  File :        FSHOffset.py
#
#  Project :     FSHOffset
#
# This file is part of Tango device class.
# 
# Tango is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Tango is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Tango.  If not, see <http://www.gnu.org/licenses/>.
# 
#
#  $Author :      sblanch$
#
#  $Revision :    $
#
#  $Date :        $
#
#  $HeadUrl :     $
# ============================================================================
#            This file is generated by POGO
#     (Program Obviously used to Generate tango Object)
# ############################################################################

__all__ = ["FSHOffset", "FSHOffsetClass", "main"]

__docformat__ = 'restructuredtext'

import PyTango
import sys
# Add additional import
#----- PROTECTED REGION ID(FSHOffset.additionnal_import) ENABLED START -----#
from FSHProcess import FSH
from time import time
from types import StringType
#----- PROTECTED REGION END -----#	//	FSHOffset.additionnal_import

# Device States Description
# INIT : 
# FAULT : 
# ON : 


class FSHOffset (PyTango.Device_4Impl):
    """Very simple Tango device server to, in an Horizontal FS, set the chamber offset when the motor moves."""
    
    # -------- Add you global variables here --------------------------
    #----- PROTECTED REGION ID(FSHOffset.global_variables) ENABLED START -----#
    def change_state(self, newstate):
        if newstate != self.get_state():
            self.push_change_event('State', newstate)
            self.set_state(newstate)

    def change_status(self, newstatus):
        if newstatus != self.get_status():
            self.push_change_event('Status', newstatus)
            self.set_status(newstatus)

    def fireEvent(self, attrName, value, timestamp=None, quality=None,
                  doLog=True):
        if quality is None:
            quality = PyTango.AttrQuality.ATTR_VALID
        if timestamp is None:
            timestamp = time()
        if doLog:
            self.info_stream("fireEvent(%s, %s, %s, %s)"
                             % (attrName, value, timestamp, quality))
        self.push_change_event(attrName, value, timestamp, quality)

    def motorPositionCallback(self):
        self.fireEvent('MotorPosition', self._fsh.positionObj.value,
                       self._fsh.positionObj.timestamp,
                       self._fsh.positionObj.quality)

    def chamberOffsetXCallback(self):
        self.fireEvent('ChamberOffsetX', self._fsh.chamberObj.value,
                       self._fsh.chamberObj.timestamp,
                       self._fsh.chamberObj.quality)

    def extendedFormulaCallback(self):
        self.fireEvent('ExtendedFormula', self._fsh.formulaObj.extendedFormula)

    #----- PROTECTED REGION END -----#	//	FSHOffset.global_variables

    def __init__(self, cl, name):
        PyTango.Device_4Impl.__init__(self,cl,name)
        self.debug_stream("In __init__()")
        FSHOffset.init_device(self)
        #----- PROTECTED REGION ID(FSHOffset.__init__) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	FSHOffset.__init__
        
    def delete_device(self):
        self.debug_stream("In delete_device()")
        #----- PROTECTED REGION ID(FSHOffset.delete_device) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	FSHOffset.delete_device

    def init_device(self):
        self.debug_stream("In init_device()")
        self.get_device_properties(self.get_device_class())
        self.attr_offset_read = 0.0
        self.attr_MotorPosition_read = 0.0
        self.attr_ChamberOffsetX_read = 0.0
        self.attr_Formula_read = ""
        self.attr_ExtendedFormula_read = ""
        #----- PROTECTED REGION ID(FSHOffset.init_device) ENABLED START -----#
        self.set_change_event('State', True, False)
        self.set_change_event('Status', True, False)
        self.change_state(PyTango.DevState.INIT)
        self.change_status("Initializing...")
        #tools for the Exec() cmd
        DS_MODULE = __import__(self.__class__.__module__)
        kM = dir(DS_MODULE)
        vM = map(DS_MODULE.__getattribute__, kM)
        self.__globals = dict(zip(kM, vM))
        self.__globals['self'] = self
        self.__globals['module'] = DS_MODULE
        self.__locals = {}
        #prepare reference objects
        try:
            self._fsh = FSH(self.motor, self.iba, self.formula,
                            error=self.error_stream, warning=self.warn_stream,
                            info=self.info_stream, debug=self.debug_stream)
            self._fsh.positionObj.appendCb(self.motorPositionCallback)
            self._fsh.positionObj.appendCb(self.extendedFormulaCallback)
            self.set_change_event('MotorPosition', True, False)
            self._fsh.chamberObj.appendCb(self.chamberOffsetXCallback)
            self._fsh.chamberObj.appendCb(self.extendedFormulaCallback)
            self.set_change_event('ChamberOffsetX', True, False)
            self.set_change_event('ExtendedFormula', True, False)
        except Exception as e:
            self._fsh = None
            self.error_stream("Cannot build the FSH object: %s" % e)
            self.change_state(PyTango.DevState.FAULT)
            self.change_status("Review the properties")
            return
        self.info_stream("Prepared the device to work with the formula %s"
                         % (self._fsh.formula))
        self.set_change_event('Offset', True, False)
        self.change_state(PyTango.DevState.ON)
        self.change_status("Ready...")
        #----- PROTECTED REGION END -----#	//	FSHOffset.init_device

    def always_executed_hook(self):
        self.debug_stream("In always_excuted_hook()")
        #----- PROTECTED REGION ID(FSHOffset.always_executed_hook) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	FSHOffset.always_executed_hook

    # -------------------------------------------------------------------------
    #    FSHOffset read/write attribute methods
    # -------------------------------------------------------------------------
    
    def read_offset(self, attr):
        self.debug_stream("In read_offset()")
        #----- PROTECTED REGION ID(FSHOffset.offset_read) ENABLED START -----#
        if self._fsh is not None:
            self.attr_offset_read = self._fsh.offset
            attr.set_value(self.attr_offset_read)
        else:
            self.warn_stream("read_offset when not build the FSH() object")
        #----- PROTECTED REGION END -----#	//	FSHOffset.offset_read
        
    def write_offset(self, attr):
        self.debug_stream("In write_offset()")
        data = attr.get_write_value()
        #----- PROTECTED REGION ID(FSHOffset.offset_write) ENABLED START -----#
        if self._fsh is not None:
            self._fsh.offset = data
            self.push_change_event('Offset', self._fsh.offset)
        else:
            self.warn_stream("write_offset when not build the FSH() object")
        #----- PROTECTED REGION END -----#	//	FSHOffset.offset_write
        
    def read_MotorPosition(self, attr):
        self.debug_stream("In read_MotorPosition()")
        #----- PROTECTED REGION ID(FSHOffset.MotorPosition_read) ENABLED START -----#
        if self._fsh is not None:
            self.attr_MotorPosition_read = self._fsh.positionObj.value
            if self.attr_MotorPosition_read is not None:
                timestamp = self._fsh.positionObj.timestamp or time()
                attr.set_value_date_quality(self.attr_MotorPosition_read,
                                            timestamp,
                                            PyTango.AttrQuality.ATTR_VALID)
            else:
                attr.set_value_date_quality(0,time(),
                                            PyTango.AttrQuality.ATTR_INVALID)
        else:
            self.warn_stream("read_MotorPosition when not build the FSH() "
                             "object")
        #----- PROTECTED REGION END -----#	//	FSHOffset.MotorPosition_read
        
    def read_ChamberOffsetX(self, attr):
        self.debug_stream("In read_ChamberOffsetX()")
        #----- PROTECTED REGION ID(FSHOffset.ChamberOffsetX_read) ENABLED START -----#
        if self._fsh is not None:
            self.attr_ChamberOffsetX_read = self._fsh.chamberObj.value
            if self.attr_ChamberOffsetX_read is not None:
                timestamp = self._fsh.chamberObj.timestamp or time()
                attr.set_value_date_quality(self.attr_ChamberOffsetX_read,
                                            timestamp,
                                            PyTango.AttrQuality.ATTR_VALID)
            else:
                attr.set_value_date_quality(0,time(),
                                            PyTango.AttrQuality.ATTR_INVALID)
        else:
            self.warn_stream("read_IBAChamberOffsetX when not build the FSH() "
                             "object")
        #----- PROTECTED REGION END -----#	//	FSHOffset.ChamberOffsetX_read
        
    def read_Formula(self, attr):
        self.debug_stream("In read_Formula()")
        #----- PROTECTED REGION ID(FSHOffset.Formula_read) ENABLED START -----#
        if self._fsh is not None:
            self.attr_Formula_read = self._fsh.formula
            attr.set_value(self.attr_Formula_read)
        #----- PROTECTED REGION END -----#	//	FSHOffset.Formula_read
        
    def read_ExtendedFormula(self, attr):
        self.debug_stream("In read_ExtendedFormula()")
        #----- PROTECTED REGION ID(FSHOffset.ExtendedFormula_read) ENABLED START -----#
        if self._fsh is not None:
            self.attr_ExtendedFormula_read = \
                self._fsh.formulaObj.extendedFormula
            attr.set_value(self.attr_ExtendedFormula_read)
        #----- PROTECTED REGION END -----#	//	FSHOffset.ExtendedFormula_read
        
    
    
            
    def read_attr_hardware(self, data):
        self.debug_stream("In read_attr_hardware()")
        #----- PROTECTED REGION ID(FSHOffset.read_attr_hardware) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	FSHOffset.read_attr_hardware


    # -------------------------------------------------------------------------
    #    FSHOffset command methods
    # -------------------------------------------------------------------------
    
    def Exec(self, argin):
        """ 
        :param argin: statement to executed
        :type argin: PyTango.DevString
        :return: result
        :rtype: PyTango.DevString
        """
        self.debug_stream("In Exec()")
        argout = ""
        #----- PROTECTED REGION ID(FSHOffset.Exec) ENABLED START -----#
        try:
            try:
                # interpretation as expression
                argout = eval(argin,self.__globals,self.__locals)
            except SyntaxError:
                # interpretation as statement
                exec argin in self.__globals, self.__locals
                argout = self.__locals.get("y")

        except Exception, exc:
            # handles errors on both eval and exec level
            argout = traceback.format_exc()

        if type(argout)==StringType:
            return argout
        elif isinstance(argout, BaseException):
            return "%s!\n%s" % (argout.__class__.__name__, str(argout))
        else:
            try:
                return pprint.pformat(argout)
            except Exception:
                return str(argout)
        #----- PROTECTED REGION END -----#	//	FSHOffset.Exec
        return argout
        

    #----- PROTECTED REGION ID(FSHOffset.programmer_methods) ENABLED START -----#
    
    #----- PROTECTED REGION END -----#	//	FSHOffset.programmer_methods

class FSHOffsetClass(PyTango.DeviceClass):
    # -------- Add you global class variables here --------------------------
    #----- PROTECTED REGION ID(FSHOffset.global_class_variables) ENABLED START -----#
    
    #----- PROTECTED REGION END -----#	//	FSHOffset.global_class_variables


    #    Class Properties
    class_property_list = {
        }


    #    Device Properties
    device_property_list = {
        'motor':
            [PyTango.DevString, 
             '',
            [] ],
        'iba':
            [PyTango.DevString, 
             '',
            [] ],
        'formula':
            [PyTango.DevString, 
             '',
            [] ],
        }


    #    Command definitions
    cmd_list = {
        'Exec':
            [[PyTango.DevString, "statement to executed"],
            [PyTango.DevString, "result"],
            {
                'Display level': PyTango.DispLevel.EXPERT,
            } ],
        }


    #    Attribute definitions
    attr_list = {
        'offset':
            [[PyTango.DevDouble,
            PyTango.SCALAR,
            PyTango.READ_WRITE],
            {
                'Memorized':"true"
            } ],
        'MotorPosition':
            [[PyTango.DevDouble,
            PyTango.SCALAR,
            PyTango.READ]],
        'ChamberOffsetX':
            [[PyTango.DevDouble,
            PyTango.SCALAR,
            PyTango.READ]],
        'Formula':
            [[PyTango.DevString,
            PyTango.SCALAR,
            PyTango.READ]],
        'ExtendedFormula':
            [[PyTango.DevString,
            PyTango.SCALAR,
            PyTango.READ]],
        }


def main():
    try:
        py = PyTango.Util(sys.argv)
        py.add_class(FSHOffsetClass, FSHOffset, 'FSHOffset')
        #----- PROTECTED REGION ID(FSHOffset.add_classes) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	FSHOffset.add_classes

        U = PyTango.Util.instance()
        U.server_init()
        U.server_run()

    except PyTango.DevFailed as e:
        print ('-------> Received a DevFailed exception:', e)
    except Exception as e:
        print ('-------> An unforeseen exception occured....', e)

if __name__ == '__main__':
    main()
