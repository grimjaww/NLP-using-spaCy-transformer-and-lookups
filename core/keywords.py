NOT_ALPHA_NUMERIC = r'[^a-zA-Z\d]'
NUMBER = r'\d+'

MONTHS_SHORT = r'(jan)|(feb)|(mar)|(apr)|(may)|(jun)|(jul)|(aug)|(sep)|(oct)|(nov)|(dec)'
MONTHS_LONG = r'(january)|(february)|(march)|(april)|(may)|(june)|(july)|(august)|(september)|(october)|(november)|(december)'
MONTH = r'(' + MONTHS_SHORT + r'|' + MONTHS_LONG + r')'

YEAR = r'(((20|19)(\d{2})))'

NAME_PATTERN = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]

EDUCATION = ['BE', 'B.E.', 'B.E', 'BS', 'B.S', 'ME', 'M.E','M.E.', 'MS', 'M.S', 'BTECH', 'MTECH','SSC', 'HSC', 'CBSE', 'ICSE', 'X', 'XII']

SECTIONS = ['accomplishments','experience','education','interests','projects','professional experience','publications','skills','certifications','objective','career objective','summary','leadership']
