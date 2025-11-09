import math

def equity_curve(prices, position=0.0):
    # 僅做簡單「隔日收盤報酬 × 部位」疊代的 equity 曲線
    eq=[1.0]
    for i in range(1, len(prices)):
        p0=prices[i-1]["close"]; p1=prices[i]["close"]
        ret = (p1/p0 - 1.0) * position
        eq.append(eq[-1]*(1.0+ret))
    return eq

def simple_stats(eq):
    if not eq: return {"final":1.0,"maxdd":0.0,"sharpe":0.0}
    final=eq[-1]
    # 近似日報酬
    rets=[(eq[i]/eq[i-1]-1.0) for i in range(1,len(eq))]
    if not rets: return {"final":final,"maxdd":0.0,"sharpe":0.0}
    # 最大回撤
    peak=eq[0]; maxdd=0.0
    for x in eq:
        peak=max(peak,x)
        maxdd=max(maxdd, (peak-x)/peak)
    # Sharpe（不年化、樣本 stdev）
    mu=sum(rets)/len(rets)
    sd=(sum((r-mu)**2 for r in rets)/max(1,len(rets)-1))**0.5
    sharpe = (mu/sd) if sd>1e-12 else 0.0
    return {"final":final,"maxdd":maxdd,"sharpe":sharpe}
