import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

def save_log(result, usage_report):
    folder = Path(__file__).parent / 'logs'
    folder.mkdir(exist_ok=True)
    stamp = datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d_%H%M')
    record = {
        'at': stamp,
        'log': result['log'],
        'picked': [{k: x[k] for k in ('title', 'url', 'source', 'event', 'reason')} for x in result.get('picked', [])],
        'verified': [{k: x[k] for k in ('headline', 'url', 'source')} for x in result.get('verified', [])],
        'usage': usage_report()[0],
        'cost_usd': round(usage_report()[1], 4),
    }
    path = folder / f'{stamp}.json'
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return path

def main():
    parser = argparse.ArgumentParser(description='AI 뉴스레터 에이전트')
    parser.add_argument('--hours', type=int, default=24)
    parser.add_argument('--publish', action='store_true', help='Discord로 실제 발행')
    parser.add_argument('--collect-only', action='store_true', help='API 키 없이 수집 단계만 점검')
    parser.add_argument('--notion-only', action='store_true', help='Discord로 보내지 않고 노션에만 저장')
    parser.add_argument('--academy', action='store_true', help='학원 학부모 뉴스레터(config_academy.json)')
    args = parser.parse_args()
    if args.academy:
        os.environ['NEWSLETTER_CONFIG'] = 'config_academy.json'
    # 설정 파일은 graph를 import할 때 읽으므로 인자를 해석한 뒤 import합니다.
    from graph import CONFIG, build, collect, usage_report
    if args.hours <= 0:
        parser.error('--hours must be positive')
    if args.collect_only:
        result = collect({'hours': args.hours})
        for item in result['collected']:
            print(f'- [{item["source"]}] {item["at"][:16]} {item["title"]}')
        print(result['log'][0])
        return
    if not os.getenv('ANTHROPIC_API_KEY'):
        parser.error('ANTHROPIC_API_KEY 환경변수(또는 .env)를 설정하세요')
    publish = args.publish or os.getenv('DRY_RUN', '1') == '0'
    to_notion_page = CONFIG.get('output') == 'notion_page'
    if publish and not to_notion_page and not os.getenv('DISCORD_WEBHOOK_URL'):
        parser.error('DISCORD_WEBHOOK_URL 환경변수(또는 .env)를 설정하세요')
    if (args.notion_only or (publish and to_notion_page)) and not os.getenv('NOTION_TOKEN'):
        parser.error('NOTION_TOKEN 환경변수(또는 .env)를 설정하세요')
    result = build().invoke({'hours': args.hours, 'publish_enabled': publish and not args.notion_only,
                             'notion_only': args.notion_only, 'drafted': [], 'log': []})
    for line in result['log']:
        print(line)
    lines, total = usage_report()
    for line in lines:
        print(f'   비용 {line}')
    print(f'⑥ 이번 실행 예상 비용 ${total:.4f} (토큰 사용량 × 공시 단가, 실제 청구는 콘솔에서 확인)')
    print(f'로그 저장: {save_log(result, usage_report)}')

if __name__ == '__main__':
    main()
