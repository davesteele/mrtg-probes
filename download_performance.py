#!/usr/bin/python

import os
import sys
import datetime
import fcntl
import json
import argparse
import subprocess
import re


jsfile = 'dl_perf.json'
jspath = None


def setup_env(workingdir):
    global jspath

    if not os.path.isdir(workingdir):
        os.makedirs(workingdir)

    jspath = os.path.join(workingdir, jsfile)
    if not os.path.exists(jspath):
        with open(jspath, 'w') as fp:
            json.dump({}, fp)


def get_lock(lockfile):
    fp = open(lockfile, 'w')
    fcntl.lockf(fp, fcntl.LOCK_EX)
    return fp


def release_lock(fp):
    fp.close()


def calc_bw(url, bps):
    """Download url and return bytes per second"""

    start = datetime.datetime.now()
    cmd = "/usr/bin/wget -qO - %s &> /dev/null" % url
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    (out, err) = p.communicate()
    bytes = len(out)
    duration = datetime.datetime.now() - start

    rate = bytes / duration.total_seconds()

    if bps:
        rate *= 8

    return rate


def dt2str(dt):
    return dt.strftime('%y-%m-%d %H:%M')


def str2dt(str):
    try:
        return datetime.datetime.strptime(str, '%y-%m-%d %H:%M')
    except ValueError:
        return datetime.datetime.strptime(str, '%y-%m-%d %H')


def store_result(url, start, result):
    """Store the new result in the JSON file, indexed by URL and time.
       Keep 24 hours worth of resutls."""

    with open(jspath, 'r') as jsfile:
        js = json.load(jsfile)

    if url not in js:
        js[url] = {}

    js[url][dt2str(start)] = result

    if len(js[url]) > 24:
        for date in sorted(js[url])[0:len(js[url]) - 24]:
            js[url].pop(date)

    with open(jspath, 'w') as jsfile:
        json.dump(js, jsfile, sort_keys=True, indent=4, separators=(',', ': '))


def parse_args():
    parser = argparse.ArgumentParser(
                description="MRTG script for logging download performance",
                epilog="Called repeatedly, this script will download a url"
                       " once per hour, and will report the latest download"
                       " speed and the slowest in the last 24"
                       " hours.",
        )

    parser.add_argument(
        'url',
        metavar='<url>',
        help="URL of the test file",
        )

    parser.add_argument(
        '-w', '--workingdir',
        metavar='<path>',
        default='/var/www/html/mrtg',
        help='working directory (with write permissions for the'
             ' mrtg poller script). Defaults to'
             ' "/var/www/html/mrtg"',
        )

    parser.add_argument(
        '-b', '--bps',
        action='store_true',
        help="Return bits-per-second, instead of bytes-per-second",
        )

    parser.add_argument(
        '-x', '--execute',
        action='store_true',
        help="(internal use only) perform the backup test",
        )

    args = parser.parse_args()

    return args

if __name__ == '__main__':

    args = parse_args()

    setup_env(args.workingdir)

    if args.execute:
        # We've been asked to calc bw for the hour. Run in background.
        lock = get_lock(os.path.join(args.workingdir, 'dl_perf.lock'))
        start = datetime.datetime.now()
        result = calc_bw(args.url, args.bps)
        store_result(args.url, start, int(result))
        release_lock(lock)
    else:
        onehr = oneday = 'UNKNOWN'

        with open(jspath, 'r') as jsfile:
            js = json.load(jsfile)

        last_dt = None
        if args.url in js and len(js[args.url]) > 0:
            last_dt = str2dt(max(js[args.url]))
            dt_age = (datetime.datetime.now() - last_dt).total_seconds()

        # See if we need to calculate a new data point
        if last_dt is None or dt_age > (3600 - 2.5 * 60):
            cmd = "%s -x -w %s %s" % (sys.argv[0], args.workingdir,
                                      args.url)
            if args.bps:
                cmd = "%s %s" % (cmd, '-b')

            subprocess.Popen(cmd.split(), shell=False,
                                          stdin=None, stdout=None,
                                          stderr=None, close_fds=True)

        # Use the data in JSON, if it is not too old
        if last_dt is not None and dt_age < 2 * 3600:
            onehr = js[args.url][max(js[args.url])]
            oneday = min([js[args.url][x] for x in js[args.url]])

        host = args.url
        m = re.search("//(.+?)/", host)
        if m:
            host = m.group(1)

        print(onehr)
        print(oneday)
        print(0)
        print(host)
