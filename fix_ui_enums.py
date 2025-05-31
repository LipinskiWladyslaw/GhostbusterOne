import re
import sys
from pathlib import Path

def fix_ui_enums(file_path: str, output_file: str):
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    code_fixed = code

    # Enum cleanup rules
    code_fixed = re.sub(r'QtCore\.Qt\.Qt::FocusPolicy::(\w+)', r'QtCore.Qt.\1', code_fixed)
    code_fixed = re.sub(r'QtCore\.Qt\.Qt::InputMethodHint::(\w+)', r'QtCore.Qt.\1', code_fixed)
    code_fixed = re.sub(r'QtCore\.Qt::FocusPolicy::(\w+)', r'QtCore.Qt.\1', code_fixed)
    code_fixed = re.sub(r'QtCore\.Qt::InputMethodHint::(\w+)', r'QtCore.Qt.\1', code_fixed)
    code_fixed = re.sub(r'QtCore\.Qt::AlignmentFlag::(\w+)', r'QtCore.Qt.\1', code_fixed)
    code_fixed = re.sub(r'QtCore\.Qt\.Qt::AlignmentFlag::(\w+)', r'QtCore.Qt.\1', code_fixed)
    code_fixed = re.sub(r'QtCore\.Qt::LayoutDirection::(\w+)', r'QtCore.Qt.\1', code_fixed)
    code_fixed = re.sub(r'QtCore\.Qt\.Qt::LayoutDirection::(\w+)', r'QtCore.Qt.\1', code_fixed)

    code_fixed = re.sub(r'QtCore\.Qt\.QFrame::Shape::(\w+)', r'QtWidgets.QFrame.\1', code_fixed)
    code_fixed = re.sub(r'QtCore\.Qt::QFrame::Shape::(\w+)', r'QtWidgets.QFrame.\1', code_fixed)
    code_fixed = re.sub(r'QFrame::Shape::(\w+)', r'QtWidgets.QFrame.\1', code_fixed)

    code_fixed = re.sub(r'QLineEdit::EchoMode::(\w+)', r'QtWidgets.QLineEdit.\1', code_fixed)
    code_fixed = re.sub(r'Qt::\w+::(\w+)', r'QtCore.Qt.\1', code_fixed)

    # Save with new output filename
    out_path = Path(output_file)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(code_fixed)
    print(f"✅ Fixed file saved as: {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_ui_enums.py <input_file.py> <output_file.py>")
    else:
        fix_ui_enums(sys.argv[1], sys.argv[2])
