import json, random
ST = ["体","力","技","速","知","心","運","魅","火","水","風","土"]
TR = {"剛腕":("力",10),"俊足":("速",10),"霊眼":("知",10),"頑健":("体",10),"強運":("運",10),"胆力":("心",10),"器用":("技",10),"麗質":("魅",10),"長命":None,"病弱":None,"臆病":None}
POOL = list(TR) + ["赤髪","銀髪","金の瞳","泣きぼくろ","左利き","大柄","小柄"]
RISK = {"近場":(80,.03,40),"遠征":(250,.10,80),"決戦":(400,.22,140)}
PLACES = ["朽葉寺","千鳥居の参道","霧沼","鬼火の原","白砂の浜","狐塚","鉄錆の坑道","月見の塔"]

def eff(p, k):
    i = ST.index(k); v = p["g"][i] + p["x"][i]
    for t in p["t"]:
        if TR.get(t) and TR[t][0] == k: v += TR[t][1]
    return v

def season(n): return f"{(n-1)//4+1}年{'春夏秋冬'[(n-1)%4]}" if n >= 1 else "開始前"

def P(S, n):
    for p in S["p"]:
        if p["n"] == n and p["d"] is None: return p
    raise ValueError("存命の一族にいない: "+n)

def offers(S):
    o = []
    for r in ("近場","遠征","決戦"):
        o.append({"r": r, "at": random.choice(PLACES) + ("の主" if r == "決戦" else ""), "need": random.sample(ST[:7], 2), "weak": random.choice(ST[8:])})
    S["o"] = o

def die(S, p, why, R):
    p["d"] = S["turn"]; p["why"] = why
    R.append(f"[GM] {p['n']}が{why}。遺言と形見の行き先を決めること" + (f"(形見:{','.join(p['k'])})" if p["k"] else ""))

def child(S, par, god, R):
    g = []; note = []
    for i, k in enumerate(ST):
        v = (par["g"][i] + god["g"][i])/2 + random.randint(-8, 12)
        gp = [q for q in S["p"] if q["id"] in par["par"] and q["gen"] > 0]
        if gp and random.random() < 0.10:
            src = random.choice(gp); v = src["g"][i]; note.append(f"{k}が隔世遺伝({src['n']})")
        g.append(max(0, min(100, round(v))))
    if random.random() < 0.05:
        i = random.randrange(12); g[i] = min(100, g[i] + random.randint(20, 40)); note.append(f"突然変異で{ST[i]}が跳ねた")
    t, h = [], []
    for x in par["t"] + god["t"]:
        if random.random() < 0.5: (t if random.random() < 0.6 else h).append(x)
    for x in par["h"] + god["h"]:
        if random.random() < 0.5:
            if x in par["h"] and x in god["h"] and random.random() < 0.4: t.append(x); note.append(f"潜性の「{x}」が表に出た")
            else: h.append(x)
    if random.random() < 0.03: x = random.choice(POOL); t.append(x); note.append(f"新しい特性「{x}」が生まれた")
    t = list(dict.fromkeys(t)); h = [x for x in dict.fromkeys(h) if x not in t]
    if len(t) > 3: note.append(f"[GM] 顕性が4つ以上：{t} からプレイヤーに3つ選ばせ、残りは潜性へ")
    life = random.randint(7, 9) + ("長命" in t) - ("病弱" in t)
    S["id"] += 1
    c = {"id": S["id"], "n": f"未命名{S['id']}", "gen": par["gen"]+1, "par": [par["id"]], "god": god["n"], "b": S["turn"], "d": None, "why": "",
         "g": g, "x": [0]*12, "t": t, "h": h, "life": life, "k": [], "w": ""}
    S["p"].append(c)
    cmp = " ".join(f"{k}{par['g'][i]}→{g[i]}←{god['g'][i]}" for i, k in enumerate(ST))
    R.append(f"誕生: {c['n']}({par['n']}×{god['n']}) {cmp} 特性:{'・'.join(t) or 'なし'}" + (" / " + " / ".join(note) if note else ""))

def turn(S, A):
    R = []; alive = [p for p in S["p"] if p["d"] is None]
    for c in S.pop("due", []):
        child(S, next(p for p in S["p"] if p["id"] == c[0]), S["gods"][c[1]], R)
    busy = set()
    q = A.get("討伐")
    if q and q.get("隊"):
        o = S["o"][q["先"]]; base, dr, pt = RISK[o["r"]]; team = [P(S, n) for n in q["隊"][:4]]
        if any(S["turn"] - p["b"] < 1 for p in team): raise ValueError("生まれたばかりの子は出陣できない")
        busy |= {p["n"] for p in team}
        pw = sum(eff(p, o["need"][0]) + eff(p, o["need"][1]) + 0.5*eff(p, o["weak"]) for p in team)
        pw *= (0.9 if any("臆病" in p["t"] for p in team) else 1) * random.uniform(0.8, 1.2)
        D = base * (1 + 0.3*S["tier"]); win = pw >= D
        R.append(f"討伐({o['at']}・{o['r']}): {'勝利' if win else '敗北'} 戦力{pw:.0f}/必要{D:.0f}")
        for p in team:
            pd = dr * (0.5 if win else 1.5) * max(0.2, 1 - (eff(p, "体") + eff(p, "運"))/300)
            if random.random() < min(0.6, pd): die(S, p, f"{o['at']}で戦死", R); continue
            for k in o["need"]:
                i = ST.index(k); p["x"][i] = min(p["g"][i]//2, p["x"][i] + random.randint(0, 3))
        got = round(pt * (1 + 0.2*S["tier"]) * (1 if win else 0.3)); S["pt"] += got; R.append(f"奉納点+{got}")
        if win and random.random() < 0.2: R.append("[GM] 形見になる品を1つ手に入れた。名前を決めて誰かの形見(k)に加えること")
        if win and o["r"] == "決戦": S["tier"] += 1; R.append("[GM] 大鬼を討った。新しい神を1柱作って「新神」で追加すること")
    for n, gi in A.get("交神", []):
        p = P(S, n); g = S["gods"][gi]; cost = round(g["pt"] * (1 - eff(p, "魅")/400))
        if n in busy or S["turn"] - p["b"] < 1: R.append(f"{n}は交神できない"); continue
        if cost > S["pt"]: R.append(f"奉納点が足りない({g['n']}:{cost})"); continue
        S["pt"] -= cost; S.setdefault("due", []).append([p["id"], gi]); busy.add(n); R.append(f"交神: {n}×{g['n']}(-{cost})")
    for p in [p for p in S["p"] if p["d"] is None and p["n"] not in busy]:
        ks = A.get("修行", {}).get(p["n"]) or sorted(ST, key=lambda k: -p["g"][ST.index(k)])[:2]
        for k in ks:
            i = ST.index(k); p["x"][i] = min(p["g"][i]//2, p["x"][i] + random.randint(1, 5))
    S["turn"] += 1
    for p in [p for p in S["p"] if p["d"] is None]:
        age = S["turn"] - p["b"]
        if age > p["life"]: die(S, p, "寿命で亡くなった", R)
        elif age == p["life"]: R.append(f"[GM] {p['n']}に衰えの兆し")
    if not any(p["d"] is None for p in S["p"]) and not S.get("due"): R.append("[GM] 一族は絶えた。終わりの処理をすること")
    offers(S)
    return R

def row(p, S):
    top = sorted(range(12), key=lambda i: -p["g"][i])[:3]
    s = " ".join(f"{ST[i]}{p['g'][i]}" for i in top)
    life = f"{season(p['b'])}〜" + (season(p["d"]) if p["d"] is not None else "(存命)")
    return f"{'★' if S['head'] == p['id'] else ''}{p['n']} [{s}|{'・'.join(p['t']) or '-'}] {life}" + (f" ×神:{p['god']}" if p.get("god") else "") + (f" ※形見:{','.join(p['k'])}" if p["k"] else "") + (f" 「{p['w']}」" if p["w"] else "") + (f" {p['why']}" if "戦死" in p["why"] else "")

def tree(S):
    kids = {}
    for p in S["p"]:
        kids.setdefault(p["par"][0] if p["par"] else None, []).append(p)
    out = []
    def walk(p, pre, last):
        out.append(pre + ("└─ " if last else "├─ ") + f"{p['gen']}代 " + row(p, S))
        ch = kids.get(p["id"], [])
        for i, c in enumerate(ch): walk(c, pre + ("    " if last else "│   "), i == len(ch)-1)
    roots = kids.get(None, [])
    for i, r in enumerate(roots): walk(r, "", i == len(roots)-1)
    print("\n".join(out))

def show(S, R):
    print(f"【{season(S['turn'])}】 奉納点:{S['pt']}  大鬼撃破:{S['tier']}")
    print("出来事: " + (" / ".join(R) if R else "特になし"))
    for p in S["p"]:
        if p["d"] is None:
            print(f"{'★' if S['head'] == p['id'] else ' '}{p['n']}({p['gen']}代) {S['turn']-p['b']}季目 {'・'.join(p['t']) or '-'}" + (f" 形見:{','.join(p['k'])}" if p["k"] else ""))
            print("   " + " ".join(f"{k}{p['g'][i]}" + (f"(+{p['x'][i]})" if p["x"][i] else "") for i, k in enumerate(ST)))
    for i, o in enumerate(S["o"]): print(f"討伐{i}: {o['at']}({o['r']}) 求:{'・'.join(o['need'])} 弱点:{o['weak']}")
    print("神: " + " / ".join(f"{i}:{g['n']}({g['pt']})" for i, g in enumerate(S["gods"])))

def run(S, A):
    for k, v in A.get("名前", {}).items():
        for p in S["p"]:
            if p["n"] == k: p["n"] = v
    for n, w in A.get("遺言", {}).items():
        next(p for p in S["p"] if p["n"] == n)["w"] = w
    for n, items in A.get("形見", {}).items(): P(S, n)["k"] += items
    if A.get("当主"): S["head"] = P(S, A["当主"])["id"]
    for g in A.get("新神", []): S["gods"].append(g)
    R = turn(S, A) if A.get("進む", True) else []
    for p in S["p"]:
        if p["d"] is not None and p["w"]:
            for k in ("x", "h", "life"): p.pop(k, None)
    show(S, R)
    if A.get("家系図") or any("誕生" in r for r in R): tree(S)
    print("STATE=" + json.dumps(S, ensure_ascii=False, separators=(",", ":")))

def new_game(names, gods):
    S = {"turn": 1, "pt": 100, "tier": 0, "id": 1, "head": 2, "o": [], "gods": [],
         "p": [{"id": 1, "n": "始祖", "gen": 0, "par": [], "god": "", "b": -8, "d": 0, "why": "鬼に敗れた", "g": [50]*12, "t": [], "k": [], "w": "この恨み、子らに託す"}]}
    for n in names:
        S["id"] += 1
        S["p"].append({"id": S["id"], "n": n, "gen": 1, "par": [1], "god": "", "b": 0, "d": None, "why": "",
                       "g": [random.randint(20, 60) for _ in ST], "x": [0]*12, "t": [random.choice(POOL)], "h": [random.choice(POOL)],
                       "life": random.randint(7, 9), "k": [], "w": ""})
    for n in gods:
        sp = random.sample(range(12), 3)
        g = [random.randint(55, 85) if i in sp else random.randint(15, 45) for i in range(12)]
        S["gods"].append({"n": n, "g": g, "t": random.sample(POOL, random.randint(1, 2)), "h": [random.choice(POOL)], "pt": round(sum(g)*0.1)})
    offers(S)
    return S
