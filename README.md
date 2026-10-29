# AI 뉴스레터 에이전트 (Claude 버전)

모두의연구소 Agt1 수업(2026-10-28) 실습 코드를 Claude API로 옮기고 수업 회고의 개선 과제 일부를 반영한 버전입니다.

**수집 collect → 선별 select → 취재·요약 report → 검수 verify → 발행 publish** (LangGraph)

| 단계 | 하는 일 | 모델(기본값) |
| --- | --- | --- |
| collect | `config.json`의 RSS 소스에서 최근 N시간 글 수집, utm 매개변수만 제거해 URL 중복 제거, 실패 소스 기록 | - |
| select | 40건 단위 예선(묶음당 8건) → 본선 → 같은 사건·매체 상한(2건) 제거 후 최대 5건 | `claude-sonnet-5-5` |
| report | `Send`로 기사마다 워커 실행, robots.txt 확인 → 본문 추출 → headline·summary·why | `claude-haiku-5-5` |
| verify | 별도 호출로 headline·summary는 원문 대조, why는 사실 추가·과장 여부를 따로 검사 | `claude-sonnet-5-5` |
| publish | 통과 기사만 Discord embed로 발행, 0건이면 하트비트(수집·선별·요약 건수) 발행 | - |

## 수업 코드 대비 달라진 점

- OpenAI → Claude API (`client.messages.parse` 구조화 출력, 모델 거절 처리). 단계별 모델은 `MODEL_SELECT / MODEL_REPORT / MODEL_VERIFY`로 바꿀 수 있습니다.
- 독자·소스·선정 개수를 코드에서 `config.json`으로 분리했습니다.
- 취재 단계를 ThreadPool 대신 LangGraph `Send` 팬아웃으로 구현했습니다.
- why를 검수 대상에 넣고(사실과 해석을 다른 기준으로), 한국어 검사를 "한글 한 글자"가 아니라 한글 비율로 바꿨습니다.
- 본선 탈락·중복 제외 목록까지 로그에 남기고 `logs/*.json`으로 저장합니다(Actions에서는 artifact로 30일 보관).
- `selftest_verify.py`: 숫자·주체를 틀린 카드와 과장된 why를 일부러 넣어 검수가 잡아내는지 확인합니다.

## 로컬 실행 (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env   # 메모장으로 열어 ANTHROPIC_API_KEY 입력
```

```powershell
.\.venv\Scripts\python run.py --collect-only   # API 키 없이 소스 수집만 점검
.\.venv\Scripts\python selftest_verify.py      # 검수 자가점검 (API 4회)
.\.venv\Scripts\python run.py                  # 전체 실행, Discord로 보내지 않음
.\.venv\Scripts\python run.py --publish        # DISCORD_WEBHOOK_URL 설정 후 실제 발행
```

`--hours 48`로 수집 기간을 바꿀 수 있습니다. API 사용은 비용이 발생합니다.

## GitHub Actions (매일 07:30 KST)

1. 이 폴더를 GitHub 저장소로 올립니다(예약 워크플로는 기본 브랜치에 있어야 동작).
2. Settings → Secrets and variables → Actions에 `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL` 등록.
3. Actions 탭 → daily-newsletter → Run workflow (dry_run=1)로 먼저 점검, 이후 dry_run=0으로 실제 발행 확인.

예약 실행은 실제 발행(DRY_RUN=0)으로 돕니다. 예약은 지연될 수 있고, 공개 저장소는 60일간 활동이 없으면 예약이 꺼질 수 있습니다. 웹훅 URL은 비밀번호처럼 다루세요.

## 남은 개선 과제

- 변경 전후를 비교할 평가셋, 발행 전 사람 승인 단계
- 사건 라벨 일관성·중복 제거 정확도 평가
- RSS가 없는 소스(예: Anthropic 뉴스)는 공식 API 등 대안 확인
