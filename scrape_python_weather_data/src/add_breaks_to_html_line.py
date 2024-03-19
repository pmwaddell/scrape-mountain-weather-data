result = ""

with open('new_table_dump.txt', 'r') as f:
    table = f.read()
    for c in table:
        if c == ">":
            result += ">" + "\n"
        else:
            result += c
    f.close()

x = open('new_table_dump_breaks.txt', 'w').write(result)
