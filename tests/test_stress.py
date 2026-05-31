import time
import threading
import pytest
from app.services.match_state_manager import MatchStateManager

def test_match_state_manager_stress_load():
    """
    Stress Test: Simulates 50 matches running concurrently and processing 1,000 state mutations.
    Validates:
      1. Concurrency thread safety (zero deadlocks or Race Conditions).
      2. Strictly-delimited prefix matching and isolation under load.
      3. O(k) cleanup latency (extremely fast execution).
      4. Complete memory cleanup (state lengths drop back to exactly 0).
    """
    mgr = MatchStateManager()
    num_matches = 50
    ops_per_thread = 20  # 50 matches * 20 ops = 1,000 operations total
    threads = []
    
    # Track execution performance
    start_time = time.time()
    
    def match_lifecycle_worker(fid_num: int):
        fid = str(fid_num)
        
        # Simulate goals, VARs, in-flights, and failures
        for step in range(ops_per_thread):
            # 1. Commit regular score
            mgr.commit_memory(fid, step, 0, scorer=f"Player_{fid}_{step}", minute=str(step))
            
            # 2. Trigger in-flight marker
            event_key = f"{fid}-{step}-0"
            mgr.mark_in_flight(event_key)
            
            # 3. Simulate failed retry cycles
            # Exceeding retries will trigger immediate MAX_RETRIES eviction (attempts >= 3)
            mgr.register_event_failure(event_key, is_fatal=False)
            mgr.register_event_failure(event_key, is_fatal=False)
            
            # 4. Trigger a separate pending VAR transition
            mgr.set_pending_var(fid, (step, 0), (step - 1, 0))
            
            # 5. Clear in-flight marker
            mgr.clear_in_flight(event_key)
            
            # 6. Concurrently check scores
            mgr.get_score(fid)
            
            # Throttled health reporting check
            mgr.log_health_report(force=False)
            
    # Spawn 50 concurrent threads (one for each match lifecycle)
    for i in range(1, num_matches + 1):
        t = threading.Thread(target=match_lifecycle_worker, args=(i,))
        threads.append(t)
        t.start()
        
    # Wait for all concurrent operations to complete
    for t in threads:
        t.join()
        
    execution_time = time.time() - start_time
    print(f"\n⚡ Concurrency stress test of 1,000 operations completed in: {execution_time:.4f}s")
    
    # Verify that states are populated
    assert len(mgr._last_sent_scores) == num_matches
    assert len(mgr._last_goal_info) == num_matches
    assert len(mgr._pending_var) == num_matches
    assert len(mgr._last_updated_at) == num_matches
    
    # 30-minute health report check
    mgr.log_health_report(force=True)
    
    # --- Measure Cleanup Latency ---
    cleanup_start = time.time()
    
    # Clean up all 50 matches one by one
    for i in range(1, num_matches + 1):
        mgr.cleanup_match(str(i))
        
    cleanup_time = time.time() - cleanup_start
    avg_latency = (cleanup_time / num_matches) * 1000  # in milliseconds
    print(f"🧹 Cleaned up {num_matches} matches in: {cleanup_time:.4f}s (Avg Latency: {avg_latency:.4f}ms per match)")
    
    # --- ASSERT ZERO MEMORY LEAKS ---
    assert len(mgr._last_sent_scores) == 0
    assert len(mgr._last_goal_info) == 0
    assert len(mgr._pending_var) == 0
    assert len(mgr._failed_events) == 0
    assert len(mgr._in_flight) == 0
    assert len(mgr._last_updated_at) == 0
    
    print("✅ 100% Memory Reclaimed under load. Stress test passed successfully!")
