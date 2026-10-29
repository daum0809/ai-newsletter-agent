import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

from graph import build, collect  # noqa: E402  (.env를 먼저 읽은 뒤 import)

def save_log(result):
    folder = Path(__file__).parent / 'logs'
    folder.mkdir(exist_ok=True)
    stamp = datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d_%H%M')
    record = {
        'at': stamp,
        'log': result['log'],
        'picked': [{k: x[k] for k in ('title', 'url', 'source', 'event', 'reason')} for x in result.get('picked', [])],
        'verified': [{k: x[k] for k in ('headline', 'url', 'source')} for x in result.get('verified', [])],
    }
    path = folder / f'{stamp}.json'
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return path

def main():
    parser = argparse.ArgumentParser(description='AI 뉴스레터 에이전트')
    parser.add_argument('--hours', type=int, default=24)
    parser.add_argument('--publish', action='store_true', help='Discord로 실제 발행')
    parser.add_argument('--collect-only', action='store_true', help='API 키 없이 수집 단계만 점검')
    args = parser.parse_args()
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
    if publish and not os.getenv('DISCORD_WEBHOOK_URL'):
        parser.error('DISCORD_WEBHOOK_URL 환경변수(또는 .env)를 설정하세요')
    result = build().invoke({'hours': args.hours, 'publish_enabled': publish, 'drafted': [], 'log': []})
    for line in result['log']:
        print(line)
    print(f'로그 저장: {save_log(result)}')

if __name__ == '__main__':
    main()
