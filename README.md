# ATS v2 - 업비트 멀티자산 자동 거래 시스템

## 📋 개요

ATS v2는 업비트에서 여러 암호화폐 자산을 동시에 모니터링하고 자동으로 거래하는 한국형 시스템입니다. 각 자산별로 독립적인 트레이딩 엔진을 운영하여 병렬 처리와 리스크 분산을 제공합니다.

## 🚀 주요 특징

- **업비트 완전 연동**: 한국 최대 암호화폐 거래소 업비트 전용
- **멀티자산 지원**: BTC, ETH, ADA 등 여러 암호화폐를 동시에 거래
- **자산별 독립 관리**: 각 자산의 평균단가, 수익률을 별도 관리 
- **병렬 처리**: ThreadPoolExecutor 기반 스레드 풀에서 엔진 실행
- **모의거래 지원**: 실제 거래 전 전략 테스트 가능
- **원화 직거래**: USD가 아닌 원화(KRW) 기준 거래
- **실시간 알림**: 거래 및 상태 알림 기능

## 📁 프로젝트 구조

```
ats_v2/
├── config/
│   └── assets.json         # 거래 자산 설정
├── core/
│   ├── engine/
│   │   ├── trader.py       # 자산별 트레이딩 엔진
│   │   └── manager.py      # 멀티자산 매니저
│   ├── data_collector.py   # 가격 데이터 수집
│   ├── portfolio.py        # 포트폴리오 관리
│   ├── trigger.py          # 매매 시그널 판단
│   ├── executor.py         # 주문 실행
│   └── notifier.py         # 알림 관리
├── utils/
│   └── logger.py           # 로깅 유틸리티
├── main.py                 # 메인 실행 파일
└── requirements.txt        # 의존성 패키지
```

## 🛠️ 설치 및 실행

1. **의존성 설치**:
```bash
pip install -r requirements.txt
```

2. **환경변수 설정**:
```bash
# example.env를 .env로 복사하여 수정
cp example.env .env

# 또는 자동 설정 스크립트 실행
python setup_upbit.py
```

3. **업비트 API 키 설정** (.env 파일에서):
```bash
UPBIT_ACCESS_KEY=your_actual_access_key
UPBIT_SECRET_KEY=your_actual_secret_key
DRY_RUN=false  # 실제 거래시
```

4. **실행**:
```bash
python main.py
```

## ⚙️ 설정

### 환경변수 설정 (.env 파일)
```bash
# 업비트 API 설정
UPBIT_ACCESS_KEY=your_upbit_access_key
UPBIT_SECRET_KEY=your_upbit_secret_key

# 거래 설정
DRY_RUN=true          # 모의거래(true) / 실제거래(false)
LOG_LEVEL=INFO        # 로그 레벨

# 시스템 설정
POLLING_INTERVAL=10   # 가격 조회 간격(초)
STATUS_UPDATE_INTERVAL=300  # 상태 알림 간격(초)
MAX_WORKERS=          # 병렬 처리 스레드 수(미설정 시 자산 수)
```

### 자산 설정 (config/assets.json)
```json
[
  {
    "symbol": "BTC/USDT",
    "base_currency": "BTC", 
    "quote_currency": "KRW",
    "trade_amount": 10000
  }
]
```

### 매매 전략 설정
- 2% 하락시 매수
- 3% 수익시 매도
- 5% 손실시 손절

## 📊 모니터링

- 실시간 콘솔 로그
- 일별 로그 파일 (`logs/` 디렉토리)
- 자산별 거래 로그

## ⚠️ 주의사항

- 기본적으로 **모의거래 모드**로 실행됩니다
- 실제 거래를 위해서는 거래소 API 연동이 필요합니다
- 투자에는 위험이 따르므므로 충분한 테스트 후 사용하세요

## 🔧 업비트 거래소 연동

### API 키 발급
1. [업비트 Open API 관리](https://upbit.com/mypage/open_api_management)에서 API 키 발급
2. 권한 설정: 자산 조회, 주문 조회, 주문하기 체크
3. `python setup_upbit.py` 실행하여 환경변수 설정

### 실제 거래 활성화
`.env` 파일에서 `DRY_RUN=false`로 변경:
```bash
DRY_RUN=false  # 실제 거래 모드
```

### 보안 관리
- **환경변수 기반**: API 키를 안전하게 관리
- **Git 제외**: .env 파일은 Git에 업로드되지 않음  
- **자동 검증**: 설정 시 API 연결 테스트 자동 실행

## 📈 확장 가능성

- 다양한 매매 전략 추가
- 기술적 지표 활용
- 웹 대시보드 추가
- 알림 채널 확장 (Slack, Discord 등) 