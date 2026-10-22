import json, random, math, datetime as dt
SUBJ = ["国語","数学","理科","社会","英語"]
ST = SUBJ + ["体力","運動","芸術","雑学","話術","清潔感","ファッション","部活"]
PLACE = {"公園":0,"図書館":0,"神社":0,"喫茶店":1500,"カラオケ":2500,"映画館":3000,"ショッピング":3000,"海":3000,"夏祭り":3000,"動物園":3000,"水族館":4000,"遊園地":7000}
JOB = {"コンビニ":(3000,8000,None,0),"引っ越し":(0,15000,("体力",300),0),"家庭教師":(6000,0,("学力",300),0),"喫茶店":(3500,9000,("清潔感",200),0)}
EV = {(5,3):"体育祭",(5,4):"中間テスト",(6,3):"大会",(7,2):"期末テスト",(8,2):"夏祭り",(10,3):"中間テスト",(10,4):"文化祭",(11,2):"大会",(12,1):"期末テスト",(12,4):"クリスマス",(1,1):"正月",(2,2):"バレンタイン",(3,1):"学年末テスト",(3,2):"ホワイトデー"}
START = dt.date(2025,4,7)
STAGE = ["未対面","顔見知り","友達","仲良し","気になる","好き","付き合っている"]

def cal(w):
    d = START + dt.timedelta(weeks=w-1)
    return d, d.year-2025+(d.month>=4), d.month, (d.day-1)//7+1

def events(S, w):
    d, y, m, k = cal(w)
    e = [EV[(m,k)]] if (m,k) in EV else []
    if (y,m,k) == (2,11,2): e.append("修学旅行")
    if (y,m) == (3,3) and k >= 1: e = ["卒業式"]
    for h in S["h"]:
        bm, bd = map(int, h["bd"].split("-"))
        if bm == m and (bd-1)//7+1 == k: e.append(h["n"]+"の誕生日")
    return e

def up(S, k, lo=8, hi=20):
    v = S["st"][k]
    g = round(random.randint(lo,hi) * (1 - v/1200) * S["_m"])
    S["st"][k] = min(999, v + max(1, g)); S["_up"].add(k)

def clean(S):
    b = S["body"]
    return S["st"]["清潔感"] * (0.8 if b["hair"] >= 8 else 1) * (1 - 0.08*b["skin"])

def btype(b):
    if b["fat"] > 22: return "ぽっちゃり"
    if b["mus"] > 75: return "がっしり"
    if b["mus"] > 60 and b["fat"] < 14: return "細マッチョ"
    if b["mus"] < 35 and b["fat"] < 16: return "細身"
    return "標準"

def looks(S, h):
    p, b, f = h["p"], S["body"], S["fix"]
    lo, hi = p["h"]
    t = b["ht"]
    sh = 100 if lo <= t <= hi else max(0, 100 - 8*min(abs(t-lo), abs(t-hi)))
    sb = 100 if btype(b) in p["b"] else 50
    sf = 100 if f["face"] in p["f"] else 50
    sv = 100 if any(x in f["voice"] for x in p["v"]) else 50
    sc, sa = min(100, clean(S)/4), min(100, S["st"]["ファッション"]/4)
    return (sh + sb + sf + 0.7*sv + p["c"]*sc + p["fa"]*sa) / (3.7 + p["c"] + p["fa"])

def attract(S, h):
    return sum(min(1, S["st"][k]/h["need"]) for k in h["a"]) / len(h["a"]) * 100

def stage(S, h):
    if h["date"]: return 6
    if not h["met"]: return 0
    L, T = h["L"], h["T"]
    if L >= 65 and T >= 60 and attract(S,h) >= 100 and not h["bf"]: return 5
    if L >= 50 and T >= 40 and not h["bf"]: return 4
    return 3 if L >= 40 else 2 if L >= 20 else 1

def touch(S, h, base, mod=0):
    s = stage(S, h); wl = [1,1,.8,.6,.4,.3,.2][s]; lk = looks(S,h)/100
    h["L"] += (base*(0.6 + 0.4*lk*wl) + 0.5*mod) * (1 - h["L"]/130)
    h["T"] += (base*attract(S,h)/100*(0.5 + 0.5*lk*wl) + 0.3*mod) * (1 - h["T"]/130) - (base if h["bf"] else 0)
    h["last"] = S["w"]; h["met"] = True

def her(S, n):
    for h in S["h"]:
        if h["n"] == n: return h
    raise ValueError("ヒロインがいない: "+n)

def week(S, A, R):
    w = S["w"]; d, y, m, k = cal(w); b = S["st"]
    S["_up"] = set(); sport = 0
    sx = S["stress"]
    S["_m"] = 1.2 if sx < 30 else 1.0 if sx < 60 else 0.8
    ev = events(S, w)
    if S["sick"] > 0:
        S["sick"] -= 1; S["stress"] = max(0, sx-20); R.append("病気で寝込んだ(行動なし)")
        acts = []
    else:
        acts = [A.get("平日","休む"), A.get("週末","休む")]
    for i, a in enumerate(acts):
        wk = i == 1; p = a.split(":"); c = p[0]
        if c == "勉強":
            subs = p[1].split(",")
            for s in subs: up(S, s, 6, 16) if len(subs) > 1 else up(S, s, 10, 22)
            S["stress"] += 6
        elif c in ("運動","芸術","雑学","話術"):
            up(S, c); S["stress"] += 3
            if c == "運動": up(S, "体力", 3, 8); sport += 1; S["stress"] += 1
        elif c == "身だしなみ":
            up(S, "清潔感"); up(S, "ファッション", 2, 6); S["stress"] += 1
        elif c in ("部活","自主練"):
            up(S, "部活", 10, 22); S["stress"] += 5
            if S["club"] == "運動": up(S, "運動", 2, 6); sport += 1
            elif S["club"] == "文化": up(S, "芸術", 2, 6)
        elif c == "バイト":
            pw, pk, req, _ = JOB[p[1]]; pay = pk if wk else pw
            if req:
                v = sum(b[s] for s in SUBJ)/5 if req[0] == "学力" else b[req[0]]
                if v < req[1]: R.append(f"{p[1]}は条件不足({req[0]}{req[1]}以上)"); continue
            if pay == 0: R.append(f"{p[1]}は{'週末' if wk else '平日'}にない"); continue
            S["money"] += pay; S["stress"] += 8 if p[1] == "引っ越し" else 6
            if p[1] == "引っ越し": up(S, "体力", 6, 14); sport += 1
            R.append(f"バイト({p[1]}) +{pay}円")
        elif c == "休む":
            S["stress"] -= 15; S["_rest"] = 1
        elif c == "遊ぶ":
            S["stress"] -= 25; S["money"] -= 2000; up(S, "話術", 2, 6)
        elif c == "買い物":
            item, yen = p[1], int(p[2])
            if yen > S["money"]: R.append("お金が足りない"); continue
            S["money"] -= yen
            if item == "服": b["ファッション"] = min(999, b["ファッション"] + round(10 + 15*min(1, yen/8000)))
            elif item == "スキンケア": S["body"]["care"] = 8
            elif item in SUBJ: up(S, item, 10, 18)
            S["items"].append(p[3] if len(p) > 3 else item)
            R.append(f"買い物: {p[3] if len(p) > 3 else item} -{yen}円")
        elif c == "美容院":
            if S["money"] < 4000: R.append("お金が足りない"); continue
            S["money"] -= 4000; S["body"]["hair"] = 0; S["stress"] -= 5
            if len(p) > 1: S["fix"]["hair"] = p[1]
        elif c == "デート":
            h = her(S, p[1]); cost = PLACE[p[2]]
            if cost > S["money"]: R.append("お金が足りない"); continue
            pr = 0.2 + h["L"]/100*0.6 + h["tr"]/100*0.2 - 0.3*h["bf"] - 0.4*(h["n"] in A.get("忙しい",[]))
            if stage(S,h) < 2: pr *= 0.5
            if random.random() > pr: R.append(f"{h['n']}にデートを断られた"); h["last"] = w; continue
            S["money"] -= cost; S["stress"] -= 10
            mod = A.get("会話",{}).get(h["n"],0) + (3 if p[2] in h["like"] else -3 if p[2] in h["hate"] else 0)
            touch(S, h, 6, mod); h["tr"] += 2; R.append(f"{h['n']}と{p[2]}でデート(-{cost}円)")
        elif c == "告白":
            h = her(S, p[1])
            if stage(S,h) >= 5: h["date"] = True; R.append(f"告白成功！{h['n']}と付き合い始めた")
            else: h["L"] -= 10; h["tr"] -= 5; S["stress"] += 20; R.append(f"{h['n']}への告白は失敗")
    # 学校での接触・電話・GMの補正
    for n in A.get("出会い",[]): her(S,n)["met"] = True; her(S,n)["last"] = w
    for n in A.get("接触",[]): touch(S, her(S,n), 2, A.get("会話",{}).get(n,0))
    if A.get("電話"):
        h = her(S, A["電話"]); touch(S, h, 2 + (2 if any(x in S["fix"]["voice"] for x in h["p"]["v"]) else 0), A.get("会話",{}).get(h["n"],0))
    for n in A.get("フェチ",[]): her(S,n)["T"] += 8
    for n in A.get("地雷",[]): her(S,n)["tr"] -= 15; her(S,n)["L"] -= 5
    for n, dv in A.get("補正",{}).items():
        h = her(S, n)
        for kk, v in dv.items(): h[kk] += max(-10, min(10, v))
    # 体
    bd = S["body"]; fx = S["fix"]
    bd["mus"] += 0.6*min(sport,2) if sport else -0.15
    fu = 1.6 if fx["build"] == "太りやすい" else 0.5 if fx["build"] == "太りにくい" else 1
    bd["fat"] += -0.12*min(sport,2) if sport else 0.08*fu
    if S["stress"] > 70: bd["fat"] += 0.12*fu
    if bd["grow"] > 0:
        g = min(bd["grow"], random.uniform(0.02,0.08)*(1.3 if S["stress"] < 40 or S.get("_rest") else 0.8))
        bd["ht"] += g; bd["grow"] -= g
    bd["hair"] += 1
    if S["stress"] >= 70 and random.random() < (0.6 if fx["skin"] == "荒れやすい" else 0.4): bd["skin"] = min(3, bd["skin"]+1)
    elif (S["stress"] < 40 or bd["care"] > 0) and random.random() < 0.35: bd["skin"] = max(0, bd["skin"]-1)
    bd["care"] = max(0, bd["care"]-1)
    bd["mus"] = max(10, min(95, bd["mus"])); bd["fat"] = max(6, min(35, bd["fat"]))
    for s in SUBJ + ["運動"]:
        if s not in S["_up"] and b[s] > 150: b[s] -= 1
    # ヒロインの生活
    for h in S["h"]:
        s = stage(S, h); gap = w - h["last"]
        if h["met"] and s >= 3 and gap > 4: h["L"] -= 1.5; h["tr"] -= 1
        if h["date"] and gap > 2: h["tr"] -= 3; h["L"] -= 2
        if h["date"] and h["tr"] < 20:
            h["date"] = False; R.append(f"{h['n']}に別れを告げられた")
        rv0 = h["rv"]
        if not h["date"]:
            h["rv"] += random.uniform(0, 2)*h["r"] - (2 if s >= 4 else 0) + (2 if h["met"] and s >= 3 and gap > 4 else 0)
        if h["bf"] and random.random() < 0.02:
            h["bf"] = False; h["rv"] = 40; R.append(f"[GM] {h['n']}が彼氏と別れた")
        if not h["bf"] and h["rv"] >= 100:
            h["bf"] = True; R.append(f"[GM] {h['n']}に彼氏ができた(相手:{h['rival']})")
        elif not h["bf"] and h["rv"] >= 80 > rv0 and h["met"]: R.append(f"[GM] {h['rival']}が{h['n']}に接近中")
        if h["met"] and s >= 3 and gap == 5: R.append(f"[GM] {h['n']}が寂しがっている")
        for kk in ("L","T","tr"): h[kk] = round(max(0, min(100, h[kk])), 1)
        h["rv"] = round(max(0, min(100, h["rv"])), 1)
    # 行事
    cf = {1.2:1.03, 1.0:1.0, 0.8:0.92}[S["_m"]]
    for e in ev:
        if "テスト" in e:
            sc = {s: max(0, min(100, round(100*(1-math.exp(-(b[s]+100)/280))*cf + random.randint(-8,8)))) for s in SUBJ}
            tot = sum(sc.values()); z = (tot-290)/55
            rank = max(1, min(240, 1 + round(239*(1 - 0.5*(1+math.erf(z/2**0.5))))))
            S["tests"].append([f"{y}年{m}月", tot, rank])
            R.append(f"{e}: " + " ".join(f"{s}{v}" for s, v in sc.items()) + f" 合計{tot} 学年{rank}位/240" + (" ※赤点あり→補習" if min(sc.values()) < 30 else ""))
        if e == "大会" and S["club"] != "帰宅":
            v = b["部活"]*0.7 + (b["運動"] if S["club"] == "運動" else b["芸術"])*0.3 + random.randint(-80,80)
            R.append("大会: " + ["初戦敗退","2回戦敗退","ベスト8","準優勝","優勝"][max(0, min(4, int(v//150)))])
        if e == "卒業式":
            c = [h for h in S["h"] if (h["date"] or stage(S,h) >= 5) and not h["bf"]]
            c.sort(key=lambda h: h["T"] + h["tr"], reverse=True)
            R.append("[GM] 鐘の下に来るのは: " + (c[0]["n"] if c else "誰もいない(ノーマルエンド)"))
            S["end"] = True
    # 小遣い・ストレス・病気
    S["stress"] = max(0, min(100, S["stress"]))
    if S["stress"] >= 80 and random.random() < (S["stress"]-75)/50:
        S["sick"] = random.randint(1,2); R.append("無理がたたって体調を崩した")
    S["w"] += 1
    if cal(S["w"])[2] != m: S["money"] += 5000; R.append("小遣い +5000円")
    S.pop("_rest", None); S.pop("_up"); S.pop("_m")
    return ev

def cond(S):
    if S["sick"]: return "病気"
    x = S["stress"]; return "絶好調" if x < 30 else "普通" if x < 60 else "不調"

def show(S, R):
    d, y, m, k = cal(S["w"]); b = S["body"]; f = S["fix"]
    out = [f"【{y}年 {m}月 第{k}週】 体調:{cond(S)} ストレス:{S['stress']} 所持金:{S['money']}円"]
    out.append(" ".join(f"{s}:{S['st'][s]}" for s in ST[:5]))
    out.append(" ".join(f"{s}:{S['st'][s]}" for s in ST[5:]))
    wt = 22*(b["ht"]/100)**2*(1 + (b["mus"]-50)/400 + (b["fat"]-16)/80)
    out.append(f"身長:{b['ht']:.1f}cm 体重:{wt:.1f}kg 筋肉:{b['mus']:.0f} 体脂肪:{b['fat']:.1f}% 体型:{btype(b)} 髪:{f['hair']}{'(伸びてきた)' if b['hair'] >= 8 else ''} 肌:{['きれい','普通','荒れ気味','ニキビ'][b['skin']]}")
    out.append("出来事: " + (" / ".join(R) if R else "特になし"))
    nx = [f"{'・'.join(events(S, S['w']+i))}" + (f"まで{i}週" if i else "(今週)") for i in range(3) if events(S, S['w']+i)]
    out.append("予定: " + (" ".join(nx) if nx else "なし"))
    out.append("[GM用] " + " | ".join(f"{h['n']}:{STAGE[stage(S,h)]} 好{h['L']} と{h['T']} 信{h['tr']} 見{looks(S,h):.0f} 惹{attract(S,h):.0f} ラ{h['rv']}{' 彼氏あり' if h['bf'] else ''}" for h in S["h"] if h["met"]))
    print("\n".join(out))

def run(S, A, n=1):
    R = []
    for i in range(n):
        ev = week(S, A, R)
        if S.get("end") or ev or any(r.startswith(("[GM]", "無理")) or "デート" in r or "告白" in r for r in R): break
    S["stress"] = round(S["stress"])
    for k in ("ht", "grow", "mus", "fat"): S["body"][k] = round(S["body"][k], 2)
    show(S, R)
    print("STATE=" + json.dumps(S, ensure_ascii=False, separators=(",", ":")))

def new_game(name, club, heroines):
    r = random.randint
    S = {"name": name, "w": 1, "money": 10000, "stress": 20, "sick": 0, "club": club, "items": [], "tests": [],
         "st": {k: r(30, 80) for k in ST},
         "fix": {"face": random.choice(["塩顔", "しょうゆ顔", "ソース顔", "童顔", "切れ長のクール系"]),
                 "voice": random.choice(["低め", "普通", "高め"]) + "・" + random.choice(["よく通る", "柔らかい", "ハスキー", "こもりがち"]),
                 "build": random.choice(["太りやすい", "普通", "太りにくい"]), "skin": random.choice(["荒れやすい", "普通", "強い"]), "hair": "短髪"},
         "body": {"ht": round(random.gauss(170, 5), 1), "grow": round(random.uniform(0, 8), 1), "mus": r(25, 55), "fat": round(random.uniform(12, 20), 1), "hair": 0, "skin": 1, "care": 0},
         "h": []}
    S["body"]["ht"] = max(160, min(180, S["body"]["ht"]))
    for h in heroines:
        h.update({"met": h.get("met", False), "date": False, "bf": False, "L": h.get("L", 5), "T": 0, "tr": 50, "rv": 0, "last": 1})
        S["h"].append(h)
    return S
