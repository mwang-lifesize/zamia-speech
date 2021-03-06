#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2013, 2014, 2016, 2017, 2018 Guenter Bartsch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# print stats about an audio corpus
#

import sys
import re
import os
import StringIO
import ConfigParser
import wave
import codecs
import logging

from optparse           import OptionParser
from speech_transcripts import Transcripts
from speech_lexicon     import Lexicon
from nltools            import misc

PROC_TITLE = 'speech_stats'

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options] corpus")

parser.add_option ("-c", "--csv", dest="csvfn", type = "str",
                   help="CSV output file")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")

(options, args) = parser.parse_args()

if len(args) != 1:
    parser.print_usage()
    sys.exit(1)

corpus_name = args[0]

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

#
# config
#

config = misc.load_config('.speechrc')

wav16_dir   = config.get("speech", "wav16")

#
# load transcripts
#

logging.info("loading transcripts...")
transcripts = Transcripts(corpus_name=corpus_name)
logging.info("loading transcripts...done.")

logging.info("splitting transcripts...")
ts_all, ts_train, ts_test = transcripts.split()
logging.info("splitting transcripts done, %d train, %d test." % (len(ts_train), len(ts_test)))

#
# audio stats
#

def format_duration(duration):
    m, s = divmod(duration, 60)
    h, m = divmod(m, 60)
    return "%3d:%02d:%02d" % (h, m, s)

def ts_stats(ts_data, ts_name):

    logging.info ('calculating %s duration...' % ts_name)

    total_duration   = 0.0
    duration_per_spk = {}
    subs_per_spk     = {}
    cnt              = 0

    for cfn in ts_data:

        wavfn = '%s/%s/%s.wav' % (wav16_dir, corpus_name, cfn)

        wavef = wave.open(wavfn, 'rb')

        num_frames = wavef.getnframes()
        frame_rate = wavef.getframerate()

        duration = float(num_frames) / float(frame_rate)

        # print '%s has %d frames at %d samples/s -> %fs' % (wavfn, num_frames, frame_rate, duration)

        total_duration += duration

        spk = ts_data[cfn]['spk']

        if not spk in duration_per_spk:
            duration_per_spk[spk] = 0.0
            subs_per_spk[spk]     = 0

        duration_per_spk[spk] += duration
        subs_per_spk[spk]     += 1

        wavef.close()

        cnt += 1

        if cnt % 1000 == 0:
           logging.info ('%6d/%6d: duration=%s (%s)' % (cnt, len(ts_data), format_duration(total_duration), ts_name))

    logging.info( "total duration of %d %s submissions: %s" % (len(ts_data), ts_name, format_duration(total_duration)))
    logging.info( "%s per user:" % ts_name)
    for spk in sorted(duration_per_spk):
        logging.info( "%-42s %s (%5d, %s)" % (spk, format_duration(duration_per_spk[spk]), subs_per_spk[spk], ts_name))

    if ts_name == 'train' and options.csvfn:
        with codecs.open(options.csvfn, 'w', 'utf8') as csvf:
            csvf.write('speaker,duration,subs\n')
            for spk in sorted(duration_per_spk):
                csvf.write( "%s,%f,%d\n" % (spk, duration_per_spk[spk], subs_per_spk[spk]))
        logging.info('%s written.' % options.csvfn)

    return total_duration

duration_test  = ts_stats(ts_test, 'test')
duration_train = ts_stats(ts_train, 'train')
duration_total = duration_test + duration_train

logging.info( "test : %s duration of %6d submissions: %s" % (corpus_name, len(ts_test), format_duration(duration_test)))
logging.info( "train: %s duration of %6d submissions: %s" % (corpus_name, len(ts_train), format_duration(duration_train)))
logging.info( "total: %s duration of %6d submissions: %s" % (corpus_name, len(ts_test) + len(ts_train), format_duration(duration_total)))



