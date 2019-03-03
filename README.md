# rtl_heatmap
Yet another heatmap generator for *rtl_power* **csv** file

Instead of reinventing the wheel again, let's use *matplotlib* graphic capability to plot
the data gathered by rtl_power

    $ ./rtl_heatmap.py -h
    usage: rtl_heatmap.py [-h] [--dbmin DBMIN] [--dbmax DBMAX] [-c COLORMAP]
                          [-f FORMAT] [-i INPUT] [--inside] [--force]
                          [--no-margin] [-o OUTPUT] [-q] [-s] [--start START]
                          [--end END] [--sort] [--yticks YTICKS] [--xlines]
                          [--ylines]

    Yet another heatmap generator for rtl_power .csv file

    optional arguments:
      -h, --help            show this help message and exit
      --dbmin DBMIN         Minimum value to consider for colormap normalization
      --dbmax DBMAX         Maximum value to consider for colormap normalization
      -c COLORMAP, --colormap COLORMAP
                            Specify the colormap to use (all to get a list of
                            available colormaps)
      -f FORMAT, --format FORMAT
                            Format of the output image file
      -i INPUT, --input INPUT
                            Input csv filename
      --inside              Draw tick label inside plot
      --force               Force overwrite of existing output file
      --no-margin           Don't draw any margin around the plot
      -o OUTPUT, --output OUTPUT
                            Explicit name for the output file
      -q, --quiet           no verbose output
      -s, --show            Show pyplot window instead of outputting an image
      --start START         Start time to use; everything before that is ignored
      --end END             End time to use; everything after that is ignored
      --sort                Sort csv file data
      --yticks YTICKS       Define tick in the time axis, xxx[h|m]
      --xlines              Show lines matching major xtick labels
      --ylines              Show lines matching major ytick labels

Example of a generated heatmap, using defaults:

![SRD860]
(SRD860.png)
