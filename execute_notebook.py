import json
import sys
import io

nb_path = r"d:\AI-Exam\SetA_25004500210146.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

global_env = {}
exec_count = 1

for cell_idx, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        code_text = "".join(cell["source"])
        print(f"Executing Code Cell {exec_count} (cell index {cell_idx})...")
        
        # Capture stdout
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        
        err = None
        try:
            exec(code_text, global_env)
        except Exception as e:
            err = str(e)
            print(f"ERROR: {e}")
        finally:
            sys.stdout = old_stdout
            
        captured_str = redirected_output.getvalue()
        
        cell["execution_count"] = exec_count
        cell["outputs"] = []
        if captured_str:
            lines = captured_str.splitlines(keepends=True)
            cell["outputs"].append({
                "name": "stdout",
                "output_type": "stream",
                "text": lines
            })
        if err:
            cell["outputs"].append({
                "ename": "Exception",
                "evalue": err,
                "output_type": "error",
                "traceback": [err]
            })
            print(f"Cell {exec_count} failed with: {err}")
        else:
            print(f"Cell {exec_count} executed successfully ({len(captured_str)} chars captured).")
            
        exec_count += 1

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print(f"\nAll {exec_count - 1} code cells executed and saved to {nb_path}!")
