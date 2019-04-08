#!/usr/bin/env python3
# coding: utf-8
import sys
import gzip
import time
import math
import os.path
import argparse
from collections import OrderedDict
from bisect import bisect_left
try:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    from matplotlib.colors import ListedColormap, hsv_to_rgb
    from mpl_toolkits.axes_grid1 import make_axes_locatable
except ImportError as i:
    print('Error: you need **matplotlib** installed for this to run.', file=sys.stderr)
    sys.exit(-1)

VERSION = '0.1'
COLORMAPS = {
    'perceptual': ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'charolastra*'],
    'sequential': ['binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink', 'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper'],
    'diverging': ['PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu', 'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic'],
    'cyclic': ['twilight+', 'twilight_shifted+', 'hsv'],
    'qualitative': ['Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2', 'Set1', 'Set2', 'Set3', 'tab10', 'tab20', 'tab20b', 'tab20c'],
    'misc': [ 'flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern', 'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg', 'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar'],
}
MHz = 10**6
kHz = 10**3

def print_quiet(s, quiet):
    if not quiet:
        print(s)
def print_error(s):
    print(s, file=sys.stderr)

def read_data(f_name, quiet):
    print_quiet(':: reading file %s' % f_name, quiet)
    if f_name.endswith('.gz'):
        f_open = lambda x: gzip.open(x, 'rt')
    else:
        f_open = lambda x: open(x, 'r')
    f = f_open(f_name)
    lines = f.readlines()
    f.close()
    return lines

def sort_and_clean(L, start=None, end=None):
    indexes = {}
    if start or end:
        if start and end is None:
            flambda = lambda x: start < x
        elif start is None and end:
            flambda = lambda x: x < end
        elif start and end:
            flambda = lambda x: start < x < end

        for i,l in enumerate(L):
            fields = [f.strip() for f in l.split(',')]
            datetimefreq = '%sT%sF%s' % (fields[0], fields[1], fields[2])
            indexes[datetimefreq] = i
        si = filter(flambda, sorted(indexes.keys()))
        return [L[indexes[i]] for i in si]
    else:
        for i,l in enumerate(L):
            fields = [f.strip() for f in l.split(',')]
            datetimefreq = '%sT%sF%s' % (fields[0], fields[1], fields[2])
            indexes[datetimefreq] = i
        return [L[indexes[i]] for i in sorted(indexes.keys())]

def is_inside(b1, b2, dir):
    if dir == 'x':
        return b1.x1 <= b2.xmax and b1.x0 >= b2.xmin
    elif dir == 'y':
        return b1.y1 <= b2.ymax and b1.y0 >= b2.ymin
    else:
        raise ValueError

def charolastra_palette():
    def loop(n):
        t = n
        if n>1:
            t = 1
        elif n<0:
            t =  1-abs(n)
        return t

    p = []
    for i in range(1024):
        g = i / 1023.0
        c = hsv_to_rgb([loop(0.65-(g-0.08)), 1, loop(0.2+g)])
        p.append(c)
    return p

def floatify(zs):
    # nix errors with -inf, windows errors with -1.#J
    zf = []
    previous = 0  # awkward for single-column rows
    for z in zs:
        try:
            z = float(z)
        except ValueError:
            z = previous
        if math.isinf(z):
            z = previous
        if math.isnan(z):
            z = previous
        zf.append(z)
        previous = z
    return zf

def print_with_columns(L, columns, prefix=''):
    index = 0
    lines = []
    for i in range(int(round(float(len(L))/columns))):
        line = L[index:index+columns]
        line = line + ['']*(columns-len(line))
        lines.append(line)
        index += columns

    for i in range(columns):
        cmax = 0
        for j in range(len(lines)):
            cmax = max(cmax, len(lines[j][i]))
        for j in range(len(lines)):
            lines[j][i] = lines[j][i].ljust(cmax+2)

    for j in range(len(lines)):
        print(prefix+''.join(lines[j]))

def find_time_index(datetimes, multiple):
    # find index that matches the multiple in minute
    indexes = []
    done = []
    ts = [time.mktime(time.strptime(dt[:19], '%Y-%m-%dT%H:%M:%S')) for dt in datetimes]
    current = min(ts)
    while current < max(ts):
        diff = [(abs(current-ts[i]), i) for i in range(len(ts))]
        tmin = min([x for x,_ in diff])
        indx = [i for x,i in diff if x == tmin][0]
        indexes.append(indx)
        current += multiple*60
    return indexes

def find_freq_index(xmin, xmax, step, modulo):
    freqs = [xmin]
    f = xmin
    while f < xmax:
        f += step
        freqs.append(f)
    freqs.append(f)
    count = len(freqs)
    indexes = []
    fc = xmin
    while fc < xmax:
        diff = [(abs(fc-freqs[i]), i) for i in range(count)]
        fmin = min([x for x,_ in diff])
        indx = [i for x,i in diff if x == fmin][0]
        indexes.append(indx)
        fc += modulo
    return indexes

def remove_ticklabel(ax, axis, bbox):
    labels = getattr(ax, 'get_%sticklabels' % axis)()
    toberemoved = []
    for i,label in enumerate(labels):
        if not is_inside(label.get_window_extent(), bbox, axis):
            toberemoved.append(i)
    ticks = list(getattr(ax, 'get_%sticks' % axis)())
    for i in reversed(toberemoved):
        del ticks[i]
    getattr(ax, 'set_%sticks' % axis)(ticks)

def frange(start, end, step):
    res = []
    x = start
    while x < end:
        res.append(x)
        x += step
    return res

def interpolate(x_list, y_list, xmin, xmax, step):
    # https://stackoverflow.com/questions/7343697/how-to-implement-linear-interpolation
    if any(y - x <= 0 for x, y in zip(x_list, x_list[1:])):
        raise ValueError("x_list must be in strictly ascending order!")
    intervals = zip(x_list, x_list[1:], y_list, y_list[1:])
    slopes = [(y2 - y1)/(x2 - x1) for x1, x2, y1, y2 in intervals]

    x = xmin
    xs = []
    ys = []
    i = 0
    while x < xmax:
        if x <= x_list[0]:
            y = y_list[0]
        elif x >= x_list[-1]:
            y = y_list[-1]
        else:
            i = bisect_left(x_list, x, lo=i) - 1 # slight optimization: use a low value to bisect
            y = y_list[i] + slopes[i] * (x - x_list[i])
        xs.append(x)
        ys.append(y)
        x += step
    return (xs, ys)

def plot_heatmap(lines, f_name, args):
    xmin = 10**10
    xmax = 0
    zmin = 100
    zmax = -100
    print_quiet(':: processing data', args.quiet)

    od = OrderedDict()
    for i,line in enumerate(lines):
        fields = [f.strip() for f in line.split(',')]
        ts = '%sT%s' % (fields[0], fields[1])
        freqs = frange(int(fields[2]), int(fields[3]), float(fields[4]))
        values = fields[6:6+len(freqs)]
        if ts not in od:
            od[ts] = []
        for i in range(len(freqs)):
            od[ts].append((freqs[i], values[i]))
    data = []
    datetimes = list(od.keys())
    count = 0
    for ts, v in od.items():
        w = sorted(v, key=lambda x:x[0])
        x = [x for x,z in w]
        z = floatify([z for x,z in w])
        xmin = min(xmin, x[0])
        xmax = max(xmax, x[-1])
        zmin = min(zmin, min(z))
        zmax = max(zmax, max(z))
        count = max(count, len(x))
        #od[ts] = (x, z)
        #if not args.interpolate:
        #    data.append(z)
        data.append(z)
    step = (xmax-xmin)/count
    #if args.interpolate:
    #    # linear interpolation to get data evenly spaced
    #    print_quiet('   interpolation', args.quiet)
    #    for ts, v in od.items():
    #        intp = interpolate(v[0], v[1], xmin, xmax, step)
    #        data.append(intp[1])

    if len(data) == 0:
        print_error('Error: we ended up with an empty data set !?')
        sys.exit(-1)

    if args.dbmin is not None and (args.dbmin > zmax or args.dbmax < zmin):
        print_error('Error: dbmin should be less than max value and/or dbmax should be greater than min value')
        sys.exit(-1)

    print_quiet('Starting at %s and ending at %s\n  from %sHz to %sHz with values from %sdB to %sdB' % (datetimes[0], datetimes[-1], xmin, xmax, zmin, zmax), args.quiet)

    print_quiet(':: rendering', args.quiet)
    fig, ax = plt.subplots()

    start = time.mktime(time.strptime(datetimes[0], '%Y-%m-%dT%H:%M:%S'))
    end = time.mktime(time.strptime(datetimes[-1], '%Y-%m-%dT%H:%M:%S'))
    si = 11 # starting index of timestamp
    if end-start > 24*60*60:
        si = 0
    def showdatetime(tick, pos):
        try:
            dt = (datetimes[int(tick)][si:16]).replace('T', ' ')
        except IndexError as i:
            dt = None
        return dt

    if args.xticks:
        txmajor  = args.xticks
    else:
        if xmax-xmin > 500*MHz:
            txmajor = 100*MHz
        elif xmax-xmin > 100*MHz:
            txmajor = 10*MHz
        elif xmax-xmin > 10*MHz:
            txmajor = 10*MHz
        elif xmax-xmin > 1*MHz:
            txmajor = MHz
        else:
            txmajor = 100*kHz
    txminor = txmajor//10

    if args.yticks is not None:
        tymajor = args.yticks
    else:
        length_min = (end-start)/60
        if length_min >= 60*24:
            tymajor = 60*2
        if length_min >= 60*6:
            tymajor = 60
        elif length_min >= 60*2:
            tymajor = 30
        else:
            tymajor = 15
    if tymajor >= 60*2:
        tyminor = tymajor//4
    elif tymajor >= 60:
        tyminor = 15
    elif tymajor >= 30:
        tyminor = 10
    elif tymajor >= 15:
        tyminor = 5
    else:
        tyminor = 5

    if txmajor < MHz:
        def showfreq(tick, pos):
            return '%.1fMHz' % ((xmin+float(tick)*float(step))/(1000*1000),)
    else:
        def showfreq(tick, pos):
            return '%dMHz' % int(round(((xmin+float(tick)*float(step))/(1000*1000))))

    if args.colormap == 'charolastra':
        args.colormap = ListedColormap(charolastra_palette())

    if args.dbmin is not None:
        print_quiet('Normalizing data set to use %ddb to %ddb range' % (args.dbmin, args.dbmax), args.quiet)
        im = ax.imshow(data, cmap=args.colormap, aspect='equal', vmin=args.dbmin, vmax=args.dbmax)
    else:
        im = ax.imshow(data, cmap=args.colormap, aspect='equal')

    # show lines matching major ticks
    if args.xlines:
        ax.grid(True, axis='x', which='major', color='white', linewidth=0.5, linestyle='-.')
    if args.ylines:
        ax.grid(True, axis='y', which='major', color='white', linewidth=0.5, linestyle='-.')

    xlength = len(data[0])
    # add the title
    if args.title:
        if args.inside:
            ax.text(xlength/2, 20, args.title, fontsize=args.fontsize+2, fontweight='demibold', color='white', horizontalalignment='center', verticalalignment='top')
        else:
            ax.text(xlength/2, -13, args.title, fontsize=args.fontsize+2, fontweight='demibold', horizontalalignment='center', verticalalignment='bottom')
    # add a summary
    if args.summary:
        summary = '''started at %s
ended at %s
from %.2f MHz to %.2f MHz
values from %s dB to %s dB''' % (datetimes[0].replace('T', ' '), datetimes[-1].replace('T', ' '), xmin/MHz, xmax/MHz, zmin, zmax)
        ax.text(xlength-xlength/250, 20, summary, fontsize=args.fontsize, color='white', horizontalalignment='right', verticalalignment='top')

    # redefine tick positions
    fi = find_freq_index(xmin, xmax, step, txminor)
    ax.set_xticks(fi[::10])
    ax.set_xticks(fi, minor=True)
    fi = find_time_index(datetimes, tyminor)
    ax.set_yticks(fi[::tymajor//tyminor])
    ax.set_yticks(fi, minor=True)
    # redefine tick labels
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(showfreq))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(showdatetime))

    ax.tick_params(labelsize=args.fontsize, width=0.5, which='both')
    # draw tick label inside plot in white
    if args.inside:
        ax.tick_params(axis='x', direction='in', which='both', colors='white', width=0.5,
            labelsize=args.fontsize, pad=-8, zorder=1000)
        ax.tick_params(axis='y', direction='in', which='both', colors='white', width=0.5,
            labelsize=args.fontsize, pad=-16-(25 if si == 0 else 0), zorder=1000)
        # remove label outside of plot
        fig.canvas.draw()
        pos = ax.get_window_extent()
        remove_ticklabel(ax, 'x', pos)
        remove_ticklabel(ax, 'y', pos)
    if args.colorbar:
        # create an axes on the right side of ax. The width of cax will be 0.3
        # inch and the padding between cax and ax will be fixed at 0.1 inch.
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size=0.3, pad=0.1)
        cb = fig.colorbar(im, cax=cax)
        if args.inside:
            cb.ax.tick_params(axis='y', direction='in', colors='white', labelsize=args.fontsize, pad=-15)
        #cb.ax.invert_yaxis() # TODO: fix the missing tick/ticklabel

    if args.show:
        plt.show()
    else:
        if args.no_margin:
            size = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
            height, width = size.height, size.width
            pad_inches = 0
        else:
            size = fig.get_size_inches()
            height, width = size[1], size[0]
            pad_inches = None
            width = size[0]
        height = height*3
        width = width*3
        fig.set_size_inches(width, height)
        fig.savefig(f_name, dpi=args.dpi, bbox_inches='tight', pad_inches=pad_inches)
        print_quiet(':: saved to %s' % f_name, args.quiet)

def main():
    parser = argparse.ArgumentParser(description='Yet another heatmap generator for rtl_power .csv file')
    parser.add_argument('--dbmin', type=float, help='Minimum value to consider for colormap normalization')
    parser.add_argument('--dbmax', type=float, help='Maximum value to consider for colormap normalization')
    parser.add_argument('-c', '--colormap', default='charolastra', help='Specify the colormap to use (use "list" to get a list of available colormaps)')
    parser.add_argument('--colorbar', default=False, action='store_true', help='Add a colorbar to the plot')
    parser.add_argument('--dpi', default=300, type=int, help='Specify dpi of output image')
    parser.add_argument('--end', help='End time to use; everything after that is ignored; expected format YYY-mm-ddTHH[:MM[:SS]]')
    parser.add_argument('-i', '--input', help='Input csv filename')
    parser.add_argument('-f', '--format', help='Format of the output image file')
    parser.add_argument('--inside', action='store_true', default=False, help='Draw tick label inside plot')
    parser.add_argument('--force', action='store_true', default=False, help='Force overwrite of existing output file')
    parser.add_argument('--fontsize', type=int, default=4, help="Font size in points (default=4)")
    #parser.add_argument('--interpolate', action='store_true', default=False, help="Interpolate data to get evenly spaced value")
    parser.add_argument('--no-margin', action='store_true', default=False, help="Don't draw any margin around the plot")
    parser.add_argument('-o', '--output', help='Explicit name for the output file')
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help='no verbose output')
    parser.add_argument('-s', '--show', action='store_true', default=False, help='Show pyplot window instead of outputting an image')
    parser.add_argument('--start', help='Start time to use; everything before that is ignored; expected format YYY-mm-ddTHH[:MM[:SS]]')
    parser.add_argument('--sort', action='store_true', default=False, help='Sort csv file data')
    parser.add_argument('--summary', action='store_true', default=False, help='Draw a summary on  plot')
    parser.add_argument('--title', help='Add a title to the plot')
    parser.add_argument('-v', '--version', action='store_true', help='Print version and exit')
    parser.add_argument('--xticks', help='Define tick in the frequency axis, xxxx[MHz,kHz]')
    parser.add_argument('--yticks', help='Define tick in the time axis, xxx[h|m]')
    parser.add_argument('--xlines', action='store_true', default=False, help='Show lines matching major xtick labels')
    parser.add_argument('--ylines', action='store_true', default=False, help='Show lines matching major ytick labels')
    args = parser.parse_args()

    if args.version:
        print('''rtl_heatmap %s
Copyright ©2019 solstice d'Hiver
GPL licensed''' % VERSION)
        sys.exit(1)

    if args.colormap == 'list':
        print('Available colormaps are:')
        for k,v in COLORMAPS.items():
            print('  - %s:' % k)
            print_with_columns(v, 6, prefix='    ')
            print()
        sys.exit(1)

    if args.input is None:
        print_error('Error: -i/--input is required')
        sys.exit(-1)
    if not os.path.isfile(args.input):
        print_error('Error: there is no such file as %s' % args.input)
        sys.exit(-1)

    if args.output and args.format:
        ext = (args.output[args.output.rindex('.')+1:]).lower()
        if ext != args.format.lower():
            print_error('Error: conflicting format and extension. Found "%s" extension and "%s" format' % (ext, args.format.lower()))
            sys.exit(-1)

    if (args.dbmin is not None and args.dbmax is None) or (args.dbmax is not None and args.dbmin is None):
        print_error('Error: please specify both --dbmin and --dbmax')
        sys.exit(-1)

    if args.colormap != 'charolastra' and args.colormap not in plt.colormaps():
        print_error('Error: colormap "%s" not found. Use "list" to see the available colormaps' % args.colormap)
        sys.exit(-1)

    if args.xticks is not None:
        unit = args.xticks[-3:].lower()
        if unit == 'mhz':
            args.xticks = int(args.xticks[:-3])*MHz
        elif unit == 'khz':
            args.xticks = int(args.xticks[:-3])*kHz
        else:
            print_error("Error: can't parse --xticks value")
            sys.exit(-1)

    if args.yticks is not None:
        if args.yticks.endswith('h'):
            args.yticks = int(args.yticks[:-1])*60
        elif args.yticks.endswith('m'):
            args.yticks = int(args.yticks[:-1])
        else:
            args.yticks = int(args.yticks)

    lines = read_data(args.input, args.quiet)
    if args.sort or args.start or args.end:
        # force also a sort if using either --start or --end
        lines = sort_and_clean(lines, start=args.start, end=args.end)

    if not args.output:
        output = args.input
        indx = output.rindex('.')
        ext = output[indx:]
        if ext.lower() == '.gz':
            output = output[:indx]
            indx = output.rindex('.')
            ext = output[indx:]
        if ext.lower() == '.csv':
            output = output[:indx]
        if not args.format:
            args.format = 'png'
        output = '%s.%s' % (output, args.format.lower())
    else:
        output = args.output
    if os.path.isfile(output) and not args.force:
        print_error('Abort: file %s already exits. Use --force to overwrite.' % output)
        sys.exit(-1)

    plot_heatmap(lines, output, args)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as k:
        pass
