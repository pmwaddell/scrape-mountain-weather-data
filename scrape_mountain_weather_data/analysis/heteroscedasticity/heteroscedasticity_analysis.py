import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.compat import lzip
import statsmodels.stats.api as sms


df = pd.read_csv('avg_snow_diff_v_time_diff_k2_6000m_may2024.csv')

# Fit regression model.
fit = smf.ols('avg_snow_diff ~ time_diff', data=df).fit()
print(fit.summary())

# Conduct the Breusch-Pagan test.
names = ['Lagrange multiplier statistic', 'p-value', 'f-value', 'f p-value']

# Get the test result:
test_result = sms.het_breuschpagan(fit.resid, fit.model.exog)
print('Breusch-Pagan test results:')
print(lzip(names, test_result))
