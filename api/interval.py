class Interval:
    day = 'P1D',
    week = 'P1W',
    month = 'P1M',
    three_months = 'P3M',
    six_months = 'P6M',
    year = 'P1Y',
    three_years = 'P3Y',
    five_years = 'P5Y',
    all = 'P50Y'

    def __repr__(self):
        return str([key for key in Interval.__dict__.keys() if not (key.startswith('__') or key.endswith('__'))])
