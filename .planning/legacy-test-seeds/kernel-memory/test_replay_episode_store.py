from agent.replay_episode_store import ReplayEpisodeStore


def test_replay_episode_store_records_structured_episode(tmp_path):
    store = ReplayEpisodeStore.from_env_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "episodes"),
            "min_messages": 4,
        },
        hermes_home=tmp_path,
    )

    older_messages = [
        {"role": "user", "content": "Investigate why nginx is failing in production."},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "terminal",
                        "arguments": "{\"command\":\"tail -n 200 /var/log/nginx/error.log\"}",
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": "permission denied at /var/log/nginx/error.log",
            "artifact_ref": {
                "artifact_id": "art_nginx123",
                "summary": "nginx error log shows permission denied",
            },
        },
        {"role": "assistant", "content": "I found a permission issue around the nginx error log."},
    ]
    summary_message = {
        "role": "assistant",
        "content": "[REPLAY LENS] nginx investigation summary",
    }

    episode = store.record_condensed_history(
        session_id="sess_episode",
        source_start_index=0,
        older_messages=older_messages,
        summary_message=summary_message,
        session_started_at=1775000000,
    )

    assert episode is not None
    assert episode["episode_id"].startswith("ep_")
    assert "On " in episode["summary"]
    assert "Investigate why nginx is failing" in episode["summary"]
    assert "terminal" in episode["tools_used_json"]
    assert "art_nginx123" in episode["artifact_refs_json"]
    assert episode["lifecycle_state"] == "new"
    assert episode["access_count"] == 0


def test_replay_episode_store_deduplicates_same_source_range(tmp_path):
    store = ReplayEpisodeStore.from_env_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "episodes"),
            "min_messages": 2,
        },
        hermes_home=tmp_path,
    )
    older_messages = [
        {"role": "user", "content": "Check auth bug."},
        {"role": "assistant", "content": "I found the auth issue."},
    ]
    summary_message = {"role": "assistant", "content": "summary"}

    first = store.record_condensed_history(
        session_id="sess_episode",
        source_start_index=0,
        older_messages=older_messages,
        summary_message=summary_message,
    )
    second = store.record_condensed_history(
        session_id="sess_episode",
        source_start_index=0,
        older_messages=older_messages,
        summary_message=summary_message,
    )

    assert first is not None
    assert second is not None
    assert first["episode_id"] == second["episode_id"]
    assert second["lifecycle_state"] == "active"
    assert int(second["access_count"]) == 1

    third = store.record_condensed_history(
        session_id="sess_episode",
        source_start_index=0,
        older_messages=older_messages,
        summary_message=summary_message,
    )

    assert third is not None
    assert third["episode_id"] == first["episode_id"]
    assert third["lifecycle_state"] == "reinforced"
    assert int(third["access_count"]) == 2

    stats = store.session_stats("sess_episode")
    assert stats["total"] == 1
    assert stats["reinforced"] == 1
    assert stats["total_access_count"] == 2
    assert stats["promoted"] == 1
