# MIT License
#
# Copyright (c) 2016 Alex Goodman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import io
import os
import sys
import difflib
import argparse
from multiprocessing import Process
import pygments
import webbrowser
from pygments.lexers import guess_lexer_for_filename
from pygments.lexer import RegexLexer
#from pygments.formatters import HtmlFormatter
from pygments.formatters import html
from pygments.token import *
# break on timeout
import signal
import magic

def signal_handler(signum, frame):
    raise Exception("Timed out!")

# Monokai is not quite right yet
PYGMENTS_STYLES = ["vs", "xcode"]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html class="no-js">
    <head>
        <!--
          html_title:    browser tab title
          reset_css:     relative path to reset css file
          pygments_css:  relative path to pygments css file
          diff_css:      relative path to diff layout css file
          page_title:    title shown at the top of the page. This should be the filename of the files being diff'd
          original_code: full html contents of original file
          modified_code: full html contents of modified file
          jquery_js:     path to jquery.min.js
          diff_js:       path to diff.js
        -->
        <meta charset="utf-8">
        <title>
            {html_title}
        </title>
        <meta name="description" content="">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="mobile-web-app-capable" content="yes">
        <link rel="stylesheet" href="{reset_css}" type="text/css">
        <link rel="stylesheet" href="{diff_css}" type="text/css">
        <link class="syntaxdef" rel="stylesheet" href="{pygments_css}" type="text/css">
    </head>
    <body>
        <div class="" id="topbar">
          <div id="filetitle">
            {page_title}     ---     added/changed/removed(right side): {added}/{changed}/{removed}
          </div>
          <div class="switches">
            <div class="switch">
              <input id="showoriginal" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="showoriginal" data-on="&#10004; Original" data-off="Original"></label>
            </div>
            <div class="switch">
              <input id="showmodified" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="showmodified" data-on="&#10004; Modified" data-off="Modified"></label>
            </div>
            <div class="switch">
              <input id="showidentical" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="showidentical" data-on="&#10004; All code" data-off="Differences"></label>
            </div>
            <div class="switch">
              <input id="highlight" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="highlight" data-on="&#10004; Highlight" data-off="Highlight"></label>
            </div>
            <div class="switch">
              <input id="codeprintmargin" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="codeprintmargin" data-on="&#10004; Margin" data-off="Margin"></label>
            </div>
            <div class="switch">
              <input id="dosyntaxhighlight" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="dosyntaxhighlight" data-on="&#10004; Syntax" data-off="Syntax"></label>
            </div>
          </div>
        </div>
        <div id="maincontainer" class="{page_width}">
            <div id="leftcode" class="left-inner-shadow codebox divider-outside-bottom">
                <div class="codefiletab">
                    &#10092; Original
                </div>
                <div class="printmargin">
                    01234567890123456789012345678901234567890123456789012345678901234567890123456789
                </div>
                {original_code}
            </div>
            <div id="rightcode" class="left-inner-shadow codebox divider-outside-bottom">
                <div class="codefiletab">
                    &#10093; Modified
                </div>
                <div class="printmargin">
                    01234567890123456789012345678901234567890123456789012345678901234567890123456789
                </div>
                {modified_code}
            </div>
        </div>
<script src="{jquery_js}" type="text/javascript"></script>
<script src="{diff_js}" type="text/javascript"></script>
    </body>
</html>
"""


class DefaultLexer(RegexLexer):
    """
    Simply lex each line as a token.
    """

    name = 'Default'
    aliases = ['default']
    filenames = ['*']

    tokens = {
        'root': [
            (r'.*\n', Text),
        ]
    }


class DiffHtmlFormatter(html.HtmlFormatter):
    """
    Formats a single source file with pygments and adds diff highlights based on the
    diff details given.
    """
    isLeft = False
    diffs = None

    def __init__(self, isLeft, diffs, *args, **kwargs):
        self.isLeft = isLeft
        self.diffs = diffs
        # keep counters for changed lines in right (second) file
        self.no_added   = 0
        self.no_diff    = 0
        self.no_removed = 0

        super(DiffHtmlFormatter, self).__init__(*args, **kwargs)

    def wrap(self, source, outfile):
        return self._wrap_code(source)

    def getChangedLineCounts(self):
        return self.no_added, self.no_diff, self.no_removed

    def getDiffLineNos(self):
        retlinenos = []
        for idx, ((left_no, left_line), (right_no, right_line), change) in enumerate(self.diffs):
            no = None
            if self.isLeft:
                if change:
                    if isinstance(left_no, int) and isinstance(right_no, int):
                        # <span class="lineno_q lineno_leftchange">
                        no = '<span class="lineno_leftchange_q">' + \
                            str(left_no) + "</span>"
                    elif isinstance(left_no, int) and not isinstance(right_no, int):
                        # <span class="lineno_q lineno_leftdel">
                        no = '<span class="lineno_leftdel_q">' + \
                            str(left_no) + "</span>"
                    elif not isinstance(left_no, int) and isinstance(right_no, int):
                        # <span class="lineno_q lineno_leftadd">
                        no = '<span class="lineno_leftadd_q">  </span>'
                else:
                    no = '<span class="lineno_lequ_q">' + str(left_no) + "</span>"
            else:
                if change:
                    if isinstance(left_no, int) and isinstance(right_no, int):
                        # <span class="lineno_q lineno_rightchange">
                        no = '<span class="lineno_rightchange_q">' + \
                            str(right_no) + "</span>"
                    elif isinstance(left_no, int) and not isinstance(right_no, int):
                        #<span class="lineno_q lineno_rightdel">
                        no = '<span class="lineno_rightdel_q">  </span>'
                    elif not isinstance(left_no, int) and isinstance(right_no, int):
                        # <span class="lineno_q lineno_rightadd">
                        no = '<span class="lineno_rightadd_q">' + \
                            str(right_no) + "</span>"
                else:
                    no = '<span class="lineno_requ_q">' + str(right_no) + "</span>"

            retlinenos.append(no)

        return retlinenos

    def _wrap_code(self, source):
        source = list(source)
        yield 0, '<pre>'

        for idx, ((left_no, left_line), (right_no, right_line), change) in enumerate(self.diffs):
            # print idx, ((left_no, left_line),(right_no, right_line),change)
            try:
                if self.isLeft:
                    if change:
                        if isinstance(left_no, int) and isinstance(right_no, int) and left_no <= len(source):
                            i, t = source[left_no - 1]
                            t = '<span class="left_diff_change">' + t + "</span>"
                        elif isinstance(left_no, int) and not isinstance(right_no, int) and left_no <= len(source):
                            i, t = source[left_no - 1]
                            t = '<span class="left_diff_del">' + t + "</span>"
                        elif not isinstance(left_no, int) and isinstance(right_no, int):
                            i, t = 1, left_line
                            t = '<span class="left_diff_add">' + t + "</span>"
                        else:
                            raise
                    else:
                        if left_no <= len(source):
                            i, t = source[left_no - 1]
                            t = '<span class="left_identical">' + t + "</span>"
                        else:
                            i = 1
                            t = left_line
                else:
                    if change:
                        # count changes for right (second) file
                        if isinstance(left_no, int) and isinstance(right_no, int) and right_no <= len(source):
                            i, t = source[right_no - 1]
                            t = '<span class="right_diff_change">' + t + "</span>"
                            self.no_diff += 1
                        elif isinstance(left_no, int) and not isinstance(right_no, int):
                            i, t = 1, right_line
                            t = '<span class="right_diff_del">' + t + "</span>"
                            self.no_removed += 1
                        elif not isinstance(left_no, int) and isinstance(right_no, int) and right_no <= len(source):
                            i, t = source[right_no - 1]
                            t = '<span class="right_diff_add">' + t + "</span>"
                            self.no_added += 1
                        else:
                            raise
                    else:
                        if right_no <= len(source):
                            i, t = source[right_no - 1]
                            t = '<span class="right_identical">' + t + "</span>"
                        else:
                            i = 1
                            t = right_line
                yield i, t
            except:
                # print "WARNING! failed to enumerate diffs fully!"
                pass  # this is expected sometimes
        yield 0, '\n</pre>'

    def _wrap_tablelinenos(self, inner):
        dummyoutfile = io.StringIO()
        lncount = 0
        for t, line in inner:
            if t:
                lncount += 1

            # compatibility Python v2/v3
            if sys.version_info > (3,0):
                dummyoutfile.write(line)
            else:
                dummyoutfile.write(unicode(line))

        fl = self.linenostart
        mw = len(str(lncount + fl - 1))
        sp = self.linenospecial
        st = self.linenostep
        la = self.lineanchors
        aln = self.anchorlinenos
        nocls = self.noclasses

        lines = []
        for i in self.getDiffLineNos():
            lines.append('{}'.format(i))

        ls = ''.join(lines)

        # in case you wonder about the seemingly redundant <div> here: since the
        # content in the other cell also is wrapped in a div, some browsers in
        # some configurations seem to mess up the formatting...
        if nocls:
            yield 0, ('<table class="{}table">'.format(self.cssclass) +
                      '<tr><td><div class="linenodiv" '
                      'style="background-color: #f0f0f0; padding-right: 10px">'
                      '<pre style="line-height: 125%">' +
                      ls + '</pre></div></td><td class="code">')
        else:
            yield 0, ('<table class="{}table">'.format(self.cssclass) +
                      '<tr><td class="linenos"><div class="linenodiv"><pre>' +
                      ls + '</pre></div></td><td class="code">')
        yield 0, dummyoutfile.getvalue()
        yield 0, '</td></tr></table>'


class CodeDiff(object):
    """
    Manages a pair of source files and generates a single html diff page comparing
    the contents.
    """
    pygmentsCssFile = "{}/html_deps/codeformats/{}.css"
    diffCssFile = "{}/html_deps/diff.css"
    diffJsFile = "{}/html_deps/diff.js"
    resetCssFile = "{}/html_deps/reset.css"
    jqueryJsFile = "{}/html_deps/jquery.min.js"




    def __init__(self, fromfile, tofile, fromtxt=None, totxt=None, name=None, format_timeout=60):
        self.cotinue_to_execute=True
        self.filename = name
        self.fromfile = fromfile
        self.format_timeout = int(format_timeout)

        # ChangedLineCounts:
        self.no_added   = 0
        self.no_diff    = 0
        self.no_removed = 0

        p1 = Process(target=self.TimeLimited(3,fromfile, tofile, fromtxt, totxt), name='test')
        p1.start()
        p1.join(timeout=3)
        self.cotinue_to_execute = True
        p1.terminate()

    def check_encoding(self, filename):
        fileinfo = magic.detect_from_filename(filename)
        if fileinfo.encoding == 'us-ascii':
            encoding = 'utf-8'
        else:
            encoding = fileinfo.encoding
        return encoding

    def getChangedLineCounts(self):
        return self.no_added, self.no_diff, self.no_removed

    def TimeLimited(self,timeout, fromfile, tofile, fromtxt=None, totxt=None, verbose=False):
        if fromtxt == None:
            try:
                encoding = self.check_encoding(fromfile)
                with io.open(fromfile, encoding=f"{encoding}") as f:
                    self.fromlines = f.readlines()
            except Exception as e:
                print("Problem reading file {}, type: {}".format(fromfile, encoding))
                print(e)
                print("Error text will be used as file contents!")
                self.fromlines = "FAILED TO READ FILE! Error: {}".format(e)
        else:
            self.fromlines = [n + "\n" for n in fromtxt.split("\n")]
        self.leftcode = "".join(self.fromlines)

        self.tofile = tofile
        if totxt == None:
            try:
                encoding = self.check_encoding(tofile)
                with io.open(tofile, encoding=f"{encoding}") as f:
                    self.tolines = f.readlines()
            except Exception as e:
                print("Problem reading file{},type: {}".format(tofile, encoding) )
                print(e)
                print("Error text will be used as file contents!")
                self.tolines = "FAILED TO READ FILE! Error: {}".format(e)
        else:
            self.tolines = [n + "\n" for n in totxt.split("\n")]
        self.rightcode = "".join(self.tolines)

        temp_file_name = tofile
        if temp_file_name == None:
            temp_file_name = fromfile
        if verbose:
            print("File(s) {} parsed before {}s timeout ".format(temp_file_name,timeout))

    def getDiffDetails(self, fromdesc='', todesc='', context=False, numlines=5, tabSize=8):
        # change tabs to spaces before it gets more difficult after we insert
        # markkup

        if not self.cotinue_to_execute:
            return

        def expand_tabs(line):
            # hide real spaces
            line = line.replace(' ', '\0')
            # expand tabs into spaces
            line = line.expandtabs(tabSize)
            # replace spaces from expanded tabs back into tab characters
            # (we'll replace them with markup after we do differencing)
            line = line.replace(' ', '\t')
            return line.replace('\0', ' ').rstrip('\n')

        self.fromlines = [expand_tabs(line) for line in self.fromlines]
        self.tolines = [expand_tabs(line) for line in self.tolines]

        # create diffs iterator which generates side by side from/to data
        if context:
            context_lines = numlines
        else:
            context_lines = None

        diffs = difflib._mdiff(self.fromlines, self.tolines, context_lines,
                               linejunk=None, charjunk=difflib.IS_CHARACTER_JUNK)
        return list(diffs)

    def format(self, options):

        if not self.cotinue_to_execute:
            return

        timeoutDetected = False

        existing_handler = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(self.format_timeout)   # 60 seconds normally
        try:
            self.diffs = self.getDiffDetails(self.fromfile, self.tofile)
        except Exception:
            print(f"Timed out! formatting FAILED for {self.filename}!")
            self.htmlContents = "COMPARE FAILED! TIMEOUT!"
            timeoutDetected = True
        finally:
            signal.signal(signal.SIGALRM, existing_handler)
            signal.alarm(0)

        if timeoutDetected:
            return

        if options.verbose:
            for diff in self.diffs:
                print("{0:6} {1:80} {2:80}".format(diff[2], diff[0], diff[1]))

        fields = ((self.leftcode, True, self.fromfile),
                  (self.rightcode, False, self.tofile))

        codeContents = []
        for (code, isLeft, filename) in fields:

            inst = DiffHtmlFormatter(isLeft,
                                     self.diffs,
                                     nobackground=False,
                                     linenos=True,
                                     style=options.syntax_css)

            try:
                self.lexer = guess_lexer_for_filename(self.filename, code)

            except pygments.util.ClassNotFound:
                if options.verbose:
                    print("No Lexer Found! Using default...")

                self.lexer = DefaultLexer()

            formatted = pygments.highlight(code, self.lexer, inst)

            # safe changed line counts for right file only...
            if isLeft  == False:
                self.no_added, self.no_diff, self.no_removed = inst.getChangedLineCounts()

            codeContents.append(formatted)

        subdir_depth = "."
        depth = int( options.depth )
        if depth > 0:
            subdir_depth =  ".."
            depth -= 1
            while depth > 0:
                subdir_depth = "../{}".format(subdir_depth)
                depth -= 1

        answers = {
            "html_title":     self.filename,
            "reset_css":      self.resetCssFile.format(subdir_depth),
            "pygments_css":   self.pygmentsCssFile.format( subdir_depth, options.syntax_css),
            "diff_css":       self.diffCssFile.format(subdir_depth),
            "page_title":     self.filename,
            "added":          self.no_added,
            "changed":        self.no_diff,
            "removed":        self.no_removed,
            "original_code":  codeContents[0],
            "modified_code":  codeContents[1],
            "jquery_js":      self.jqueryJsFile.format(subdir_depth),
            "diff_js":        self.diffJsFile.format(subdir_depth),
            "page_width":     "page-80-width" if options.print_width else "page-full-width"
        }

        self.htmlContents = HTML_TEMPLATE.format(**answers)

    def write(self, path):
        if not self.cotinue_to_execute:
            return
        path_only = path[:path.rfind("/")]
        if not os.path.exists(path_only):
            os.makedirs(path_only)
        fh = io.open(path, 'w')
        fh.write(self.htmlContents)
        fh.close()


def main(file1, file2, outputpath, options):
    codeDiff = CodeDiff(file1, file2, name=file2, format_timeout=options.timeout)
    codeDiff.format(options)
    codeDiff.write(outputpath)

def show(outputpath):
    path = os.path.abspath(outputpath)
    webbrowser.open('file://' + path)

if __name__ == "__main__":
    description = """Given two source files this application\
creates an html page which highlights the differences between the two. """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-s', '--show', action='store_true',
                        help='show html in a browser.')
    parser.add_argument('-p', '--print-width', action='store_true',
        help='Restrict code to 80 columns wide. (printer friendly in landscape)')
    parser.add_argument('-c', '--syntax-css', action='store', default="vs",
        help='Pygments CSS for code syntax highlighting. Can be one of: {}'.format(str(PYGMENTS_STYLES)))
    parser.add_argument('-v', '--verbose', action='store_true', help='show verbose output.')
    parser.add_argument('-o', '--outputpath', action='store', default = 'index.html' )
    parser.add_argument('-d', '--depth', action='store',default='0', help="subdir depth for output file")
    parser.add_argument('--timeout', action="store", help="timeout for page formatting in seconds (defaults to 60)", default=60)
    parser.add_argument('file1', help='source file to compare ("before" file).')
    parser.add_argument('file2', help='source file to compare ("after" file).')

    args = parser.parse_args()

    if args.syntax_css not in PYGMENTS_STYLES:
        raise ValueError("Syntax CSS (-c) must be one of {}.".format(PYGMENTS_STYLES))

    main(args.file1, args.file2, args.outputpath, args)
    if args.show:
        show(args.outputpath)
