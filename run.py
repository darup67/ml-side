import json, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor
raw = json.load(open('daily.json'))
rows, stats = [], {}
for tk in ['MNQ=F', 'MES=F']:
    d = pd.DataFrame(raw[tk], columns=['d','o','h','l','c']); d['d'] = pd.to_datetime(d['d'])
    d = d[d['d'] >= d['d'].max() - pd.DateOffset(years=3)].reset_index(drop=True)
    name = tk[:3]
    tg = {'up': d.h - d.o, 'down': d.o - d.l, 'range': d.h - d.l}
    for k, s in tg.items():
        stats[(name, k)] = s
        for i, v in enumerate(s):
            rows.append((f'{name}_{k}', pd.Timestamp('2023-01-01') + pd.Timedelta(days=i), float(v)))
df = pd.DataFrame(rows, columns=['item_id','timestamp','target'])
ts = TimeSeriesDataFrame.from_data_frame(df, id_column='item_id', timestamp_column='timestamp')
H, HOLD = 5, 60
n = len(stats[('MNQ','up')])
cut = n - HOLD
def upto(m):  # series truncated to first m observations
    return ts.slice_by_timestep(0, m)
pred = TimeSeriesPredictor(prediction_length=H, target='target', eval_metric='MAE', path='ag_models', verbosity=1)
pred.fit(upto(cut), hyperparameters={'Chronos2': {}, 'Chronos': {'model_path': 'bolt_small'}, 'SeasonalNaive': {}, 'ETS': {}, 'Theta': {}, 'DirectTabular': {}}, time_limit=900, enable_ensemble=True)
print(pred.leaderboard(upto(n), silent=True)[['model','score_test','score_val','fit_time_marginal']])
# rolling backtest over the holdout: 12 windows of 5 days, models not refit
errs = {}
for w in range(0, HOLD - H + 1, H):
    m = cut + w
    f = pred.predict(upto(m), model=None)
    act = ts.slice_by_timestep(m, m + H)
    for it in f.item_ids:
        e = np.abs(f.loc[it]['mean'].values - act.loc[it]['target'].values)
        errs.setdefault(it, []).append(e.mean())
    for mname in ['Chronos2', 'Chronos[bolt_small]', 'SeasonalNaive', 'ETS', 'Theta', 'DirectTabular']:
        try:
            g = pred.predict(upto(m), model=mname)
            for it in g.item_ids:
                e = np.abs(g.loc[it]['mean'].values - act.loc[it]['target'].values).mean()
                errs.setdefault((it, mname), []).append(e)
        except Exception as ex:
            errs.setdefault(('ERR', mname), [str(ex)[:80]])
    # naive baselines
    for it in f.item_ids:
        hist = upto(m).loc[it]['target'].values; a = act.loc[it]['target'].values
        errs.setdefault((it, 'mean3y'), []).append(np.abs(hist.mean() - a).mean())
        errs.setdefault((it, 'mean20d'), []).append(np.abs(hist[-20:].mean() - a).mean())
out = {}
for k, v in errs.items():
    if isinstance(k, tuple): out[f'{k[0]}|{k[1]}'] = float(np.mean(v)) if not isinstance(v[0], str) else v[0]
    else: out[f'{k}|ENSEMBLE(best)'] = float(np.mean(v))
json.dump(out, open('backtest.json', 'w'), indent=1)
final = pred.predict(ts)
res = {}
for it in final.item_ids: res[it] = final.loc[it]['mean'].values.round(1).tolist()
json.dump({'avg3y': {f'{a}_{b}': float(s.mean()) for (a, b), s in stats.items()}, 'last20': {f'{a}_{b}': float(s.tail(20).mean()) for (a, b), s in stats.items()}, 'forecast5d': res, 'days': n}, open('forecast.json', 'w'), indent=1)
print('done')
