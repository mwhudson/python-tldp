#! /usr/bin/python
# -*- coding: utf8 -*-

from __future__ import absolute_import, division, print_function

import os
import logging

from tldp.utils import which, firstfoundfile
from tldp.utils import arg_isexecutable, isexecutable
from tldp.utils import arg_isreadablefile, isreadablefile

from tldp.doctypes.common import BaseDoctype, SignatureChecker, depends

logger = logging.getLogger(__name__)


def docbookdsl_finder():
    locations = [
      '/usr/share/sgml/docbook/stylesheet/dsssl/modular/html/docbook.dsl',
      '/usr/share/sgml/docbook/dsssl-stylesheets/html/docbook.dsl',
      ]
    return firstfoundfile(locations)


def ldpdsl_finder():
    locations = [
      '/usr/share/sgml/docbook/stylesheet/dsssl/ldp/ldp.dsl',
      ]
    return firstfoundfile(locations)


class DocbookSGML(BaseDoctype, SignatureChecker):
    formatname = 'DocBook SGML 3.x/4.x'
    extensions = ['.sgml']
    signatures = ['-//Davenport//DTD DocBook V3.0//EN',
                  '-//OASIS//DTD DocBook V3.1//EN',
                  '-//OASIS//DTD DocBook V4.1//EN',
                  '-//OASIS//DTD DocBook V4.2//EN', ]

    required = {'docbooksgml_jw': isexecutable,
                'docbooksgml_openjade': isexecutable,
                'docbooksgml_dblatex': isexecutable,
                'docbooksgml_html2text': isexecutable,
                'docbooksgml_collateindex': isexecutable,
                'docbooksgml_ldpdsl': isreadablefile,
                'docbooksgml_docbookdsl': isreadablefile,
                }

    def chdir_output(self):
        os.chdir(self.output.dirname)
        return True

    @depends(chdir_output)
    def copy_static_resources(self):
        source = list()
        for d in ('images', 'resources'):
            fullpath = os.path.join(self.source.dirname, d)
            fullpath = os.path.abspath(fullpath)
            if os.path.isdir(fullpath):
                source.append('"' + fullpath + '"')
            if not source:
                logger.debug("%s no images or resources to copy",
                             self.source.stem)
                return True
            s = 'rsync --archive --verbose %s ./' % (' '.join(source))
        return self.shellscript(s)

    @depends(copy_static_resources)
    def make_blank_indexsgml(self):
        indexsgml = os.path.join(self.source.dirname, 'index.sgml')
        self.indexsgml = os.path.isfile(indexsgml)
        if self.indexsgml:
            return True
        '''generate an empty index.sgml file (in output dir)'''
        s = '''"{config.docbooksgml_collateindex}" \\
                  -N \\
                  -o \\
                  "index.sgml"'''
        return self.shellscript(s)

    @depends(make_blank_indexsgml)
    def move_blank_indexsgml_into_source(self):
        '''move a blank index.sgml file into the source tree'''
        if self.indexsgml:
            return True
        s = '''mv \\
                 --no-clobber \\
                 --verbose \\
                 -- "index.sgml" "{source.dirname}/index.sgml"'''
        return self.shellscript(s)

    @depends(move_blank_indexsgml_into_source)
    def make_data_indexsgml(self):
        '''collect document's index entries into a data file (HTML.index)'''
        if self.indexsgml:
            return True
        s = '''"{config.docbooksgml_openjade}" \\
                  -t sgml \\
                  -V html-index \\
                  -d "{config.docbooksgml_docbookdsl}" \\
                  "{source.filename}"'''
        return self.shellscript(s)

    @depends(make_data_indexsgml)
    def make_indexsgml(self):
        '''generate the final document index file (index.sgml)'''
        if self.indexsgml:
            return True
        s = '''"{config.docbooksgml_collateindex}" \\
                  -g \\
                  -t Index \\
                  -i doc-index \\
                  -o "index.sgml" \\
                     "HTML.index" \\
                     "{source.filename}"'''
        return self.shellscript(s)

    @depends(make_indexsgml)
    def move_indexsgml_into_source(self):
        '''move the generated index.sgml file into the source tree'''
        if self.indexsgml:
            return True
        indexsgml = os.path.join(self.source.dirname, 'index.sgml')
        s = '''mv \\
                 --verbose \\
                 --force \\
                 -- "index.sgml" "{source.dirname}/index.sgml"'''
        moved = self.shellscript(s)
        if moved:
            logger.debug("%s created %s", self.source.stem, indexsgml)
            self.removals.append(indexsgml)
            return True
        return False

    @depends(move_indexsgml_into_source)
    def cleaned_indexsgml(self):
        '''clean the junk from the output dir after building the index.sgml'''
        # -- be super cautious before removing a bunch of files
        cwd = os.getcwd()
        if not os.path.samefile(cwd, self.output.dirname):
            logger.error("%s (cowardly) refusing to clean directory %s", cwd)
            logger.error("%s expected to find %s", self.output.dirname)
            return False
        s = '''find . -mindepth 1 -maxdepth 1 -not -type d -delete -print'''
        return self.shellscript(s)

    @depends(cleaned_indexsgml)
    def make_htmls(self):
        '''create a single page HTML output (with incorrect name)'''
        s = '''"{config.docbooksgml_jw}" \\
                  -f docbook \\
                  -b html \\
                  --dsl "{config.docbooksgml_ldpdsl}#html" \\
                  -V nochunks \\
                  -V '%callout-graphics-path%=images/callouts/' \\
                  -V '%stock-graphics-extension%=.png' \\
                  --output . \\
                  "{source.filename}"'''
        return self.shellscript(s)

    @depends(make_htmls)
    def make_name_htmls(self):
        '''correct the single page HTML output name'''
        s = 'mv -v --no-clobber -- "{output.name_html}" "{output.name_htmls}"'
        return self.shellscript(s)

    @depends(make_name_htmls)
    def make_name_txt(self):
        '''create text output (from single-page HTML)'''
        s = '''"{config.docbooksgml_html2text}" > "{output.name_txt}" \\
                  -style pretty \\
                  -nobs \\
                  "{output.name_htmls}"'''
        return self.shellscript(s)

    def make_pdf_with_jw(self):
        '''use jw (openjade) to create a PDF'''
        s = '''"{config.docbooksgml_jw}" \\
                  -f docbook \\
                  -b pdf \\
                  --output . \\
                  "{source.filename}"'''
        return self.shellscript(s)

    def make_pdf_with_dblatex(self):
        '''use dblatex (fallback) to create a PDF'''
        s = '''"{config.docbooksgml_dblatex}" \\
                  -F sgml \\
                  -t pdf \\
                  -o "{output.name_pdf}" \\
                     "{source.filename}"'''
        return self.shellscript(s)

    @depends(cleaned_indexsgml)
    def make_name_pdf(self):
        stem = self.source.stem
        classname = self.__class__.__name__
        logger.info("%s calling method %s.%s",
                    stem, classname, 'make_pdf_with_jw')
        if self.make_pdf_with_jw():
            return True
        logger.error("%s jw failed creating PDF, falling back to dblatex...",
                     stem)
        logger.info("%s calling method %s.%s",
                    stem, classname, 'make_pdf_with_dblatex')
        return self.make_pdf_with_dblatex()

    @depends(make_name_htmls)
    def make_html(self):
        '''create chunked HTML outputs'''
        s = '''"{config.docbooksgml_jw}" \\
                 -f docbook \\
                 -b html \\
                 --dsl "{config.docbooksgml_ldpdsl}#html" \\
                 -V '%callout-graphics-path%=images/callouts/' \\
                 -V '%stock-graphics-extension%=.png' \\
                 --output . \\
                 "{source.filename}"'''
        return self.shellscript(s)

    @depends(make_html)
    def make_name_html(self):
        '''rename openjade's index.html to LDP standard name STEM.html'''
        s = 'mv -v --no-clobber -- "{output.name_indexhtml}" "{output.name_html}"'
        return self.shellscript(s)

    @depends(make_name_html)
    def make_name_indexhtml(self):
        '''create final index.html symlink'''
        s = 'ln -svr -- "{output.name_html}" "{output.name_indexhtml}"'
        return self.shellscript(s)

    @classmethod
    def argparse(cls, p):
        descrip = 'executables and data files for %s' % (cls.formatname,)
        g = p.add_argument_group(title=cls.__name__, description=descrip)
        g.add_argument('--docbooksgml-docbookdsl', type=arg_isreadablefile,
                       default=docbookdsl_finder(),
                       help='full path to html/docbook.dsl [%(default)s]')
        g.add_argument('--docbooksgml-ldpdsl', type=arg_isreadablefile,
                       default=ldpdsl_finder(),
                       help='full path to ldp/ldp.dsl [%(default)s]')
        g.add_argument('--docbooksgml-jw', type=arg_isexecutable,
                       default=which('jw'),
                       help='full path to jw [%(default)s]')
        g.add_argument('--docbooksgml-html2text', type=arg_isexecutable,
                       default=which('html2text'),
                       help='full path to html2text [%(default)s]')
        g.add_argument('--docbooksgml-openjade', type=arg_isexecutable,
                       default=which('openjade'),
                       help='full path to openjade [%(default)s]')
        g.add_argument('--docbooksgml-dblatex', type=arg_isexecutable,
                       default=which('dblatex'),
                       help='full path to dblatex [%(default)s]')
        g.add_argument('--docbooksgml-collateindex', type=arg_isexecutable,
                       default=which('collateindex.pl'),
                       help='full path to collateindex [%(default)s]')

#
# -- end of file
