import difflib
import json

from workflow import run_workflow

if __name__ == "__main__":
    input_data = {
        "conversation_thread": "...",
        "channel": "LinkedIn",
        "prospect_profile_url": "https://linkedin.com/in/example",
        "prospect_company_url": "https://linkedin.com/company/example",
        "prospect_company_website": "https://example.com",
        "qubit_context": "Qubit Capital context or product info here",
    }
    result = run_workflow(**input_data)
    print(json.dumps(result, indent=2))


def safe_exec_python(code: str, input_data: dict) -> dict:
    """
    Safely execute a Python code snippet with input_data as local variables.
    Returns a dict with 'result' or 'error'.
    """
    # Restrict builtins
    safe_builtins = {
        "range": range,
        "len": len,
        "min": min,
        "max": max,
        "sum": sum,
        "sorted": sorted,
        "abs": abs,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "list": list,
        "dict": dict,
        "set": set,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
    }
    local_vars = dict(input_data)
    try:
        compiled = compile(code, "<python_step>", "exec")
        exec(compiled, {"__builtins__": safe_builtins}, local_vars)
        return {"result": local_vars.get("result", None)}
    except Exception as e:
        return {"error": str(e)}


# GED utility


def generalized_edit_distance(a, b):
    """Compute the Levenshtein (edit) distance between two strings or lists."""
    return difflib.SequenceMatcher(None, a, b).ratio()


# Data sorting utility


def sort_data(data, key=None, reverse=False):
    """Sort a list of dicts or primitives by key (if dicts)."""
    if isinstance(data, list) and data and isinstance(data[0], dict) and key:
        return sorted(data, key=lambda x: x.get(key), reverse=reverse)
    return sorted(data, reverse=reverse)
