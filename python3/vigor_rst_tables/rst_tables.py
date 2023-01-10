import re
import textwrap
from unicodedata import east_asian_width

import vim


def buffer_encoding():
    return vim.eval("&enc")


def get_table_bounds():
    row, _ = vim.current.window.cursor
    upper = lower = row
    try:
        while vim.current.buffer[upper - 1].strip():
            upper -= 1
    except IndexError:
        pass
    else:
        upper += 1

    try:
        while vim.current.buffer[lower - 1].strip():
            lower += 1
    except IndexError:
        pass
    else:
        lower -= 1

    return (upper, lower)


def join_rows(rows, sep="\n"):
    """Given a list of rows (a list of lists) this function returns a
    flattened list where each the individual columns of all rows are joined
    together using the line separator.

    """
    output = []
    for row in rows:
        # grow output array, if necessary
        if len(output) <= len(row):
            for i in range(len(row) - len(output)):
                output.extend([[]])

        for i, field in enumerate(row):
            field_text = field.strip()
            if field_text:
                output[i].append(field_text)
    return [sep.join(lines) for lines in output]


def line_is_separator(line):
    return re.match("^[\t +=-]+$", line)


def has_line_seps(raw_lines):
    for line in raw_lines:
        if line_is_separator(line):
            return True
    return False


def partition_raw_lines(raw_lines):
    """Partitions a list of raw input lines so that between each partition, a
    table row separator can be placed.

    """
    if not has_line_seps(raw_lines):
        return [[x] for x in raw_lines]

    curr_part = []
    parts = [curr_part]
    for line in raw_lines:
        if line_is_separator(line):
            curr_part = []
            parts.append(curr_part)
        else:
            curr_part.append(line)

    # remove any empty partitions (typically the first and last ones)
    return filter(lambda x: x != [], parts)


def unify_table(table):
    """Given a list of rows (i.e. a table), this function returns a new table
    in which all rows have an equal amount of columns.  If all full column is
    empty (i.e. all rows have that field empty), the column is removed.

    """
    max_fields = max(len(row) for row in table)
    empty_cols = [True] * max_fields
    output = []
    for row in table:
        curr_len = len(row)
        if curr_len < max_fields:
            row += [""] * (max_fields - curr_len)
        output.append(row)

        # register empty columns (to be removed at the end)
        for index, row_text in enumerate(row):
            if row_text.strip():
                empty_cols[index] = False

    # remove empty columns from all rows
    table = output
    output = []
    for row in table:
        cols = []
        for index, row_text in enumerate(row):
            should_remove = empty_cols[index]
            if not should_remove:
                cols.append(row_text)
        output.append(cols)

    return output


def split_table_row(row_string):
    if row_string.find("|") >= 0:
        # first, strip off the outer table drawings
        row_string = re.sub(r"^\s*\||\|\s*$", "", row_string)
        return re.split(r"\s*\|\s*", row_string.strip())
    return re.split(r"\s\s+", row_string.rstrip())


def parse_table(raw_lines):
    row_partition = partition_raw_lines(raw_lines)
    lines = [
        join_rows([split_table_row(cell) for cell in row_string])
        for row_string in row_partition
    ]
    return unify_table(lines)


def table_line(widths, header=False):
    if header:
        linechar = "="
    else:
        linechar = "-"
    sep = "+"
    parts = []
    for width in widths:
        parts.append(linechar * width)
    if parts:
        parts = [""] + parts + [""]
    return sep.join(parts)


def str_width(unicode_text):
    """calc string width, support cjk characters."""
    return sum(1 + (east_asian_width(c) in "WF") for c in unicode_text)


def get_field_width(field_text):
    field_text = field_text.decode(buffer_encoding())
    return max(str_width(s) for s in field_text.split("\n"))


def split_row_into_lines(row):
    row = [field.split("\n") for field in row]
    height = max(len(field_lines) for field_lines in row)
    turn_table = []
    for i in range(height):
        fields = []
        for field_lines in row:
            if i < len(field_lines):
                fields.append(field_lines[i])
            else:
                fields.append("")
        turn_table.append(fields)
    return turn_table


def get_column_widths(table):
    widths = []
    for row in table:
        num_fields = len(row)
        # dynamically grow
        if num_fields >= len(widths):
            widths.extend([0] * (num_fields - len(widths)))
        for i in range(num_fields):
            field_width = get_field_width(row[i])
            widths[i] = max(widths[i], field_width)
    return widths


def get_column_widths_from_border_spec(part):
    border = None
    for row in part:
        if line_is_separator(row):
            border = row.strip()
            break

    if border is None:
        raise RuntimeError("Cannot reflow this table. Top table border not found.")

    left = right = None
    if border[0] == "+":
        left = 1
    if border[-1] == "+":
        right = -1
    return [max(0, len(drawing) - 2) for drawing in border[left:right].split("+")]


def pad_fields(row, widths):
    """Pads fields of the given row, so each field lines up nicely with the
    others.
    """

    # Pad all fields using the calculated widths
    new_row = []
    for index, row_text in enumerate(row):
        unicode_len = str_width(row_text.decode(buffer_encoding()))
        col = " " + row_text + " " * int(widths[index] - unicode_len + 1)
        new_row.append(col)
    return new_row


def wrap_text(text, width):
    """wrap text, support cjk characters."""
    text = text.decode(buffer_encoding())
    lines = []
    while len(text) > 0:
        wide = width
        # check 1st string, if too wide, then guess again;
        guess = textwrap.wrap(text, wide)[0]
        while str_width(guess) > width:
            wide -= (str_width(guess) - width + 1) / 2
            guess = textwrap.wrap(text, wide)[0]
        lines.append(guess.encode(buffer_encoding()))
        text = text[len(guess) :].strip()
    return lines


def reflow_row_contents(row, widths):
    new_row = []
    for i, field in enumerate(row):
        wrapped_lines = wrap_text(field.replace("\n", " "), widths[i])
        new_row.append("\n".join(wrapped_lines))
    return new_row


def draw_table(table, manual_widths=None):
    if table == []:
        return []

    if manual_widths is None:
        col_widths = get_column_widths(table)
    else:
        col_widths = manual_widths
        new_widths = get_column_widths(table)
        if len(new_widths) > len(col_widths):
            col_widths += new_widths[len(col_widths) :]

    # Reserve room for the spaces
    sep_col_widths = [x + 2 for x in col_widths]
    header_line = table_line(sep_col_widths, header=True)
    normal_line = table_line(sep_col_widths)

    output = [normal_line]
    first = True
    for row in table:

        if manual_widths:
            row = reflow_row_contents(row, manual_widths)

        row_lines = split_row_into_lines(row)

        # draw the lines (num_lines) for this row
        for row_line in row_lines:
            row_line = pad_fields(row_line, col_widths)
            output.append("|".join([""] + row_line + [""]))

        # then, draw the separator
        if first:
            output.append(header_line)
            first = False
        else:
            output.append(normal_line)

    return output


def get_indent(line):
    return line[0 : len(line) - len(line.lstrip())]


def apply_indent(table, indent):
    return [indent + row for row in table]


def create_table(header=True):
    upper, lower = get_table_bounds()
    part = vim.current.buffer[upper - 1 : lower]
    indent = get_indent(part[0])
    table = parse_table(part)
    part = draw_table(table)
    vim.current.buffer[upper - 1 : lower] = apply_indent(part, indent)


def reflow_table(header=True):
    upper, lower = get_table_bounds()
    part = vim.current.buffer[upper - 1 : lower]
    indent = get_indent(part[0])
    table = parse_table(part)
    widths = get_column_widths_from_border_spec(part)
    table = parse_table(part)
    part = draw_table(table, widths)
    vim.current.buffer[upper - 1 : lower] = apply_indent(part, indent)
