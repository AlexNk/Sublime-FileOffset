# Author: Alexander Nazarenko (NazarenkoAl@gmail.com)
import sublime, sublime_plugin

class FileOffsetCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        positions = self._collect_positions()
        offsets = self._calc_offsets(positions)

        is_long = (len(offsets) > 1)
        text = self._format_result(offsets, positions, is_long)
        self._show_result(text, len(offsets))

    def _collect_positions(self):
        ret = []
        for sel in self.view.sel():
            (bpos, epos) = (sel.begin(), sel.end())
            (brow, bcol) = self.view.rowcol(bpos)
            if (sel.empty()):
                (erow, ecol) = (brow, bcol) 
            else:
                (erow, ecol) = self.view.rowcol(epos)
            ret.append([(brow, bcol, bpos), (erow, ecol, epos)])
        return ret

    def _calc_offsets(self, positions):
        def _offsets_by_file():
            def _get_offset(l, c, state):
                while (state["line_num"] <= l):
                    state["line_offset"] = state["file"].tell()
                    state["line"] = state["file"].readline()
                    state["line_num"] += 1
                col_offset = len(state["line"][:c].encode(self.view.encoding()))
                return state["line_offset"] + col_offset
            ret = []
            f = open(self.view.file_name(), "rt", encoding=self.view.encoding())
            state = { "file": f, "line_num": 0, "line": "", }
            for ((brow, bcol, bpos), (erow, ecol, epos)) in positions:
                bo = _get_offset(brow, bcol, state)
                if ((brow, bcol) == (erow, ecol)):
                    ret.append((bo, bo))
                else:
                    eo = _get_offset(erow, ecol, state)
                    ret.append((bo, eo))
            return ret
        def _offsets_by_pos():
            ret = []
            for pos in positions:
                ((brow, bcol, bpos), (erow, ecol, epos)) = pos
                ret.append((bpos, epos))
            return ret

        if (self.view.file_name()):
            return _offsets_by_file()
        else:
            return _offsets_by_pos()
        
    def _get_substring_at_pos(self, apos, l):
        (brow, bcol, bsel) = apos[0]
        pos = self.view.text_point(brow, bcol)
        substr = self.view.substr(sublime.Region(pos, pos + l))
        return substr.split("\n")[0]

    def _format_result(self, offsets, positions, show_substr):
        text = "File name: %s\n\n" % self.view.file_name()
        for i in range(len(offsets)):
            (bo, eo) = offsets[i]
            if (bo != eo):
                text += "0x%08X (%d) - 0x%08X (%d)" % (bo, bo, eo, eo)
                if (show_substr):
                    text += "\t" + self._get_substring_at_pos(positions[i], 16)
            else:
                text += "0x%08X (%d)" % (bo, bo)
            text += "\n"
        return text

    def _show_result(self, text, is_long):
        #print(text)
        if (is_long):
            self.view.run_command("file_offset_show_result", {"text":text})
        else:
            sublime.message_dialog(text)

class FileOffsetShowResultCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        n = sublime.active_window().new_file()
        n.set_scratch(True)
        n.insert(edit, 0, text)
