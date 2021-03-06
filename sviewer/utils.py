# -*- coding: utf-8 -*-
"""
Created on Fri Dec 23 11:25:04 2016

@author: Serj
"""
from astropy.modeling.functional_models import Moffat1D
import inspect
from itertools import compress
from math import atan2,degrees
import numpy as np
import os
from scipy.stats import rv_continuous
import threading
import time

def include(filename):
    if os.path.exists(filename):
        exec(open(filename).read())

class Timer:
    """
    class for timing options
    """
    def __init__(self, name='', verbose=True):
        self.start = time.time()
        self.name = name
        self.verbose = verbose
        if self.name != '':
            self.name += ': '

    def restart(self):
        self.start = time.time()
    
    def time(self, st=''):
        s = self.start
        self.start = time.time()
        if self.verbose:
            print(self.name + str(st) + ':', self.start - s)
        return self.start - s
        
    def get_time_hhmmss(self, st):
        end = time.time()
        m, s = divmod(end - self.start, 60)
        h, m = divmod(m, 60)
        time_str = "%02d:%02d:%02d" % (h, m, s)
        print(st, time_str)
        return time_str

    def sleep(self, t=0):
        time.sleep(t)

class MaskableList(list):
    """
    make list to be maskable like numpy arrays
    """
    def __getitem__(self, index):
        try:
            return super(MaskableList, self).__getitem__(index)
        except TypeError:
            return MaskableList(compress(self, index))

    def uniqueappend(self, other):
        for line in other:
            if line not in self:
                self.append(line)
        return self

def debug(o, name=None):
    s = '' if name is None else name+': '
    print(s + str(o) + ' ('+inspect.stack()[1][3]+')')

def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=30, fill='█'):
    """
    Call in a loop to create terminal progress bar 
    (taken from https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console)
    parameters:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()

def add_field(a, descr, vals=None):
    """
    Return a new array that is like "a", but has additional fields.

    Arguments:
      a     -- a structured numpy array
      descr -- a numpy type description of the new fields
      vals  -- a numpy array to be added in the field. If None - nothing to add

    The contents of "a" are copied over to the appropriate fields in
    the new array, whereas the new fields are uninitialized.  The
    arguments are not modified.

    >>> sa = numpy.array([(1, 'Foo'), (2, 'Bar')], \
                         dtype=[('id', int), ('name', 'S3')])
    >>> sa.dtype.descr == numpy.dtype([('id', int), ('name', 'S3')])
    True
    >>> sb = add_field(sa, [('score', float)])
    >>> sb.dtype.descr == numpy.dtype([('id', int), ('name', 'S3'), \
                                       ('score', float)])
    True
    >>> numpy.all(sa['id'] == sb['id'])
    True
    >>> numpy.all(sa['name'] == sb['name'])
    True
    """
    if a.dtype.fields is None:
        raise ValueError("`A' must be a structured numpy array")
    b = np.empty(a.shape, dtype=a.dtype.descr + descr)
    for name in a.dtype.names:
        b[name] = a[name]
    b[descr[0][0]] = vals
    return b

def slice_fields(a, fields):
    """
    Slice numpy structured array

    Arguments:
        - a         : a structured numpy array
    :param fields:
    :return:
    """
    dtype2 = np.dtype({name:a.dtype.fields[name] for name in fields})
    return np.ndarray(a.shape, dtype2, a, 0, a.strides)

def hms_to_deg(coord):
    print(coord)
    if ':' in coord:
        h, m, s = int(coord.split(':')[0]), int(coord.split(':')[1]), float(coord.split(':')[2])
    elif 'h' in coord:
        h, m, s = int(coord[:coord.index('h')]), int(coord[coord.index('h')+1:coord.index('m')]), float(coord[coord.index('m')+1:])
    else:
        h, m, s = int(coord[:2]), int(coord[2:4]), float(coord[4:])
    print((h * 3600 + m * 60 + s) / 240)
    return (h * 3600 + m * 60 + s) / 240

def dms_to_deg(coord):
    if ':' in coord:
        d, m, s = int(coord.split(':')[0]), int(coord.split(':')[1]), float(coord.split(':')[2])
    elif 'h' in coord:
        d, m, s = int(coord[:coord.index('d')]), int(coord[coord.index('d')+1:coord.index('m')]), float(coord[coord.index('m')+1:])
    else:
        d, m, s = int(coord[:3]), int(coord[3:5]), float(coord[5:])
    print(d, m, s)
    return d + (m * 60 + s) / 3600

#Label line with line2D label data
def labelLine(line, x, label=None, align=True, xpos=0, ypos=0, **kwargs):

    ax = line.get_axes()
    xdata = line.get_xdata()
    ydata = line.get_ydata()

    if (x < xdata[0]) or (x > xdata[-1]):
        print('x label location is outside data range!')
        return

    #Find corresponding y co-ordinate and angle of the line
    ip = 1
    for i in range(len(xdata)):
        if x < xdata[i]:
            ip = i
            break

    y = ydata[ip-1] + (ydata[ip]-ydata[ip-1])*(x-xdata[ip-1])/(xdata[ip]-xdata[ip-1])

    if not label:
        label = line.get_label()

    if align:
        #Compute the slope
        dx = xdata[ip] - xdata[ip-1]
        dy = ydata[ip] - ydata[ip-1]
        ang = degrees(atan2(dy,dx))

        #Transform to screen co-ordinates
        pt = np.array([x,y]).reshape((1,2))
        trans_angle = ax.transData.transform_angles(np.array((ang,)),pt)[0]

    else:
        trans_angle = 0

    #Set a bunch of keyword arguments
    if 'color' not in kwargs:
        kwargs['color'] = line.get_color()

    if ('horizontalalignment' not in kwargs) and ('ha' not in kwargs):
        kwargs['ha'] = 'center'

    if ('verticalalignment' not in kwargs) and ('va' not in kwargs):
        kwargs['va'] = 'center'

    if 'backgroundcolor' not in kwargs:
        kwargs['backgroundcolor'] = ax.get_axis_bgcolor()

    if 'clip_on' not in kwargs:
        kwargs['clip_on'] = True

    if 'zorder' not in kwargs:
        kwargs['zorder'] = 2.5

    print(x, y, label, trans_angle)
    return ax.text(x+xpos, y+ypos, label, rotation=trans_angle, **kwargs)

def labelLines(lines, align=True, xvals=None, **kwargs):

    ax = lines[0].get_axes()
    labLines = []
    labels = []

    #Take only the lines which have labels other than the default ones
    for line in lines:
        label = line.get_label()
        if "_line" not in label:
            labLines.append(line)
            labels.append(label)

    if xvals is None:
        xmin,xmax = ax.get_xlim()
        xvals = np.linspace(xmin, xmax, len(labLines)+2)[1:-1]

    for line, x, label in zip(labLines, xvals, labels):
        labelLine(line, x, label, align, **kwargs)


class roman():
    def __init__(self):
        self.table = [['M', 1000], ['CM', 900], ['D', 500], ['CD', 400], ['C', 100], ['XC', 90], ['L', 50], ['XL', 40],
                      ['X', 10], ['IX', 9], ['V', 5], ['IV', 4], ['I', 1]]

    def int_to_roman(self, integer):
        """
        Convert arabic number to roman number.
        parameter:
            - integer         :  a number to convert
        return: r
            - r               :  a roman number
        """
        parts = []
        for letter, value in self.table:
            while value <= integer:
                integer -= value
                parts.append(letter)
        return ''.join(parts)

    def roman_to_int(self, string):
        """
        Convert roman number to integer.
        parameter:
            - string          :  a roman to convert
        return: i
            - i               :  an integer
        """
        result = 0
        for letter, value in self.table:
            while string.startswith(letter):
                result += value
                string = string[len(letter):]
        return result

    def separate_ion(self, string):
        ind = np.min([string[1:].index(letter) for letter, value in self.table if letter in string[1:]]) + 1
        return string[:ind], string[ind:]

    @classmethod
    def int(cls, string):
        s = cls()
        return s.roman_to_int(string)

    @classmethod
    def roman(cls, integer):
        s = cls()
        return s.int_to_roman(integer)

    @classmethod
    def ion(cls, string):
        s = cls()
        return s.separate_ion(string)

class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

# ---------------------------------------------------------
# fitting functions

class moffat_func(rv_continuous):
    "Moffat spectral distribution"

    def _pdf(self, x):
        # return 1.198436723 / gamma ** 2 * (1 + (x / gamma)**2) ** (-4.765)
        return 1.198436723 * (1 + x ** 2) ** (-4.765)

def moffat_fit(x, a, x_0, gamma, c):
    moffat = Moffat1D(a, x_0, gamma, 4.765)
    return moffat(x) + c

