# fastapi-skeleton

FastAPI 멀티 앱 모노레포 템플릿입니다. `uv` 워크스페이스로 구성되어 있으며 `common` 패키지를 공유합니다.

## 구조
```
.
├── pyproject.toml
├── uv.lock
├── packages/
│   └── common/
│       ├── pyproject.toml
│       └── src/common/
│           ├── db/
│           ├── alembic/
│           └── lib/
└── apps/
    ├── internal_api/
    ├── external_api/
    └── backoffice_api/
├── cli_apps/
│   └── ops_cli/
```

## 요구사항
- Python 3.14+
- uv

## 빠른 시작
```bash
# 워크스페이스 의존성 설치
uv sync

# 환경변수 설정 (예시: internal-api)
export APP_NAME=internal-api
export APP_ENV=local
export APP_LOG_LEVEL=info
export DB_URL=postgresql+psycopg://user:pass@localhost:5432/appdb
export AUTH_API_KEY=internal-dev-key
export AUTH_API_KEY_HEADER=X-API-Key
export ALEMBIC_MODEL_MODULES=common.db.models,backoffice_api.db.models

# 앱 실행 (예시)
uv run --package internal-api fastapi run internal_api.main:app --reload --host 0.0.0.0 --port 8001
uv run --package external-api fastapi run external_api.main:app --reload --host 0.0.0.0 --port 8002
uv run --package backoffice-api fastapi run backoffice_api.main:app --reload --host 0.0.0.0 --port 8003

# CLI 실행 (예시)
uv run --package internal-api internal-api ping
uv run --package external-api external-api ping
uv run --package backoffice-api backoffice-api ping

# 배치 실행 (예시)
uv run --package internal-api internal-api batch template --limit 50 --dry-run
uv run --package external-api external-api batch template --limit 50 --dry-run
uv run --package backoffice-api backoffice-api batch template --limit 50 --dry-run

# 상위 CLI 앱 실행 (예시)
uv run --package ops-cli ops-cli ping
uv run --package ops-cli ops-cli batch sample
uv run --package ops-cli ops-cli kafka sample
```

루트 `dependencies`에 워크스페이스 패키지를 명시했기 때문에 `uv sync`만으로 앱/패키지 의존성이 설치됩니다.

## 공통 패키지(common)
- SQLAlchemy 베이스/세션
- 공통 모델
- Alembic 단일 마이그레이션
- 공통 설정/로깅/에러

## Import 규칙
- `__init__.py`에서 re-export 하지 않습니다.
- 사용처에서는 모듈을 명시적으로 import합니다.
- 예: `from common.db.session import get_db_session`, `from internal_api.batch.app import app as batch_app`

## 모델 네이밍/패키지 분리 규칙
- 모델 이름은 도메인/테이블 기준으로 간결하게 정의합니다. 예: `User`, `Order`, `OAuthToken`
- 앱 이름 프리픽스(`Common/Backoffice/External/Internal`)는 사용하지 않습니다.
- 공통 모델은 `packages/common/src/common/db/models/`에 둡니다.
- 앱 전용 모델은 `apps/<app>/src/<app>/db/models/`에 둡니다.
- 앱 전용 모델을 구분해야 하면 **모델명 대신 테이블명**에 스코프를 반영합니다. 예: `backoffice_oauth_tokens`
- 공통 모델은 여러 앱에서 동일 규칙으로 사용되는 엔티티만 포함합니다.

## 마이그레이션
- `packages/common/src/common/alembic`에 단일 마이그레이션 디렉토리 유지
- 앱 전용 모델을 포함하려면 `ALEMBIC_MODEL_MODULES` 환경변수로 로딩 대상 모듈을 지정
- 로딩 실패 또는 테이블 미등록 시 명확한 오류로 중단

`ALEMBIC_MODEL_MODULES`에 `common.db.models`는 자동 포함됩니다.

예시:
```bash
export ALEMBIC_MODEL_MODULES=common.db.models,backoffice_api.db.models
```

## 마이그레이션 절차 (권장)
1. DB 접속과 모델 모듈을 환경변수로 설정합니다.
```bash
export DB_URL=postgresql+psycopg://user:pass@localhost:5432/appdb
export ALEMBIC_MODEL_MODULES=common.db.models,backoffice_api.db.models
```

2. 새 마이그레이션 생성합니다.
```bash
uv run --package common alembic -c packages/common/alembic.ini revision --autogenerate -m "init"
```

3. 마이그레이션 적용합니다.
```bash
uv run --package common alembic -c packages/common/alembic.ini upgrade head
```

4. 필요 시 롤백합니다.
```bash
uv run --package common alembic -c packages/common/alembic.ini downgrade -1
```

## 샘플 모델/마이그레이션
- 샘플 모델: `packages/common/src/common/db/models/sample.py`
- 초기 마이그레이션 템플릿: `packages/common/src/common/alembic/versions/0001_initial.py`
- OAuth 토큰 마이그레이션 템플릿: `packages/common/src/common/alembic/versions/0002_oauth_tokens.py`

## 환경변수 네이밍 규칙
- 공통: `APP_NAME`, `APP_ENV`, `APP_LOG_LEVEL`
- DB: `DB_URL`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`
- API Key: `AUTH_API_KEY`, `AUTH_API_KEY_HEADER`
- Google OAuth: `AUTH_GOOGLE_CLIENT_ID`, `AUTH_GOOGLE_CLIENT_SECRET`, `AUTH_GOOGLE_REDIRECT_URI`, `AUTH_TOKEN_ENC_KEY`
- Alembic: `ALEMBIC_MODEL_MODULES`

`AUTH_TOKEN_ENC_KEY`는 32바이트 원문 키 또는 32바이트의 base64 인코딩 키를 권장합니다.

## 환경변수 예시
internal-api/external-api 공통:
```bash
export APP_NAME=internal-api
export APP_ENV=local
export APP_LOG_LEVEL=info
export DB_URL=postgresql+psycopg://user:pass@localhost:5432/appdb
export DB_POOL_SIZE=5
export DB_MAX_OVERFLOW=10
export AUTH_API_KEY=internal-dev-key
export AUTH_API_KEY_HEADER=X-API-Key
```

backoffice-api:
```bash
export APP_NAME=backoffice-api
export APP_ENV=local
export APP_LOG_LEVEL=info
export DB_URL=postgresql+psycopg://user:pass@localhost:5432/appdb
export AUTH_GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
export AUTH_GOOGLE_CLIENT_SECRET=yyy
export AUTH_GOOGLE_REDIRECT_URI=http://localhost:8003/auth/google/callback
export AUTH_TOKEN_ENC_KEY=base64-32-bytes-or-strong-key
```

external-api 예시(필요 시 APP_NAME과 API Key만 변경):
```bash
export APP_NAME=external-api
export AUTH_API_KEY=external-dev-key
```

## 운영 환경 예시(.env 샘플)
운영 환경용 예시는 아래 파일을 참고하세요.
- `.env.internal.example`
- `.env.external.example`
- `.env.backoffice.example`

## CLI 배치 구조
- 각 앱에 `batch` 서브커맨드를 둡니다.
- 예시 명령: `internal-api batch template --limit 100 --dry-run`
- 실제 배치 작업은 `apps/<app>/src/<app>/batch/app.py`에 추가합니다.
- 기본 템플릿은 입력 옵션, JSON 출력, 트랜잭션 커밋/롤백 패턴을 포함합니다.
- 서비스/리포지토리 예시는 `services/batch_service.py`, `repositories/sample_repository.py`를 참고하세요.
- 대규모 배치/컨슈머는 `cli_apps` 하위에서 별도 CLI 앱으로 운영합니다.

## 개발 도구
```bash
# lint/format
uv run ruff check .
uv run ruff format .

# type check
uv run ty check

# tests
uv run pytest
```

테스트는 기본으로 `DB_URL=sqlite+aiosqlite:///:memory:`를 사용하도록 `tests/conftest.py`에서 설정합니다.
테스트 전에는 `uv sync`로 워크스페이스 패키지를 설치하세요.

## 앱별 인증
- internal-api: API Key
- external-api: API Key
- backoffice-api: Google OAuth (refresh/access 토큰은 `AUTH_TOKEN_ENC_KEY`로 암호화 저장)

모듈 위치:
- `apps/internal_api/src/internal_api/auth/api_key.py`
- `apps/external_api/src/external_api/auth/api_key.py`
- `apps/backoffice_api/src/backoffice_api/auth/google_oauth.py`

## Health Checks
모든 앱은 인증 없이 아래 엔드포인트를 제공합니다.
- `GET /liveness`
- `GET /readiness` (DB 연결 체크 포함)

## Google OAuth API (backoffice-api)
`GET /auth/google/authorize`  
Query: `state` (필수), `scope` (기본: `openid email profile`)  
Response: `{ "authorize_url": "..." }`

`POST /auth/google/exchange`  
Body: `{ "code": "...", "subject": "...", "redirect_uri": "..." }`  
Response: `{ "id": 1, "provider": "google", "subject": "...", "expires_at": "..." }`

`POST /auth/google/refresh`  
Body: `{ "subject": "..." }`  
Response: `{ "id": 1, "provider": "google", "subject": "...", "expires_at": "..." }`
