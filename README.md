# MRTG Probes


This repository contains [MRTG](https://oss.oetiker.ch/mrtg/doc/mrtg.en.html) data
collection scripts for plotting different metrics.


### download_performance.py

Plot '1 hour' and '24 hour' download performance numbers from a specific site,
specified by URL. It uses a file lock to prevent parallel download tests.

    $ download_performance.py -h
    usage: download_performance.py [-h] [-w <path>] [-b] [-x] <url>
    
    MRTG script for logging download performance
    
    positional arguments:
      <url>                 URL of the test file
    
    optional arguments:
      -h, --help            show this help message and exit
      -w <path>, --workingdir <path>
                            working directory (with write permissions for the mrtg
                            poller script). Defaults to "/var/www/html/mrtg"
      -b, --bps             Return bits-per-second, instead of bytes-per-second
      -x, --execute         (internal use only) perform the backup test
    
    Called repeatedly, this script will download a url once per hour, and will
    report the latest download speed and the slowest in the last 24 hours.



Example MRTG configuration file, for monitoring download performance from 'otto':

    EnableIPv6: no
    WorkDir: /var/www/html/mrtg
    
    Title[otto_bw]: otto bandwidth monitoring
    Target[otto_bw]: `/usr/local/bin/download_performance.py -b -w /var/www/html/mrtg http://otto/testfile`
    Directory[otto_bw]: ottobw
    MaxBytes[otto_bw]: 30000000
    PageTop[otto_bw]: <h1>otto download performance</h1>
    YLegend[otto_bw]: Speed
    ShortLegend[otto_bw]: bps
    LegendO[otto_bw]: 24 Hr min
    LegendI[otto_bw]: 1 Hr performance
    Options[otto_bw]: growright, noinfo, gauge
