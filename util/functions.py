import yaml
import qubit_templates

# YAML 設定ファイルを読み込む関数
def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)

    flat_data = flatten_dict(config)
    global_data = {f"{k}": v for k, v in flat_data.items()}
    qubit_templates.__dict__.update(global_data)

    return global_data

# 再帰的にフラットな変数名で辞書を展開
def flatten_dict(d, parent_key="", sep="_"):
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items
