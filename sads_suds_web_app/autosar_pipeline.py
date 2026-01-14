from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, Field


class FunctionInfo(BaseModel):
    name: str
    signature: str = ""
    file: str = ""
    line: int = 0
    storage: str = ""
    swc: str = ""
    evidence: str = ""
    confidence: str = "high"


class VariableInfo(BaseModel):
    name: str
    vartype: str = ""
    file: str = ""
    line: int = 0
    storage: str = ""
    swc: str = ""
    evidence: str = ""
    confidence: str = "high"


class RteInterfaceInfo(BaseModel):
    api: str
    direction: str
    port: str = ""
    data_element: str = ""
    callee: str = ""
    caller_function: str = ""
    file: str = ""
    line: int = 0
    swc: str = ""
    evidence: str = ""
    confidence: str = "high"


class PipelineState(BaseModel):
    source_files: Dict[str, str] = Field(default_factory=dict)
    build_config: Dict[str, Any] = Field(default_factory=dict)
    preprocessed_files: Dict[str, str] = Field(default_factory=dict)
    swc_candidates: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    functions: List[FunctionInfo] = Field(default_factory=list)
    variables: List[VariableInfo] = Field(default_factory=list)
    rte_interfaces: List[RteInterfaceInfo] = Field(default_factory=list)
    csv_path: str = ""


RTE_PATTERNS = [
    (r"\bRte_Read_([A-Za-z0-9_]+)\b", "read"),
    (r"\bRte_IRead_([A-Za-z0-9_]+)\b", "read"),
    (r"\bRte_Write_([A-Za-z0-9_]+)\b", "write"),
    (r"\bRte_IWrite_([A-Za-z0-9_]+)\b", "write"),
    (r"\bRte_IStatus_([A-Za-z0-9_]+)\b", "status"),
    (r"\bRte_Call_([A-Za-z0-9_]+)\b", "call"),
    (r"\bRte_IrvRead_([A-Za-z0-9_]+)\b", "irvread"),
    (r"\bRte_IrvWrite_([A-Za-z0-9_]+)\b", "irvwrite"),
    (r"\bRte_Prm_([A-Za-z0-9_]+)\b", "prm"),
    (r"\bRte_Mode_([A-Za-z0-9_]+)\b", "mode"),
    (r"\bRte_Switch_([A-Za-z0-9_]+)\b", "switch"),
]

COMMENT_BLOCK = re.compile(r"/\*.*?\*/", re.DOTALL)
COMMENT_LINE = re.compile(r"//.*?$", re.MULTILINE)

FUNC_DEF_REGEX = re.compile(
    r"""(?P<storage>\bstatic\b\s+)?(?P<rtype>[A-Za-z_][\w\s\*\(\)]*?)\s+
        (?P<name>[A-Za-z_]\w*)\s*\((?P<params>[^;]*?)\)\s*\{""",
    re.VERBOSE | re.MULTILINE
)

GLOBAL_VAR_REGEX = re.compile(
    r"""^(?P<storage>\bstatic\b\s+)?(?P<type>[A-Za-z_][\w\s\*]*?)\s+
        (?P<name>[A-Za-z_]\w*)\s*(=\s*[^;]+)?\s*;""",
    re.VERBOSE | re.MULTILINE
)


def strip_comments(code: str) -> str:
    code = re.sub(COMMENT_BLOCK, "", code)
    code = re.sub(COMMENT_LINE, "", code)
    return code


def guess_swc_from_filename(path: str) -> Optional[str]:
    base = os.path.basename(path)
    m = re.match(r"Rte_([A-Za-z0-9_]+)\.(h|c)$", base)
    if m:
        return m.group(1)

    parts = path.replace("\\", "/").split("/")
    if len(parts) >= 2:
        parent = parts[-2]
        if re.match(r"^[A-Za-z][A-Za-z0-9_]*$", parent):
            return parent
    return None


def best_effort_parse_rte_name(api: str, direction: str) -> Tuple[str, str, str]:
    if "_" not in api:
        return "", "", ""
    tail = api[4:] if api.startswith("Rte_") else api
    chunks = tail.split("_", 1)
    if len(chunks) != 2:
        return "", "", ""
    rest = chunks[1]
    parts = rest.split("_")
    if len(parts) < 2:
        return "", "", ""
    port = parts[0]
    de_or_op = "_".join(parts[1:])
    if direction == "call":
        return port, "", de_or_op
    else:
        return port, de_or_op, ""


def line_number_at_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def extract_with_regex_fallback(preprocessed_files: Dict[str, str], issues: List[str]) -> Tuple[List[FunctionInfo], List[VariableInfo]]:
    functions: List[FunctionInfo] = []
    variables: List[VariableInfo] = []

    for path, code in preprocessed_files.items():
        for m in FUNC_DEF_REGEX.finditer(code):
            name = m.group("name")
            storage = "static" if m.group("storage") else "unknown"
            rtype = " ".join(m.group("rtype").split())
            params = " ".join(m.group("params").split())
            sig = f"{rtype} {name}({params})"
            line = line_number_at_offset(code, m.start())
            functions.append(FunctionInfo(
                name=name,
                signature=sig,
                file=path,
                line=line,
                storage=storage,
                confidence="low",
                evidence="regex fallback (function def pattern)"
            ))

        for m in GLOBAL_VAR_REGEX.finditer(code):
            name = m.group("name")
            vartype = " ".join(m.group("type").split())
            storage = "static" if m.group("storage") else "unknown"
            line = line_number_at_offset(code, m.start())
            variables.append(VariableInfo(
                name=name,
                vartype=vartype,
                file=path,
                line=line,
                storage=storage,
                confidence="low",
                evidence="regex fallback (global var pattern)"
            ))

    issues.append("Fallback(regex) 모드로 심볼을 추출했습니다. (정확도 보장 불가: 매크로/헤더/조건부 컴파일 영향)")
    return functions, variables


def find_enclosing_function_by_line(functions: List[FunctionInfo], file: str, line: int) -> str:
    candidates = [f for f in functions if f.file == file and f.line <= line]
    if not candidates:
        return ""
    return sorted(candidates, key=lambda x: x.line)[-1].name


def extract_rte_calls(preprocessed_files: Dict[str, str], functions: List[FunctionInfo]) -> List[RteInterfaceInfo]:
    rte_list: List[RteInterfaceInfo] = []
    for path, code in preprocessed_files.items():
        for pat, direction in RTE_PATTERNS:
            for m in re.finditer(pat, code):
                api = m.group(0)
                line = line_number_at_offset(code, m.start())
                port, de, callee = best_effort_parse_rte_name(api, direction)

                caller = find_enclosing_function_by_line(functions, path, line)
                conf = "high" if caller else "low"
                ev = f"regex match: {pat}"
                if not caller:
                    ev += " | caller function unresolved"

                rte_list.append(RteInterfaceInfo(
                    api=api,
                    direction=direction,
                    port=port,
                    data_element=de,
                    callee=callee,
                    caller_function=caller,
                    file=path,
                    line=line,
                    confidence=conf,
                    evidence=ev
                ))
    return rte_list


def run_pipeline(source_files: Dict[str, str], build_config: Optional[Dict[str, Any]] = None) -> PipelineState:
    build_config = build_config or {}
    state = PipelineState(source_files=source_files, build_config=build_config)
    
    # Preprocess
    pre: Dict[str, str] = {}
    for path, code in state.source_files.items():
        norm = code.replace("\r\n", "\n").replace("\r", "\n")
        pre[path] = strip_comments(norm)
    state.preprocessed_files = pre
    
    # SWC candidates
    swcs = set()
    for path in state.preprocessed_files.keys():
        swc = guess_swc_from_filename(path)
        if swc:
            swcs.add(swc)
    state.swc_candidates = sorted(swcs)
    if not state.swc_candidates:
        state.issues.append("SWC 후보를 파일/경로 기반으로 추정하지 못했습니다. (SWC 매핑 정확도 저하 가능)")
    
    # Extract symbols
    ok, funcs, vars_ = try_extract_with_libclang(state.preprocessed_files, state.build_config, state.issues)
    if not ok:
        funcs, vars_ = extract_with_regex_fallback(state.preprocessed_files, state.issues)
    state.functions = funcs
    state.variables = vars_
    
    # Extract RTE
    state.rte_interfaces = extract_rte_calls(state.preprocessed_files, state.functions)
    
    # Map to SWC
    def map_item(file_path: str) -> Tuple[str, str, str]:
        swc = guess_swc_from_filename(file_path) or ""
        if swc:
            return swc, "high", f"SWC inferred from path/filename: {file_path}"
        return "", "low", f"SWC unresolved for file: {file_path}"

    for f in state.functions:
        swc, conf, ev = map_item(f.file)
        f.swc = swc
        if f.confidence == "low" and conf == "high":
            f.confidence = "medium"
        elif f.confidence != "low":
            f.confidence = conf
        f.evidence += f" | {ev}"

    for v in state.variables:
        swc, conf, ev = map_item(v.file)
        v.swc = swc
        if v.confidence == "low" and conf == "high":
            v.confidence = "medium"
        elif v.confidence != "low":
            v.confidence = conf
        v.evidence += f" | {ev}"

    for r in state.rte_interfaces:
        swc, conf, ev = map_item(r.file)
        r.swc = swc
        if r.confidence == "low" and conf == "high":
            r.confidence = "medium"
        elif r.confidence != "low":
            r.confidence = conf
        r.evidence += f" | {ev}"

    unresolved = sum(1 for x in (state.functions + state.variables) if not x.swc)
    if unresolved:
        state.issues.append(f"{unresolved}개 심볼이 SWC에 결정적으로 매핑되지 않았습니다(규칙 기반).")
    
    # Export CSV
    rows: List[Dict[str, Any]] = []

    for f in state.functions:
        rows.append({
            "swc": f.swc,
            "kind": "function",
            "name": f.name,
            "signature": f.signature,
            "scope": f.storage,
            "file": f.file,
            "line": f.line,
            "direction": "",
            "port": "",
            "data_element": "",
            "callee": "",
            "caller_function": "",
            "confidence": f.confidence,
            "evidence": f.evidence,
        })

    for v in state.variables:
        rows.append({
            "swc": v.swc,
            "kind": "variable",
            "name": v.name,
            "signature": v.vartype,
            "scope": v.storage,
            "file": v.file,
            "line": v.line,
            "direction": "",
            "port": "",
            "data_element": "",
            "callee": "",
            "caller_function": "",
            "confidence": v.confidence,
            "evidence": v.evidence,
        })

    for r in state.rte_interfaces:
        rows.append({
            "swc": r.swc,
            "kind": "rte_interface",
            "name": r.api,
            "signature": "",
            "scope": "",
            "file": r.file,
            "line": r.line,
            "direction": r.direction,
            "port": r.port,
            "data_element": r.data_element,
            "callee": r.callee,
            "caller_function": r.caller_function,
            "confidence": r.confidence,
            "evidence": r.evidence,
        })

    df = pd.DataFrame(rows)
    out = state.build_config.get("output_csv", "autosar_swc_extract.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    state.csv_path = out
    
    # Quality report
    low_or_med = 0
    for x in state.functions + state.variables:
        if x.confidence in ("low", "medium"):
            low_or_med += 1
    for x in state.rte_interfaces:
        if x.confidence in ("low", "medium"):
            low_or_med += 1

    if low_or_med:
        state.issues.append(f"총 {low_or_med}개 항목이 low/medium confidence 입니다. CSV 결과를 검증하세요.")
    
    return state


def try_extract_with_libclang(preprocessed_files: Dict[str, str], build_config: Dict[str, Any], issues: List[str]) -> Tuple[bool, List[FunctionInfo], List[VariableInfo]]:
    try:
        from clang.cindex import Index, TranslationUnit, Config, CursorKind, StorageClass
    except Exception:
        return False, [], []

    libclang_path = build_config.get("libclang_path")
    if libclang_path:
        try:
            Config.set_library_file(libclang_path)
        except Exception:
            issues.append(f"libclang_path 설정 실패: {libclang_path}")

    include_dirs: List[str] = build_config.get("include_dirs", [])
    defines: Dict[str, str] = build_config.get("defines", {})
    extra_flags: List[str] = build_config.get("extra_flags", [])

    clang_args: List[str] = []
    for inc in include_dirs:
        clang_args += ["-I", inc]
    for k, v in defines.items():
        if v is None or v == "":
            clang_args += [f"-D{k}"]
        else:
            clang_args += [f"-D{k}={v}"]
    clang_args += extra_flags

    idx = Index.create()
    functions: List[FunctionInfo] = []
    variables: List[VariableInfo] = []

    c_files = [p for p in preprocessed_files.keys() if p.endswith(".c")]
    if not c_files:
        c_files = list(preprocessed_files.keys())

    for path in c_files:
        code = preprocessed_files[path]
        unsaved = [(path, code)]
        try:
            tu = idx.parse(
                path,
                args=clang_args,
                unsaved_files=unsaved,
                options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
            )
        except Exception as e:
            issues.append(f"libclang parse 실패({path}): {e}")
            return False, [], []

        for d in tu.diagnostics:
            if d.severity >= 3:
                issues.append(f"libclang diagnostic({path}): {d}")

        def walk(cursor):
            nonlocal functions, variables
            for c in cursor.get_children():
                if c.kind == CursorKind.FUNCTION_DECL and c.is_definition():
                    loc = c.location
                    storage = "static" if c.storage_class == StorageClass.STATIC else "global"
                    sig = f"{c.result_type.spelling} {c.spelling}(" + ", ".join(
                        [f"{a.type.spelling} {a.spelling}".strip() for a in c.get_arguments()]
                    ) + ")"
                    functions.append(FunctionInfo(
                        name=c.spelling,
                        signature=sig,
                        file=str(loc.file) if loc.file else path,
                        line=loc.line or 0,
                        storage=storage,
                        confidence="high",
                        evidence="libclang AST"
                    ))

                if c.kind == CursorKind.VAR_DECL:
                    loc = c.location
                    storage = "static" if c.storage_class == StorageClass.STATIC else "global"
                    variables.append(VariableInfo(
                        name=c.spelling,
                        vartype=c.type.spelling,
                        file=str(loc.file) if loc.file else path,
                        line=loc.line or 0,
                        storage=storage,
                        confidence="high",
                        evidence="libclang AST"
                    ))
                walk(c)

        walk(tu.cursor)

    return True, functions, variables


def load_c_files_from_directory(directory_path: str) -> Dict[str, str]:
    """Load all .c files from directory and subdirectories"""
    source_files = {}
    
    if not os.path.exists(directory_path):
        return source_files
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".c"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    source_files[file_path] = content
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return source_files
