"""검수 노드가 실제로 오류를 잡는지 확인합니다. (API 호출 4회)

정확한 카드는 통과, 숫자·주체를 틀린 카드와 과장된 why는 탈락해야 합니다.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

from graph import check  # noqa: E402

BODY = (
    'Acme AI said on Tuesday it raised $60 million in a Series B round led by Example Ventures. '
    'The startup, founded three months ago, builds open-source code review agents. '
    'CEO Jane Park said the money will be used to hire engineers in Seoul and Berlin. '
    'The company plans to release a free tier of its agent next quarter. ' * 3
)
GOOD = {'headline': 'Acme AI, 6000만 달러 시리즈 B 유치',
        'summary': 'Acme AI가 Example Ventures 주도로 6000만 달러를 유치했습니다. 회사는 설립 3개월 된 오픈소스 코드 리뷰 에이전트 스타트업입니다. 자금은 서울과 베를린 엔지니어 채용에 쓰입니다.',
        'why': '다음 분기에 무료 요금제가 나오면 팀에서 비용 부담 없이 코드 리뷰 에이전트를 시험해 볼 수 있습니다.'}
CASES = [
    ('정확한 카드', GOOD, True),
    ('금액 오류', {**GOOD, 'headline': 'Acme AI, 6억 달러 시리즈 B 유치'}, False),
    ('주체 오류', {**GOOD, 'summary': GOOD['summary'].replace('Example Ventures', 'Google')}, False),
    ('why 과장', {**GOOD, 'why': '이번 투자로 Acme AI는 GitHub Copilot을 제치고 업계 1위가 확실합니다.'}, False),
]

ok = 0
for name, card, expected in CASES:
    verdict = check({'body': BODY, **card})
    got = verdict.facts_ok and verdict.why_ok
    ok += got == expected
    print(f'{"PASS" if got == expected else "FAIL"} {name}: 기대={expected} 결과={got} '
          f'(facts_ok={verdict.facts_ok}, why_ok={verdict.why_ok}) {verdict.reason[:100]}')
print(f'{ok}/{len(CASES)} 일치')
