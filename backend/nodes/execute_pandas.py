import pandas as pd
import numpy as np


ALLOWED_BUILTINS = {"len": len, "range": range, "round": round, "print": print}


def execute_pandas(state: dict) -> dict:
    code = state["pandas_code"]
    df = state["df"]  # passed in by graph, loaded once at session start

    sandbox = {"df": df, "pd": pd, "np": np, **ALLOWED_BUILTINS}

    try:
        result = eval(code, {"__builtins__": {}}, sandbox)  # no builtins = no imports/os/sys
        return {**state, "result": result, "error": ""}
    except Exception as e:
        return {**state, "result": None, "error": str(e)}