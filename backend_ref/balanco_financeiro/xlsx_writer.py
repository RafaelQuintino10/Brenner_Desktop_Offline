
"""Escritor XLSX pequeno usando apenas a biblioteca padrão.

Mantém os valores monetários como números nas células; fórmulas possuem
valor calculado em cache para programas que não recalculam imediatamente.
Textos provenientes de usuários sempre são inline strings, não fórmulas.
"""
from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO
import re
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
P = 'http://schemas.openxmlformats.org/package/2006/relationships'
C = 'http://schemas.openxmlformats.org/package/2006/content-types'


def tag(name):
    return f'{{{M}}}{name}'


def xml_bytes(root):
    # Usar namespace padrão evita problemas em leitores XLSX mais restritivos.
    result = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    return (result.replace(b'xmlns:ns0=', b'xmlns=', 1)
                  .replace(b'<ns0:', b'<')
                  .replace(b'</ns0:', b'</'))


def column_label(num):
    result = ''
    while num:
        num, idx = divmod(num - 1, 26)
        result = chr(65 + idx) + result
    return result


@dataclass(frozen=True)
class Money:
    value: object


@dataclass(frozen=True)
class Percent:
    value: object  # O percentual entra como 10 (dez por cento).


@dataclass(frozen=True)
class Formula:
    expression: str
    cached: object
    is_money: bool = True


def _clean(value):
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', str(value or ''))


def _write_cell(row_element, reference, raw, is_header=False):
    if raw is None:
        return

    attrs = {'r': reference}
    style = 1 if is_header else 0
    if isinstance(raw, Formula):
        attrs['s'] = '2' if raw.is_money else '0'
        cell = ET.SubElement(row_element, tag('c'), attrs)
        ET.SubElement(cell, tag('f')).text = raw.expression.lstrip('=')
        ET.SubElement(cell, tag('v')).text = str(raw.cached)
        return
    if isinstance(raw, Money):
        attrs['s'] = '2'
        raw = raw.value
    elif isinstance(raw, Percent):
        attrs['s'] = '3'
        raw = Decimal(str(raw.value)) / Decimal('100')
    elif is_header:
        attrs['s'] = '1'

    if isinstance(raw, (int, float, Decimal)) and not isinstance(raw, bool):
        cell = ET.SubElement(row_element, tag('c'), attrs)
        ET.SubElement(cell, tag('v')).text = str(raw)
    else:
        attrs['t'] = 'inlineStr'
        cell = ET.SubElement(row_element, tag('c'), attrs)
        inline = ET.SubElement(cell, tag('is'))
        text = ET.SubElement(inline, tag('t'))
        text.text = _clean(raw)
        if text.text and text.text[:1].isspace():
            text.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')


def _sheet_xml(rows, widths, autofilter=True):
    root = ET.Element(tag('worksheet'))
    ncols = max([len(row) for row in rows] or [1])
    nrows = max(1, len(rows))
    ET.SubElement(root, tag('dimension'), {'ref': f'A1:{column_label(ncols)}{nrows}'})
    views = ET.SubElement(root, tag('sheetViews'))
    view = ET.SubElement(views, tag('sheetView'), {'workbookViewId': '0', 'showGridLines': '0'})
    ET.SubElement(view, tag('pane'), {'ySplit': '1', 'topLeftCell': 'A2', 'activePane': 'bottomLeft', 'state': 'frozen'})
    ET.SubElement(root, tag('sheetFormatPr'), {'defaultRowHeight': '16'})
    cols = ET.SubElement(root, tag('cols'))
    for i in range(1, ncols + 1):
        ET.SubElement(cols, tag('col'), {
            'min': str(i), 'max': str(i),
            'width': str(widths[i - 1] if i <= len(widths) else 18), 'customWidth': '1',
        })
    body = ET.SubElement(root, tag('sheetData'))
    for r, values in enumerate(rows, 1):
        row_element = ET.SubElement(body, tag('row'), {'r': str(r), 'ht': '23' if r == 1 else '18', 'customHeight': '1'})
        for i, val in enumerate(values, 1):
            _write_cell(row_element, f'{column_label(i)}{r}', val, is_header=(r == 1))
    if autofilter and nrows > 1:
        ET.SubElement(root, tag('autoFilter'), {'ref': f'A1:{column_label(ncols)}{nrows}'})
    ET.SubElement(root, tag('pageMargins'), {'left': '0.3', 'right': '0.3', 'top': '0.5', 'bottom': '0.5', 'header': '0.2', 'footer': '0.2'})
    return xml_bytes(root)


def _styles_xml():
    style = ET.Element(tag('styleSheet'))
    formats = ET.SubElement(style, tag('numFmts'), {'count': '2'})
    ET.SubElement(formats, tag('numFmt'), {'numFmtId': '164', 'formatCode': '"R$" #,##0.00;[Red]("R$" #,##0.00)'})
    ET.SubElement(formats, tag('numFmt'), {'numFmtId': '165', 'formatCode': '0.00%'})
    fonts = ET.SubElement(style, tag('fonts'), {'count': '2'})
    standard = ET.SubElement(fonts, tag('font'))
    ET.SubElement(standard, tag('sz'), {'val': '10'})
    ET.SubElement(standard, tag('name'), {'val': 'Aptos'})
    bold = ET.SubElement(fonts, tag('font'))
    ET.SubElement(bold, tag('b'))
    ET.SubElement(bold, tag('sz'), {'val': '10'})
    ET.SubElement(bold, tag('color'), {'rgb': 'FFFFFFFF'})
    ET.SubElement(bold, tag('name'), {'val': 'Aptos'})
    fills = ET.SubElement(style, tag('fills'), {'count': '3'})
    ET.SubElement(ET.SubElement(fills, tag('fill')), tag('patternFill'), {'patternType': 'none'})
    ET.SubElement(ET.SubElement(fills, tag('fill')), tag('patternFill'), {'patternType': 'gray125'})
    gold = ET.SubElement(ET.SubElement(fills, tag('fill')), tag('patternFill'), {'patternType': 'solid'})
    ET.SubElement(gold, tag('fgColor'), {'rgb': 'FF332719'})
    ET.SubElement(gold, tag('bgColor'), {'indexed': '64'})
    borders = ET.SubElement(style, tag('borders'), {'count': '1'})
    border = ET.SubElement(borders, tag('border'))
    for side in ['left', 'right', 'top', 'bottom', 'diagonal']:
        ET.SubElement(border, tag(side))
    cell_style_xfs = ET.SubElement(style, tag('cellStyleXfs'), {'count': '1'})
    ET.SubElement(cell_style_xfs, tag('xf'), {'numFmtId': '0', 'fontId': '0', 'fillId': '0', 'borderId': '0'})
    cell_xfs = ET.SubElement(style, tag('cellXfs'), {'count': '4'})
    for num_fmt, font, fill in [(0, 0, 0), (0, 1, 2), (164, 0, 0), (165, 0, 0)]:
        ET.SubElement(cell_xfs, tag('xf'), {
            'numFmtId': str(num_fmt), 'fontId': str(font),
            'fillId': str(fill), 'borderId': '0', 'xfId': '0',
            'applyNumberFormat': '1' if num_fmt else '0',
            'applyFill': '1' if fill else '0',
        })
    cell_styles = ET.SubElement(style, tag('cellStyles'), {'count': '1'})
    ET.SubElement(cell_styles, tag('cellStyle'), {'name': 'Normal', 'xfId': '0', 'builtinId': '0'})
    return xml_bytes(style)


def workbook_bytes(sheets):
    """sheets: [(nome_da_aba, rows, widths, autofilter), ...]"""
    workbook = ET.Element(tag('workbook'), {f'{{{R}}}dummy': ''})
    workbook.attrib.pop(f'{{{R}}}dummy')  # Garante namespace r ao serializar os ids.
    sheets_node = ET.SubElement(workbook, tag('sheets'))
    relations = ET.Element(f'{{{P}}}Relationships')
    content = ET.Element(f'{{{C}}}Types')
    ET.SubElement(content, f'{{{C}}}Default', {'Extension': 'rels', 'ContentType': 'application/vnd.openxmlformats-package.relationships+xml'})
    ET.SubElement(content, f'{{{C}}}Default', {'Extension': 'xml', 'ContentType': 'application/xml'})
    ET.SubElement(content, f'{{{C}}}Override', {'PartName': '/xl/workbook.xml', 'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'})
    ET.SubElement(content, f'{{{C}}}Override', {'PartName': '/xl/styles.xml', 'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml'})

    for i, (name, _rows, _widths, _filter) in enumerate(sheets, 1):
        if len(name) > 31:
            raise ValueError('Nome de aba com mais de 31 caracteres.')
        ET.SubElement(sheets_node, tag('sheet'), {'name': name, 'sheetId': str(i), f'{{{R}}}id': f'rId{i}'})
        ET.SubElement(relations, f'{{{P}}}Relationship', {
            'Id': f'rId{i}', 'Type': f'{R}/worksheet', 'Target': f'worksheets/sheet{i}.xml',
        })
        ET.SubElement(content, f'{{{C}}}Override', {
            'PartName': f'/xl/worksheets/sheet{i}.xml',
            'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml',
        })
    ET.SubElement(workbook, tag('calcPr'), {'calcId': '191029', 'fullCalcOnLoad': '1'})
    ET.SubElement(relations, f'{{{P}}}Relationship', {
        'Id': f'rId{len(sheets)+1}', 'Type': f'{R}/styles', 'Target': 'styles.xml',
    })
    root_rel = ET.Element(f'{{{P}}}Relationships')
    ET.SubElement(root_rel, f'{{{P}}}Relationship', {
        'Id': 'rId1', 'Type': f'{R}/officeDocument', 'Target': 'xl/workbook.xml',
    })

    output = BytesIO()
    with ZipFile(output, 'w', compression=ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', xml_bytes(content))
        archive.writestr('_rels/.rels', xml_bytes(root_rel))
        archive.writestr('xl/workbook.xml', xml_bytes(workbook))
        archive.writestr('xl/_rels/workbook.xml.rels', xml_bytes(relations))
        archive.writestr('xl/styles.xml', _styles_xml())
        for i, (_name, rows, widths, autofilter) in enumerate(sheets, 1):
            archive.writestr(f'xl/worksheets/sheet{i}.xml', _sheet_xml(rows, widths, autofilter))
    return output.getvalue()
