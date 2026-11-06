import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("doc_audit", os.path.join(HERE, "..", "..", "skills", "writing", "deslop", "scripts", "doc_audit.py"))
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
A.H.HOUSE = True  # the Arial check is a house rule


def para(text, font=None, style="NORMAL_TEXT"):
    ts = {"weightedFontFamily": {"fontFamily": font}} if font else {}
    return {"paragraph": {"paragraphStyle": {"namedStyleType": style}, "elements": [{"textRun": {"content": text, "textStyle": ts}}]}}


def doc(normal, *content):
    return {"namedStyles": {"styles": [{"namedStyleType": "NORMAL_TEXT", "textStyle": {"weightedFontFamily": {"fontFamily": normal}}}]},
            "body": {"content": list(content)}}


def test_doc_with_default_arial_is_flagged():
    _, fonts, _ = A.doc_read(doc("Arial", para("hello there")))
    assert fonts == {"Arial": 11}
    assert "Arial" in A.font_hits(fonts)[0][1]


def test_doc_with_no_font_set_counts_as_arial():
    d = {"namedStyles": {"styles": [{"namedStyleType": "NORMAL_TEXT", "textStyle": {}}]}, "body": {"content": [para("plain")]}}
    assert A.font_hits(A.doc_read(d)[1])


def test_doc_style_in_google_sans_passes():
    _, fonts, _ = A.doc_read(doc("Arial", para("hello", "Google Sans")))
    assert A.font_hits(fonts) == []


def test_table_cells_are_read():
    table = {"table": {"tableRows": [{"tableCells": [{"content": [para("in a cell", "Arial")]}]}]}}
    lines, fonts, cells = A.doc_read(doc("Google Sans", table))
    assert lines == ["in a cell"]
    assert cells == {"in a cell"}
    assert A.font_hits(fonts)


def test_slide_runs_are_counted():
    p = {"slides": [{"pageElements": [{"shape": {"text": {"textElements": [{"textRun": {"content": "Title", "style": {"fontFamily": "Arial"}}}]}}}]}]}
    assert A.slide_fonts(p) == {"Arial": 5}


def lists(**levels):
    return {"lists": {k: {"listProperties": {"nestingLevels": [v]}} for k, v in levels.items()}}


def test_html_import_dots_count_as_dots():
    assert A.has_dots(lists(a={"glyphType": "GLYPH_TYPE_UNSPECIFIED", "startNumber": 1}))
    assert A.has_dots(lists(a={"glyphSymbol": "●"}))


def test_numbered_list_is_not_dots():
    assert not A.has_dots(lists(a={"glyphType": "DECIMAL", "glyphFormat": "%0."}))
    assert not A.has_dots({})
