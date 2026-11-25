"""Langfuse 추적 (선택 기능).

LANGFUSE_PUBLIC_KEY·LANGFUSE_SECRET_KEY가 있을 때만 켜집니다. 키가 없거나, langfuse 패키지가 없거나,
Langfuse 서버가 꺼져 있어도 추적만 빠지고 에이전트는 예전과 똑같이 돕니다(추적 오류는 모두 삼킵니다).
"""
import os
from contextlib import contextmanager
from functools import wraps

_client = None  # None = 아직 확인 전, False = 꺼짐


def client():
    global _client
    if _client is None:
        _client = False
        if os.getenv('LANGFUSE_PUBLIC_KEY') and os.getenv('LANGFUSE_SECRET_KEY'):
            try:
                from langfuse import Langfuse, is_default_export_span
                # anthropic SDK가 스스로 만드는 OTel span(anthropic.messages.create)은 llm()의 generation과
                # 토큰이 겹치므로 내보내지 않습니다. 비용·오류는 llm()의 generation에 기록됩니다.
                _client = Langfuse(should_export_span=lambda span: is_default_export_span(span) and not (
                    span.instrumentation_scope and span.instrumentation_scope.name.startswith('com.anthropic')))
            except Exception:
                _client = False
    return _client or None


def update(obs, **fields):
    """관찰 객체에 값을 덧붙입니다. 추적이 꺼졌거나 실패해도 조용히 넘어갑니다."""
    if obs is None:
        return
    try:
        obs.update(**fields)
    except Exception:
        pass


@contextmanager
def observation(name, as_type='span', trace_name=None, **fields):
    """span·generation 하나를 열고 닫습니다. 본문에서 난 예외는 ERROR로 기록한 뒤 그대로 다시 던집니다."""
    lf, opened, obs, scope = client(), None, None, None
    if lf:
        try:
            if trace_name:
                from langfuse import propagate_attributes
                scope = propagate_attributes(trace_name=trace_name)
                scope.__enter__()
            opened = lf.start_as_current_observation(name=name, as_type=as_type, **fields)
            obs = opened.__enter__()
        except Exception:
            opened = obs = None
    try:
        yield obs
    except BaseException as exc:
        update(obs, level='ERROR', status_message=f'{type(exc).__name__}: {exc}'[:1000])
        _close(opened, scope, exc)
        raise
    else:
        _close(opened, scope, None)


def _close(opened, scope, exc):
    args = (type(exc), exc, exc.__traceback__) if exc else (None, None, None)
    for cm in (opened, scope):
        if cm is not None:
            try:
                cm.__exit__(*args)
            except Exception:
                pass


def node(name, fn):
    """LangGraph 노드 함수를 span으로 감쌉니다. 노드 로그 줄을 output으로 남깁니다."""
    @wraps(fn)
    def wrapper(state):
        meta = {'title': state.get('title'), 'url': state.get('url')} if name == 'report' else None
        with observation(name, input=meta) as obs:
            result = fn(state)
            update(obs, output={'log': (result or {}).get('log')})
            return result
    return wrapper


def flush():
    lf = client()
    if lf:
        try:
            lf.flush()
        except Exception:
            pass
