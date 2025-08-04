import sys
import random
import itertools
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QHBoxLayout, QCheckBox, QLineEdit, QScrollArea, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt

class InventoryRow(QWidget):
    def __init__(self, key='', entries='', parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.key_edit = QLineEdit(key)
        self.key_edit.setMaximumWidth(40)
        self.entries_edit = QLineEdit(entries)
        self.entries_edit.setPlaceholderText("p/b/t/...")

        self.layout.addWidget(QLabel("Key:"))
        self.layout.addWidget(self.key_edit)
        self.layout.addWidget(QLabel("Entries:"))
        self.layout.addWidget(self.entries_edit)
        self.setLayout(self.layout)

    def get_data(self):
        return self.key_edit.text().strip(), self.entries_edit.text().strip()

class ConlangGeneratorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conlang Word Generator")

        self.exclude_repeats = True
        self.add_dictionary = True
        self.num_words = 100
        self.rule = 'CV(C)'
        self.inventories = {
            'C': 'p/b/t/',
            'V': 'a/e/i/',
        }

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.inventories_layout = QVBoxLayout()
        self.inventory_rows = []

        title_label = QLabel("Conlang Dictionary Generator")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 30px;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(title_label)

        inv_label = QLabel("Inventories")
        inv_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
            }
        """)
        instructions_label = QLabel("""
* Key and entries seperated by '/'
* '()' signifies optional use
""")
        instructions_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
            }
        """)
        main_layout.addWidget(inv_label)
        main_layout.addWidget(instructions_label)

        main_layout.addLayout(self.inventories_layout, stretch=1)

        for c, v in self.inventories.items():
            self.add_inventory_row(c, v)

        add_inv_btn = QPushButton("+ Add Inventory")
        add_inv_btn.clicked.connect(self.on_add_inventory)
        main_layout.addWidget(add_inv_btn)

        rule_layout = QHBoxLayout()
        rule_layout.addWidget(QLabel("Rule:"))
        self.rule_edit = QLineEdit(self.rule)
        rule_layout.addWidget(self.rule_edit)
        main_layout.addLayout(rule_layout)

        self.exclude_cb = QCheckBox("Exclude repeated words")
        self.exclude_cb.setChecked(True)
        self.exclude_cb.stateChanged.connect(self.on_option_changed)

        self.add_dict_cb = QCheckBox("Add English dictionary")
        self.add_dict_cb.setChecked(True)
        self.add_dict_cb.stateChanged.connect(self.on_option_changed)

        main_layout.addWidget(self.exclude_cb)
        main_layout.addWidget(self.add_dict_cb)

        generate_btn = QPushButton("Generate Words")
        generate_btn.clicked.connect(self.on_generate)
        main_layout.addWidget(generate_btn)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        main_layout.addWidget(self.output_box, stretch=2)

        self.setLayout(main_layout)
        self.resize(600, 600)

    def add_inventory_row(self, key='', entries=''):
        row = InventoryRow(key, entries)
        self.inventories_layout.addWidget(row)
        self.inventory_rows.append(row)

    def on_add_inventory(self):
        self.add_inventory_row()

    def on_option_changed(self):
        self.exclude_repeats = self.exclude_cb.isChecked()
        self.add_dictionary = self.add_dict_cb.isChecked()

    def parse_rule(self, rule:str):
        parsed = []
        i = 0
        while i < len(rule):
            if rule[i] == '(':
                end = rule.index(')', i)
                opt_part = list(rule[i+1:end])
                parsed.append((opt_part, True))
                i = end + 1
            else:
                parsed.append(([rule[i]], False))
                i += 1
        return parsed

    def generate_rule_variants(self, parsed):
        options = []
        for letters, optional in parsed:
            if optional:
                options.append([[], letters])
            else:
                options.append([letters])
        variants = []
        for combo in itertools.product(*options):
            variant = list(itertools.chain(*combo))
            if variant:
                variants.append(variant)
        return variants

    def words_for_pattern(self, pattern, inventories):
        pools = []
        for symbol in pattern:
            if symbol in inventories:
                pools.append(inventories[symbol])
            else:
                pools.append([symbol])
        for combo in itertools.product(*pools):
            yield "".join(combo)

    def on_generate(self):
        inventories = {}
        for row in self.inventory_rows:
            key, entries = row.get_data()
            if not key:
                continue
            normalized = entries.strip().strip('/')
            inventories[key] = [e for e in normalized.split('/') if e]

        if not inventories:
            QMessageBox.warning(self, "Input Error", "Please add at least one inventory with a key and entries.")
            return

        rule = self.rule_edit.text().strip()
        if not rule:
            QMessageBox.warning(self, "Input Error", "Please enter a valid rule.")
            return

        try:
            num_words = int(self.num_words)
        except:
            num_words = 100

        parsed_rule = self.parse_rule(rule)
        rule_variants = self.generate_rule_variants(parsed_rule)

        english_words = []
        if self.add_dictionary:
            try:
                with open("english_words.txt", "r", encoding="utf-8") as f:
                    english_words = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                QMessageBox.warning(self, "File Not Found", "english_words.txt file not found.")
                return
            english_words = english_words[:num_words]

        all_words = []
        seen_words = set()
        for pattern in rule_variants:
            for word in self.words_for_pattern(pattern, inventories):
                if self.exclude_repeats and word in seen_words:
                    continue
                all_words.append(word)
                seen_words.add(word)

        random.shuffle(all_words)
        clang_dictionary = all_words[:num_words]

        out_lines = []
        if self.add_dictionary:
            for new_word, eng_word in zip(clang_dictionary, english_words):
                out_lines.append(f"{new_word} - {eng_word}")
        else:
            out_lines = clang_dictionary

        self.output_box.setPlainText("\n".join(out_lines))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget {
            background: #121b2b;
        }
        QPushButton {
            font-size: 15px;
            font-weight: 600;
            padding: 10px;
            margin: 10px;
            border-radius: 17px;
            border: none;
            background: #232c3c;
        }
        QTextEdit {
            font-size: 15px;
            padding: 10px;
            margin: 10px;
            border-radius: 15px;
            background: #232c3c;
        }
        QCheckBox {
            font-size: 15px;
            margin: 10px;
            padding: 10px;
        }
        QCheckBox::indicator {
            padding: 15px;
            border-radius: 7px;
            border: none;
            background: #232c3c;
        }
        QCheckBox::indicator:checked {
            background: #eee;
        }
        QLineEdit {
            padding: 0px;
            margin: 5px;
            height: 30px;
            padding-left: 10px;
            padding-right: 10px;
            background: #232c3c;
            border-radius: 5px;
        }
        QLabel {
            margin: 10px;
        }
    """)
    window = ConlangGeneratorApp()
    window.show()
    sys.exit(app.exec())
