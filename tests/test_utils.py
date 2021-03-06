# -*- coding: utf8 -*-
#
# Copyright (c) 2016 Linux Documentation Project

from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals

import os
import stat
import uuid
import errno
import posix
import unittest
from tempfile import mkdtemp
from tempfile import NamedTemporaryFile as ntf

from tldptesttools import TestToolsFilesystem

# -- SUT
from tldp.utils import which, execute
from tldp.utils import statfile, statfiles, stem_and_ext
from tldp.utils import arg_isexecutable, isexecutable
from tldp.utils import arg_isreadablefile, isreadablefile
from tldp.utils import arg_isdirectory, arg_isloglevel
from tldp.utils import arg_isstr
from tldp.utils import swapdirs


class Test_isexecutable_and_friends(unittest.TestCase):

    def test_isexecutable(self):
        f = ntf(prefix='executable-file')
        self.assertFalse(isexecutable(f.name))
        mode = stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR
        os.chmod(f.name, mode)
        self.assertTrue(isexecutable(f.name))

    def test_arg_isexecutable(self):
        f = ntf(prefix='executable-file')
        self.assertIsNone(arg_isexecutable(f.name))
        mode = stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR
        os.chmod(f.name, mode)
        self.assertEqual(f.name, arg_isexecutable(f.name))


class Test_isreadablefile_and_friends(unittest.TestCase):

    def test_isreadablefile(self):
        f = ntf(prefix='readable-file')
        self.assertTrue(isreadablefile(f.name))
        mode = os.stat(f.name).st_mode
        os.chmod(f.name, 0)
        if 0 == os.getuid():
            self.assertTrue(isreadablefile(f.name))
        else:
            self.assertFalse(isreadablefile(f.name))
        os.chmod(f.name, mode)

    def test_arg_isreadablefile(self):
        f = ntf(prefix='readable-file')
        self.assertEqual(f.name, arg_isreadablefile(f.name))
        mode = os.stat(f.name).st_mode
        os.chmod(f.name, 0)
        if 0 == os.getuid():
            self.assertEqual(f.name, arg_isreadablefile(f.name))
        else:
            self.assertIsNone(arg_isreadablefile(f.name))
        os.chmod(f.name, mode)


class Test_arg_isstr(unittest.TestCase):

    def test_arg_isstr(self):
        self.assertEqual('s', arg_isstr('s'))
        self.assertEqual(None, arg_isstr(7))


class Test_arg_isloglevel(unittest.TestCase):

    def test_arg_isloglevel_integer(self):
        self.assertEqual(7, arg_isloglevel(7))
        self.assertEqual(40, arg_isloglevel('frobnitz'))
        self.assertEqual(20, arg_isloglevel('INFO'))
        self.assertEqual(10, arg_isloglevel('DEBUG'))


class Test_arg_isdirectory(TestToolsFilesystem):

    def test_arg_isdirectory(self):
        self.assertTrue(arg_isdirectory(self.tempdir))
        f = ntf(dir=self.tempdir)
        self.assertFalse(arg_isdirectory(f.name))


class Test_execute(TestToolsFilesystem):

    def test_execute_returns_zero(self):
        exe = which('true')
        result = execute([exe], logdir=self.tempdir)
        self.assertEqual(0, result)

    def test_execute_stdout_to_devnull(self):
        exe = which('cat')
        cmd = [exe, '/etc/hosts']
        devnull = open('/dev/null', 'w')
        result = execute(cmd, stdout=devnull, logdir=self.tempdir)
        devnull.close()
        self.assertEqual(0, result)

    def test_execute_stderr_to_devnull(self):
        exe = which('cat')
        cmd = [exe, '/etc/hosts']
        devnull = open('/dev/null', 'w')
        result = execute(cmd, stderr=devnull, logdir=self.tempdir)
        devnull.close()
        self.assertEqual(0, result)

    def test_execute_returns_nonzero(self):
        exe = which('false')
        result = execute([exe], logdir=self.tempdir)
        self.assertEqual(1, result)

    def test_execute_exception_when_logdir_none(self):
        exe = which('true')
        with self.assertRaises(ValueError) as ecm:
            execute([exe], logdir=None)
        e = ecm.exception
        self.assertTrue('logdir must be a directory' in e.args[0])

    def test_execute_exception_when_logdir_enoent(self):
        exe = which('true')
        logdir = os.path.join(self.tempdir, 'nonexistent-directory')
        with self.assertRaises(IOError) as ecm:
            execute([exe], logdir=logdir)
        e = ecm.exception
        self.assertTrue('nonexistent' in e.filename)


class Test_which(unittest.TestCase):

    def test_good_which_python(self):
        python = which('python')
        self.assertIsNotNone(python)
        self.assertTrue(os.path.isfile(python))
        qualified_python = which(python)
        self.assertEqual(python, qualified_python)

    def test_bad_silly_name(self):
        silly = which('silliest-executable-name-which-may-yet-be-possible')
        self.assertIsNone(silly)

    def test_fq_executable(self):
        f = ntf(prefix='tldp-which-test', delete=False)
        f.close()
        notfound = which(f.name)
        self.assertIsNone(notfound)
        mode = stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH
        os.chmod(f.name, mode)
        found = which(f.name)
        self.assertEqual(f.name, found)
        os.unlink(f.name)


class Test_statfiles(unittest.TestCase):

    def test_statfiles_dir_in_result(self):
        '''Assumes that directory ./sample-documents/ exists here'''
        here = os.path.dirname(os.path.abspath(__file__))
        statinfo = statfiles(here, relative=here)
        self.assertIsInstance(statinfo, dict)
        adoc = 'sample-documents/asciidoc-complete.txt'
        self.assertTrue(adoc in statinfo)

    def test_statfiles_dir_rel(self):
        here = os.path.dirname(os.path.abspath(__file__))
        statinfo = statfiles(here, relative=here)
        self.assertIsInstance(statinfo, dict)
        self.assertTrue(os.path.basename(__file__) in statinfo)

    def test_statfiles_dir_abs(self):
        here = os.path.dirname(os.path.abspath(__file__))
        statinfo = statfiles(here)
        self.assertIsInstance(statinfo, dict)
        self.assertTrue(__file__ in statinfo)

    def test_statfiles_file_rel(self):
        here = os.path.dirname(os.path.abspath(__file__))
        statinfo = statfiles(__file__, relative=here)
        self.assertIsInstance(statinfo, dict)
        self.assertTrue(os.path.basename(__file__) in statinfo)

    def test_statfiles_file_abs(self):
        statinfo = statfiles(__file__)
        self.assertIsInstance(statinfo, dict)
        self.assertTrue(__file__ in statinfo)

    def test_statfiles_nonexistent_file(self):
        here = os.path.dirname(os.path.abspath(__file__))
        this = os.path.join(here, str(uuid.uuid4()))
        statinfo = statfiles(this)
        self.assertIsInstance(statinfo, dict)
        self.assertEqual(0, len(statinfo))


class Test_statfile(TestToolsFilesystem):

    def test_statfile_bogustype(self):
        with self.assertRaises(TypeError):
            statfile(0)

    def test_statfile_enoent(self):
        f = ntf(dir=self.tempdir)
        self.assertIsNone(statfile(f.name + '-ENOENT_TEST'))

    def test_statfile_exception(self):
        f = ntf(dir=self.tempdir)
        omode = os.stat(self.tempdir).st_mode
        os.chmod(self.tempdir, 0)
        if 0 != os.getuid():
            with self.assertRaises(Exception) as ecm:
                statfile(f.name)
            e = ecm.exception
            self.assertIn(e.errno, (errno.EPERM, errno.EACCES))
            os.chmod(self.tempdir, omode)
        stbuf = statfile(f.name)
        self.assertIsInstance(stbuf, posix.stat_result)


class Test_stem_and_ext(unittest.TestCase):

    def test_stem_and_ext_final_slash(self):
        r0 = stem_and_ext('/h/q/t/z/Frobnitz-HOWTO')
        r1 = stem_and_ext('/h/q/t/z/Frobnitz-HOWTO/')
        self.assertEqual(r0, r1)

    def test_stem_and_ext_rel_abs(self):
        r0 = stem_and_ext('/h/q/t/z/Frobnitz-HOWTO')
        r1 = stem_and_ext('Frobnitz-HOWTO/')
        self.assertEqual(r0, r1)


class Test_swapdirs(TestToolsFilesystem):

    def test_swapdirs_bogusarg(self):
        with self.assertRaises(OSError) as ecm:
            swapdirs('/path/to/frickin/impossible/dir', None)
        e = ecm.exception
        self.assertTrue(errno.ENOENT is e.errno)

    def test_swapdirs_b_missing(self):
        a = mkdtemp(dir=self.tempdir)
        b = a + '-B'
        self.assertFalse(os.path.exists(b))
        swapdirs(a, b)
        self.assertTrue(os.path.exists(b))

    def test_swapdirs_with_file(self):
        a = mkdtemp(dir=self.tempdir)
        afile = os.path.join(a, 'silly')
        b = mkdtemp(dir=self.tempdir)
        bfile = os.path.join(b, 'silly')
        with open(afile, 'w'):
            pass
        self.assertTrue(os.path.exists(a))
        self.assertTrue(os.path.exists(afile))
        self.assertTrue(os.path.exists(b))
        self.assertFalse(os.path.exists(bfile))
        swapdirs(a, b)
        self.assertTrue(os.path.exists(a))
        self.assertFalse(os.path.exists(afile))
        self.assertTrue(os.path.exists(b))
        self.assertTrue(os.path.exists(bfile))

#
# -- end of file
