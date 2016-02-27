#! /usr/bin/python
# -*- coding: utf8 -*-

from __future__ import absolute_import, division, print_function

import os
import sys
import logging
from argparse import Namespace

import tldp
from tldp.utils import arg_isloglevel

logger = logging.getLogger(__name__)


def detail(config, args):
    i = tldp.inventory.Inventory(config.pubdir, config.sourcedir)
    width = Namespace()
    width.status = max([len(x) for x in tldp.inventory.status_types])
    width.stem = max([len(x) for x in i.source.keys()])
    # -- if user just said "list" with no args, then give the user something
    #    sane, "all"; it would make sense for this to be "work", too, but
    #    "all" seems to be less surprising
    #
    if not args:
        args.append('all')
    for arg in args:
        status_class = tldp.inventory.status_classes[arg]
        for status in status_class:
            s = getattr(i, status, None)
            assert s is not None
            for stem, doc in s.items():
                # -- a 'stale' or 'broken' document is implicitly a 'published'
                #    document as well, but we only want to list each document
                #    once
                #
                if doc.status == status:
                    doc.detail(width, config.verbose, file=sys.stdout)
    return 0


def status(config, args):
    i = tldp.inventory.Inventory(config.pubdir, config.sourcedir)
    width = Namespace()
    width.status = max([len(x) for x in tldp.inventory.status_types])
    width.count = len(str(len(i.source.keys())))
    for status in tldp.inventory.status_types:
        if status == 'all':
            continue
        count = len(getattr(i, status, 0))
        s = '{0:{w.status}}  {1:{w.count}}  '.format(status, count, w=width)
        print(s, end="")
        if config.verbose:
            print(', '.join(getattr(i, status).keys()))
        else:
            abbrev = getattr(i, status).keys()
            s = ''
            if abbrev:
                s = s + abbrev.pop(0)
                while abbrev and len(s) < 50:
                    s = s + ', ' + abbrev.pop()
                if abbrev:
                    s = s + ', and %d more ...' % (len(abbrev))
            print(s)
    return 0


def build(config, args):
    targets = list()
    stems = list()
    if args:
        for arg in args:
            if os.path.isfile(arg) or os.path.isdir(arg):
                source = tldp.sources.SourceDocument(arg)
                targets.append(source)
            else:
                stems.append(arg)
    if stems or not args:
        i = tldp.inventory.Inventory(config.pubdir, config.sourcedir)
        if stems:
            for source in i.source.values():
                if source.stem in stems:
                    targets.append(source)
        else:
            targets.extend(i.new.values())
            targets.extend(i.stale.values())
            targets.extend(i.broken.values())
    for source in targets:
        if source.stem in config.skip:
            logger.info("%s skipping build per request", source.stem)
            continue
        if not source.output:
            dirname = os.path.join(config.pubdir, source.stem)
            source.output = tldp.outputs.OutputDirectory(dirname)
        if not source.doctype:
            logger.warning("%s skipping document of unknown doctype", 
                           source.stem)
            continue
        output = source.output
        runner = source.doctype(source=source, output=output, config=config)
        runner.generate()
    return 0


def run():
    # -- may want to see option parsing, so set --loglevel as
    #    soon as possible
    if '--loglevel' in sys.argv:
        levelarg = 1 + sys.argv.index('--loglevel')
        level = arg_isloglevel(sys.argv[levelarg])
        logger.setLevel(level)

    # -- produce a configuration from CLI, ENV and CFG
    #
    tag = os.path.basename(sys.argv[0]).strip('.py')
    argv = sys.argv[1:]
    config, args = tldp.config.collectconfiguration(tag, argv)


    # -- check to see if the user wishes to --list things
    #    this function and friends is called 'detail', because
    #    Python reserves a special (fundamental) meaning for the word
    #    list; but for the end-user they are synonyms
    #
    if config.detail:
        sys.exit(detail(config, args))

    # -- check to see if the user wants --status output
    #
    if config.status:
        if config.pubdir is None:
            sys.exit("Option --pubdir required for --status.")
        if not config.sourcedir:
            sys.exit("Option --sourcedir required for --status.")
        sys.exit(status(config, args))

    # -- our primary action is to try to build
    if config.build is None:
        config.all = True
    sys.exit(build(config, args))


if __name__ == '__main__':
    run()

#
# -- end of file
