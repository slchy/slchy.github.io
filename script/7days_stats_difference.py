import json
import os
import sys

def process_ingress_json_diff(input_filename, output_filename):
    try:
        if not os.path.exists(input_filename):
            raise FileNotFoundError(f"找不到输入的JSON file: '{input_filename}'")

        with open(input_filename, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"解析JSON失败，文件格式有误: {e}")

        if not isinstance(data, list):
            raise TypeError("输入的JSON数据根节点必须是列表（Array）格式。")
        
        if len(data) == 0:
            raise ValueError("【捕获异常】JSON数据为空（[]），无法执行做差操作。")
            
        if len(data) == 1:
            raise ValueError("【捕获异常】JSON数据仅包含1项，无法计算首尾两项的差值。")

        first_item = data[0]
        last_item = data[-1]

        diff_result = {
            "first_id": first_item.get("id"),
            "last_id": last_item.get("id"),
            "time_elapsed_seconds": last_item.get("timestamp", 0) - first_item.get("timestamp", 0),
            "stats_difference": {}
        }

        first_stats = first_item.get("stats", {})
        last_stats = last_item.get("stats", {})

        for key, last_val in last_stats.items():
            if key in first_stats:
                first_val = first_stats[key]
                if isinstance(last_val, (int, float)) and isinstance(first_val, (int, float)):
                    diff_result["stats_difference"][key] = last_val - first_val

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(diff_result, f, ensure_ascii=False, indent=4)
        
        print(f"【成功】差值数据已写入: '{output_filename}'")
        return True

    except (ValueError, TypeError, FileNotFoundError) as e:
        print(f"【工作流异常中断】: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"【未知系统错误】: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    process_ingress_json_diff("data/gamedata.json", "data/stats_difference.json")
