import os

import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.compat import lzip
import statsmodels.stats.api as sms


result = ""
for filename in os.listdir(os.getcwd()):
    if filename[-4:] != '.csv':
        continue

    result += filename + '\n'
    df = pd.read_csv(filename)

    # Fit regression model.
    fit = smf.ols('y ~ x', data=df).fit()
    result += str(fit.summary()) + '\n\n'

    # Conduct the Breusch-Pagan test.
    names = ['Lagrange multiplier statistic', 'p-value', 'f-value', 'f p-value']

    # Get the test result:
    test_result = sms.het_breuschpagan(fit.resid, fit.model.exog)
    result += 'Breusch-Pagan test results:' + str(lzip(names, test_result))
    result += '\n\n\n\n\n'

with open("heteroscedasticity_analysis_results.txt", "w") as file:
    file.write(result)
