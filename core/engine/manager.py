import json
import time
import threading
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, Future
from core.engine.trader import TraderEngine
from core.config import config
from utils.logger import get_logger

logger = get_logger(__name__)

class TraderManager:
    """멀티자산 트레이딩 매니저

    각 자산별 엔진을 ThreadPoolExecutor에서 병렬로 실행한다.
    """
    
    def __init__(self, config_file: str = "config/assets.json", dry_run: bool = None):
        self.config_file = config_file
        # 환경변수에서 설정 가져오기
        self.dry_run = dry_run if dry_run is not None else config.dry_run
        self.engines = {}
        self.is_running = False
        self.engine_futures: Dict[str, Future] = {}
        self.executor: ThreadPoolExecutor | None = None
        self.status_update_interval = config.status_update_interval
        self.run_interval = config.polling_interval

        self._load_assets()
        self.max_workers = config.max_workers or len(self.engines)
        logger.info(f"트레이딩 매니저 초기화 완료: {len(self.engines)}개 자산")
    
    def _load_assets(self):
        """자산 설정 로드 및 엔진 초기화"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                assets = json.load(f)
            
            for asset in assets:
                symbol = asset["symbol"]
                engine = TraderEngine(asset, self.dry_run)
                self.engines[symbol] = engine
                logger.info(f"[{symbol}] 엔진 로드 완료")
                
        except Exception as e:
            logger.error(f"자산 설정 로드 실패: {e}")
            raise
    
    def start(self):
        """전체 매니저 시작"""
        if self.is_running:
            logger.warning("이미 실행 중입니다")
            return
        
        self.is_running = True
        logger.info("트레이딩 매니저 시작")
        
        # 각 엔진 시작
        for symbol, engine in self.engines.items():
            engine.start()
        
        # 병렬 실행 시작
        self._start_parallel_execution()
        
        # 상태 업데이트 쓰레드 시작
        self._start_status_thread()
    
    def stop(self):
        """전체 매니저 중지"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("트레이딩 매니저 중지 중...")
        
        # 각 엔진 중지
        for symbol, engine in self.engines.items():
            engine.stop()
        
        # 풀 종료 대기
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
            self.engine_futures.clear()

        logger.info("트레이딩 매니저 중지 완료")

    def _start_parallel_execution(self):
        """병렬 실행 시작 (ThreadPoolExecutor 사용)"""
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        for symbol, engine in self.engines.items():
            future = self.executor.submit(self._run_engine_loop, symbol, engine)
            self.engine_futures[symbol] = future
            logger.info(f"[{symbol}] 엔진 작업 제출")
    
    def _run_engine_loop(self, symbol: str, engine: TraderEngine):
        """개별 엔진 실행 루프"""
        logger.info(f"[{symbol}] 엔진 루프 시작")
        
        while self.is_running and engine.is_running:
            try:
                success = engine.run_once()
                if not success:
                    logger.warning(f"[{symbol}] 실행 실패, 대기 후 재시도")
                
                time.sleep(self.run_interval)
                
            except Exception as e:
                logger.error(f"[{symbol}] 루프 오류: {e}")
                time.sleep(self.run_interval * 2)  # 오류시 더 긴 대기
        
        logger.info(f"[{symbol}] 엔진 루프 종료")
    
    def _start_status_thread(self):
        """상태 업데이트 쓰레드 시작"""
        def status_loop():
            while self.is_running:
                try:
                    self._send_status_updates()
                    time.sleep(self.status_update_interval)
                except Exception as e:
                    logger.error(f"상태 업데이트 오류: {e}")
                    time.sleep(60)
        
        status_thread = threading.Thread(
            target=status_loop,
            name="StatusUpdater",
            daemon=True
        )
        status_thread.start()
        logger.info("상태 업데이트 쓰레드 시작")
    
    def _send_status_updates(self):
        """모든 엔진의 상태 알림 전송"""
        for symbol, engine in self.engines.items():
            try:
                engine.send_status_notification()
            except Exception as e:
                logger.error(f"[{symbol}] 상태 알림 실패: {e}")
    
    def get_overall_status(self) -> Dict:
        """전체 시스템 상태 반환"""
        status = {
            "manager": {
                "is_running": self.is_running,
                "total_engines": len(self.engines),
                "active_threads": sum(1 for f in self.engine_futures.values() if not f.done()),
                "dry_run": self.dry_run
            },
            "engines": {}
        }
        
        total_value = 0
        total_profit = 0
        
        for symbol, engine in self.engines.items():
            engine_status = engine.get_status()
            status["engines"][symbol] = engine_status
            
            # 전체 수익 계산
            portfolio = engine_status.get("portfolio", {})
            if portfolio.get("current_value"):
                total_value += portfolio["current_value"]
            if portfolio.get("profit"):
                total_profit += portfolio["profit"]
        
        status["manager"]["total_value"] = total_value
        status["manager"]["total_profit"] = total_profit
        status["manager"]["total_profit_rate"] = (total_profit / total_value * 100) if total_value > 0 else 0
        
        return status
    
    def reload_config(self):
        """설정 다시 로드"""
        logger.info("설정 다시 로드 시작")
        
        # 기존 엔진 중지
        for engine in self.engines.values():
            engine.stop()
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
            self.engine_futures.clear()
        
        # 새 설정 로드
        self.engines.clear()
        self._load_assets()
        
        # 실행 중이면 다시 시작
        if self.is_running:
            for engine in self.engines.values():
                engine.start()
            self._start_parallel_execution()
        
        logger.info("설정 다시 로드 완료")
    
    def add_asset(self, asset_config: Dict):
        """새 자산 추가"""
        symbol = asset_config["symbol"]
        if symbol in self.engines:
            logger.warning(f"[{symbol}] 이미 존재하는 자산")
            return
        
        engine = TraderEngine(asset_config, self.dry_run)
        self.engines[symbol] = engine
        
        if self.is_running:
            engine.start()
            if self.executor is None:
                self._start_parallel_execution()
            else:
                future = self.executor.submit(self._run_engine_loop, symbol, engine)
                self.engine_futures[symbol] = future
        
        logger.info(f"[{symbol}] 새 자산 추가 완료")
    
    def remove_asset(self, symbol: str):
        """자산 제거"""
        if symbol not in self.engines:
            logger.warning(f"[{symbol}] 존재하지 않는 자산")
            return
        
        # 엔진 중지
        self.engines[symbol].stop()
        
        # 실행 중인 Future 종료 대기
        if symbol in self.engine_futures:
            future = self.engine_futures.pop(symbol)
            try:
                future.result(timeout=5)
            except Exception:
                pass
        
        # 엔진 제거
        del self.engines[symbol]
        logger.info(f"[{symbol}] 자산 제거 완료") 
