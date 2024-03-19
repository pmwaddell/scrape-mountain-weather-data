result = ""

with open('np_forecast_table.txt', 'r') as f:
    table = f.read()
    for c in table:
        if c == ">":
            result += ">" + "\n"
        else:
            result += c
    f.close()

x = open('np_forecast_table_breaks.txt', 'w').write(result)
