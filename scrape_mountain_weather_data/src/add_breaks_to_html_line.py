result = ""

with open('../data/2500_for_table.txt', 'r') as f:
    table = f.read()
    for c in table:
        if c == ">":
            result += ">" + "\n"
        else:
            result += c
    f.close()

x = open('../data/2500_breaks.txt', 'w').write(result)
