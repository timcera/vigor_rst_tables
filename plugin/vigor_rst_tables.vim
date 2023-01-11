if !has('python3')
    echomsg 'You need python3 support to use this plugin'
    finish
endif

python3 from vigor_rst_tables import rst_tables

map ,,c :python3 rst_tables.create_table()<CR>
map ,,f :python3 rst_tables.reflow_table()<CR>
map ,,C :python3 rst_tables.create_table(header=False)<CR>
map ,,F :python3 rst_tables.reflow_table(header=False)<CR>
