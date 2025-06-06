#!/usr/bin/env python3
"""
ATS v2 - 멀티자산 자동 거래 시스템
"""

import signal
import sys
import time
from core.engine.manager import TraderManager
from core.config import config
from utils.logger import get_logger

logger = get_logger("ATS_V2_Main")

def signal_handler(signum, frame):
    """시그널 핸들러"""
    logger.info(f"시그널 {signum} 수신, 종료 준비 중...")
    if 'manager' in globals():
        manager.stop()
    sys.exit(0)

def main():
    """메인 함수"""
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=== ATS v2 멀티자산 트레이딩 시스템 시작 ===")
    
    try:
        # 트레이딩 매니저 초기화 (환경변수 기반)
        global manager
        manager = TraderManager()  # 환경변수에서 설정 로드
        
        # 현재 모드 출력
        mode = "모의거래" if config.dry_run else "실제거래"
        logger.info(f"거래 모드: {mode}")
        if config.has_api_keys:
            logger.info("업비트 API 키 설정 확인됨")
        else:
            logger.warning("업비트 API 키 미설정 - 모의거래만 가능")
        
        # 시스템 시작
        manager.start()
        
        # 메인 루프
        while True:
            try:
                time.sleep(60)  # 1분마다 상태 체크
                status = manager.get_overall_status()
                
                if status["manager"]["is_running"]:
                    active_engines = status["manager"]["active_threads"]
                    total_engines = status["manager"]["total_engines"]
                    logger.info(f"시스템 정상 동작 중: {active_engines}/{total_engines} 엔진 활성")
                else:
                    logger.warning("매니저가 중지되었습니다")
                    break
                    
            except KeyboardInterrupt:
                logger.info("사용자 중단 요청")
                break
                
    except Exception as e:
        logger.error(f"시스템 오류: {e}")
        
    finally:
        logger.info("시스템 종료 중...")
        if 'manager' in globals():
            manager.stop()
        logger.info("=== ATS v2 종료 완료 ===")

if __name__ == "__main__":
    main() 