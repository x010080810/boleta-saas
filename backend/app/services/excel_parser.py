import pandas as pd
import os


def parse_excel(filepath: str) -> dict:
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".xls":
        df = pd.read_excel(filepath, engine="xlrd", header=None)
    else:
        df = pd.read_excel(filepath, engine="openpyxl", header=None)

    if df.empty:
        return {"empleados": [], "columnas_ing": [], "columnas_desc": [], "columnas_apor": []}

    header_row = None
    for idx in range(min(10, len(df))):
        row = df.iloc[idx].astype(str).str.strip().str.lower()
        if row.str.contains("tipo_documento").any() or row.str.contains("tipo documento").any():
            header_row = idx
            break

    if header_row is None:
        first_col = df.iloc[:, 0].astype(str).str.strip().str.lower()
        tipo_doc_rows = first_col[first_col.str.contains("01|dni|ce", na=False)]
        if not tipo_doc_rows.empty:
            header_row = 0
        else:
            if len(df) > 0:
                header_row = 0
            else:
                return {"empleados": [], "columnas_ing": [], "columnas_desc": [], "columnas_apor": []}

    df.columns = df.iloc[header_row].astype(str).str.strip().str.lower().str.replace(
        " ", "_"
    ).str.replace("á", "a").str.replace("é", "e").str.replace("í", "i").str.replace(
        "ó", "o"
    ).str.replace("ú", "u").str.replace("ñ", "n")

    df = df.iloc[header_row + 1:].reset_index(drop=True)

    col_map = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if "tipo" in col_lower and "documento" in col_lower:
            col_map["tipo_documento"] = col
        elif col_lower in ("numero_documento", "n_documento", "nro_documento", "documento", "n°"):
            col_map["numero_documento"] = col
        elif "apellidos" in col_lower or "nombre" in col_lower and "completo" in col_lower:
            col_map["apellidos_nombres"] = col
        elif col_lower in ("email", "correo", "correo_electronico", "e_mail", "mail"):
            col_map["email"] = col
        elif col_lower == "cargo":
            col_map["cargo"] = col
        elif "fecha" in col_lower and "ingreso" in col_lower:
            col_map["fecha_ingreso"] = col
        elif "dias" in col_lower and ("labor" in col_lower or "trabaj" in col_lower):
            col_map["dias_laborados"] = col
        elif col_lower in ("asignacion_familiar", "asignacion familiar"):
            col_map["asignacion_familiar"] = col
        elif col_lower in ("total_ingresos", "total ingresos"):
            col_map["total_ingresos"] = col
        elif col_lower in ("total_descuentos", "total descuentos"):
            col_map["total_descuentos"] = col
        elif col_lower in ("neto_pagar", "neto a pagar", "sueldo por pagar", "neto"):
            col_map["neto_pagar"] = col
        elif col_lower in ("neto_pagar_usd", "neto a pagar en usd", "neto_usd"):
            col_map["neto_pagar_usd"] = col

    columnas_ing = [c for c in df.columns if c.upper().startswith("ING_")]
    columnas_desc = [c for c in df.columns if c.upper().startswith("DESC_")]
    columnas_apor = [c for c in df.columns if c.upper().startswith("APOR_")]

    empleados = []
    for idx, row in df.iterrows():
        if pd.isna(row.get(col_map.get("numero_documento", ""), None)):
            continue

        doc_num = str(row.get(col_map.get("numero_documento", ""), ""))
        if doc_num.strip() in ("", "nan", "none", "nat"):
            continue

        empleado = {"_fila": idx + header_row + 2}

        for target, source in col_map.items():
            val = row.get(source)
            if pd.isna(val):
                empleado[target] = None if target != "dias_laborados" else 30
                if target in ("total_ingresos", "total_descuentos", "neto_pagar", "neto_pagar_usd"):
                    empleado[target] = 0.0
            else:
                if target in ("total_ingresos", "total_descuentos", "neto_pagar", "neto_pagar_usd", "dias_laborados"):
                    try:
                        empleado[target] = float(val)
                    except (ValueError, TypeError):
                        empleado[target] = 0.0
                else:
                    empleado[target] = str(val).strip()

        for col in columnas_ing:
            val = row.get(col)
            try:
                empleado[col] = float(val) if pd.notna(val) else 0.0
            except (ValueError, TypeError):
                empleado[col] = 0.0

        for col in columnas_desc:
            val = row.get(col)
            try:
                empleado[col] = float(val) if pd.notna(val) else 0.0
            except (ValueError, TypeError):
                empleado[col] = 0.0

        for col in columnas_apor:
            val = row.get(col)
            try:
                empleado[col] = float(val) if pd.notna(val) else 0.0
            except (ValueError, TypeError):
                empleado[col] = 0.0

        if "tipo_documento" not in col_map:
            empleado["tipo_documento"] = "01"

        if "total_ingresos" not in col_map:
            empleado["total_ingresos"] = sum(empleado.get(c, 0) for c in columnas_ing)
        if "total_descuentos" not in col_map:
            empleado["total_descuentos"] = sum(empleado.get(c, 0) for c in columnas_desc)
        if "neto_pagar" not in col_map:
            empleado["neto_pagar"] = empleado["total_ingresos"] - empleado["total_descuentos"]

        empleados.append(empleado)

    return {
        "empleados": empleados,
        "columnas_ing": columnas_ing,
        "columnas_desc": columnas_desc,
        "columnas_apor": columnas_apor,
    }
