#!/usr/bin/env python3
"""
업비트 API 연동 설정 스크립트 (환경변수 기반)
"""

import os
from getpass import getpass

def setup_env_file():
    """환경변수 파일 설정"""
    print("=== 업비트 API 연동 설정 (환경변수 기반) ===")
    print("업비트 Open API에서 발급받은 키를 입력해주세요.")
    print("https://upbit.com/mypage/open_api_management")
    print()
    
    access_key = input("Access Key: ").strip()
    secret_key = getpass("Secret Key (입력시 화면에 표시되지 않음): ").strip()
    
    if not access_key or not secret_key:
        print("❌ Access Key와 Secret Key를 모두 입력해주세요.")
        return False
    
    # .env 파일 생성
    env_content = f"""# 업비트 API 설정
UPBIT_ACCESS_KEY={access_key}
UPBIT_SECRET_KEY={secret_key}

# 거래 설정
DRY_RUN=true
LOG_LEVEL=INFO

# 알림 설정 (선택사항)
DISCORD_WEBHOOK_URL=
SLACK_WEBHOOK_URL=

# 시스템 설정
POLLING_INTERVAL=0.3
STATUS_UPDATE_INTERVAL=300
"""
    
    # .env 파일 저장
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ .env 파일이 생성되었습니다")
    
    # API 연결 테스트
    print("\n📡 API 연결 테스트 중...")
    try:
        # 환경변수 로드
        import os
        os.environ['UPBIT_ACCESS_KEY'] = access_key
        os.environ['UPBIT_SECRET_KEY'] = secret_key
        
        from core.upbit_client import UpbitClient
        
        client = UpbitClient(access_key, secret_key)
        accounts = client.get_accounts()
        
        if accounts:
            print("✅ API 연결 성공!")
            print(f"보유 자산 수: {len(accounts)}개")
            
            # KRW 잔고 확인
            krw_balance = 0
            for account in accounts:
                if account['currency'] == 'KRW':
                    krw_balance = float(account['balance'])
                    break
            
            print(f"원화 잔고: {krw_balance:,.0f} KRW")
            
            if krw_balance < 5000:
                print("⚠️  주의: 최소 주문 금액(5,000원) 미만입니다.")
            else:
                print("✅ 거래 가능한 잔고 확인됨")
        else:
            print("❌ API 연결 실패: 계좌 정보를 가져올 수 없습니다.")
            return False
            
    except Exception as e:
        print(f"❌ API 연결 테스트 실패: {e}")
        return False
    
    return True

def show_usage():
    """사용법 안내"""
    print("\n📚 사용법:")
    print("1. 실제 거래를 원한다면 .env 파일에서 DRY_RUN=false로 변경")
    print("2. python main.py 실행")
    print()
    print("🔧 환경변수 설정:")
    print("- DRY_RUN: 모의거래(true) / 실제거래(false)")
    print("- LOG_LEVEL: DEBUG, INFO, WARNING, ERROR")
    print("- POLLING_INTERVAL: 가격 조회 간격(초)")
    print("- STATUS_UPDATE_INTERVAL: 상태 알림 간격(초)")

def main():
    print("🚀 ATS v2 업비트 연동 설정 (환경변수 기반)")
    
    if setup_env_file():
        print("\n🎉 설정이 완료되었습니다!")
        show_usage()
        print("\n⚠️  주의사항:")
        print("- .env 파일에는 민감한 정보가 포함되어 있습니다")
        print("- .env 파일을 절대 공개하지 마세요")
        print("- Git에 커밋하지 않도록 주의하세요")
        print("- 모의거래에서 충분히 테스트 후 실제 거래를 진행하세요")
        print("- 투자는 본인 책임하에 진행하세요")
    else:
        print("\n❌ 설정에 실패했습니다. 다시 시도해주세요.")

if __name__ == "__main__":
    main() 