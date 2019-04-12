# rtl_heatmap
Yet another heatmap generator for *rtl_power* **csv** file

Instead of reinventing the wheel, let's use *matplotlib* graphic capability to plot
the data gathered by rtl_power. All *matplotlib* colormaps are available and also the infamous 'charolastra' one (twilight+ colormaps only in matplotlib 3.x and above).

    $ ./rtl_heatmap.py -h

    usage: rtl_heatmap.py [-h] [--dbmin DBMIN] [--dbmax DBMAX] [-c COLORMAP]
                          [--colorbar] [--dpi DPI] [--end END] [-i INPUT]
                          [-f FORMAT] [--inside] [--force] [--no-margin]
                          [-o OUTPUT] [-q] [-s] [--start START] [--summary]
                          [--title TITLE] [-v] [--xticks XTICKS] [--yticks YTICKS]
                          [--xlines] [--ylines]

    Yet another heatmap generator for rtl_power .csv file

    optional arguments:
      -h, --help            show this help message and exit
      --dbmin DBMIN         Minimum value to consider for colormap normalization
      --dbmax DBMAX         Maximum value to consider for colormap normalization
      -c COLORMAP, --colormap COLORMAP
                            Specify the colormap to use (use "list" to get a list
                            of available colormaps)
      --colorbar            Add a colorbar to the plot
      --dpi DPI             Specify dpi of output image
      --end END             End time to use; everything after that is ignored;
                            expected format YYY-mm-ddTHH[:MM[:SS]]
      -i INPUT, --input INPUT
                            Input csv filename
      -f FORMAT, --format FORMAT
                            Format of the output image file
      --inside              Draw tick label inside plot
      --force               Force overwrite of existing output file
      --no-margin           Don't draw any margin around the plot
      -o OUTPUT, --output OUTPUT
                            Explicit name for the output file
      -q, --quiet           no verbose output
      -s, --show            Show pyplot window instead of outputting an image
      --start START         Start time to use; everything before that is ignored;
                            expected format YYY-mm-ddTHH[:MM[:SS]]
      --summary             Draw a summary on plot
      --title TITLE         Add a title to the plot
      -v, --version         Print version and exit
      --xticks XTICKS       Define tick in the frequency axis, xxxx[MHz,kHz]
      --yticks YTICKS       Define tick in the time axis, xxx[h|m]
      --xlines              Show lines matching major xtick labels
      --ylines              Show lines matching major ytick labels

# Examples
Example of a generated heatmap, using defaults, scan from 100 MHz to 1100 MHz for 12 hours. Following image has been resized; original image is 10396x1421 at 72 dpi.

![fullscan/defaults](img/fullscan-d.png)

## Title, summary, ylines, colorbar
You can add a title, a (auto-generated) summary, ylines matching the yticks, a legend in the form of a colorbar, and specify the spacing of yticks. For example, using `--colorbar --ylines --title 'Full scan 100 MHz-1100 MHz/12h' --summary`

![zoomed in details](img/fullscan-details.png)

At the center is the resized image, and around it, are details at the original resolution. At the top, the title, at its right, the summary, at the right the colorbar, at the bottom a xtick label, at the left ytick labels.

## No margin
You can also remove margin around the plot and draw the labels inside it. Using `-c viridis --no-margin --inside --ylines --yticks 1h`

![Full spectrum scan](img/fullscan-vniyy.png)

## Normalization
If you expect the same color scale for different data set, you need to specify a normalization range by using --dbmin and --dbmax.

Here, the data set has value from -27.81dB to -3.23dB.
- With no normalization, the colormap auto-adjust to the data set range.
- With normalization, you specify the full range that the colormap should span, even the value not present in the data set.

## Truncation
You can "truncate" your data set by using `--start/--end` to specify the start and/or the end time to be used.

You can also use `--dbmin/--dbmax` switches to "truncate" the data set for values outside a given range.
For example, if the values span -27.81dB to -3.23dB and you specify `--dbmin -20` and `--dbmax -3` then values lesser than -20 will be plotted as the min value i.e. -20 and values greate than -3 will be plotted as the max value i.e -3.

|No normalization|Normalization by specifying `--dbmin -40 --dbmax 5`|
|---|---|
|![No normalisation](img/LPD433.png)|![normalization](img/LPD433dbset.png)|


|Truncated data set from 08:00 to 09:00|Truncation specified with `--dbmin -20 --dbmax -3`|
|---|---|
|![Truncation](img/LPD433hour.png)|![Truncation](img/LPD433trunc.png)|
