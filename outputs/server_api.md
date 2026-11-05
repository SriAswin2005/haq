# Server API test results

Mode: mock/offline; 8 tests; successful=True.
Source input hashes stable during tests: True. Run evidence: C:\E drive\KuKu Technologies\ai-lawyer\outputs\runs\api-mock-20261105T223005.562739Z.
TestClient checks ordered SSE content, not proxy buffering or time-to-first-event over a network.
Feedback privacy assertions cover question/answer text; user-entered feedback reasons remain metadata.

- __main__.ServerAPITests.test_browser_state_restores_after_session_cache_is_cleared: pass (0.164 s)
- __main__.ServerAPITests.test_feedback_explicit_false_also_omits_text: pass (0.028 s)
- __main__.ServerAPITests.test_feedback_omits_question_and_answer_by_default: pass (0.037 s)
- __main__.ServerAPITests.test_feedback_stores_conversation_only_with_explicit_consent: pass (0.040 s)
- __main__.ServerAPITests.test_rate_limit_is_shared_by_turn_and_stream_and_blocks_work: pass (0.039 s)
- __main__.ServerAPITests.test_real_flag_without_environment_key_is_rejected_before_app_import: pass (0.319 s)
- __main__.ServerAPITests.test_stream_error_is_terminal_and_does_not_echo_exception_text: pass (0.010 s)
- __main__.ServerAPITests.test_stream_stage_order_and_final_result: pass (0.108 s)
