"""Compile 게임 오디오 추출기.

    compile-audio extract <게임 폴더 또는 파일> <출력 폴더>

형식은 파일 내용으로 판별하므로 어떤 파일이 무슨 형식인지 몰라도 됨. 묶음 하나마다
<출력>/<파일 이름>/ 아래에 곡은 bgm_NN.mid, 효과음은 se_NN.wav, 항목별 정보는 index.json.
결과는 <출력>/extract_report.tsv에도 남는다.

    compile-audio info <파일>      묶음 안 항목을 풀지 않고 나열
"""
import argparse
import os
import sys

from . import extract as ex
from . import mlk, wlk
from .detect import NotAudio, load


def cmd_extract(args):
    counts, rows = {}, []
    for r in ex.scan(args.src):
        if r.status == ex.OK:
            ex.save(r, args.dest)
            print(f"  {r.source}: {r.kind}{' ' + r.variant if r.variant else ''} -- {r.note}")
        counts[r.status] = counts.get(r.status, 0) + 1
        rows.append(r)
    os.makedirs(args.dest, exist_ok=True)
    with open(os.path.join(args.dest, "extract_report.tsv"), "w", encoding="utf-8") as f:
        f.write("원본\t상태\t형식\t변종\t비고\n")
        for r in rows:
            f.write("\t".join((r.source, r.status, r.kind, r.variant, r.note)) + "\n")
    print(" / ".join(f"{k} {counts.get(k, 0)}" for k in (ex.OK, ex.SKIPPED, ex.UNKNOWN)))
    return 0


def cmd_info(args):
    try:
        kind, parsed = load(open(args.src, "rb").read())
    except NotAudio as e:
        print(f"{args.src}: {e}", file=sys.stderr)
        return 1
    if kind == "mlk":
        print(f"MLK {len(parsed)}곡")
        for s in parsed:
            i = mlk.smf_info(s.data)
            loop = "반복" if s.loop else "한 번"
            at = f"@{i.loop_tick}" if i.loop_tick is not None else ""
            print(f"  {s.index:2d} flag {s.flag} {loop}{at:>8s} 분해능 {i.division} 끝 {i.end_tick} {s.size:>7,}B")
    else:
        print(f"WLK {parsed.variant} {len(parsed.samples)}개 (꼬리 {parsed.trailing}B)")
        for s in parsed.samples:
            ex_ = f" extra {list(s.extra)}" if s.extra else ""
            print(f"  {s.index:2d} {s.rate:>6d}Hz {s.bits}bit {s.channels}ch {s.frames:>7,}프레임{ex_}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="compile-audio", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("extract", help="MLK·WLK를 판별해 .mid/.wav로 풂")
    p.add_argument("src")
    p.add_argument("dest")
    p.set_defaults(func=cmd_extract)
    p = sub.add_parser("info", help="묶음 안을 나열")
    p.add_argument("src")
    p.set_defaults(func=cmd_info)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
