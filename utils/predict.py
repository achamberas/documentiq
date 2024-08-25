import os
import sys
import re
import json

import pandas as pd
import numpy as np
import dill
import scipy
import sklearn

# from sklearn import preprocessing
from datetime import datetime, timedelta

def predict(data, model, israndom, scenario={}, update_model=False):

    if len(data) == 0:
        data['prediction'] = None
        return data
    
    modelfile = open('models/' + model + '.pkl','rb')
    
    results = dill.load(modelfile)
    modelfile.close()
    
    model = results['model']
    model_type = results['model_type']
    stdev = results['stdev']
    features = results['features']
    columns = [f['name'] for f in features]
    
    # check for missing features in dataset
    x_cols = {'vc':data.columns}
    c = pd.DataFrame.from_dict(x_cols)
    f = pd.DataFrame.from_dict(features).reset_index(drop=True)

    if len(f) > 0:
        r = f.merge(c, how='left', left_on='name', right_on='vc')[['name', 'vc']]
        m = r['name'][r['vc'].isna()]
    
        if len(m) > 0:
            print('Missing features:')
            print(m)
            # return
    
    # X = pd.DataFrame(index=range(0, len(data)))
    ip = data.copy()
    X = pd.DataFrame(index=ip.index)
    
    # apply feature transformations
    for f in features:
        fname = f['name']
        
        for key in data.columns:
            if (re.match(key, fname) and data[key].dtypes == 'object') or key == fname:
                # transform date feature to dateparts
                if f['transform'] == 'dtimes':
                    test_date = pd.to_datetime(data[key], errors='coerce', infer_datetime_format=True)
                    if test_date.notna().any() \
                        and (re.match(r"datetime64(.*)", data[key].dtypes.name) \
                        or data[key].dtypes == 'object'):
                        data[key] = pd.to_datetime(data[key], errors='coerce', infer_datetime_format=True)
                        X[key] = data[key]
                        add_datepart(X, key, drop=True, prefix=key+'_')
                    
                # check if column is a string and generate dummy/ohe vars
                elif data[key].dtypes.name in ['object','category']:
                    for key_value in f['values']:
                        X = X.copy()
                        X[str(fname)+'_'+str(key_value)] = np.where(data[key].eq(key_value), 1, 0)
                        
                # standardize numeric if model does so
                elif data[key].dtypes in ['float64', 'int64', 'int8'] and f['transform'] == 'stdize':
                    min_x = f['min']
                    max_x = f['max']
                    X[key] = (data[[key]] - min_x) / max_x
                    #min_max_scaler = preprocessing.MinMaxScaler()
                    #X[key] = min_max_scaler.fit_transform(data[[key]])
                else:
                    X[key] = data[key]

    # run predictions
    if model_type == 'survival':

        period = results['period']
        surv = model.predict_survival_function(X, return_array=False)
        data['index'] = data.index
        
        # find max possible period
        data[period + '_max'] = np.asarray(model.event_times_).max()
        data[period + '_adj'] = data[[period, period + '_max']].min(axis=1).astype(int)
        
        data['prediction'] = data[[period + '_adj', 'index']].apply(lambda x: surv[x[1]](x[0]), axis=1)
        data = data.drop(columns=['index', period + '_max', period + '_adj'], axis=1)

        if israndom:
            data['randomuniform'] = np.random.uniform(0, 1, len(data))
            data['prediction'] = data[['prediction', 'randomuniform']].apply(lambda x: 1 if x[1] > x[0] else 0, axis=1)
            data = data.drop(columns=['randomuniform'], axis=1)

    elif model_type == 'classification':
        data['prediction'] = model.predict(X)
        if israndom:
            data['randomuniform'] = np.random.uniform(0, 1, len(data))
            data['prediction'] = data[['prediction', 'randomuniform']].apply(lambda x: 1 if x[1] > x[0] else 0, axis=1)
            data = data.drop(columns=['randomuniform'], axis=1)

    elif model_type == 'regression':
        data['prediction'] = model.predict(X)
        if israndom:
            data['prediction'] = data['prediction'] * (1 + np.random.normal(0, stdev, len(data)))

    elif model_type == 'simulation':
        model = dill.loads(model)
        m = model()
        data = m.simulation(scenario, data)
        
    elif model_type == '3pm api':
        model = dill.loads(model)
        m = model()
        data = m.score(data, features)
        
    return data
        
def make_date(df, date_field):
    "Make sure `df[date_field]` is of the right date type."
    field_dtype = df[date_field].dtype
    if isinstance(field_dtype, pd.core.dtypes.dtypes.DatetimeTZDtype):
        field_dtype = np.datetime64
    if not np.issubdtype(field_dtype, np.datetime64):
        df[date_field] = pd.to_datetime(df[date_field], infer_datetime_format=True)

def add_datepart(df, field_name, prefix=None, drop=True, time=False):
    "Helper function that adds columns relevant to a date in the column `field_name` of `df`."
    make_date(df, field_name)
    field = df[field_name]
    # prefix = ifnone(prefix, re.sub('[Dd]ate$', '', field_name))
    prefix = re.sub('[Dd]ate$', '', field_name) if not prefix else prefix
    attr = ['Year', 'Month', 'Week', 'Day', 'Dayofweek', 'Dayofyear', 'Is_month_end', 'Is_month_start',
            'Is_quarter_end', 'Is_quarter_start', 'Is_year_end', 'Is_year_start']
    if time: attr = attr + ['Hour', 'Minute', 'Second']
    # Pandas removed `dt.week` in v1.1.10
    week = field.dt.isocalendar().week.astype(field.dt.day.dtype) if hasattr(field.dt, 'isocalendar') else field.dt.week
    for n in attr: df[prefix + n] = getattr(field.dt, n.lower()) if n != 'Week' else week
    mask = ~field.isna()
    df[prefix + 'Elapsed'] = np.where(mask,field.values.astype(np.int64) // 10 ** 9,np.nan)
    if drop: df.drop(field_name, axis=1, inplace=True)
    return df
