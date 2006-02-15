# GUI Application automation and testing library
# Copyright (C) 2006 Mark Mc Mahon
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
#    Free Software Foundation, Inc.,
#    59 Temple Place,
#    Suite 330,
#    Boston, MA 02111-1307 USA

"""The application module is the main one that users will user first.

When starting to automate and application you must initialize an instance
of the Application class. Then you must `start_()`_ that application or
`connect_()`_ to a running instance of that application.

Once you have an Application instance you can access dialogs in that
application either by using one of the methods below. ::

   dlg = app.YourDialogTitle
   dlg = app.window_(title = "your title", class = "your class", ...)
   dlg = app['Your Dialog Title']

Similarly once you have a dialog you can get a control from that dialog
in almost exactly the same ways. ::

  ctrl = dlg.YourControlTitle
  ctrl = dlg.control_(title = "Your control", class = "Button", ...)
  ctrl = dlg["Your control"]

**Note:** For attribute access of controls and dialogs you do not have to
have the title of the control exactly, it does a best match of the
avialable dialogs or controls.

**See also:**
  `findwindows.find_windows()`_   for the keyword arguments that can be
  passed to both `Application.window_()`_ and `ActionDialog.control_()`_

.. _start_(): class-pywinauto.application.Application.html#start_
.. _connect_(): class-pywinauto.application.Application.html#connect_
.. _findwindows.find_windows():  module-pywinauto.findwindows.html#find_windows
.. _Application.window_(): class-pywinauto.application.Application.html#window_
.. _ActionDialog.control_(): class-pywinauto.application.ActionDialog.html#control_

"""

__revision__ = "$Revision$"

import time
##import os.path
##import os

import ctypes

import win32structures
import win32functions
import controls
import findbestmatch
import findwindows
import handleprops

#import appdata


class AppStartError(Exception):
    "There was a problem starting the Application"
    pass

class ProcessNotFoundError(Exception):
    "Could not find that process"
    pass

class AppNotConnected(Exception):
    "Application has been connected to a process yet"
    pass



# Maximum wait time for a window to exist
window_find_timeout = 3

# How long to sleep between each try to looking for a window
window_retry_interval = .09

# Maximum wait time to wait for the first window of an
# application to exist
app_start_timeout = 10

# Maximum wait time when checking if a control exists
exists_timeout = .5

# How long to sleep between each try when checking if the window exists
exists_retry_interval = .3



def set_timing(
    win_find = 3,
    win_retry =.09,
    app_start = 10,
    exists = .5,
    exists_retry = .3,
    after_click = 0,
    after_menu = 0,
    after_sendkeys = .03,
    after_button_click = 0,
    after_close = .2):

    """Set the timing for various things

    :win_find: = 3    Max time to look for a window
    :win_retry: =.09  Retry interval when finding a window
    :app_start: = 10  Max time to look for a window after app start
    :exists: = .5     Max time to check a window exists
    :exists_retry: = .3  Retry interval when checking a window exists
    :after_click: = 0    Delay after a mouse click
    :after_menu: = 0     Delay after a menu selection
    :after_sendkeys: = .03   Delay after each Sendkeys key
    :after_button_click: = 0 Delay after a button click
    :after_close: = .2       Delay after the CloseClick action

    """

    global window_find_timeout
    window_find_timeout = win_find
    global window_retry_interval
    window_retry_interval = win_retry
    global app_start_timeout
    app_start_timeout = app_start
    global exists_timeout
    exists_timeout = exists
    global exists_retry_interval
    exists_retry_interval = exists_retry


    import controls.HwndWrapper
    controls.HwndWrapper.delay_after_click = after_click
    controls.HwndWrapper.delay_after_menuselect = after_menu
    controls.HwndWrapper.delay_after_sendkeys_key = after_sendkeys
    controls.HwndWrapper.delay_after_button_click = after_button_click
    controls.HwndWrapper.delay_before_after_close_click = after_close



#=========================================================================
class WindowSpecification(object):
    """A specificiation for finding a window or control

    Windows are resolved when used.
    You can also wait for existance or non existance of a window
    """

    def __init__(self, search_criteria):
        """Initailize the class

        :search_criteria: the criteria to match a dialog
        """
        # kwargs will contain however to find this window
        self.criteria = [search_criteria, ]

    def __call__(self, *args, **kwargs):
        "No __call__ so return a usefull error"

        if "best_match" in self.criteria[-1]:
            raise AttributeError(
                "WindowSpecification class has no '%s' method" %
                self.criteria[-1]['best_match'])

        message = \
        "You tried to execute a function call on a WindowSpecification " \
        "instance. You probably have a typo for one of the methods of this " \
        "class.\n" \
        "The criteria leading up to this is: " + str(self.criteria)

        raise AttributeError(message)

    def ctrl_(self):
        "Allow the calling code to get the HwndWrapper object"
        return _resolve_control(self.criteria)

    def window_(self, **criteria):
        "Add the criteria that will be matched when we resolve the control"

        new_item = WindowSpecification(self.criteria[0])
        new_item.criteria.append(criteria)

        return new_item

    def __getitem__(self, key):
        """Allow access to dialogs/controls through item access

        This allows::

            app.['DialogTitle']['ControlTextClass']

        to be used to access dialogs and controls.

        Both this and __getattr__ use the rules outlined in the
        HowTo document.
        """

        # FUTURE REQUIREMENT - NOT REQUIRED YET
        # if we already have 2 levels of criteria (dlg, control)
        # then resolve the control and do a getitem on it for the
        # key
        #if len(self.criteria) == 2:
        #    return self.__resolvewindow()[key]
        # END FUTURE REQUIREMENT - NOT REQUIRED YET

        new_item = WindowSpecification(self.criteria[0])
        new_item.criteria.append({"best_match" : key})

        # We don't really want this because it brings us back to
        # not being able to do app.Dlg.Control.WaitExists()
        #if len(self.criteria) == 2:
        #    return self._resolve_control()

        return new_item

    # now there is a problem what if we do
    #app.Dlg.Click(), or app.Dlg.Font
    # one way would be to resolve on __call__
    # or maybe resolve - if window found and attribute found
    # then return it

    # - resolve on call - that will handle all actions
    # - We know the first one is a dialog so we an
    #   check if the attr is in the list of Dialog attributes!
    def __getattr__(self, attr):
        """Attribute access for this class

        If we already have criteria for both dialog and control then
        resolve the control and return the requested attribute.

        If we have only criteria for the dialog but the attribute
        requested is an attribute of DialogWrapper then resolve the
        dialog and return the requested attribute.

        Otherwise delegate functionality to __getitem__() - which
        sets the appropriate criteria for the control.
        """

        from pywinauto.controls.win32_controls import DialogWrapper

        #if self.criteria[0].has_key("title_re") and \
        #    "Document" in self.criteria[0]['title_re']:
        #    print attr, self.criteria

        # if we already have 2 levels of criteria (dlg, conrol)
        # this third must be an attribute so resolve and get the
        # attribute and return it
        if len(self.criteria) == 2:
            return getattr(
                _resolve_control(
                    self.criteria,
                    window_find_timeout,
                    window_retry_interval),
                attr)

        else:
            # if we have been asked for an attribute of the dialog
            # then resolve the window and return the attribute
            if len(self.criteria) == 1 and hasattr(DialogWrapper, attr):
                return getattr(
                    self.WaitReady(
                        window_find_timeout,
                        window_retry_interval),
                    attr)

        # It is a dialog/control criterion so let getitem
        # deal with it
        return self[attr]



    def Exists(self, timeout = exists_timeout):
        "Check if the window exists"

        # modify the criteria as Exists should look for all
        # windows - including not visible and disabled
        exists_criteria = []
        for criterion in self.criteria[:]:
            criterion['enabled_only'] = False
            criterion['visible_only'] = False
            exists_criteria.append(criterion)

        try:
            _resolve_control(
                exists_criteria, timeout, exists_retry_interval)

            return True
        except (findwindows.WindowNotFoundError, findbestmatch.MatchError):
            return False



    def WaitReady(self,
        timeout = window_find_timeout,
        wait_interval = window_retry_interval):
        "Wait for the control to be ready (Exists, Visible and Enabled)"

        # modify the criteria as Exists should look for all
        # windows - including not visible and disabled
        ready_criteria = []
        for criterion in self.criteria[:]:
            criterion['enabled_only'] = True
            criterion['visible_only'] = True
            ready_criteria.append(criterion)

        ctrl = _resolve_control(
            ready_criteria,
            timeout,
            wait_interval)

        return ctrl

#    def WaitEnabled(self):
#
#        ctrl = _resolve_control(
#            self.criteria,
#            timeout,
#            wait_interval)
#
#    def WaitVisible(self):
#        pass
#    def WaitNotExists(self):
#        pass
    def WaitNotEnabled(self,
        timeout = window_find_timeout,
        wait_interval = window_retry_interval):
        "Wait for the control to be disabled or not exist"

        waited = 0
        while True:

            try:
                # stop trying if it is not enabled
                if not _resolve_control(self.criteria).IsEnabled():
                    break

            # stop trying if the window doesn't exist
            except (
                findwindows.WindowNotFoundError, findbestmatch.MatchError):
                break

            # stop trying if we have reached the timeout
            if waited >= timeout:
                break

            # other wise wait the interval, and try again
            time.sleep(wait_interval)
            waited += wait_interval


    def WaitNotVisible(self,
        timeout = window_find_timeout,
        wait_interval = window_retry_interval):
        "Wait for the control to be invisible or not exist"

        # modify the criteria as Exists should look for all
        # windows - including not visible and disabled
        notvisible_criteria = []
        for criterion in self.criteria[:]:
            criterion['enabled_only'] = False
            criterion['visible_only'] = False
            notvisible_criteria.append(criterion)

        waited = 0
        while True:

            try:
                # stop trying if it is not enabled
                if not _resolve_control(notvisible_criteria).IsVisible():
                    break

            # stop trying if the window doesn't exist
            except (findwindows.WindowNotFoundError, findbestmatch.MatchError):
                break

            # stop trying if we have reached the timeout
            if waited >= timeout:
                break

            # other wise wait the interval, and try again
            time.sleep(wait_interval)
            waited += wait_interval

    def print_control_identifiers(self):
        """Prints the 'identifiers'

        If you pass in a control then it just prints the identifiers
        for that control

        If you pass in a dialog then it prints the identiferis for all
        controls in the dialog

        :Note: The identifiers printed by this method have not been made
               unique. So if you have 2 edit boxes, they will both have "Edit"
               listed in their identifiers. In reality though the first one
               can be refered to as "Edit", "Edit0", "Edit1" and the 2nd
               should be refered to as "Edit2".

        """
        ctrl = _resolve_control(
            self.criteria,
            window_find_timeout,
            window_retry_interval)

        if ctrl.IsDialog():
            ctrls_to_print = ctrl.Children()
            dialog_controls = ctrl.Children()
        else:
            dialog_controls = ctrl.TopLevelParent().Children()
            ctrls_to_print = [ctrl]

        # filter out hidden controls
        ctrls_to_print = [ctrl for ctrl in ctrls_to_print if ctrl.IsVisible()]
        for ctrl in ctrls_to_print:
            print "%s - %s   %s"% (
                ctrl.Class(), ctrl.WindowText(), str(ctrl.Rectangle()))

            print "\t",
            for text in findbestmatch.get_control_names(
                ctrl, dialog_controls):

                print "'%s'" % text.encode("unicode_escape"),
            print













def _resolve_control(criteria_, timeout = 0, wait_interval = .2):
    """Find a control using criteria

    :criteria: - a list that contains 1 or 2 dictionaries
                 1st element is search criteria for the dialog
                 2nd element is the search criteria for a control of the dialog
    :timeout: -  maximum length of time to try to find the controls (default 0)
    :wait_interval: - how long to wait between each retry (default .2)
    """


    criteria = [crit.copy() for crit in criteria_]


#
##    app_data = ReadAppData(criteria)
##
##    if app_data:
##
##        # if best match was specified for the dialog
##        # then we need to replace it with other values
##        # for now we will just use Class
##        for crit in ['best_match', 'title', 'title_re']:
##            if crit in criteria[0]:
##                del(criteria[0][crit])
##                criteria[0]['class_name'] = app_data[0].Class()#['Class']
##
##            if len(criteria) > 1:
##                # find the best match of the application data
##                if criteria[1].has_key('best_match'):
##                    best_match = findbestmatch.find_best_control_matches(
##                        criteria[1]['best_match'], app_data)[0]
##
##                    #visible_controls = [ctrl in app_data if ctrl.IsVisible()]
##
##                    #find the index of the best match item
##                    ctrl_index = app_data.index(best_match)
##                    #print best_match[0].WindowText()
##                    ctrl_index, best_match.WindowText()
##
##                    criteria[1]['ctrl_index'] = ctrl_index -1
##                    #criteria[1]['class_name'] = best_match.Class()
##                    #del(criteria[1]['best_match'])
##
## One idea here would be to run the new criteria on the app_data dialog and
## if it returns more then one control then you figure out which one would be
## best - so that you have that info when running on the current dialog
##
##            #for criterion in criteria[1:]:
##                # this part is weird - we now have to go off and find the
##                # index, class, text of the control in the app_data
##                # and then find the best match for this control in the
##                # current dialog
##            #    pass
##
##    else:
##        #print "No Appdata for ", criteria[0]
##        pass
##

    waited = 0
    while True:
        try:
            dialog = controls.WrapHandle(
                findwindows.find_window(**criteria[0]))

            # if there is only criteria for a dialog then return it
            if not len(criteria) == 1:
                # so there was criteria for a control, add the extra criteria
                # that are required for child controls
                ctrl_criteria = criteria[1]
                ctrl_criteria["top_level_only"] = False
                ctrl_criteria["parent"] = dialog.handle

                # resolve the control and return it
                ctrl = controls.WrapHandle(
                    findwindows.find_window(**ctrl_criteria))
                break
            else:
                ctrl = dialog
                break
        except (findwindows.WindowNotFoundError, findbestmatch.MatchError):
            if waited < timeout:
                waited += wait_interval
                time.sleep(wait_interval)
            else:
                raise

    #appdata.WriteAppDataForDialog(criteria, dialog)

    return ctrl

#=========================================================================
class Application(object):
    "Represents an application"
    def __init__(self):
        "Set the attributes"
        self.process = None
        self.xmlpath = ''

    def _start(self, *args, **kwargs):
        "start_ used to be named _start"
        import warnings
        message = "_start and _connect are deprecated " \
            "please use start_ and connect_"
        warnings.warn(message, DeprecationWarning)
        self.start_(*args, **kwargs)

    def _connect(self, *args, **kwargs):
        "connect_ used to be named _connect"
        import warnings
        message = "_start and _connect are deprecated " \
            "please use start_ and connect_"
        warnings.warn(message, DeprecationWarning)
        self.connect_(*args, **kwargs)

    def start_(self, cmd_line, timeout = app_start_timeout):
        "Starts the application giving in cmd_line"

        start_info = win32structures.STARTUPINFOW()
        start_info.sb = ctypes.sizeof(start_info)

        proc_info = win32structures.PROCESS_INFORMATION()

        # we need to wrap the command line as it can be modified
        # by the function
        command_line = ctypes.c_wchar_p(unicode(cmd_line))

        # Actually create the process
        ret = win32functions.CreateProcess(
            0, 					# module name
            command_line,		# command line
            0, 					# Process handle not inheritable.
            0, 					# Thread handle not inheritable.
            0, 					# Set handle inheritance to FALSE.
            0, 					# No creation flags.
            0, 					# Use parent's environment block.
            0,  				# Use parent's starting directory.
            ctypes.byref(start_info),# Pointer to STARTUPINFO structure.
            ctypes.byref(proc_info)) # Pointer to PROCESS_INFORMATION structure

        # if it failed for some reason
        if not ret:
            message = 'Could not create the process "%s"\n'\
                'Error returned by CreateProcess: ' + str(ctypes.WinError())
            raise AppStartError(message)

        self.process = proc_info.dwProcessId

        start = time.time()
        while time.time() - start < timeout:
            if not win32functions.WaitForInputIdle(
                proc_info.hProcess, timeout * 1000):
                break
                #raise AppStartError(
                #    "WaitForInputIdle: " + str(ctypes.WinError()))

            if self.windows_():
                break

            time.sleep(.5)

        return self


    def connect_(self, **kwargs):
        "Connects to an already running process"

        connected = False
        if 'process' in kwargs:
            self.process = kwargs['process']
            AssertValidProcess(self.process)
            connected = True

        elif 'handle' in kwargs:

            if not handleprops.iswindow(kwargs['handle']):
                message = "Invalid handle 0x%x passed to connect_()"% (
                    kwargs['handle'])
                raise RuntimeError(message)


            self.process = handleprops.processid(kwargs['handle'])

            connected = True

        elif 'path' in kwargs:
            self.process = process_from_module(kwargs['path'])
            connected = True

        elif kwargs:
            handle = findwindows.find_window(**kwargs)
            self.process = handleprops.processid(handle)
            connected = True

        if not connected:
            raise RuntimeError(
                "You must specify one of process, handle or path")

        return self

    def top_window_(self):
        "Return the current top window of the dialog"
        if not self.process:
            raise AppNotConnected("Please use start_ or connect_ before "
                "trying anything else")

        time.sleep(exists_timeout)
        # very simple
        windows = findwindows.find_windows(process = self.process)
        criteria = {}
        criteria['handle'] = windows[0]

        return WindowSpecification(criteria)

    def windows_(self, **kwargs):
        "Return a list of the handles for top level windows of the application"

        if not self.process:
            raise AppNotConnected("Please use start_ or connect_ before "
                "trying anything else")

        if 'visible_only' not in kwargs:
            kwargs['visible_only'] = False

        if 'enabled_only' not in kwargs:
            kwargs['enabled_only'] = False

        kwargs['process'] = self.process

        windows = findwindows.find_windows(**kwargs)

        return [controls.WrapHandle(win) for win in windows]


    def window_(self, **kwargs):
        """Return a window of the application

        You can specify the same parameters as findwindows.find_windows.
        It will add the process parameter to ensure that the window is from
        the current process.
        """
        if not self.process:
            raise AppNotConnected(
                "Please use start_ or connect_ before trying anything else")

        # add the restriction for this particular process
        kwargs['process'] = self.process

        return WindowSpecification(kwargs)

    def __getitem__(self, key):
        "Find the specified dialog of the application"

        # delegate searching functionality to self.window_()
        return self.window_(best_match = key)

    def __getattr__(self, key):
        "Find the spedified dialog of the application"

        # delegate all functionality to item access
        return self[key]


def AssertValidProcess(process_id):
    "Raise ProcessNotFound error if process_id is not a valid process id"
    # Set instance variable _module if not already set
    process_handle = win32functions.OpenProcess(
        0x400 | 0x010, 0, process_id) # read and query info

    if not process_handle:
        message = "Process with ID '%d' could not be opened" % process_id
        raise ProcessNotFoundError(message)

    return process_handle



#=========================================================================
def process_module(process_id):
    "Return the string module name of this process"
    process_handle = AssertValidProcess(process_id)

    # get module name from process handle
    filename = (ctypes.c_wchar * 2000)()
    win32functions.GetModuleFileNameEx(
        process_handle, 0, ctypes.byref(filename), 2000)

    # return the process value
    return filename.value

#=========================================================================
def process_from_module(module):
    "Return the running process with path module"

    # set up the variable to pass to EnumProcesses
    processes = (ctypes.c_int * 2000)()
    bytes_returned = ctypes.c_int()

    # collect all the running processes
    ctypes.windll.psapi.EnumProcesses(
        ctypes.byref(processes),
        ctypes.sizeof(processes),
        ctypes.byref(bytes_returned))

    # check if any of the running process has this module
    for i in range(0, bytes_returned.value / ctypes.sizeof(ctypes.c_int)):
        try:
            p_module = process_module(processes[i]).lower()
            if module.lower() in p_module:
                return processes[i]
        except ProcessNotFoundError:
            pass

    message = "Could not find any process with a module of '%s'" % module
    raise ProcessNotFoundError(message)


