# Compile 오디오 추출기 (compile-audio)

## 개요

Compile 윈도우판 게임의 오디오 묶음을 풀어 곡은 표준 MIDI(`.mid`), 효과음은 `.wav`로 꺼내는
파이썬 도구. [`compile-gfx`](https://github.com/flvrdoyster/compile-gfx)의 짝으로, 같은 방침을 따름.

**추출 전용.** 재삽입, 그리고 MIDI를 소리로 바꾸는 렌더링(사운드폰트·합성기·반복 이어붙이기)은
각 프로젝트가 따로 함. 여기에는 그 프로젝트들이 저마다 복사해 두던 컨테이너 지식만 모음.

| 확장자 | 내용 | 변종 | 확인한 게임 |
|---|---|---|---|
| `.MLK` | MIDI 곡 묶음 | 하나 | 환세쾌진극(`SMASH.MLK`, 14곡) · 취호전(`MIDDATA.MLK`, 20곡) · 패유기(`HAIYUKI.MLK`, 14곡) |
| `.WLK` | 효과음 PCM 묶음 | 헤더 없음 / `WLKF0200` | 환세쾌진극(`GENSEI.WLK`, 10개) · 취호전(`PCMDATA.WLK`, 54개) · 패유기(`HAIYUKI.WLK`, 17개) |

확장자가 아니라 내용으로 판별함. 바이트 레이아웃은 [`FORMATS.md`](FORMATS.md).

## 사용법

```bash
pip install git+https://github.com/flvrdoyster/compile-audio
compile-audio extract <게임 폴더 또는 파일> <출력 폴더>
compile-audio info <파일>          # 풀지 않고 항목만 나열
```

묶음 하나마다 `<출력>/<파일 이름>/`이 생기고 그 안에 `bgm_NN.mid` 또는 `se_NN.wav`와
`index.json`(항목별 플래그·반복 틱·샘플레이트 등)이 들어감. 번호는 컨테이너 안 0부터의 순번.
파일마다 결과는 `<출력>/extract_report.tsv`에 남음.

```python
from compileaudio import load
kind, parsed = load(open("SMASH.MLK", "rb").read())    # ("mlk", [Song, ...])
```

## 테스트

```bash
pip install -e ".[dev]" && pytest
COMPILE_AUDIO_CORPUS=<MLK·WLK가 든 폴더> pytest     # 실제 파일 해시 회귀
python tests/make_manifest.py <폴더>                  # 출력이 의도적으로 바뀐 때만
```

합성 컨테이너 테스트는 게임 데이터 없이 돌고, 코퍼스 테스트는 결과 해시만 비교함(게임 파일은
저장소에 없음). 환세쾌진극의 변환 결과(`bgm_*.mid`·`se_*.wav` 24개)와 바이트 단위로 같음을 확인함.

## 범위 밖

- **렌더링**: MIDI → 소리는 사운드폰트·합성기 선택에 달려 있어 여기 두지 않음.
- **PC-98판**(`SONG.DAT` + `FPLAY.COM` 같은 자체 드라이버 형식)은 다른 형식이라 이 도구가 다루지 않음.
- **디스크 이미지**(ISO 등)는 안을 열지 못함 -- 파일을 먼저 꺼내야 함.
