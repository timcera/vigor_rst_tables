
Heavily refactored code primarily from philpep/vim-rst-tables, which is also
based on nvie/vim-rst-tables.  Many forks of nvie/vim-rst-tables exist.

It is a modification of the standard RST-Table vim plugin plus following features:

    1. Support only for Python 3
    2. fix column width containing Chinese and other double wide characters

-------------------------------------------------------------

This plugin allows to create and edit restructuredText tables easily.

Its adds two new commands:

    ,,c  ->  Creates a new restructuredText table with headers.
    ,,f  ->  Fix table columns in a table with headers.

For example, if you have a paragraph with data like this:

    nombre      apellido    edad
    pepe        zarate      28
    toto        garcia      29

you can press ",,c" to create a simple table:

    +--------+----------+------+
    | nombre | apellido | edad |
    +========+==========+======+
    | pepe   | zarate   | 28   |
    +--------+----------+------+
    | toto   | garcia   | 29   |
    +--------+----------+------+


Now, if you change the table content, for example adding characters
to the first content row.

    +--------+----------+------+
    | nombre | apellido | edad |
    +========+==========+======+
    | Un nombre muy largo que rompe la tabla   | zarate   | 28   |
    +--------+----------+------+
    | toto   | un appellido largo...   | 29   |
    +--------+----------+------+

you need to fix the columns widths. So, press ",,f" and you will gets:

    +----------------------------------------+-----------------------+------+
    | nombre                                 | apellido              | edad |
    +========================================+=======================+======+
    | Un nombre muy largo que rompe la tabla | zarate                | 28   |
    +----------------------------------------+-----------------------+------+
    | toto                                   | un appellido largo... | 29   |
    +----------------------------------------+-----------------------+------+
