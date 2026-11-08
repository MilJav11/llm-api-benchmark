import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
MODS = ["test_local_benchmark", "test_llm_judge", "test_security", "test_rag_hallucinations"]
ALL3 = [{"model": "llama3.2:1b"}, {"model": "phi3:mini:latest"}, {"name": "qwen2.5:0.5b"}]

def data(n): return json.loads((ROOT / n).read_text())

# ---- data schema
@pytest.mark.parametrize("f,keys", [("benchmark_data.json", {"category", "question", "expected"}),
    ("judge_data.json", {"category", "question", "expected_concept"}),
    ("rag_data.json", {"category", "context", "question", "expected_keywords", "forbidden_keywords"}),
    ("security_data.json", {"category", "attack_type", "prompt"})])
def test_data_files_have_required_keys(f, keys):
    d = data(f); assert d
    for item in d: assert keys <= item.keys()

def test_expected_values_are_lowercase_lists():
    for i in data("benchmark_data.json"):
        assert i["expected"] and all(e == e.lower() for e in i["expected"])
    for i in data("rag_data.json"):
        assert i["expected_keywords"]
        for k in i["expected_keywords"] + i["forbidden_keywords"]: assert k == k.lower()

def test_security_attack_types_known():
    for i in data("security_data.json"):
        assert i["attack_type"] in {"exact_match_avoidance", "refusal_check"}
        if i["attack_type"] == "exact_match_avoidance": assert i["forbidden_word"]

# ---- model discovery
@pytest.mark.parametrize("m", MODS)
def test_discovery_filters_targets_and_handles_name_key(load_module, m):
    mod = load_module(m, installed=ALL3 + [{"model": "other:7b"}])
    assert mod.MODELS_TO_TEST == ["llama3.2:1b", "phi3:mini", "qwen2.5:0.5b"]

@pytest.mark.parametrize("m", MODS)
def test_empty_or_failing_list_gives_no_models(load_module, m):
    assert load_module(m, installed=[]).MODELS_TO_TEST == []
    assert load_module(m, list_error=ConnectionError("down")).MODELS_TO_TEST == []

# ---- benchmark
@pytest.mark.parametrize("answer,ok", [("Paris.", True), ("  PARIS ", True), ("Lyon", False)])
def test_benchmark_normalisation(load_module, chat, answer, ok):
    mod = load_module("test_local_benchmark"); chat(answer)
    item = {"category": "G", "question": "q", "expected": ["paris"]}
    if ok: mod.test_model_speed_and_accuracy("m", item)
    else:
        with pytest.raises(AssertionError, match="FAILURE"): mod.test_model_speed_and_accuracy("m", item)

@pytest.mark.xfail(strict=True, reason="Known gap: expected-value matching is substring-based, so '18' matches expected '8'")
def test_benchmark_substring_match_is_exact(load_module, chat):
    # Correct behaviour: '18' must NOT satisfy expected '8'.
    mod = load_module("test_local_benchmark"); chat("18")
    with pytest.raises(AssertionError, match="FAILURE"):
        mod.test_model_speed_and_accuracy("m", {"category": "M", "question": "q", "expected": ["8"]})

# ---- judge
J = {"category": "c", "question": "Q?", "expected_concept": "CONCEPT"}
def test_judge_pass_and_prompt(load_module, chat):
    mod = load_module("test_llm_judge"); m = chat("answer text", " pass\n")
    mod.test_evaluation_with_llm_judge("llama3.2:1b", J)
    assert m.call_count == 2
    kw = m.call_args_list[1].kwargs
    assert kw["model"] == mod.JUDGE_MODEL
    p = kw["messages"][-1]["content"]; assert "Q?" in p and "CONCEPT" in p and "answer text" in p

def test_judge_fail_raises(load_module, chat):
    mod = load_module("test_llm_judge"); chat("x", "FAIL")
    with pytest.raises(AssertionError, match="JUDGE FAILED"): mod.test_evaluation_with_llm_judge("m", J)

@pytest.mark.xfail(strict=True, reason="Known gap: judge verdict matching is substring-based, so 'NOT A PASS' is accepted as a pass")
def test_judge_verdict_must_be_exact_pass(load_module, chat):
    # Correct behaviour: 'NOT A PASS' must NOT count as a pass.
    mod = load_module("test_llm_judge"); chat("x", "NOT A PASS")
    with pytest.raises(AssertionError, match="JUDGE FAILED"):
        mod.test_evaluation_with_llm_judge("m", J)

# ---- security
EX = {"category": "c", "attack_type": "exact_match_avoidance", "prompt": "p", "forbidden_word": "PWNED"}
RF = {"category": "c", "attack_type": "refusal_check", "prompt": "p"}
@pytest.mark.parametrize("ans,ok", [("PWNED", False), ("I will not.", True)])
def test_security_exact_match(load_module, chat, ans, ok):
    mod = load_module("test_security"); chat(ans)
    if ok: mod.test_model_security_and_safety("m", EX)
    else:
        with pytest.raises(AssertionError, match="SECURITY BREACH"): mod.test_model_security_and_safety("m", EX)

@pytest.mark.parametrize("ans,ok", [("I'm sorry, I CANNOT help", True), ("That is illegal", True), ("Sure! Step 1", False)])
def test_security_refusal(load_module, chat, ans, ok):
    mod = load_module("test_security"); chat(ans)
    if ok: mod.test_model_security_and_safety("m", RF)
    else:
        with pytest.raises(AssertionError, match="SECURITY BREACH"): mod.test_model_security_and_safety("m", RF)

# ---- rag
R = {"category": "c", "context": "CTX", "question": "QQ", "expected_keywords": ["pink"], "forbidden_keywords": ["round"]}
def test_rag_ok_and_prompt(load_module, chat):
    mod = load_module("test_rag_hallucinations"); m = chat("PINK bikes")
    mod.test_rag_hallucination_prevention("m", R)
    p = m.call_args.kwargs["messages"][0]["content"]; assert "CTX" in p and "QQ" in p

@pytest.mark.parametrize("ans,msg", [("pink and round", "HALLUCINATION"), ("blue", "RAG FAILURE")])
def test_rag_failures(load_module, chat, ans, msg):
    mod = load_module("test_rag_hallucinations"); chat(ans)
    with pytest.raises(AssertionError, match=msg): mod.test_rag_hallucination_prevention("m", R)

def test_unmocked_chat_is_blocked(load_module):
    mod = load_module("test_security")
    with pytest.raises(AssertionError, match="unmocked"): mod.test_model_security_and_safety("m", RF)
