"""GM用ランナー。状態は saves/<game>.json に保存する。

使い方:
  python3 engine/play.py kane '{"平日":"勉強:数学","週末":"休む"}' [週数]
  python3 engine/play.py ichizoku '{"討伐":{"先":0,"隊":["楓"]}}'
  python3 engine/play.py <game> --new '<new_game の引数をJSON配列で>'
"""
import contextlib, io, json, pathlib, sys

root = pathlib.Path(__file__).resolve().parent
game, arg = sys.argv[1], sys.argv[2]
ns = {}
exec((root / f"{game}.py").read_text(encoding="utf-8"), ns)
save = root.parent / "saves" / f"{game}.json"

if arg == "--new":
    S = ns["new_game"](*json.loads(sys.argv[3]))
    A, rest = ({"平日": "休む", "週末": "休む"}, [1]) if game == "kane" else ({"進む": False, "家系図": True}, [])
else:
    S = json.loads(save.read_text(encoding="utf-8"))
    A, rest = json.loads(arg), [int(x) for x in sys.argv[3:]]

out = io.StringIO()
with contextlib.redirect_stdout(out):
    ns["run"](S, A, *rest)
text, state = out.getvalue().split("STATE=")
save.write_text(state.strip(), encoding="utf-8")
print(text.rstrip())
