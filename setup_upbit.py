#!/usr/bin/env python3
"""
업비트 API 연동 설정 스크립트
"""

import json
import os
from getpass import getpass

def setup_upbit_config():
    """업비트 API 설정"""
    print("=== 업비트 API 연동 설정 ===")
    print("업비트 Open API에서 발급받은 키를 입력해주세요.")
    print("https://upbit.com/mypage/open_api_management")
    print()
    
    access_key = input("Access Key: ").strip()
    secret_key = getpass("Secret Key (입력시 화면에 표시되지 않음): ").strip()
    
    if not access_key or not secret_key:
        print("❌ Access Key와 Secret Key를 모두 입력해주세요.")
        return False
    
    config = {
        "access_key": access_key,
        "secret_key": secret_key,
        "market_mapping": {
            "BTC/USDT": "KRW-BTC",
            "ETH/USDT": "KRW-ETH",
            "ADA/USDT": "KRW-ADA"
        },
        "min_order_amounts": {
            "KRW-BTC": 5000,
            "KRW-ETH": 5000,
            "KRW-ADA": 5000
        }
    }
    
    # 설정 저장
    config_dir = "config"
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, "upbit_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 업비트 설정이 저장되었습니다: {config_file}")
    
    # API 연결 테스트
    print("\n📡 API 연결 테스트 중...")
    try:
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

def main():
    print("🚀 ATS v2 업비트 연동 설정")
    
    if setup_upbit_config():
        print("\n🎉 설정이 완료되었습니다!")
        print("이제 main.py를 실행하여 실제 거래를 시작할 수 있습니다.")
        print("\n⚠️  주의사항:")
        print("- 모의거래에서 충분히 테스트 후 실제 거래를 진행하세요")
        print("- 투자는 본인 책임하에 진행하세요")
        print("- 손실 가능성을 충분히 고려하세요")
    else:
        print("\n❌ 설정에 실패했습니다. 다시 시도해주세요.")

if __name__ == "__main__":
    main() 