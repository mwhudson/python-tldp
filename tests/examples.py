
from __future__ import absolute_import, division, print_function

import os

import tldp.doctypes

opj = os.path.join
testdatadir = os.path.join(os.path.dirname(__file__), 'testdata')

ex_linuxdoc = {
               'ext': '.sgml',
               'type': tldp.doctypes.linuxdoc.Linuxdoc,
               'filename': opj(testdatadir, 'linuxdoc-simple.sgml'),
              }

ex_docbooksgml = {
                  'ext': '.sgml',
                  'type': tldp.doctypes.docbooksgml.DocbookSGML,
                  'filename': opj(testdatadir, 'docbooksgml-simple.sgml'),
                 }

ex_docbook4xml = {
                 'ext': '.xml',
                 'type': tldp.doctypes.docbook4xml.Docbook4XML,
                 'filename': opj(testdatadir, 'docbook4xml-simple.xml'),
                }

ex_docbook5xml = {
                 'ext': '.xml',
                 'type': tldp.doctypes.docbook5xml.Docbook5XML,
                 'filename': opj(testdatadir, 'docbook5xml-simple.xml'),
                }

ex_rst = {
          'ext': '.rst',
          'type': tldp.doctypes.rst.RestructuredText,
          'filename': opj(testdatadir, 'restructuredtext-simple.rst'),
         }

ex_text = {
           'ext': '.txt',
           'type': tldp.doctypes.text.Text,
           'filename': opj(testdatadir, 'text-simple.txt'),
          }

ex_markdown = {
               'ext': '.md',
               'type': tldp.doctypes.markdown.Markdown,
               'filename': opj(testdatadir, 'markdown-simple.md'),
              }


# -- a bit ugly, but grab each dict
examples = [y for x, y in locals().items() if x.startswith('ex_')]

for ex in examples:
    ex['content'] = open(ex['filename']).read()


# -- end of file