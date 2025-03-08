import pandas as pd

def statistics(selected):
        non_duct = len(selected[selected['Heat Type'].isin(['🔴  Hot Air-no Duc', '🔴  Hot Water'])])
        total_properties = int(selected['living_area'].count())
        total_living_area = int(selected['living_area'].sum())

        return non_duct, total_properties, total_living_area

def hvac_sizes(tons):
    # calculates the number and size of hvacs needed to meet capacity need in tons
    rt = tons
    c = 6
    s = []
    while rt > 0 and c > 2:
        if rt - c < 0:
            c = c - 1
        else:
            rt = rt - c
            s.append(c)

    if rt > 0:
        s.append(3)

    return s

def tons_hvac(sa, ch, o, ed, w):
    """
    https://www.indeed.com/career-advice/career-development/manual-j-calculation

    (House surface in square feet) x (height of the ceiling) = 8
    (Number of occupants) x 100 BTU = 1 per 500 SF
    (Number of exterior doors) x 1,000 BTU 1 per 500 SF
    (Number of windows) x 1,000 BTU 1 per 100 SF

    HVAC Tons = BTU/12000
    """

    btu = sa * ch + 100 * o + 1000 * ed + 1000 * w
    hvac_tons = btu / 12000

    return hvac_tons


def borehole_length(hvacs, fh):

    """
    Borehold Length
    L = [HCD x (COPD - 1) / COPD x (RB + RG x FH)] / [TG - (EWTmin + LWTmin) / 2]
    HCD is the heat pump heating capacity at design heating conditions in Btu/hr. This is a property of the heat pump and defined by the manufacturer.
    COPD is the coefficient of performance at design heating conditions. This is also a property of the heat pump and defined by the manufacturer.
    RB is the borehole thermal resistance, in hr ft F/Btu. This is calculated using the dimensions and the thermal resistance of the material the ground loop itself is made out of, as well as the thermal resistance of the grout used.
    RG is the steady-state thermal resistance of the ground surrounding the borehole. Dandelion calculates this by using data on ground thermal resistance from thousands of installations throughout the U.S. as well as publicly available geological data.
    FH is the run fraction in heating mode during the heating design month (January). This metric refers to the proportion of time the heat pump operates in heating mode during the coldest month of the year.
    TG is the average ground temperature along the borehole length. Dandelion uses publicly available geological data to determine this value (temperature is relatively consistent throughout the entire depth of the borehole).
    EWTmin is the minimum entering water temperature at heating design conditions, in degrees F. We use 30F for EWTmin.
    LWTmin is the minimum leaving water temperature at heating design conditions, in degrees F. This value is calculated using the performance tables provided by the heat pump manufacturer.
    """

    hps = pd.read_csv('data/heat_pump_specs.csv')
    df = hps[hps['Load'].eq('Full')].set_index('Size (Tons)')
    # 'dict', 'list', 'series', 'index'
    specs = df.to_dict(orient='index')

    borehole_length = 0

    for h in hvacs:
        hcd = specs[h]['Heating Capacity (BTU/HR)']
        copd = specs[h]['COP']

        rb = 0.2
        rg = 0.3
        tg = 55
        ewt_min = 30
        lwt_min = 10

        l = (hcd * (copd - 1) / copd * (rb + rg * fh)) / (tg - (ewt_min + lwt_min) / 2)
        borehole_length = borehole_length + l

    return int(borehole_length)

def eui(selected):
    # calculate the energy use index (EUI)
    return 1